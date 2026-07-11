#include "SCARWeaponAttachmentBlueprintLibrary.h"

#include "SCARPhonePreviewParity.h"

#include "Blueprint/UserWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/PanelWidget.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/LightComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "TimerManager.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "UObject/UnrealType.h"
#include "UObject/EnumProperty.h"

namespace SCARWeaponAttachmentInternal
{
	static constexpr TCHAR BodycamCharacterClassPath[] =
		TEXT("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter_C");

	static constexpr TCHAR ModdingWidgetClassPath[] =
		TEXT("/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding_C");

	static constexpr TCHAR ItemSlotEnumPath[] =
		TEXT("/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_ItemSlots.ENUM_ItemSlots");

	static constexpr TCHAR SightEnumPath[] =
		TEXT("/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_Sights.ENUM_Sights");

	static constexpr TCHAR LaserEnumPath[] =
		TEXT("/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_Laser.ENUM_Laser");

	static constexpr TCHAR MuzzleEnumPath[] =
		TEXT("/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_Muzzle.ENUM_Muzzle");

	static constexpr TCHAR GripEnumPath[] =
		TEXT("/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_LeftHand.ENUM_LeftHand");

	static FProperty* FindPropertyByHint(UStruct* Owner, const TCHAR* Hint)
	{
		if (!Owner || !Hint)
		{
			return nullptr;
		}

		for (TFieldIterator<FProperty> It(Owner); It; ++It)
		{
			if (It->GetName().Contains(Hint))
			{
				return *It;
			}
		}

		return nullptr;
	}

	static FProperty* FindExactProperty(UStruct* Owner, const FName PropertyName)
	{
		return Owner ? Owner->FindPropertyByName(PropertyName) : nullptr;
	}

	static uint8 ReadByteProperty(const FProperty* Property, const void* Container)
	{
		if (!Property || !Container)
		{
			return 0;
		}

		if (const FByteProperty* ByteProperty = CastField<FByteProperty>(Property))
		{
			return ByteProperty->GetPropertyValue_InContainer(Container);
		}

		if (const FEnumProperty* EnumProperty = CastField<FEnumProperty>(Property))
		{
			const void* ValuePtr = EnumProperty->ContainerPtrToValuePtr<void>(Container);
			if (const FNumericProperty* Underlying = EnumProperty->GetUnderlyingProperty())
			{
				return static_cast<uint8>(Underlying->GetSignedIntPropertyValue(ValuePtr));
			}
		}

		return 0;
	}

	static void WriteByteProperty(FProperty* Property, void* Container, const uint8 Value)
	{
		if (!Property || !Container)
		{
			return;
		}

		if (FByteProperty* ByteProperty = CastField<FByteProperty>(Property))
		{
			ByteProperty->SetPropertyValue_InContainer(Container, Value);
			return;
		}

		if (FEnumProperty* EnumProperty = CastField<FEnumProperty>(Property))
		{
			void* ValuePtr = EnumProperty->ContainerPtrToValuePtr<void>(Container);
			if (FNumericProperty* Underlying = EnumProperty->GetUnderlyingProperty())
			{
				Underlying->SetIntPropertyValue(ValuePtr, static_cast<int64>(Value));
			}
		}
	}

	static UEnum* LoadKitEnum(const TCHAR* Path)
	{
		return LoadObject<UEnum>(nullptr, Path);
	}

	static int32 GetValidEnumCount(UEnum* Enum)
	{
		if (!Enum)
		{
			return 1;
		}

		const int32 Count = Enum->NumEnums();
		if (Count <= 0)
		{
			return 1;
		}

		const FString LastName = Enum->GetNameStringByIndex(Count - 1);
		return LastName.EndsWith(TEXT("_MAX")) ? FMath::Max(1, Count - 1) : Count;
	}

	static FText GetEnumDisplayName(UEnum* Enum, const uint8 Value)
	{
		if (!Enum)
		{
			return FText::FromString(FString::FromInt(Value));
		}

		return Enum->GetDisplayNameTextByValue(static_cast<int64>(Value));
	}

	static const TCHAR* GetEnumPathForCategory(const ESCARWeaponAttachmentCategory Category)
	{
		switch (Category)
		{
		case ESCARWeaponAttachmentCategory::Sight:
			return SightEnumPath;
		case ESCARWeaponAttachmentCategory::Laser:
			return LaserEnumPath;
		case ESCARWeaponAttachmentCategory::Muzzle:
			return MuzzleEnumPath;
		case ESCARWeaponAttachmentCategory::Grip:
		default:
			return GripEnumPath;
		}
	}

	static FProperty* GetAttachmentField(FStructProperty* AttachmentsStruct, const ESCARWeaponAttachmentCategory Category)
	{
		if (!AttachmentsStruct)
		{
			return nullptr;
		}

		switch (Category)
		{
		case ESCARWeaponAttachmentCategory::Sight:
			return FindPropertyByHint(AttachmentsStruct->Struct, TEXT("Sight"));
		case ESCARWeaponAttachmentCategory::Laser:
			return FindPropertyByHint(AttachmentsStruct->Struct, TEXT("Laser"));
		case ESCARWeaponAttachmentCategory::Muzzle:
			return FindPropertyByHint(AttachmentsStruct->Struct, TEXT("Muzzle"));
		case ESCARWeaponAttachmentCategory::Grip:
		default:
			return FindPropertyByHint(AttachmentsStruct->Struct, TEXT("Grip"));
		}
	}

	static FName ResolveEquippedSlotPropertyName(AActor* Character)
	{
		const FProperty* EquippedWeaponProperty = FindExactProperty(Character->GetClass(), TEXT("EquippedWeapon"));
		if (!EquippedWeaponProperty)
		{
			return NAME_None;
		}

		const uint8 EquippedSlot = ReadByteProperty(EquippedWeaponProperty, Character);
		UEnum* SlotEnum = LoadKitEnum(ItemSlotEnumPath);
		if (!SlotEnum)
		{
			return NAME_None;
		}

		const FString SlotName = SlotEnum->GetNameStringByValue(static_cast<int64>(EquippedSlot));
		if (SlotName.Contains(TEXT("PRIMARY"), ESearchCase::IgnoreCase))
		{
			return TEXT("PrimarySlot");
		}
		if (SlotName.Contains(TEXT("SECONDARY"), ESearchCase::IgnoreCase))
		{
			return TEXT("SecondarySlot");
		}
		if (SlotName.Contains(TEXT("HAND"), ESearchCase::IgnoreCase))
		{
			return TEXT("HandsSlot");
		}
		if (SlotName.Contains(TEXT("MELEE"), ESearchCase::IgnoreCase))
		{
			return TEXT("MeleeSlot");
		}
		if (SlotName.Contains(TEXT("THROW"), ESearchCase::IgnoreCase))
		{
			return TEXT("ThrowableSlot");
		}

		return NAME_None;
	}

	static FStructProperty* GetEquippedSlotProperty(AActor* Character)
	{
		const FName SlotPropertyName = ResolveEquippedSlotPropertyName(Character);
		if (SlotPropertyName.IsNone())
		{
			return nullptr;
		}

		return CastField<FStructProperty>(FindExactProperty(Character->GetClass(), SlotPropertyName));
	}

	static AActor* GetSpawnedWeapon(AActor* Character)
	{
		if (FObjectProperty* SpawnedItemProperty = CastField<FObjectProperty>(
				FindExactProperty(Character->GetClass(), TEXT("SpawnedItem"))))
		{
			return Cast<AActor>(SpawnedItemProperty->GetObjectPropertyValue_InContainer(Character));
		}

		return nullptr;
	}

	static bool WeaponSupportsAttachments(AActor* Weapon)
	{
		if (!Weapon)
		{
			return false;
		}

		const FString ClassName = Weapon->GetClass()->GetName();
		if (ClassName.Contains(TEXT("EmptyHands"), ESearchCase::IgnoreCase)
			|| ClassName.Contains(TEXT("Granade"), ESearchCase::IgnoreCase))
		{
			return false;
		}

		return Weapon->FindFunction(FName(TEXT("SpawnAttachments"))) != nullptr;
	}

	static FStructProperty* GetItemDataProperty(UStruct* Owner)
	{
		if (FStructProperty* ItemData = CastField<FStructProperty>(FindPropertyByHint(Owner, TEXT("ItemData"))))
		{
			return ItemData;
		}

		return CastField<FStructProperty>(FindExactProperty(Owner, TEXT("ItemData")));
	}

	static FStructProperty* GetAttachmentsProperty(FStructProperty* ItemDataProperty)
	{
		if (!ItemDataProperty)
		{
			return nullptr;
		}

		return CastField<FStructProperty>(FindPropertyByHint(ItemDataProperty->Struct, TEXT("Attachments")));
	}

	static bool CopySlotToWeaponItemData(AActor* Character, FStructProperty* SlotProperty)
	{
		AActor* Weapon = GetSpawnedWeapon(Character);
		FStructProperty* WeaponItemDataProperty = GetItemDataProperty(Weapon ? Weapon->GetClass() : nullptr);
		if (!Weapon || !SlotProperty || !WeaponItemDataProperty)
		{
			return false;
		}

		const void* SlotData = SlotProperty->ContainerPtrToValuePtr<void>(Character);
		void* WeaponItemData = WeaponItemDataProperty->ContainerPtrToValuePtr<void>(Weapon);
		WeaponItemDataProperty->CopyCompleteValue(WeaponItemData, SlotData);
		return true;
	}

	static void CallSetWeaponAmmoData(AActor* Weapon, const bool bIsPickUp)
	{
		if (!Weapon)
		{
			return;
		}

		UFunction* Function = Weapon->FindFunction(FName(TEXT("SetWeaponAmmoData")));
		if (!Function)
		{
			return;
		}

		struct FSetWeaponAmmoDataParams
		{
			bool IsPickUp = false;
		};

		FSetWeaponAmmoDataParams Params;
		Params.IsPickUp = bIsPickUp;
		Weapon->ProcessEvent(Function, &Params);
	}

	static void CallSpawnAttachments(AActor* Weapon)
	{
		if (!Weapon)
		{
			return;
		}

		if (UFunction* Function = Weapon->FindFunction(FName(TEXT("SpawnAttachments"))))
		{
			Weapon->ProcessEvent(Function, nullptr);
		}
	}

	static constexpr TCHAR LaserBeamMeshPath[] =
		TEXT("/Game/BodycamFPSKIT/Blueprints/Attachments/Laser/Meshes/SM_LaserBeam.SM_LaserBeam");

	static constexpr TCHAR LaserBeamMaterialPath[] =
		TEXT("/Game/BodycamFPSKIT/Blueprints/Attachments/Laser/Materials/Lasers/MI_Laser.MI_Laser");

	static const FName ScarArLaserBeamComponentName(TEXT("SCAR_AR_LaserBeam"));
	static const FName ScarArLaserDotComponentName(TEXT("SCAR_AR_LaserDot"));
	static const FName ScarArFlashGlowComponentName(TEXT("SCAR_AR_FlashGlow"));

	static constexpr uint8 BodycamLaserNoneEnum = 0;
	static constexpr uint8 BodycamLaserFlashEnum = 3;
	static constexpr uint8 BodycamLaserBeamEnum = 4;

	static UStaticMesh* GetLaserBeamMesh()
	{
		static UStaticMesh* CachedMesh = LoadObject<UStaticMesh>(nullptr, LaserBeamMeshPath);
		return CachedMesh;
	}

	static UMaterialInterface* GetLaserBeamMaterial()
	{
		static UMaterialInterface* CachedMaterial = LoadObject<UMaterialInterface>(nullptr, LaserBeamMaterialPath);
		return CachedMaterial;
	}

	static constexpr TCHAR LaserAttachmentMeshPath[] =
		TEXT("/Game/BodycamFPSKIT/Demo/Meshes/SM_Laser.SM_Laser");

	static UStaticMesh* GetLaserAttachmentMesh()
	{
		static UStaticMesh* CachedMesh = LoadObject<UStaticMesh>(nullptr, LaserAttachmentMeshPath);
		return CachedMesh;
	}

	static void MirrorWeaponPrimitiveRendering(UPrimitiveComponent* Target, const UPrimitiveComponent* Template);

	static AActor* GetWeaponObjectRef(AActor* Weapon, const FName PropertyName);

	static void ConfigureARAttachmentPrimitive(
		UPrimitiveComponent* Component,
		const bool bVisible,
		const UPrimitiveComponent* RenderTemplate = nullptr)
	{
		if (!Component)
		{
			return;
		}

		Component->SetHiddenInGame(!bVisible);
		Component->SetVisibility(bVisible, true);
		Component->SetOwnerNoSee(false);
		Component->SetOnlyOwnerSee(false);
		Component->SetCastHiddenShadow(false);
		Component->SetBoundsScale(3.f);

		if (RenderTemplate)
		{
			if (Component->GetWorld() && SCARPhonePreviewParity::ShouldUseMobileCameraPath(Component->GetWorld()))
			{
				// Laser beam/dot must composite in world space over AR passthrough.
				Component->SetFirstPersonPrimitiveType(EFirstPersonPrimitiveType::WorldSpaceRepresentation);
				Component->SetOwnerNoSee(false);
				Component->SetOnlyOwnerSee(false);
				Component->SetCastHiddenShadow(false);
				Component->SetBoundsScale(4.f);
			}
			else
			{
				MirrorWeaponPrimitiveRendering(Component, RenderTemplate);
			}
			return;
		}

		if (Component->GetWorld() && SCARPhonePreviewParity::ShouldUseMobileCameraPath(Component->GetWorld()))
		{
			// Mobile AR composites world-space weapon geometry over passthrough.
			Component->SetFirstPersonPrimitiveType(EFirstPersonPrimitiveType::WorldSpaceRepresentation);
		}
		else
		{
			Component->SetFirstPersonPrimitiveType(EFirstPersonPrimitiveType::FirstPerson);
		}
	}

	static void ConfigureARAttachmentLight(ULightComponent* Light, const bool bVisible)
	{
		if (!Light)
		{
			return;
		}

		Light->SetHiddenInGame(!bVisible);
		Light->SetVisibility(bVisible);
		Light->SetCastShadows(false);

		constexpr float FlashlightIntensity = 30000.f;
		if (bVisible)
		{
			Light->SetIntensity(FlashlightIntensity);
			if (USpotLightComponent* SpotLight = Cast<USpotLightComponent>(Light))
			{
				SpotLight->SetAttenuationRadius(8000.f);
				SpotLight->SetInnerConeAngle(18.f);
				SpotLight->SetOuterConeAngle(42.f);
			}
		}
	}

	static uint8 ReadWeaponLaserEnum(AActor* Weapon)
	{
		if (!Weapon)
		{
			return 0;
		}

		FStructProperty* ItemDataProperty = GetItemDataProperty(Weapon->GetClass());
		if (!ItemDataProperty)
		{
			return 0;
		}

		const void* ItemData = ItemDataProperty->ContainerPtrToValuePtr<void>(Weapon);
		FStructProperty* AttachmentsProperty = GetAttachmentsProperty(ItemDataProperty);
		if (!AttachmentsProperty)
		{
			return 0;
		}

		const void* AttachmentsData = AttachmentsProperty->ContainerPtrToValuePtr<void>(ItemData);
		FProperty* LaserField = GetAttachmentField(AttachmentsProperty, ESCARWeaponAttachmentCategory::Laser);
		if (!LaserField)
		{
			return 0;
		}

		return ReadByteProperty(LaserField, AttachmentsData);
	}

	static USkeletalMeshComponent* FindWeaponItemMesh(AActor* Weapon)
	{
		if (!Weapon)
		{
			return nullptr;
		}

		TArray<USkeletalMeshComponent*> MeshComponents;
		Weapon->GetComponents<USkeletalMeshComponent>(MeshComponents);
		for (USkeletalMeshComponent* MeshComponent : MeshComponents)
		{
			if (MeshComponent && MeshComponent->GetName().Contains(TEXT("Item_Mesh")))
			{
				return MeshComponent;
			}
		}

		return MeshComponents.Num() > 0 ? MeshComponents[0] : nullptr;
	}

	static USceneComponent* FindWeaponLaserMount(AActor* Weapon)
	{
		if (!Weapon)
		{
			return nullptr;
		}

		TArray<USceneComponent*> SceneComponents;
		Weapon->GetComponents<USceneComponent>(SceneComponents);
		for (USceneComponent* SceneComponent : SceneComponents)
		{
			if (SceneComponent && SceneComponent->GetName().Equals(TEXT("Laser"), ESearchCase::IgnoreCase))
			{
				return SceneComponent;
			}
		}

		return nullptr;
	}

	static USceneComponent* FindLaserBeamOriginOnLaserRef(AActor* Weapon)
	{
		if (AActor* LaserRef = GetWeaponObjectRef(Weapon, TEXT("LaserRef")))
		{
			TInlineComponentArray<USceneComponent*> Components(LaserRef);
			for (USceneComponent* Component : Components)
			{
				if (Component && Component->GetName().Contains(TEXT("LaserBeam"), ESearchCase::IgnoreCase))
				{
					return Component;
				}
			}

			if (USceneComponent* RootComponent = LaserRef->GetRootComponent())
			{
				return RootComponent;
			}
		}

		return nullptr;
	}

	static USceneComponent* FindLaserAttachParent(AActor* Weapon)
	{
		if (USceneComponent* LaserMount = FindWeaponLaserMount(Weapon))
		{
			return LaserMount;
		}

		if (!Weapon)
		{
			return nullptr;
		}

		TInlineComponentArray<UStaticMeshComponent*> StaticMeshes(Weapon);
		for (UStaticMeshComponent* MeshComponent : StaticMeshes)
		{
			if (MeshComponent && MeshComponent->GetName().Contains(TEXT("LaserMesh")))
			{
				return MeshComponent;
			}
		}

		if (USkeletalMeshComponent* ItemMesh = FindWeaponItemMesh(Weapon))
		{
			return ItemMesh;
		}

		return Weapon->GetRootComponent();
	}

	static USceneComponent* FindArLaserBeamAttachParent(AActor* Weapon)
	{
		if (USceneComponent* BeamOrigin = FindLaserBeamOriginOnLaserRef(Weapon))
		{
			return BeamOrigin;
		}

		return FindLaserAttachParent(Weapon);
	}

	struct FLaserEmissionFrame
	{
		FVector Location = FVector::ZeroVector;
		FRotator Rotation = FRotator::ZeroRotator;
		bool bValid = false;
	};

	static FLaserEmissionFrame ResolveLaserEmissionFrame(AActor* Weapon)
	{
		FLaserEmissionFrame Frame;

		if (AActor* LaserRef = GetWeaponObjectRef(Weapon, TEXT("LaserRef")))
		{
			TInlineComponentArray<UStaticMeshComponent*> HousingMeshes(LaserRef);
			for (UStaticMeshComponent* HousingMesh : HousingMeshes)
			{
				if (!HousingMesh || !HousingMesh->GetName().Equals(TEXT("Mesh"), ESearchCase::IgnoreCase))
				{
					continue;
				}

				Frame.Location = HousingMesh->GetComponentLocation();
				Frame.Rotation = HousingMesh->GetComponentRotation();
				const FVector Forward = HousingMesh->GetForwardVector();
				if (const UStaticMesh* HousingAsset = HousingMesh->GetStaticMesh())
				{
					const FBox BoundingBox = HousingAsset->GetBoundingBox();
					Frame.Location += Forward * FMath::Max(BoundingBox.Max.X, 0.f);
				}

				Frame.bValid = true;
				return Frame;
			}

			if (USceneComponent* BeamOrigin = FindLaserBeamOriginOnLaserRef(Weapon))
			{
				Frame.Location = BeamOrigin->GetComponentLocation();
				Frame.Rotation = BeamOrigin->GetComponentRotation();
				Frame.bValid = true;
				return Frame;
			}
		}

		if (USceneComponent* Mount = FindLaserAttachParent(Weapon))
		{
			Frame.Location = Mount->GetComponentLocation();
			Frame.Rotation = Mount->GetComponentRotation();
			Frame.bValid = true;
		}

		return Frame;
	}

	static USceneComponent* ResolveLaserTraceSource(AActor* Weapon)
	{
		if (USceneComponent* BeamOrigin = FindLaserBeamOriginOnLaserRef(Weapon))
		{
			return BeamOrigin;
		}

		return FindLaserAttachParent(Weapon);
	}

	static float BoundsCorrectionFromMesh(const UStaticMeshComponent* MeshComponent, const float ScaleAxis)
	{
		if (!MeshComponent || !MeshComponent->GetStaticMesh())
		{
			return 0.f;
		}

		const FBox BoundingBox = MeshComponent->GetStaticMesh()->GetBoundingBox();
		return FMath::Max(-BoundingBox.Min.X, 0.f) * ScaleAxis;
	}

	static void ApplyArLaserBeamWorldTransform(
		UStaticMeshComponent* BeamComponent,
		const FLaserEmissionFrame& EmissionFrame,
		const float BeamDistance)
	{
		if (!BeamComponent || !EmissionFrame.bValid)
		{
			return;
		}

		float MeshLength = 100.f;
		if (const UStaticMesh* BeamMeshAsset = BeamComponent->GetStaticMesh())
		{
			const FBoxSphereBounds Bounds = BeamMeshAsset->GetBounds();
			MeshLength = FMath::Max(Bounds.BoxExtent.X * 2.f, 1.f);
		}

		const float ScaleAxis = BeamDistance / MeshLength;
		const FVector Forward = EmissionFrame.Rotation.Vector();
		const float ForwardPivotCorrection = BoundsCorrectionFromMesh(BeamComponent, ScaleAxis);
		const FVector EmissionStart = EmissionFrame.Location + Forward * ForwardPivotCorrection;

		BeamComponent->DetachFromComponent(FDetachmentTransformRules::KeepWorldTransform);
		BeamComponent->SetWorldLocation(EmissionStart);
		BeamComponent->SetWorldRotation(EmissionFrame.Rotation);
		BeamComponent->SetWorldScale3D(FVector(ScaleAxis, 1.f, 1.f));
	}

	static bool IsMobileArPassthroughWorld(const UWorld* World)
	{
		return World && SCARPhonePreviewParity::ShouldUseMobileCameraPath(World);
	}

	static void ConfigureMobileArOverlayPrimitive(UPrimitiveComponent* Component, const bool bVisible)
	{
		if (!Component)
		{
			return;
		}

		Component->SetHiddenInGame(!bVisible);
		Component->SetVisibility(bVisible, true);
		Component->SetOwnerNoSee(false);
		Component->SetOnlyOwnerSee(false);
		Component->SetCastHiddenShadow(false);
		Component->SetBoundsScale(8.f);
		Component->SetFirstPersonPrimitiveType(EFirstPersonPrimitiveType::WorldSpaceRepresentation);
	}

	static void MirrorWeaponPrimitiveRendering(UPrimitiveComponent* Target, const UPrimitiveComponent* Template)
	{
		if (!Target || !Template)
		{
			return;
		}

		Target->SetFirstPersonPrimitiveType(Template->FirstPersonPrimitiveType);
		Target->SetOwnerNoSee(false);
		Target->SetOnlyOwnerSee(false);
		Target->SetCastHiddenShadow(false);
		Target->SetBoundsScale(FMath::Max(Template->BoundsScale, 2.f));
	}

	static UStaticMeshComponent* FindNamedStaticMeshComponent(AActor* Owner, const FName ComponentName)
	{
		if (!Owner)
		{
			return nullptr;
		}

		TInlineComponentArray<UStaticMeshComponent*> MeshComponents(Owner);
		for (UStaticMeshComponent* MeshComponent : MeshComponents)
		{
			if (MeshComponent && MeshComponent->GetFName() == ComponentName)
			{
				return MeshComponent;
			}
		}

		return nullptr;
	}

	static UStaticMeshComponent* FindOrAddArStaticMeshComponent(
		AActor* Owner,
		const FName ComponentName,
		USceneComponent* AttachParent)
	{
		if (!Owner || !AttachParent)
		{
			return nullptr;
		}

		if (UStaticMeshComponent* Existing = FindNamedStaticMeshComponent(Owner, ComponentName))
		{
			if (Existing->GetAttachParent() != AttachParent)
			{
				Existing->AttachToComponent(AttachParent, FAttachmentTransformRules::SnapToTargetIncludingScale);
			}
			return Existing;
		}

		UStaticMeshComponent* NewComponent = NewObject<UStaticMeshComponent>(
			Owner,
			UStaticMeshComponent::StaticClass(),
			ComponentName,
			RF_Transient);
		if (!NewComponent)
		{
			return nullptr;
		}

		NewComponent->SetupAttachment(AttachParent);
		NewComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		NewComponent->SetGenerateOverlapEvents(false);
		Owner->AddInstanceComponent(NewComponent);
		NewComponent->RegisterComponent();
		return NewComponent;
	}

	static AActor* GetWeaponObjectRef(AActor* Weapon, const FName PropertyName)
	{
		if (!Weapon)
		{
			return nullptr;
		}

		if (FObjectProperty* Property = CastField<FObjectProperty>(Weapon->GetClass()->FindPropertyByName(PropertyName)))
		{
			return Cast<AActor>(Property->GetObjectPropertyValue_InContainer(Weapon));
		}

		return nullptr;
	}

	static bool TraceLaserBeamHitFromFrame(
		AActor* Weapon,
		const FLaserEmissionFrame& EmissionFrame,
		FVector& OutHitLocation,
		float& OutDistance)
	{
		OutHitLocation = FVector::ZeroVector;
		OutDistance = 5000.f;

		if (!Weapon || !EmissionFrame.bValid)
		{
			return false;
		}

		UWorld* World = Weapon->GetWorld();
		if (!World)
		{
			return false;
		}

		const FVector Start = EmissionFrame.Location;
		const FVector Forward = EmissionFrame.Rotation.Vector();
		const FVector End = Start + Forward * 10000.f;

		FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(ScarLaserBeamTrace), true, Weapon);
		QueryParams.AddIgnoredActor(Weapon);

		if (AActor* LaserRef = GetWeaponObjectRef(Weapon, TEXT("LaserRef")))
		{
			QueryParams.AddIgnoredActor(LaserRef);
		}

		FHitResult Hit;
		if (World->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, QueryParams))
		{
			OutHitLocation = Hit.ImpactPoint;
			OutDistance = FMath::Clamp(FVector::Dist(Start, Hit.ImpactPoint), 50.f, 10000.f);
			return true;
		}

		OutHitLocation = End;
		OutDistance = 5000.f;
		return false;
	}

	static bool TraceLaserBeamHit(
		AActor* Weapon,
		const USceneComponent* TraceSource,
		FVector& OutHitLocation,
		float& OutDistance)
	{
		if (!TraceSource)
		{
			return TraceLaserBeamHitFromFrame(Weapon, ResolveLaserEmissionFrame(Weapon), OutHitLocation, OutDistance);
		}

		FLaserEmissionFrame Frame;
		Frame.Location = TraceSource->GetComponentLocation();
		Frame.Rotation = TraceSource->GetComponentRotation();
		Frame.bValid = true;
		return TraceLaserBeamHitFromFrame(Weapon, Frame, OutHitLocation, OutDistance);
	}

	static float TraceLaserBeamDistance(AActor* Weapon, const USceneComponent* AttachParent)
	{
		FVector HitLocation = FVector::ZeroVector;
		float Distance = 5000.f;
		TraceLaserBeamHit(Weapon, AttachParent, HitLocation, Distance);
		return Distance;
	}

	static void ConfigureBoostedLaserMaterial(UStaticMeshComponent* MeshComponent)
	{
		if (!MeshComponent)
		{
			return;
		}

		UMaterialInterface* BaseMaterial = GetLaserBeamMaterial();
		if (!BaseMaterial)
		{
			return;
		}

		UMaterialInstanceDynamic* DynamicMaterial = UMaterialInstanceDynamic::Create(BaseMaterial, MeshComponent);
		if (!DynamicMaterial)
		{
			return;
		}

		DynamicMaterial->SetVectorParameterValue(TEXT("EmissiveColor"), FLinearColor(50.f, 0.f, 0.f));
		DynamicMaterial->SetScalarParameterValue(TEXT("EmissiveStrength"), 250.f);
		MeshComponent->SetMaterial(0, DynamicMaterial);
	}

	static void EnsureArLaserBeamOnWeapon(AActor* Weapon, const bool bVisible, const UPrimitiveComponent* RenderTemplate)
	{
		USceneComponent* AttachParent = FindArLaserBeamAttachParent(Weapon);
		const FLaserEmissionFrame EmissionFrame = ResolveLaserEmissionFrame(Weapon);
		if (!AttachParent || !EmissionFrame.bValid)
		{
			return;
		}

		UStaticMeshComponent* BeamComponent =
			FindOrAddArStaticMeshComponent(Weapon, ScarArLaserBeamComponentName, AttachParent);
		if (!BeamComponent)
		{
			return;
		}

		if (UStaticMesh* BeamMesh = GetLaserBeamMesh())
		{
			BeamComponent->SetStaticMesh(BeamMesh);
		}

		ConfigureBoostedLaserMaterial(BeamComponent);

		const bool bMobileAr = IsMobileArPassthroughWorld(Weapon->GetWorld());
		if (bMobileAr)
		{
			ConfigureMobileArOverlayPrimitive(BeamComponent, bVisible);
		}
		else
		{
			if (RenderTemplate)
			{
				MirrorWeaponPrimitiveRendering(BeamComponent, RenderTemplate);
			}
			ConfigureARAttachmentPrimitive(BeamComponent, bVisible);
		}

		if (!bVisible)
		{
			return;
		}

		float BeamDistance = 5000.f;
		FVector HitLocation = FVector::ZeroVector;
		TraceLaserBeamHitFromFrame(Weapon, EmissionFrame, HitLocation, BeamDistance);

		const bool bAttachedToBodycamBeamOrigin = FindLaserBeamOriginOnLaserRef(Weapon) != nullptr;
		if (bMobileAr || !bAttachedToBodycamBeamOrigin)
		{
			ApplyArLaserBeamWorldTransform(BeamComponent, EmissionFrame, BeamDistance);
		}
		else
		{
			BeamComponent->AttachToComponent(
				AttachParent,
				FAttachmentTransformRules::SnapToTargetIncludingScale);

			float MeshLength = 100.f;
			if (const UStaticMesh* BeamMeshAsset = BeamComponent->GetStaticMesh())
			{
				const FBoxSphereBounds Bounds = BeamMeshAsset->GetBounds();
				MeshLength = FMath::Max(Bounds.BoxExtent.X * 2.f, 1.f);
			}

			const float ScaleAxis = BeamDistance / MeshLength;
			const float ForwardOffset = BoundsCorrectionFromMesh(BeamComponent, 1.f);
			BeamComponent->SetRelativeLocation(FVector(ForwardOffset, 0.f, 0.f));
			BeamComponent->SetRelativeRotation(FRotator::ZeroRotator);
			BeamComponent->SetRelativeScale3D(FVector(ScaleAxis, 1.f, 1.f));
		}
	}

	static void EnsureArLaserDotOnWeapon(AActor* Weapon, const bool bVisible)
	{
		if (!Weapon)
		{
			return;
		}

		USceneComponent* AttachParent = Weapon->GetRootComponent();
		if (!AttachParent)
		{
			return;
		}

		UStaticMeshComponent* DotComponent =
			FindOrAddArStaticMeshComponent(Weapon, ScarArLaserDotComponentName, AttachParent);
		if (!DotComponent)
		{
			return;
		}

		if (UStaticMesh* BeamMesh = GetLaserBeamMesh())
		{
			DotComponent->SetStaticMesh(BeamMesh);
		}

		ConfigureBoostedLaserMaterial(DotComponent);
		ConfigureMobileArOverlayPrimitive(DotComponent, bVisible);

		if (!bVisible)
		{
			return;
		}

		const FLaserEmissionFrame EmissionFrame = ResolveLaserEmissionFrame(Weapon);
		if (!EmissionFrame.bValid)
		{
			return;
		}

		FVector HitLocation = FVector::ZeroVector;
		float BeamDistance = 5000.f;
		TraceLaserBeamHitFromFrame(Weapon, EmissionFrame, HitLocation, BeamDistance);

		DotComponent->DetachFromComponent(FDetachmentTransformRules::KeepWorldTransform);
		DotComponent->SetWorldLocation(HitLocation);
		DotComponent->SetWorldRotation(FRotator::ZeroRotator);
		DotComponent->SetWorldScale3D(FVector(0.08f));
	}

	static void EnsureArFlashGlowOnWeapon(AActor* Weapon, const bool bVisible, const UPrimitiveComponent* RenderTemplate)
	{
		USceneComponent* AttachParent = FindLaserAttachParent(Weapon);
		if (!AttachParent)
		{
			return;
		}

		UStaticMeshComponent* GlowComponent =
			FindOrAddArStaticMeshComponent(Weapon, ScarArFlashGlowComponentName, AttachParent);
		if (!GlowComponent)
		{
			return;
		}

		if (UStaticMesh* HousingMesh = GetLaserAttachmentMesh())
		{
			GlowComponent->SetStaticMesh(HousingMesh);
		}

		if (UMaterialInstanceDynamic* DynamicMaterial = UMaterialInstanceDynamic::Create(
				GetLaserBeamMaterial(),
				GlowComponent))
		{
			DynamicMaterial->SetVectorParameterValue(TEXT("EmissiveColor"), FLinearColor(30.f, 28.f, 20.f));
			DynamicMaterial->SetScalarParameterValue(TEXT("EmissiveStrength"), 80.f);
			GlowComponent->SetMaterial(0, DynamicMaterial);
		}

		if (Weapon->GetWorld() && IsMobileArPassthroughWorld(Weapon->GetWorld()))
		{
			ConfigureMobileArOverlayPrimitive(GlowComponent, bVisible);
		}
		else
		{
			MirrorWeaponPrimitiveRendering(GlowComponent, RenderTemplate);
			ConfigureARAttachmentPrimitive(GlowComponent, bVisible);
		}
		if (bVisible)
		{
			GlowComponent->SetRelativeScale3D(FVector(1.2f));
		}
	}

	static AActor* ResolveBodycamCharacter(APawn* Pawn)
	{
		if (!Pawn)
		{
			return nullptr;
		}

		static UClass* BodycamCharacterClass = nullptr;
		if (!BodycamCharacterClass)
		{
			BodycamCharacterClass = LoadClass<AActor>(nullptr, BodycamCharacterClassPath);
		}

		return BodycamCharacterClass && Pawn->IsA(BodycamCharacterClass) ? Pawn : nullptr;
	}

	static uint8 ResolveAttachmentLaserEnum(AActor* Character, AActor* Weapon)
	{
		uint8 AttachmentLaserEnum = ReadWeaponLaserEnum(Weapon);
		if (AttachmentLaserEnum == BodycamLaserNoneEnum && Character)
		{
			FStructProperty* SlotProperty = GetEquippedSlotProperty(Character);
			if (SlotProperty)
			{
				const void* SlotData = SlotProperty->ContainerPtrToValuePtr<void>(Character);
				FStructProperty* AttachmentsProperty = GetAttachmentsProperty(SlotProperty);
				if (AttachmentsProperty)
				{
					const void* AttachmentsData = AttachmentsProperty->ContainerPtrToValuePtr<void>(SlotData);
					if (FProperty* LaserField = GetAttachmentField(AttachmentsProperty, ESCARWeaponAttachmentCategory::Laser))
					{
						AttachmentLaserEnum = ReadByteProperty(LaserField, AttachmentsData);
					}
				}
			}
		}

		if (AttachmentLaserEnum == BodycamLaserNoneEnum && GetWeaponObjectRef(Weapon, TEXT("LaserRef")))
		{
			AttachmentLaserEnum = BodycamLaserBeamEnum;
		}

		return AttachmentLaserEnum;
	}

	static void InvokeLaserDotTrace(AActor* LaserActor)
	{
		if (!LaserActor)
		{
			return;
		}

		if (UFunction* TraceFunction = LaserActor->FindFunction(FName(TEXT("LaserDotTrace"))))
		{
			LaserActor->ProcessEvent(TraceFunction, nullptr);
		}
	}

	static void InvokeLaserActiveReplication(AActor* LaserActor)
	{
		if (!LaserActor)
		{
			return;
		}

		if (UFunction* OnRepFunction = LaserActor->FindFunction(FName(TEXT("OnRep_LaserActive"))))
		{
			LaserActor->ProcessEvent(OnRepFunction, nullptr);
		}
	}

	static void SetLaserActorActiveFlag(AActor* LaserActor, const bool bActive)
	{
		if (!LaserActor)
		{
			return;
		}

		if (FBoolProperty* LaserActiveProperty = CastField<FBoolProperty>(
				FindExactProperty(LaserActor->GetClass(), TEXT("LaserActive"))))
		{
			LaserActiveProperty->SetPropertyValue_InContainer(LaserActor, bActive);
		}

		InvokeLaserActiveReplication(LaserActor);
	}

	static void HideScarArOverlayComponents(AActor* Weapon)
	{
		if (!Weapon)
		{
			return;
		}

		for (const FName ComponentName : { ScarArLaserBeamComponentName, ScarArLaserDotComponentName, ScarArFlashGlowComponentName })
		{
			if (UStaticMeshComponent* Overlay = FindNamedStaticMeshComponent(Weapon, ComponentName))
			{
				Overlay->SetHiddenInGame(true);
				Overlay->SetVisibility(false, true);
			}
		}
	}

	static void DestroyOrphanBodycamLaserActors(AActor* Weapon, AActor* ActiveLaserRef)
	{
		if (!Weapon)
		{
			return;
		}

		TArray<AActor*> AttachedActors;
		Weapon->GetAttachedActors(AttachedActors, true, true);
		for (AActor* AttachedActor : AttachedActors)
		{
			if (!AttachedActor || AttachedActor == ActiveLaserRef || AttachedActor == Weapon)
			{
				continue;
			}

			if (AttachedActor->GetClass()->GetName().Contains(TEXT("BP_Laser")))
			{
				AttachedActor->Destroy();
			}
		}
	}

	static void EnsureWeaponLaserActorRefs(AActor* Weapon, const uint8 AttachmentLaserEnum)
	{
		if (!Weapon || AttachmentLaserEnum == BodycamLaserNoneEnum)
		{
			return;
		}

		AActor* LaserRef = GetWeaponObjectRef(Weapon, TEXT("LaserRef"));
		const bool bNeedsRespawn = !LaserRef || !IsValid(LaserRef) || LaserRef->IsActorBeingDestroyed();
		if (!bNeedsRespawn)
		{
			return;
		}

		static TMap<TWeakObjectPtr<AActor>, double> LastRespawnAttemptSeconds;
		const UWorld* World = Weapon->GetWorld();
		const double Now = World ? static_cast<double>(World->GetTimeSeconds()) : 0.0;
		if (const double* LastAttempt = LastRespawnAttemptSeconds.Find(Weapon))
		{
			if (Now - *LastAttempt < 0.25)
			{
				return;
			}
		}

		LastRespawnAttemptSeconds.Add(Weapon, Now);
		CallSpawnAttachments(Weapon);
	}

	static void ForceShowBodycamLaserVisuals(
		AActor* LaserActor,
		const bool bWantLaser,
		const bool bWantFlash,
		const UPrimitiveComponent* RenderTemplate,
		const bool bSuppressBeamForMobileOverlay)
	{
		if (!LaserActor)
		{
			return;
		}

		LaserActor->SetActorHiddenInGame(false);
		LaserActor->SetActorTickEnabled(bWantLaser || bWantFlash);

		if (FBoolProperty* UseIRLaserProperty = CastField<FBoolProperty>(
				FindExactProperty(LaserActor->GetClass(), TEXT("UseIRLaser"))))
		{
			UseIRLaserProperty->SetPropertyValue_InContainer(LaserActor, false);
		}

		SetLaserActorActiveFlag(LaserActor, bWantLaser);

		TInlineComponentArray<UPrimitiveComponent*> Primitives(LaserActor);
		for (UPrimitiveComponent* Component : Primitives)
		{
			if (!Component)
			{
				continue;
			}

			const FString Name = Component->GetName();
			const bool bIsBeam = Name.Contains(TEXT("Beam"), ESearchCase::IgnoreCase)
				|| Name.Contains(TEXT("Dot"), ESearchCase::IgnoreCase)
				|| Name.Contains(TEXT("Decal"), ESearchCase::IgnoreCase);
			const bool bIsFlashMesh = Name.Contains(TEXT("Flash"), ESearchCase::IgnoreCase)
				&& !Name.Contains(TEXT("Light"), ESearchCase::IgnoreCase);
			const bool bIsLaserHousingMesh = Name.Equals(TEXT("Mesh"), ESearchCase::IgnoreCase);

			if (bIsBeam)
			{
				if (bSuppressBeamForMobileOverlay && bWantLaser)
				{
					Component->SetHiddenInGame(true);
					Component->SetVisibility(false, true);
				}
				else
				{
					ConfigureARAttachmentPrimitive(Component, bWantLaser, RenderTemplate);
				}
			}
			else if (bIsFlashMesh)
			{
				ConfigureARAttachmentPrimitive(Component, bWantFlash, RenderTemplate);
			}
			else if (bIsLaserHousingMesh && (bWantLaser || bWantFlash))
			{
				ConfigureARAttachmentPrimitive(Component, true, RenderTemplate);
			}
		}

		TInlineComponentArray<ULightComponent*> Lights(LaserActor);
		for (ULightComponent* Light : Lights)
		{
			ConfigureARAttachmentLight(Light, bWantFlash);
		}

		if (bWantLaser)
		{
			InvokeLaserDotTrace(LaserActor);
			SetLaserActorActiveFlag(LaserActor, true);
			InvokeLaserDotTrace(LaserActor);
		}
	}

	static bool IsLaserFlashPrimitive(const UPrimitiveComponent* Component)
	{
		if (!Component)
		{
			return false;
		}

		const FString Name = Component->GetName();
		return Name.Contains(TEXT("Laser"), ESearchCase::IgnoreCase)
			|| Name.Contains(TEXT("Flash"), ESearchCase::IgnoreCase)
			|| Name.Contains(TEXT("Beam"), ESearchCase::IgnoreCase)
			|| Name.Contains(TEXT("Dot"), ESearchCase::IgnoreCase)
			|| Name.Contains(TEXT("Decal"), ESearchCase::IgnoreCase);
	}

	static void SyncWeaponIntegratedLaserMesh(AActor* Weapon, const uint8 AttachmentLaserEnum)
	{
		if (!Weapon || AttachmentLaserEnum == BodycamLaserNoneEnum)
		{
			return;
		}

		UStaticMesh* AttachmentMesh = GetLaserAttachmentMesh();

		TInlineComponentArray<UStaticMeshComponent*> MeshComponents(Weapon);
		for (UStaticMeshComponent* MeshComponent : MeshComponents)
		{
			if (!MeshComponent || !MeshComponent->GetName().Contains(TEXT("LaserMesh"), ESearchCase::IgnoreCase))
			{
				continue;
			}

			if (AttachmentMesh && MeshComponent->GetStaticMesh() != AttachmentMesh)
			{
				MeshComponent->SetStaticMesh(AttachmentMesh);
			}

			ConfigureARAttachmentPrimitive(MeshComponent, true);
		}
	}

	static void SyncWeaponLaserFlashEffects(AActor* Character, AActor* Weapon)
	{
		if (!Weapon)
		{
			return;
		}

		const uint8 AttachmentLaserEnum = ResolveAttachmentLaserEnum(Character, Weapon);
		const bool bWantFlash = AttachmentLaserEnum == BodycamLaserFlashEnum;
		const bool bWantLaser = AttachmentLaserEnum == BodycamLaserBeamEnum;

		USkeletalMeshComponent* ItemMesh = FindWeaponItemMesh(Weapon);
		const UPrimitiveComponent* RenderTemplate = ItemMesh ? static_cast<UPrimitiveComponent*>(ItemMesh) : nullptr;

		const bool bMobileAr = IsMobileArPassthroughWorld(Weapon->GetWorld());
		const bool bSuppressBodycamBeam = bMobileAr && bWantLaser;

		if (AttachmentLaserEnum == BodycamLaserNoneEnum)
		{
			HideScarArOverlayComponents(Weapon);
			return;
		}

		EnsureWeaponLaserActorRefs(Weapon, AttachmentLaserEnum);
		SyncWeaponIntegratedLaserMesh(Weapon, AttachmentLaserEnum);

		if (AActor* LaserRef = GetWeaponObjectRef(Weapon, TEXT("LaserRef")))
		{
			ForceShowBodycamLaserVisuals(LaserRef, bWantLaser, bWantFlash, RenderTemplate, bSuppressBodycamBeam);
		}

		if (AActor* AkimboLaserRef = GetWeaponObjectRef(Weapon, TEXT("AkimboLaserRef")))
		{
			ForceShowBodycamLaserVisuals(AkimboLaserRef, bWantLaser, bWantFlash, RenderTemplate, bSuppressBodycamBeam);
		}

		if (bMobileAr)
		{
			EnsureArLaserBeamOnWeapon(Weapon, bWantLaser, RenderTemplate);
			EnsureArLaserDotOnWeapon(Weapon, bWantLaser);
			EnsureArFlashGlowOnWeapon(Weapon, bWantFlash, RenderTemplate);
		}
	}

	static void ApplyARAttachmentEffectsToActor(AActor* Actor, const bool bForceVisible)
	{
		if (!Actor)
		{
			return;
		}

		Actor->SetActorHiddenInGame(false);

		TInlineComponentArray<UPrimitiveComponent*> Primitives(Actor);
		for (UPrimitiveComponent* Component : Primitives)
		{
			if (IsLaserFlashPrimitive(Component))
			{
				ConfigureARAttachmentPrimitive(Component, bForceVisible);
			}
		}

		TInlineComponentArray<ULightComponent*> Lights(Actor);
		for (ULightComponent* Light : Lights)
		{
			ConfigureARAttachmentLight(Light, bForceVisible);
		}

		TArray<AActor*> AttachedActors;
		Actor->GetAttachedActors(AttachedActors, true, true);
		for (AActor* AttachedActor : AttachedActors)
		{
			ApplyARAttachmentEffectsToActor(AttachedActor, bForceVisible);
		}
	}

	static void EnsureWeaponLaserFlashEffectsInternal(AActor* Character, AActor* Weapon)
	{
		SyncWeaponLaserFlashEffects(Character, Weapon);
	}

	static void EnsureWeaponLaserFlashEffectsDeferred(AActor* Character, AActor* Weapon)
	{
		EnsureWeaponLaserFlashEffectsInternal(Character, Weapon);

		UWorld* World = Weapon ? Weapon->GetWorld() : nullptr;
		if (!World)
		{
			return;
		}

		TWeakObjectPtr<AActor> WeakCharacter(Character);
		TWeakObjectPtr<AActor> WeakWeapon(Weapon);
		World->GetTimerManager().SetTimerForNextTick([WeakCharacter, WeakWeapon]()
		{
			if (WeakWeapon.IsValid())
			{
				EnsureWeaponLaserFlashEffectsInternal(WeakCharacter.Get(), WeakWeapon.Get());
			}
		});
	}

	static bool ReadAttachmentValue(
		AActor* Character,
		const ESCARWeaponAttachmentCategory Category,
		uint8& OutValue)
	{
		FStructProperty* SlotProperty = GetEquippedSlotProperty(Character);
		if (!SlotProperty)
		{
			return false;
		}

		const void* SlotData = SlotProperty->ContainerPtrToValuePtr<void>(Character);
		FStructProperty* AttachmentsProperty = GetAttachmentsProperty(SlotProperty);
		if (!AttachmentsProperty)
		{
			return false;
		}

		const void* AttachmentsData = AttachmentsProperty->ContainerPtrToValuePtr<void>(SlotData);
		FProperty* Field = GetAttachmentField(AttachmentsProperty, Category);
		if (!Field)
		{
			return false;
		}

		OutValue = ReadByteProperty(Field, AttachmentsData);
		return true;
	}

	static bool WriteAttachmentValue(
		AActor* Character,
		const ESCARWeaponAttachmentCategory Category,
		const uint8 Value)
	{
		FStructProperty* SlotProperty = GetEquippedSlotProperty(Character);
		if (!SlotProperty)
		{
			return false;
		}

		void* SlotData = SlotProperty->ContainerPtrToValuePtr<void>(Character);
		FStructProperty* AttachmentsProperty = GetAttachmentsProperty(SlotProperty);
		if (!AttachmentsProperty)
		{
			return false;
		}

		void* AttachmentsData = AttachmentsProperty->ContainerPtrToValuePtr<void>(SlotData);
		FProperty* Field = GetAttachmentField(AttachmentsProperty, Category);
		if (!Field)
		{
			return false;
		}

		WriteByteProperty(Field, AttachmentsData, Value);
		return true;
	}

	static void ForEachWidgetRecursive(UWidget* Widget, TFunctionRef<void(UWidget*)> Callback)
	{
		if (!Widget)
		{
			return;
		}

		Callback(Widget);

		if (UPanelWidget* Panel = Cast<UPanelWidget>(Widget))
		{
			const int32 ChildCount = Panel->GetChildrenCount();
			for (int32 ChildIndex = 0; ChildIndex < ChildCount; ++ChildIndex)
			{
				ForEachWidgetRecursive(Panel->GetChildAt(ChildIndex), Callback);
			}
		}
	}

	static void HideWeaponModdingInspectHint(UUserWidget* ModdingWidget)
	{
		if (!ModdingWidget || !ModdingWidget->WidgetTree || !ModdingWidget->WidgetTree->RootWidget)
		{
			return;
		}

		ForEachWidgetRecursive(ModdingWidget->WidgetTree->RootWidget, [](UWidget* Widget)
		{
			UTextBlock* TextBlock = Cast<UTextBlock>(Widget);
			if (!TextBlock)
			{
				return;
			}

			const FString Text = TextBlock->GetText().ToString();
			if (Text.Contains(TEXT("INSPECT"), ESearchCase::IgnoreCase)
				|| Text.Contains(TEXT("PRESS"), ESearchCase::IgnoreCase))
			{
				TextBlock->SetVisibility(ESlateVisibility::Collapsed);
			}
		});
	}

	static UHorizontalBox* FindWidestHorizontalBox(UUserWidget* ModdingWidget)
	{
		if (!ModdingWidget || !ModdingWidget->WidgetTree || !ModdingWidget->WidgetTree->RootWidget)
		{
			return nullptr;
		}

		UHorizontalBox* WidestBox = nullptr;
		float WidestWidth = 0.f;

		ForEachWidgetRecursive(ModdingWidget->WidgetTree->RootWidget, [&WidestBox, &WidestWidth](UWidget* Widget)
		{
			UHorizontalBox* HorizontalBox = Cast<UHorizontalBox>(Widget);
			if (!HorizontalBox)
			{
				return;
			}

			HorizontalBox->ForceLayoutPrepass();
			const float DesiredWidth = HorizontalBox->GetDesiredSize().X;
			if (DesiredWidth > WidestWidth)
			{
				WidestWidth = DesiredWidth;
				WidestBox = HorizontalBox;
			}
		});

		return WidestBox;
	}

	static void ResetWidgetRenderTransform(UWidget* Widget)
	{
		if (!Widget)
		{
			return;
		}

		Widget->SetRenderTransformPivot(FVector2D(0.5f, 0.5f));
		Widget->SetRenderTranslation(FVector2D::ZeroVector);
		Widget->SetRenderScale(FVector2D(1.f, 1.f));
	}

	static UWidget* FindAttachmentPanelRoot(UUserWidget* ModdingWidget)
	{
		if (!ModdingWidget)
		{
			return nullptr;
		}

		UWidget* SightWidget = ModdingWidget->GetWidgetFromName(TEXT("Sight"));
		if (!SightWidget)
		{
			return FindWidestHorizontalBox(ModdingWidget);
		}

		UWidget* Parent = SightWidget->GetParent();
		if (!Parent)
		{
			return SightWidget;
		}

		// Typical Bodycam layout: VerticalBox -> [label HorizontalBox, combo HorizontalBox].
		if (UWidget* GrandParent = Parent->GetParent())
		{
			if (Cast<UVerticalBox>(GrandParent))
			{
				return GrandParent;
			}

			// Column layout: HorizontalBox -> VerticalBox (label + combo) per attachment.
			if (Cast<UVerticalBox>(Parent))
			{
				return GrandParent;
			}
		}

		return Parent;
	}

	static void ResetAllAttachmentRenderTransforms(UUserWidget* ModdingWidget)
	{
		if (!ModdingWidget || !ModdingWidget->WidgetTree || !ModdingWidget->WidgetTree->RootWidget)
		{
			return;
		}

		ForEachWidgetRecursive(ModdingWidget->WidgetTree->RootWidget, [](UWidget* Widget)
		{
			if (Cast<UHorizontalBox>(Widget) || Cast<UVerticalBox>(Widget))
			{
				ResetWidgetRenderTransform(Widget);
			}
		});

		ResetWidgetRenderTransform(ModdingWidget);
	}

	static void MakeModdingMenuClickThroughEmptyAreas(UUserWidget* ModdingWidget)
	{
		if (!ModdingWidget || !ModdingWidget->WidgetTree || !ModdingWidget->WidgetTree->RootWidget)
		{
			return;
		}

		// Let touches pass through empty overlay space so the Attachments button stays tappable.
		ModdingWidget->WidgetTree->RootWidget->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
	}

	static bool IsWeaponModdingMenuShown(UUserWidget* ModdingWidget)
	{
		if (!ModdingWidget)
		{
			return false;
		}

		if (ModdingWidget->IsInViewport() || ModdingWidget->GetParent() != nullptr)
		{
			return true;
		}

		const ESlateVisibility Visibility = ModdingWidget->GetVisibility();
		return Visibility != ESlateVisibility::Collapsed && Visibility != ESlateVisibility::Hidden;
	}

	static void ClearWeaponModdingWidgetReference(AActor* Character, FObjectProperty* UIModdingProperty)
	{
		if (Character && UIModdingProperty)
		{
			UIModdingProperty->SetObjectPropertyValue_InContainer(Character, nullptr);
		}
	}

	static UUserWidget* CreateWeaponModdingWidget(APlayerController* PlayerController)
	{
		if (!PlayerController)
		{
			return nullptr;
		}

		static TSubclassOf<UUserWidget> ModdingWidgetClass =
			LoadClass<UUserWidget>(nullptr, ModdingWidgetClassPath);
		if (!ModdingWidgetClass)
		{
			return nullptr;
		}

		return CreateWidget<UUserWidget>(PlayerController, ModdingWidgetClass);
	}

	static bool CloseWeaponModdingMenu(
		APlayerController* PlayerController,
		AActor* Character,
		UUserWidget* ModdingWidget,
		FObjectProperty* UIModdingProperty)
	{
		if (!ModdingWidget)
		{
			return false;
		}

		if (Character)
		{
			if (UFunction* CloseModdingFunction = Character->FindFunction(FName(TEXT("CloseModding"))))
			{
				Character->ProcessEvent(CloseModdingFunction, nullptr);
			}
		}

		ModdingWidget->RemoveFromParent();
		ClearWeaponModdingWidgetReference(Character, UIModdingProperty);

		if (PlayerController)
		{
			if (APawn* Pawn = PlayerController->GetPawn())
			{
				USCARWeaponAttachmentBlueprintLibrary::RefreshEquippedWeaponAttachments(Pawn);
			}

			PlayerController->SetShowMouseCursor(false);
			PlayerController->bEnableClickEvents = false;
			PlayerController->bEnableTouchEvents = false;
			FInputModeGameOnly InputMode;
			PlayerController->SetInputMode(InputMode);
		}

		return true;
	}

	static void SetAttachmentPanelCanvasLayout(
		UWidget* AttachmentPanel,
		const float ViewportWidth,
		const float ViewportHeight,
		const bool bPortrait)
	{
		UCanvasPanelSlot* CanvasSlot = AttachmentPanel ? Cast<UCanvasPanelSlot>(AttachmentPanel->Slot) : nullptr;
		if (!CanvasSlot)
		{
			return;
		}

		if (bPortrait)
		{
			// Horizontally centered, slightly above mid-screen so it sits over the weapon view.
			CanvasSlot->SetAnchors(FAnchors(0.5f, 0.5f, 0.5f, 0.5f));
			CanvasSlot->SetAlignment(FVector2D(0.5f, 0.5f));
			CanvasSlot->SetPosition(FVector2D(0.f, -ViewportHeight * 0.10f));
		}
		else
		{
			CanvasSlot->SetAnchors(FAnchors(0.5f, 0.f, 0.5f, 0.f));
			CanvasSlot->SetAlignment(FVector2D(0.5f, 0.f));
			CanvasSlot->SetPosition(FVector2D(0.f, 36.f));
		}

		CanvasSlot->SetAutoSize(true);
	}

	static void ApplyWeaponModdingPortraitLayoutInternal(
		UUserWidget* ModdingWidget,
		APlayerController* PlayerController)
	{
		if (!ModdingWidget || !PlayerController)
		{
			return;
		}

		int32 ViewportWidth = 0;
		int32 ViewportHeight = 0;
		PlayerController->GetViewportSize(ViewportWidth, ViewportHeight);
		if (ViewportWidth == 0 || ViewportHeight == 0)
		{
			return;
		}

		ResetAllAttachmentRenderTransforms(ModdingWidget);

		UWidget* AttachmentPanel = FindAttachmentPanelRoot(ModdingWidget);
		if (!AttachmentPanel)
		{
			return;
		}

		const bool bPortrait = ViewportHeight > ViewportWidth;
		SetAttachmentPanelCanvasLayout(
			AttachmentPanel,
			static_cast<float>(ViewportWidth),
			static_cast<float>(ViewportHeight),
			bPortrait);

		if (bPortrait)
		{
			HideWeaponModdingInspectHint(ModdingWidget);

			ModdingWidget->ForceLayoutPrepass();
			AttachmentPanel->ForceLayoutPrepass();

			constexpr float FallbackPanelWidth = 820.f;
			float PanelWidth = AttachmentPanel->GetDesiredSize().X;
			if (PanelWidth < 500.f)
			{
				PanelWidth = FallbackPanelWidth;
			}

			// Use nearly the full screen width so the menu reads larger while staying inside bounds.
			const float AvailableWidth = static_cast<float>(ViewportWidth) * 0.97f;
			const float Scale = FMath::Min(1.f, AvailableWidth / PanelWidth);

			AttachmentPanel->SetRenderTransformPivot(FVector2D(0.5f, 0.5f));
			AttachmentPanel->SetRenderTranslation(FVector2D::ZeroVector);
			AttachmentPanel->SetRenderScale(FVector2D(Scale, Scale));
		}
	}
}

void USCARWeaponAttachmentBlueprintLibrary::ApplyWeaponModdingPortraitLayout(
	UUserWidget* ModdingWidget,
	APlayerController* PlayerController)
{
	SCARWeaponAttachmentInternal::ApplyWeaponModdingPortraitLayoutInternal(ModdingWidget, PlayerController);
}

bool USCARWeaponAttachmentBlueprintLibrary::ToggleBodycamWeaponModdingMenu(APlayerController* PlayerController)
{
	using namespace SCARWeaponAttachmentInternal;

	if (!PlayerController || !PlayerController->IsLocalController())
	{
		return false;
	}

	AActor* Character = ResolveBodycamCharacter(PlayerController->GetPawn());
	if (!Character)
	{
		UE_LOG(LogTemp, Warning, TEXT("SCAR attachments: pawn is not BP_FPCharacter"));
		return false;
	}

	if (!GetSpawnedWeapon(Character))
	{
		UE_LOG(LogTemp, Warning, TEXT("SCAR attachments: equip a weapon before opening modding UI"));
		return false;
	}

	FObjectProperty* UIModdingProperty =
		CastField<FObjectProperty>(FindExactProperty(Character->GetClass(), TEXT("UI_Modding")));
	if (!UIModdingProperty)
	{
		UE_LOG(LogTemp, Warning, TEXT("SCAR attachments: UI_Modding property missing on character"));
		return false;
	}

	UUserWidget* ModdingWidget =
		Cast<UUserWidget>(UIModdingProperty->GetObjectPropertyValue_InContainer(Character));

	if (IsWeaponModdingMenuShown(ModdingWidget))
	{
		CloseWeaponModdingMenu(PlayerController, Character, ModdingWidget, UIModdingProperty);
		UE_LOG(LogTemp, Log, TEXT("SCAR attachments: closed Bodycam UI_WeaponModding"));
		return true;
	}

	if (ModdingWidget)
	{
		ModdingWidget->RemoveFromParent();
		ClearWeaponModdingWidgetReference(Character, UIModdingProperty);
		ModdingWidget = nullptr;
	}

	ModdingWidget = CreateWeaponModdingWidget(PlayerController);
	if (!ModdingWidget)
	{
		UE_LOG(LogTemp, Warning, TEXT("SCAR attachments: CreateWidget UI_WeaponModding failed"));
		return false;
	}

	UIModdingProperty->SetObjectPropertyValue_InContainer(Character, ModdingWidget);
	ModdingWidget->AddToViewport(100);

	MakeModdingMenuClickThroughEmptyAreas(ModdingWidget);
	ApplyWeaponModdingPortraitLayoutInternal(ModdingWidget, PlayerController);

	PlayerController->SetShowMouseCursor(true);
	PlayerController->bEnableClickEvents = true;
	PlayerController->bEnableTouchEvents = true;

	FInputModeGameAndUI InputMode;
	InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
	InputMode.SetHideCursorDuringCapture(false);
	PlayerController->SetInputMode(InputMode);

	if (APawn* Pawn = PlayerController->GetPawn())
	{
		USCARWeaponAttachmentBlueprintLibrary::RefreshEquippedWeaponAttachments(Pawn);
	}

	UE_LOG(LogTemp, Log, TEXT("SCAR attachments: opened Bodycam UI_WeaponModding"));
	return true;
}

bool USCARWeaponAttachmentBlueprintLibrary::SupportsWeaponAttachments(APawn* Pawn)
{
	using namespace SCARWeaponAttachmentInternal;

	AActor* Character = ResolveBodycamCharacter(Pawn);
	if (!Character)
	{
		return false;
	}

	return WeaponSupportsAttachments(GetSpawnedWeapon(Character));
}

FText USCARWeaponAttachmentBlueprintLibrary::GetEquippedWeaponAttachmentLabel(
	APawn* Pawn,
	const ESCARWeaponAttachmentCategory Category)
{
	using namespace SCARWeaponAttachmentInternal;

	AActor* Character = ResolveBodycamCharacter(Pawn);
	if (!Character || !WeaponSupportsAttachments(GetSpawnedWeapon(Character)))
	{
		return FText::FromString(TEXT("N/A"));
	}

	uint8 Value = 0;
	if (!ReadAttachmentValue(Character, Category, Value))
	{
		return FText::FromString(TEXT("N/A"));
	}

	UEnum* Enum = LoadKitEnum(GetEnumPathForCategory(Category));
	return GetEnumDisplayName(Enum, Value);
}

bool USCARWeaponAttachmentBlueprintLibrary::CycleEquippedWeaponAttachment(
	APawn* Pawn,
	const ESCARWeaponAttachmentCategory Category)
{
	using namespace SCARWeaponAttachmentInternal;

	AActor* Character = ResolveBodycamCharacter(Pawn);
	AActor* Weapon = Character ? GetSpawnedWeapon(Character) : nullptr;
	if (!Character || !WeaponSupportsAttachments(Weapon))
	{
		return false;
	}

	uint8 CurrentValue = 0;
	if (!ReadAttachmentValue(Character, Category, CurrentValue))
	{
		return false;
	}

	UEnum* Enum = LoadKitEnum(GetEnumPathForCategory(Category));
	const int32 EnumCount = GetValidEnumCount(Enum);
	const uint8 NextValue = static_cast<uint8>((static_cast<int32>(CurrentValue) + 1) % EnumCount);
	if (!WriteAttachmentValue(Character, Category, NextValue))
	{
		return false;
	}

	RefreshEquippedWeaponAttachments(Pawn);
	return true;
}

void USCARWeaponAttachmentBlueprintLibrary::RefreshEquippedWeaponAttachments(APawn* Pawn)
{
	using namespace SCARWeaponAttachmentInternal;

	AActor* Character = ResolveBodycamCharacter(Pawn);
	AActor* Weapon = Character ? GetSpawnedWeapon(Character) : nullptr;
	if (!Character || !WeaponSupportsAttachments(Weapon))
	{
		return;
	}

	FStructProperty* SlotProperty = GetEquippedSlotProperty(Character);
	CopySlotToWeaponItemData(Character, SlotProperty);
	CallSetWeaponAmmoData(Weapon, true);
	CallSpawnAttachments(Weapon);
	EnsureWeaponLaserFlashEffectsDeferred(Character, Weapon);
}

void USCARWeaponAttachmentBlueprintLibrary::ApplySpawnedWeaponAttachments(APawn* Pawn)
{
	using namespace SCARWeaponAttachmentInternal;

	AActor* Character = ResolveBodycamCharacter(Pawn);
	AActor* Weapon = Character ? GetSpawnedWeapon(Character) : nullptr;
	if (!Character || !WeaponSupportsAttachments(Weapon))
	{
		return;
	}

	CallSetWeaponAmmoData(Weapon, true);
	CallSpawnAttachments(Weapon);
	EnsureWeaponLaserFlashEffectsDeferred(Character, Weapon);
}

void USCARWeaponAttachmentBlueprintLibrary::EnsureWeaponLaserFlashEffectsForPawn(APawn* Pawn)
{
	using namespace SCARWeaponAttachmentInternal;

	AActor* Character = ResolveBodycamCharacter(Pawn);
	AActor* Weapon = Character ? GetSpawnedWeapon(Character) : nullptr;
	EnsureWeaponLaserFlashEffectsInternal(Character, Weapon);
}

void USCARWeaponAttachmentBlueprintLibrary::EnsureWeaponLaserFlashEffects(AActor* Weapon)
{
	SCARWeaponAttachmentInternal::EnsureWeaponLaserFlashEffectsDeferred(nullptr, Weapon);
}
