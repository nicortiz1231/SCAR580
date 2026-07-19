#include "SCARWeaponAttachmentBlueprintLibrary.h"

#include "SCARDeviceTorch.h"
#include "SCARPhonePreviewParity.h"

#include "Blueprint/UserWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/ComboBoxString.h"
#include "Components/HorizontalBox.h"
#include "Components/PanelWidget.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/LocalLightComponent.h"
#include "Components/LightComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/Texture.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
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

		// Prefer exact / GUID-mangled Bodycam names (Laser_38_...) over loose substring matches.
		FProperty* ContainsMatch = nullptr;
		const FString HintString(Hint);
		const FString HintPrefix = HintString + TEXT("_");
		for (TFieldIterator<FProperty> It(Owner); It; ++It)
		{
			const FString Name = It->GetName();
			if (Name.Equals(HintString) || Name.StartsWith(HintPrefix))
			{
				return *It;
			}
			if (!ContainsMatch && Name.Contains(HintString))
			{
				ContainsMatch = *It;
			}
		}

		return ContainsMatch;
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

	// Light-function + cookie from Zombie Survival / FirstPersonHorrorKit flashlight.
	static constexpr TCHAR HorrorFlashLightFunctionPath[] =
		TEXT("/Game/FirstPersonHorrorKit/Demo/FPFlashlightAnims/Mesh/Material/M_Light.M_Light");

	// Exact cookie texture used by M_Light — drawn small/additive over AR so rings+hotspot match the kit.
	static constexpr TCHAR HorrorFlashCookieTexturePath[] =
		TEXT("/Game/FirstPersonHorrorKit/Demo/FPFlashlightAnims/Mesh/Textures/T_FlashlightD.T_FlashlightD");

	static constexpr TCHAR SoftFlashSpotMaterialPath[] =
		TEXT("/Game/SCAR580/Materials/M_AR_FlashCookie.M_AR_FlashCookie");

	static constexpr TCHAR FlashSpotPlaneMeshPath[] =
		TEXT("/Engine/BasicShapes/Plane.Plane");

	/** Wider cone so soft outer spill matches the kit reference (~half screen). */
	static constexpr float FlashOuterConeDegrees = 17.f;
	static constexpr float FlashInnerConeDegrees = 5.f;

	static const FName ScarArLaserBeamComponentName(TEXT("SCAR_AR_LaserBeam"));
	static const FName ScarArLaserDotComponentName(TEXT("SCAR_AR_LaserDot"));
	static const FName ScarArFlashGlowComponentName(TEXT("SCAR_AR_FlashGlow"));
	static const FName ScarArFlashConeComponentName(TEXT("SCAR_AR_FlashCone"));
	static const FName ScarArFlashSpotComponentName(TEXT("SCAR_AR_FlashSpot"));

	static constexpr uint8 BodycamLaserNoneEnum = 0;
	static constexpr uint8 BodycamLaserFlashEnum = 3;
	static constexpr uint8 BodycamLaserBeamEnum = 4;

	static bool IsValidBodycamLaserEnum(const uint8 Value)
	{
		return Value == BodycamLaserNoneEnum
			|| Value == BodycamLaserFlashEnum
			|| Value == BodycamLaserBeamEnum;
	}

	static uint8 NormalizeBodycamLaserEnum(const uint8 Value)
	{
		if (IsValidBodycamLaserEnum(Value))
		{
			return Value;
		}

		// Do NOT remap 1/2 — Bodycam's Attachments combo is ordered EMPTY, LASER, FLASH, so
		// writing combo index 2 for FLASH must not become Laser. Invalid values stay None.
		return BodycamLaserNoneEnum;
	}

	static uint8 MapLaserOptionLabelToEnum(const FString& OptionLabel)
	{
		const FString Upper = OptionLabel.ToUpper();
		if (Upper.Contains(TEXT("FLASH")))
		{
			return BodycamLaserFlashEnum;
		}
		if (Upper.Contains(TEXT("LASER")))
		{
			return BodycamLaserBeamEnum;
		}
		if (Upper.Contains(TEXT("EMPTY")) || Upper.Contains(TEXT("NONE")))
		{
			return BodycamLaserNoneEnum;
		}
		return BodycamLaserNoneEnum;
	}

	/** Survives menu close — Bodycam slot/ItemData often store Laser(4) when the combo said FLASH. */
	static TMap<TWeakObjectPtr<AActor>, uint8> LatchedLaserEnumByWeapon;

	static void LatchLaserEnumForWeapon(AActor* Weapon, const uint8 EnumValue)
	{
		if (Weapon)
		{
			LatchedLaserEnumByWeapon.Add(Weapon, EnumValue);
		}
	}

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

	static UMaterialInterface* GetHorrorFlashLightFunction()
	{
		static UMaterialInterface* CachedMaterial = LoadObject<UMaterialInterface>(nullptr, HorrorFlashLightFunctionPath);
		return CachedMaterial;
	}

	static UTexture* GetHorrorFlashCookieTexture()
	{
		static UTexture* CachedTexture = LoadObject<UTexture>(nullptr, HorrorFlashCookieTexturePath);
		return CachedTexture;
	}

	static UMaterialInterface* GetSoftFlashSpotMaterial()
	{
		static UMaterialInterface* CachedMaterial = LoadObject<UMaterialInterface>(nullptr, SoftFlashSpotMaterialPath);
		return CachedMaterial;
	}

	static UStaticMesh* GetFlashSpotPlaneMesh()
	{
		static UStaticMesh* CachedMesh = LoadObject<UStaticMesh>(nullptr, FlashSpotPlaneMeshPath);
		return CachedMesh;
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

	static bool ReadAttachmentValue(
		AActor* Character,
		const ESCARWeaponAttachmentCategory Category,
		uint8& OutValue);
	static bool WriteAttachmentValue(
		AActor* Character,
		const ESCARWeaponAttachmentCategory Category,
		const uint8 Value);

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

		// FirstPersonHorrorKit flashlight: SpotLight + M_Light (exact asset cookie), tight cone.
		constexpr float FlashlightIntensity = 80.f; // candelas
		if (USpotLightComponent* SpotLight = Cast<USpotLightComponent>(Light))
		{
			if (bVisible)
			{
				if (UMaterialInterface* LightFunction = GetHorrorFlashLightFunction())
				{
					SpotLight->SetLightFunctionMaterial(LightFunction);
					SpotLight->SetLightFunctionScale(FVector(1.f, 1.f, 1.f));
					SpotLight->SetLightFunctionFadeDistance(0.f);
				}

				SpotLight->SetMobility(EComponentMobility::Movable);
				SpotLight->SetIntensityUnits(ELightUnits::Candelas);
				SpotLight->SetIntensity(FlashlightIntensity);
				SpotLight->SetAttenuationRadius(4000.f);
				SpotLight->SetInnerConeAngle(FlashInnerConeDegrees);
				SpotLight->SetOuterConeAngle(FlashOuterConeDegrees);
				SpotLight->SetLightColor(FLinearColor(1.f, 1.f, 0.97f));
				SpotLight->SetUseInverseSquaredFalloff(true);
				SpotLight->SetVisibility(true);
				SpotLight->SetHiddenInGame(false);
				SpotLight->SetCastShadows(false);
				SpotLight->SetLightingChannels(false, true, false);
			}
			else
			{
				SpotLight->SetLightFunctionMaterial(nullptr);
				SpotLight->SetIntensity(0.f);
			}
		}
		else if (bVisible)
		{
			Light->SetIntensity(FlashlightIntensity * 1000.f);
		}
		else
		{
			Light->SetIntensity(0.f);
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
		// Thicker beam in AR/PIE so it reads clearly over passthrough camera.
		const bool bMobileAr = BeamComponent->GetWorld()
			&& SCARPhonePreviewParity::ShouldUseMobileCameraPath(BeamComponent->GetWorld());
		const float Thickness = bMobileAr ? 3.5f : 1.f;
		BeamComponent->SetWorldScale3D(FVector(ScaleAxis, Thickness, Thickness));
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
		Component->SetCastShadow(false);
		Component->SetBoundsScale(16.f);
		Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Component->SetGenerateOverlapEvents(false);
		// Draw in foreground so the beam/cone composites over AR passthrough in PIE and device.
		Component->SetDepthPriorityGroup(SDPG_Foreground);
		Component->SetFirstPersonPrimitiveType(EFirstPersonPrimitiveType::WorldSpaceRepresentation);
		Component->SetTranslucentSortPriority(100);
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
			if (MeshComponent
				&& IsValid(MeshComponent)
				&& !MeshComponent->IsUnreachable()
				&& MeshComponent->GetFName() == ComponentName)
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
		// Attach under weapon root so hiding Bodycam LaserBeam never hides this overlay.
		USceneComponent* AttachParent = Weapon ? Weapon->GetRootComponent() : nullptr;
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
		BeamDistance = FMath::Max(BeamDistance, 800.f);

		// Always world-space scale so the full beam is visible from hipfire (not only reload/ADS).
		ApplyArLaserBeamWorldTransform(BeamComponent, EmissionFrame, BeamDistance);
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

	static void DestroyScarFlashConeMeshes(AActor* Owner)
	{
		if (!Owner)
		{
			return;
		}

		for (const FName ComponentName :
			{ ScarArFlashConeComponentName,
			  ScarArFlashGlowComponentName,
			  FName(TEXT("SCAR_FlashCone")) })
		{
			if (UStaticMeshComponent* Mesh = FindNamedStaticMeshComponent(Owner, ComponentName))
			{
				Mesh->SetHiddenInGame(true);
				Mesh->SetVisibility(false, true);
				Mesh->DestroyComponent();
			}
		}

		TInlineComponentArray<UStaticMeshComponent*> Meshes(Owner);
		for (UStaticMeshComponent* Mesh : Meshes)
		{
			if (!Mesh)
			{
				continue;
			}
			const FString Name = Mesh->GetName();
			// Keep SCAR_AR_FlashSpot — that is the AR passthrough cookie overlay.
			if (Name.Contains(TEXT("SCAR_FlashCone"), ESearchCase::IgnoreCase)
				|| Name.Contains(TEXT("SCAR_AR_FlashCone"), ESearchCase::IgnoreCase)
				|| Name.Contains(TEXT("SCAR_AR_FlashGlow"), ESearchCase::IgnoreCase))
			{
				Mesh->SetHiddenInGame(true);
				Mesh->SetVisibility(false, true);
				Mesh->DestroyComponent();
			}
		}
	}

	static USpotLightComponent* FindFlashlightSpotLight(AActor* LaserActor)
	{
		if (!LaserActor)
		{
			return nullptr;
		}

		TInlineComponentArray<USpotLightComponent*> SpotLights(LaserActor);
		for (USpotLightComponent* SpotLight : SpotLights)
		{
			if (SpotLight && SpotLight->GetName().Contains(TEXT("Flash"), ESearchCase::IgnoreCase))
			{
				return SpotLight;
			}
		}
		return SpotLights.Num() > 0 ? SpotLights[0] : nullptr;
	}

	/** Exact zombie-pack flashlight: SpotLight + M_Light. Stay attached — never detach (causes FP arm jitter). */
	static void EnsureHorrorKitFlashlightSpot(AActor* LaserActor, AActor* Weapon, const bool bVisible)
	{
		if (!LaserActor)
		{
			return;
		}

		USpotLightComponent* SpotLight = FindFlashlightSpotLight(LaserActor);
		if (!SpotLight && bVisible)
		{
			USceneComponent* AttachParent = LaserActor->GetRootComponent();
			if (!AttachParent && Weapon)
			{
				AttachParent = FindLaserAttachParent(Weapon);
			}
			if (!AttachParent)
			{
				return;
			}

			SpotLight = NewObject<USpotLightComponent>(
				LaserActor,
				USpotLightComponent::StaticClass(),
				TEXT("SCAR_HorrorFlashSpot"),
				RF_Transient);
			if (!SpotLight)
			{
				return;
			}

			SpotLight->SetupAttachment(AttachParent);
			SpotLight->SetRelativeLocation(FVector::ZeroVector);
			SpotLight->SetRelativeRotation(FRotator::ZeroRotator);
			LaserActor->AddInstanceComponent(SpotLight);
			SpotLight->RegisterComponent();
		}

		if (!SpotLight)
		{
			return;
		}

		ConfigureARAttachmentLight(SpotLight, bVisible);
		if (bVisible)
		{
			// Keep hierarchy intact — LaserActor already tracks the weapon/arms aim.
			if (SpotLight->GetAttachParent() == nullptr && LaserActor->GetRootComponent())
			{
				SpotLight->AttachToComponent(
					LaserActor->GetRootComponent(),
					FAttachmentTransformRules::SnapToTargetNotIncludingScale);
			}
			SpotLight->SetRelativeLocation(FVector::ZeroVector);
			SpotLight->SetRelativeRotation(FRotator::ZeroRotator);
			SpotLight->SetVisibility(true);
			SpotLight->SetHiddenInGame(false);
			SpotLight->SetActive(true);
		}
		else
		{
			SpotLight->SetActive(false);
		}
	}

	/**
	 * SpotLights cannot light AR camera passthrough. Overlay the exact M_Light cookie
	 * (T_FlashlightD) as a small additive disc. Uses absolute world transform only —
	 * never attach/detach from the weapon skeletal mesh (that jittered FP arms).
	 */
	static void EnsureArFlashCookieOverlay(AActor* Weapon, const bool bVisible)
	{
		if (!Weapon)
		{
			return;
		}

		if (!bVisible)
		{
			if (UStaticMeshComponent* Existing = FindNamedStaticMeshComponent(Weapon, ScarArFlashSpotComponentName))
			{
				Existing->SetHiddenInGame(true);
				Existing->SetVisibility(false, true);
				Existing->DestroyComponent();
			}
			return;
		}

		const FLaserEmissionFrame EmissionFrame = ResolveLaserEmissionFrame(Weapon);
		if (!EmissionFrame.bValid)
		{
			return;
		}

		const FVector Forward = EmissionFrame.Rotation.Vector();
		FVector HitLocation = EmissionFrame.Location + Forward * 320.f;
		FVector FaceNormal = -Forward;
		float HitDistance = 320.f;

		if (UWorld* World = Weapon->GetWorld())
		{
			const FVector End = EmissionFrame.Location + Forward * 10000.f;
			FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(ScarFlashCookieTrace), true, Weapon);
			QueryParams.AddIgnoredActor(Weapon);
			if (AActor* LaserRef = GetWeaponObjectRef(Weapon, TEXT("LaserRef")))
			{
				QueryParams.AddIgnoredActor(LaserRef);
			}

			FHitResult Hit;
			if (World->LineTraceSingleByChannel(Hit, EmissionFrame.Location, End, ECC_Visibility, QueryParams))
			{
				HitLocation = Hit.ImpactPoint + Hit.ImpactNormal * 1.5f;
				FaceNormal = Hit.ImpactNormal;
				HitDistance = FMath::Clamp(Hit.Distance, 100.f, 2200.f);
			}
		}

		UStaticMeshComponent* CookieComponent = FindNamedStaticMeshComponent(Weapon, ScarArFlashSpotComponentName);
		if (!CookieComponent)
		{
			USceneComponent* Root = Weapon->GetRootComponent();
			if (!Root)
			{
				return;
			}

			CookieComponent = NewObject<UStaticMeshComponent>(
				Weapon,
				UStaticMeshComponent::StaticClass(),
				ScarArFlashSpotComponentName,
				RF_Transient);
			if (!CookieComponent)
			{
				return;
			}

			// Attach to weapon root once, then use absolute world transform so we never
			// re-parent against the animated ItemMesh / FP arms hierarchy.
			CookieComponent->SetupAttachment(Root);
			Weapon->AddInstanceComponent(CookieComponent);
			CookieComponent->RegisterComponent();
			CookieComponent->SetUsingAbsoluteLocation(true);
			CookieComponent->SetUsingAbsoluteRotation(true);
			CookieComponent->SetUsingAbsoluteScale(true);

			if (UStaticMesh* PlaneMesh = GetFlashSpotPlaneMesh())
			{
				CookieComponent->SetStaticMesh(PlaneMesh);
			}

			if (UMaterialInterface* CookieMaterial = GetSoftFlashSpotMaterial())
			{
				if (UMaterialInstanceDynamic* DynamicMaterial =
						UMaterialInstanceDynamic::Create(CookieMaterial, CookieComponent))
				{
					if (UTexture* Cookie = GetHorrorFlashCookieTexture())
					{
						DynamicMaterial->SetTextureParameterValue(TEXT("Cookie"), Cookie);
					}
					DynamicMaterial->SetScalarParameterValue(TEXT("Strength"), 4.5f);
					DynamicMaterial->SetScalarParameterValue(TEXT("Softness"), 0.70f);
					DynamicMaterial->SetScalarParameterValue(TEXT("Spill"), 0.30f);
					DynamicMaterial->SetVectorParameterValue(
						TEXT("Tint"),
						FLinearColor(0.97f, 0.98f, 1.f, 1.f));
					CookieComponent->SetMaterial(0, DynamicMaterial);
				}
				else
				{
					CookieComponent->SetMaterial(0, CookieMaterial);
				}
			}

			ConfigureMobileArOverlayPrimitive(CookieComponent, true);
			CookieComponent->SetCastShadow(false);
			CookieComponent->SetTranslucentSortPriority(120);
		}
		else
		{
			CookieComponent->SetHiddenInGame(false);
			CookieComponent->SetVisibility(true, true);
			CookieComponent->SetUsingAbsoluteLocation(true);
			CookieComponent->SetUsingAbsoluteRotation(true);
			CookieComponent->SetUsingAbsoluteScale(true);
		}

		const float SpotRadius =
			HitDistance * FMath::Tan(FMath::DegreesToRadians(FlashOuterConeDegrees)) * 1.12f;
		float MeshHalfSize = 50.f;
		if (const UStaticMesh* PlaneAsset = CookieComponent->GetStaticMesh())
		{
			const FBox BoundingBox = PlaneAsset->GetBoundingBox();
			MeshHalfSize = FMath::Max(0.5f * FMath::Max(BoundingBox.GetSize().X, BoundingBox.GetSize().Y), 1.f);
		}
		const float ScaleXY = FMath::Clamp(SpotRadius / MeshHalfSize, 0.15f, 22.f);

		CookieComponent->SetWorldLocation(HitLocation);
		CookieComponent->SetWorldRotation(FRotationMatrix::MakeFromZ(FaceNormal).Rotator());
		CookieComponent->SetWorldScale3D(FVector(ScaleXY, ScaleXY, 1.f));
	}

	static void EnsureArFlashGlowOnWeapon(AActor* Weapon, const bool bVisible, const UPrimitiveComponent* RenderTemplate)
	{
		(void)RenderTemplate;
		EnsureArFlashCookieOverlay(Weapon, bVisible);
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

	static uint8 ReadLaserEnumFromObjectItemData(UObject* Owner)
	{
		if (!Owner)
		{
			return BodycamLaserNoneEnum;
		}

		FStructProperty* ItemDataProperty = GetItemDataProperty(Owner->GetClass());
		if (!ItemDataProperty)
		{
			return BodycamLaserNoneEnum;
		}

		const void* ItemData = ItemDataProperty->ContainerPtrToValuePtr<void>(Owner);
		FStructProperty* AttachmentsProperty = GetAttachmentsProperty(ItemDataProperty);
		if (!AttachmentsProperty)
		{
			return BodycamLaserNoneEnum;
		}

		const void* AttachmentsData = AttachmentsProperty->ContainerPtrToValuePtr<void>(ItemData);
		FProperty* LaserField = GetAttachmentField(AttachmentsProperty, ESCARWeaponAttachmentCategory::Laser);
		if (!LaserField)
		{
			return BodycamLaserNoneEnum;
		}

		return NormalizeBodycamLaserEnum(ReadByteProperty(LaserField, AttachmentsData));
	}

	static uint8 ReadLaserEnumFromEquippedSlot(AActor* Character)
	{
		if (!Character)
		{
			return BodycamLaserNoneEnum;
		}

		FStructProperty* SlotProperty = GetEquippedSlotProperty(Character);
		if (!SlotProperty)
		{
			return BodycamLaserNoneEnum;
		}

		const void* SlotData = SlotProperty->ContainerPtrToValuePtr<void>(Character);
		FStructProperty* AttachmentsProperty = GetAttachmentsProperty(SlotProperty);
		if (!AttachmentsProperty)
		{
			return BodycamLaserNoneEnum;
		}

		const void* AttachmentsData = AttachmentsProperty->ContainerPtrToValuePtr<void>(SlotData);
		FProperty* LaserField = GetAttachmentField(AttachmentsProperty, ESCARWeaponAttachmentCategory::Laser);
		if (!LaserField)
		{
			return BodycamLaserNoneEnum;
		}

		return NormalizeBodycamLaserEnum(ReadByteProperty(LaserField, AttachmentsData));
	}

	static UUserWidget* GetModdingWidget(AActor* Character)
	{
		if (!Character)
		{
			return nullptr;
		}

		FObjectProperty* UIModdingProperty =
			CastField<FObjectProperty>(FindExactProperty(Character->GetClass(), TEXT("UI_Modding")));
		if (!UIModdingProperty)
		{
			return nullptr;
		}

		return Cast<UUserWidget>(UIModdingProperty->GetObjectPropertyValue_InContainer(Character));
	}

	static uint8 ReadLaserEnumFromModdingWidget(AActor* Character)
	{
		return ReadLaserEnumFromObjectItemData(GetModdingWidget(Character));
	}

	static bool ReadLaserEnumFromModdingCombo(AActor* Character, uint8& OutEnum)
	{
		UUserWidget* ModdingWidget = GetModdingWidget(Character);
		if (!ModdingWidget || !ModdingWidget->WidgetTree)
		{
			return false;
		}

		// Prefer the Laser combo's selected label — Bodycam fills options as EMPTY/LASER/FLASH
		// but may write GetEnumeratorValueFromIndex(comboIndex), which maps FLASH → Laser(4).
		TArray<UWidget*> AllWidgets;
		ModdingWidget->WidgetTree->GetAllWidgets(AllWidgets);
		for (UWidget* Widget : AllWidgets)
		{
			UComboBoxString* Combo = Cast<UComboBoxString>(Widget);
			if (!Combo)
			{
				continue;
			}

			const FString WidgetName = Combo->GetName();
			const bool bLooksLikeLaserCombo = WidgetName.Contains(TEXT("Laser"), ESearchCase::IgnoreCase)
				|| Combo->FindOptionIndex(TEXT("FLASH")) != INDEX_NONE
				|| Combo->FindOptionIndex(TEXT("Flash")) != INDEX_NONE;
			if (!bLooksLikeLaserCombo)
			{
				continue;
			}

			const FString Selected = Combo->GetSelectedOption();
			if (Selected.IsEmpty())
			{
				continue;
			}

			OutEnum = MapLaserOptionLabelToEnum(Selected);
			return true;
		}

		return false;
	}

	static void WriteWeaponLaserEnum(AActor* Weapon, const uint8 Value)
	{
		if (!Weapon)
		{
			return;
		}

		FStructProperty* ItemDataProperty = GetItemDataProperty(Weapon->GetClass());
		if (!ItemDataProperty)
		{
			return;
		}

		void* ItemData = ItemDataProperty->ContainerPtrToValuePtr<void>(Weapon);
		FStructProperty* AttachmentsProperty = GetAttachmentsProperty(ItemDataProperty);
		if (!AttachmentsProperty)
		{
			return;
		}

		void* AttachmentsData = AttachmentsProperty->ContainerPtrToValuePtr<void>(ItemData);
		if (FProperty* LaserField = GetAttachmentField(AttachmentsProperty, ESCARWeaponAttachmentCategory::Laser))
		{
			WriteByteProperty(LaserField, AttachmentsData, Value);
		}
	}

	static bool ReadActorBoolProperty(AActor* Actor, const TCHAR* PropertyName, bool& OutValue)
	{
		if (!Actor || !PropertyName)
		{
			return false;
		}

		if (FBoolProperty* BoolProperty =
				CastField<FBoolProperty>(FindExactProperty(Actor->GetClass(), PropertyName)))
		{
			OutValue = BoolProperty->GetPropertyValue_InContainer(Actor);
			return true;
		}

		return false;
	}

	static uint8 InferLaserEnumFromLaserRef(AActor* Weapon)
	{
		AActor* LaserRef = GetWeaponObjectRef(Weapon, TEXT("LaserRef"));
		if (!LaserRef || !IsValid(LaserRef) || LaserRef->IsActorBeingDestroyed())
		{
			return BodycamLaserNoneEnum;
		}

		// Bodycam UI_WeaponModding SpawnAttachments creates BP_Laser for both Flash and Laser.
		// Distinguish via UseFlashlight — never assume LaserRef always means beam mode.
		bool bUseFlashlight = false;
		if (ReadActorBoolProperty(LaserRef, TEXT("UseFlashlight"), bUseFlashlight))
		{
			return bUseFlashlight ? BodycamLaserFlashEnum : BodycamLaserBeamEnum;
		}

		bool bLaserActive = false;
		if (ReadActorBoolProperty(LaserRef, TEXT("LaserActive"), bLaserActive) && bLaserActive)
		{
			return BodycamLaserBeamEnum;
		}

		return BodycamLaserBeamEnum;
	}

	static uint8 ResolveAttachmentLaserEnum(AActor* Character, AActor* Weapon)
	{
		// Attachments menu combo label is authoritative: Bodycam may store Laser(4) when the
		// user picked FLASH because combo order (EMPTY,LASER,FLASH) != enum index order.
		uint8 ComboEnum = BodycamLaserNoneEnum;
		if (ReadLaserEnumFromModdingCombo(Character, ComboEnum))
		{
			LatchLaserEnumForWeapon(Weapon, ComboEnum);
			return ComboEnum;
		}

		// Menu closed — keep the last combo selection so Refresh/CopySlot can't revert FLASH→LASER.
		if (const uint8* Latched = LatchedLaserEnumByWeapon.Find(Weapon))
		{
			return *Latched;
		}

		const uint8 WeaponEnum = NormalizeBodycamLaserEnum(ReadWeaponLaserEnum(Weapon));
		if (WeaponEnum != BodycamLaserNoneEnum)
		{
			return WeaponEnum;
		}

		const uint8 SlotEnum = ReadLaserEnumFromEquippedSlot(Character);
		if (SlotEnum != BodycamLaserNoneEnum)
		{
			return SlotEnum;
		}

		const uint8 WidgetEnum = ReadLaserEnumFromModdingWidget(Character);
		if (WidgetEnum != BodycamLaserNoneEnum)
		{
			return WidgetEnum;
		}

		return InferLaserEnumFromLaserRef(Weapon);
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

	static void SetLaserActorUseFlashlightFlag(AActor* LaserActor, const bool bUseFlashlight)
	{
		if (!LaserActor)
		{
			return;
		}

		if (FBoolProperty* UseFlashlightProperty = CastField<FBoolProperty>(
				FindExactProperty(LaserActor->GetClass(), TEXT("UseFlashlight"))))
		{
			UseFlashlightProperty->SetPropertyValue_InContainer(LaserActor, bUseFlashlight);
		}
	}

	static void InvokeActorBoolFunction(AActor* Target, const FName FunctionName, const bool bValue)
	{
		if (!Target)
		{
			return;
		}

		UFunction* Function = Target->FindFunction(FunctionName);
		if (!Function || Function->ParmsSize <= 0)
		{
			return;
		}

		void* Parms = FMemory_Alloca(Function->ParmsSize);
		FMemory::Memzero(Parms, Function->ParmsSize);

		for (TFieldIterator<FProperty> It(Function); It && (It->PropertyFlags & CPF_Parm); ++It)
		{
			if (It->HasAnyPropertyFlags(CPF_ReturnParm))
			{
				continue;
			}

			if (FBoolProperty* BoolProperty = CastField<FBoolProperty>(*It))
			{
				BoolProperty->SetPropertyValue_InContainer(Parms, bValue);
				break;
			}
		}

		Target->ProcessEvent(Function, Parms);
	}

	static void ClearWeaponObjectRef(AActor* Weapon, const FName PropertyName)
	{
		if (!Weapon)
		{
			return;
		}

		if (FObjectProperty* Property = CastField<FObjectProperty>(
				Weapon->GetClass()->FindPropertyByName(PropertyName)))
		{
			Property->SetObjectPropertyValue_InContainer(Weapon, nullptr);
		}
	}

	static bool IsBodycamLaserActor(const AActor* Actor)
	{
		return Actor && Actor->GetClass()->GetName().Contains(TEXT("BP_Laser"));
	}

	static void DestroyScarArOverlayComponents(AActor* Weapon)
	{
		if (!Weapon)
		{
			return;
		}

		for (const FName ComponentName :
			{ ScarArLaserBeamComponentName,
			  ScarArLaserDotComponentName,
			  ScarArFlashGlowComponentName,
			  ScarArFlashConeComponentName,
			  ScarArFlashSpotComponentName })
		{
			if (UStaticMeshComponent* Overlay = FindNamedStaticMeshComponent(Weapon, ComponentName))
			{
				Overlay->SetHiddenInGame(true);
				Overlay->SetVisibility(false, true);
				Overlay->DestroyComponent();
			}
		}
	}

	static void DestroyScarArLaserOverlays(AActor* Weapon)
	{
		if (!Weapon)
		{
			return;
		}

		for (const FName ComponentName : { ScarArLaserBeamComponentName, ScarArLaserDotComponentName })
		{
			if (UStaticMeshComponent* Overlay = FindNamedStaticMeshComponent(Weapon, ComponentName))
			{
				Overlay->SetHiddenInGame(true);
				Overlay->SetVisibility(false, true);
				Overlay->DestroyComponent();
			}
		}
	}

	static void HideScarArOverlayComponents(AActor* Weapon)
	{
		DestroyScarArOverlayComponents(Weapon);
	}

	static void DestroyBodycamLaserActor(AActor* LaserActor)
	{
		if (!IsValid(LaserActor))
		{
			return;
		}

		LaserActor->SetActorTickEnabled(false);
		LaserActor->SetActorHiddenInGame(true);

		TInlineComponentArray<USceneComponent*> Components(LaserActor);
		for (USceneComponent* Component : Components)
		{
			if (Component)
			{
				Component->SetVisibility(false, true);
				Component->SetHiddenInGame(true);
			}
		}

		LaserActor->Destroy();
	}

	static void DestroyAllBodycamLaserActorsForWeapon(AActor* Weapon)
	{
		if (!Weapon)
		{
			return;
		}

		TSet<AActor*> ToDestroy;

		if (AActor* LaserRef = GetWeaponObjectRef(Weapon, TEXT("LaserRef")))
		{
			ToDestroy.Add(LaserRef);
		}
		if (AActor* AkimboLaserRef = GetWeaponObjectRef(Weapon, TEXT("AkimboLaserRef")))
		{
			ToDestroy.Add(AkimboLaserRef);
		}

		TArray<AActor*> AttachedActors;
		Weapon->GetAttachedActors(AttachedActors, true, true);
		for (AActor* AttachedActor : AttachedActors)
		{
			if (IsBodycamLaserActor(AttachedActor))
			{
				ToDestroy.Add(AttachedActor);
			}
		}

		// Bodycam None can detach BP_Laser without destroying it — sweep orphans by owner.
		if (UWorld* World = Weapon->GetWorld())
		{
			static TMap<TWeakObjectPtr<AActor>, double> LastOrphanSweepSeconds;
			const double Now = static_cast<double>(World->GetTimeSeconds());
			bool bShouldSweepWorld = true;
			if (const double* LastSweep = LastOrphanSweepSeconds.Find(Weapon))
			{
				bShouldSweepWorld = (Now - *LastSweep) >= 0.25;
			}

			if (bShouldSweepWorld)
			{
				LastOrphanSweepSeconds.Add(Weapon, Now);
				for (TActorIterator<AActor> It(World); It; ++It)
				{
					AActor* Candidate = *It;
					if (!IsBodycamLaserActor(Candidate) || ToDestroy.Contains(Candidate))
					{
						continue;
					}

					if (Candidate->GetOwner() == Weapon || Candidate->GetAttachParentActor() == Weapon)
					{
						ToDestroy.Add(Candidate);
					}
				}
			}
		}

		ClearWeaponObjectRef(Weapon, TEXT("LaserRef"));
		ClearWeaponObjectRef(Weapon, TEXT("AkimboLaserRef"));

		for (AActor* LaserActor : ToDestroy)
		{
			DestroyBodycamLaserActor(LaserActor);
		}

		DestroyScarArOverlayComponents(Weapon);
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

			if (IsBodycamLaserActor(AttachedActor))
			{
				DestroyBodycamLaserActor(AttachedActor);
			}
		}
	}

	static void SetSceneComponentVisible(USceneComponent* Component, const bool bVisible)
	{
		if (!Component)
		{
			return;
		}

		Component->SetHiddenInGame(!bVisible);
		Component->SetVisibility(bVisible, true);
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

	static FLaserEmissionFrame ResolveLaserActorEmissionFrame(AActor* LaserActor)
	{
		FLaserEmissionFrame Frame;
		if (!LaserActor)
		{
			return Frame;
		}

		TInlineComponentArray<UStaticMeshComponent*> HousingMeshes(LaserActor);
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

		if (USceneComponent* RootComponent = LaserActor->GetRootComponent())
		{
			Frame.Location = RootComponent->GetComponentLocation();
			Frame.Rotation = RootComponent->GetComponentRotation();
			Frame.bValid = true;
		}

		return Frame;
	}

	static UStaticMeshComponent* FindNamedOrContainingStaticMesh(AActor* Owner, const TCHAR* NameHint)
	{
		if (!Owner || !NameHint)
		{
			return nullptr;
		}

		TInlineComponentArray<UStaticMeshComponent*> MeshComponents(Owner);
		for (UStaticMeshComponent* MeshComponent : MeshComponents)
		{
			if (MeshComponent && IsValid(MeshComponent)
				&& MeshComponent->GetName().Contains(NameHint, ESearchCase::IgnoreCase))
			{
				return MeshComponent;
			}
		}

		return nullptr;
	}

	static void ForceLongVisibleLaserBeam(AActor* LaserActor, AActor* Weapon)
	{
		UStaticMeshComponent* BeamComponent = FindNamedOrContainingStaticMesh(LaserActor, TEXT("LaserBeam"));
		if (!BeamComponent)
		{
			return;
		}

		if (UStaticMesh* BeamMesh = GetLaserBeamMesh())
		{
			BeamComponent->SetStaticMesh(BeamMesh);
		}

		ConfigureBoostedLaserMaterial(BeamComponent);
		// Critical for AR/PIE hipfire: world-space representation, not first-person-only.
		ConfigureMobileArOverlayPrimitive(BeamComponent, true);

		FLaserEmissionFrame EmissionFrame = ResolveLaserActorEmissionFrame(LaserActor);
		if (!EmissionFrame.bValid && Weapon)
		{
			EmissionFrame = ResolveLaserEmissionFrame(Weapon);
		}

		float BeamDistance = 5000.f;
		FVector HitLocation = FVector::ZeroVector;
		if (Weapon)
		{
			TraceLaserBeamHitFromFrame(Weapon, EmissionFrame, HitLocation, BeamDistance);
		}
		BeamDistance = FMath::Clamp(BeamDistance, 1500.f, 10000.f);

		ApplyArLaserBeamWorldTransform(BeamComponent, EmissionFrame, BeamDistance);
	}

	static void ForceVisibleFlashConeOnLaserActor(AActor* LaserActor, const bool bVisible)
	{
		(void)bVisible;
		DestroyScarFlashConeMeshes(LaserActor);
	}

	static void HardHideBodycamLaserBeam(AActor* LaserActor)
	{
		if (!LaserActor)
		{
			return;
		}

		SetLaserActorActiveFlag(LaserActor, false);
		InvokeActorBoolFunction(LaserActor, FName(TEXT("ToggleLaser")), false);

		TInlineComponentArray<USceneComponent*> SceneComponents(LaserActor);
		for (USceneComponent* Component : SceneComponents)
		{
			if (!Component)
			{
				continue;
			}

			const FString Name = Component->GetName();
			if (Name.Contains(TEXT("Beam"), ESearchCase::IgnoreCase)
				|| Name.Contains(TEXT("Dot"), ESearchCase::IgnoreCase)
				|| Name.Contains(TEXT("Decal"), ESearchCase::IgnoreCase))
			{
				SetSceneComponentVisible(Component, false);
				if (UStaticMeshComponent* Mesh = Cast<UStaticMeshComponent>(Component))
				{
					Mesh->SetWorldScale3D(FVector(0.001f));
				}
			}
		}
	}

	static void ForceShowBodycamLaserVisuals(
		AActor* LaserActor,
		AActor* Weapon,
		const bool bWantLaser,
		const bool bWantFlash)
	{
		if (!LaserActor)
		{
			return;
		}

		const bool bShowAttachment = bWantLaser || bWantFlash;

		// Only fire BP toggles / heavy mesh setup when mode changes — per-frame ProcessEvent
		// + overlay reconfig on the laser housing was jittering FP arms with FLASH equipped.
		static TMap<TWeakObjectPtr<AActor>, uint8> LastModeByLaserActor;
		const uint8 ModeKey = static_cast<uint8>((bWantLaser ? 1 : 0) | (bWantFlash ? 2 : 0));
		const uint8* LastMode = LastModeByLaserActor.Find(LaserActor);
		const bool bModeChanged = !LastMode || *LastMode != ModeKey;
		if (bModeChanged)
		{
			LastModeByLaserActor.Add(LaserActor, ModeKey);
		}

		LaserActor->SetActorHiddenInGame(!bShowAttachment);
		LaserActor->SetActorEnableCollision(false);
		LaserActor->SetActorTickEnabled(bWantLaser);

		if (bModeChanged)
		{
			if (FBoolProperty* UseIRLaserProperty = CastField<FBoolProperty>(
					FindExactProperty(LaserActor->GetClass(), TEXT("UseIRLaser"))))
			{
				UseIRLaserProperty->SetPropertyValue_InContainer(LaserActor, false);
			}

			SetLaserActorUseFlashlightFlag(LaserActor, bWantFlash);
			InvokeActorBoolFunction(LaserActor, FName(TEXT("ToggleLaser")), bWantLaser);
			InvokeActorBoolFunction(LaserActor, FName(TEXT("ToggleFlashlight")), bWantFlash);
			SetLaserActorActiveFlag(LaserActor, bWantLaser);

			TInlineComponentArray<USceneComponent*> SceneComponents(LaserActor);
			for (USceneComponent* Component : SceneComponents)
			{
				if (!Component || Component->GetFName() == TEXT("SCAR_FlashCone"))
				{
					continue;
				}

				const FString Name = Component->GetName();
				const bool bIsBeamOrDot = Name.Contains(TEXT("Beam"), ESearchCase::IgnoreCase)
					|| Name.Contains(TEXT("Dot"), ESearchCase::IgnoreCase)
					|| Name.Contains(TEXT("Decal"), ESearchCase::IgnoreCase);
				const bool bIsHousing = Name.Equals(TEXT("Mesh"), ESearchCase::IgnoreCase);

				if (bIsBeamOrDot)
				{
					SetSceneComponentVisible(Component, bWantLaser);
					if (bWantLaser)
					{
						if (UPrimitiveComponent* Primitive = Cast<UPrimitiveComponent>(Component))
						{
							ConfigureMobileArOverlayPrimitive(Primitive, true);
						}
					}
					else if (UStaticMeshComponent* Mesh = Cast<UStaticMeshComponent>(Component))
					{
						Mesh->SetWorldScale3D(FVector(0.001f));
					}
				}
				else if (bIsHousing)
				{
					SetSceneComponentVisible(Component, bShowAttachment);
					if (bShowAttachment)
					{
						if (UPrimitiveComponent* Primitive = Cast<UPrimitiveComponent>(Component))
						{
							ConfigureMobileArOverlayPrimitive(Primitive, true);
						}
					}
				}
			}

			TInlineComponentArray<ULightComponent*> Lights(LaserActor);
			for (ULightComponent* Light : Lights)
			{
				if (Cast<USpotLightComponent>(Light)
					&& Light->GetName().Contains(TEXT("Flash"), ESearchCase::IgnoreCase))
				{
					ConfigureARAttachmentLight(Light, bWantFlash);
				}
				else if (bWantFlash && Cast<USpotLightComponent>(Light) && FindFlashlightSpotLight(LaserActor) == Light)
				{
					ConfigureARAttachmentLight(Light, true);
				}
			}
		}

		if (bWantLaser)
		{
			ForceLongVisibleLaserBeam(LaserActor, Weapon);
			InvokeLaserDotTrace(LaserActor);
			SetLaserActorActiveFlag(LaserActor, true);
			ForceLongVisibleLaserBeam(LaserActor, Weapon);
			if (bModeChanged)
			{
				EnsureHorrorKitFlashlightSpot(LaserActor, Weapon, false);
			}
		}
		else if (bWantFlash)
		{
			if (bModeChanged)
			{
				HardHideBodycamLaserBeam(LaserActor);
				EnsureHorrorKitFlashlightSpot(LaserActor, Weapon, true);
			}
		}
		else
		{
			if (bModeChanged)
			{
				HardHideBodycamLaserBeam(LaserActor);
				EnsureHorrorKitFlashlightSpot(LaserActor, Weapon, false);
			}
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
		if (!Weapon)
		{
			return;
		}

		const bool bShowHousing = AttachmentLaserEnum == BodycamLaserFlashEnum
			|| AttachmentLaserEnum == BodycamLaserBeamEnum;
		UStaticMesh* AttachmentMesh = GetLaserAttachmentMesh();

		static TMap<TWeakObjectPtr<AActor>, uint8> LastHousingEnumByWeapon;
		const uint8* LastHousing = LastHousingEnumByWeapon.Find(Weapon);
		const bool bHousingChanged = !LastHousing || *LastHousing != AttachmentLaserEnum;
		if (bHousingChanged)
		{
			LastHousingEnumByWeapon.Add(Weapon, AttachmentLaserEnum);
		}

		TInlineComponentArray<UStaticMeshComponent*> MeshComponents(Weapon);
		for (UStaticMeshComponent* MeshComponent : MeshComponents)
		{
			if (!MeshComponent || !MeshComponent->GetName().Contains(TEXT("LaserMesh"), ESearchCase::IgnoreCase))
			{
				continue;
			}

			if (bShowHousing && AttachmentMesh && MeshComponent->GetStaticMesh() != AttachmentMesh)
			{
				MeshComponent->SetStaticMesh(AttachmentMesh);
			}

			if (bHousingChanged)
			{
				ConfigureARAttachmentPrimitive(MeshComponent, bShowHousing);
				if (bShowHousing)
				{
					ConfigureMobileArOverlayPrimitive(MeshComponent, true);
				}
			}
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

		// Drive the physical iPhone LED torch with the FLASH attachment (on-device only).
		{
			static bool bDeviceTorchOn = false;
			if (bWantFlash != bDeviceTorchOn)
			{
				SCARDeviceTorch::SetEnabled(bWantFlash);
				bDeviceTorchOn = bWantFlash;
				UE_LOG(
					LogTemp,
					Warning,
					TEXT("SCAR device torch: %s"),
					bWantFlash ? TEXT("ON") : TEXT("OFF"));
			}
		}

		// Keep weapon ItemData aligned when it drifts. Do NOT rewrite the equipped slot every
		// tick — that fought Bodycam and jittered FP arms. Slot is committed on menu close.
		LatchLaserEnumForWeapon(Weapon, AttachmentLaserEnum);
		if (NormalizeBodycamLaserEnum(ReadWeaponLaserEnum(Weapon)) != AttachmentLaserEnum)
		{
			WriteWeaponLaserEnum(Weapon, AttachmentLaserEnum);
		}

		static TMap<TWeakObjectPtr<AActor>, uint8> LastLoggedEnumByWeapon;
		const uint8* LastLogged = LastLoggedEnumByWeapon.Find(Weapon);
		if (!LastLogged || *LastLogged != AttachmentLaserEnum)
		{
			LastLoggedEnumByWeapon.Add(Weapon, AttachmentLaserEnum);
			UE_LOG(
				LogTemp,
				Warning,
				TEXT("SCAR laser/flash sync: weapon=%s enum=%u flash=%d laser=%d LaserRef=%s (w=%u slot=%u ui=%u)"),
				*Weapon->GetName(),
				static_cast<uint32>(AttachmentLaserEnum),
				bWantFlash ? 1 : 0,
				bWantLaser ? 1 : 0,
				GetWeaponObjectRef(Weapon, TEXT("LaserRef")) ? TEXT("yes") : TEXT("no"),
				static_cast<uint32>(NormalizeBodycamLaserEnum(ReadWeaponLaserEnum(Weapon))),
				static_cast<uint32>(ReadLaserEnumFromEquippedSlot(Character)),
				static_cast<uint32>(ReadLaserEnumFromModdingWidget(Character)));
		}

		if (AttachmentLaserEnum == BodycamLaserNoneEnum)
		{
			DestroyAllBodycamLaserActorsForWeapon(Weapon);
			SyncWeaponIntegratedLaserMesh(Weapon, BodycamLaserNoneEnum);
			return;
		}

		EnsureWeaponLaserActorRefs(Weapon, AttachmentLaserEnum);
		SyncWeaponIntegratedLaserMesh(Weapon, AttachmentLaserEnum);

		AActor* LaserRef = GetWeaponObjectRef(Weapon, TEXT("LaserRef"));
		if (!LaserRef)
		{
			CallSpawnAttachments(Weapon);
			LaserRef = GetWeaponObjectRef(Weapon, TEXT("LaserRef"));
		}

		if (LaserRef)
		{
			ForceShowBodycamLaserVisuals(LaserRef, Weapon, bWantLaser, bWantFlash);
		}

		if (AActor* AkimboLaserRef = GetWeaponObjectRef(Weapon, TEXT("AkimboLaserRef")))
		{
			ForceShowBodycamLaserVisuals(AkimboLaserRef, Weapon, bWantLaser, bWantFlash);
		}

		USkeletalMeshComponent* ItemMesh = FindWeaponItemMesh(Weapon);
		const UPrimitiveComponent* RenderTemplate = ItemMesh;

		// Laser = AR beam overlays. Flash = SpotLight+M_Light + AR cookie overlay (like laser over passthrough).
		if (bWantLaser)
		{
			EnsureArLaserBeamOnWeapon(Weapon, true, RenderTemplate);
			EnsureArLaserDotOnWeapon(Weapon, true);
			EnsureHorrorKitFlashlightSpot(LaserRef, Weapon, false);
			EnsureArFlashCookieOverlay(Weapon, false);
		}
		else if (bWantFlash)
		{
			DestroyScarArLaserOverlays(Weapon);
			// SpotLight is armed once in ForceShowBodycamLaserVisuals; only update the cookie here.
			EnsureArFlashCookieOverlay(Weapon, true);
		}
		else
		{
			DestroyScarArOverlayComponents(Weapon);
			EnsureHorrorKitFlashlightSpot(LaserRef, Weapon, false);
			EnsureArFlashCookieOverlay(Weapon, false);
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

		// Commit combo selection BEFORE tearing down the widget / copying slot→weapon.
		// Otherwise FLASH (combo label) is lost and Bodycam's wrong Laser(4) in the slot wins.
		AActor* Weapon = Character ? GetSpawnedWeapon(Character) : nullptr;
		uint8 ComboEnum = BodycamLaserNoneEnum;
		const bool bHaveCombo = ReadLaserEnumFromModdingCombo(Character, ComboEnum);
		if (bHaveCombo && Weapon)
		{
			LatchLaserEnumForWeapon(Weapon, ComboEnum);
			WriteWeaponLaserEnum(Weapon, ComboEnum);
			WriteAttachmentValue(Character, ESCARWeaponAttachmentCategory::Laser, ComboEnum);
			UE_LOG(
				LogTemp,
				Warning,
				TEXT("SCAR attachments: commit on close enum=%u (Flash=3 Laser=4 None=0)"),
				static_cast<uint32>(ComboEnum));
		}
		else if (Weapon)
		{
			if (const uint8* Latched = LatchedLaserEnumByWeapon.Find(Weapon))
			{
				WriteWeaponLaserEnum(Weapon, *Latched);
				WriteAttachmentValue(Character, ESCARWeaponAttachmentCategory::Laser, *Latched);
			}
		}

		if (Character)
		{
			if (UFunction* CloseModdingFunction = Character->FindFunction(FName(TEXT("CloseModding"))))
			{
				Character->ProcessEvent(CloseModdingFunction, nullptr);
			}

			// Bodycam CloseModding may rewrite ItemData — re-apply committed selection.
			if (Weapon)
			{
				if (bHaveCombo)
				{
					WriteWeaponLaserEnum(Weapon, ComboEnum);
					WriteAttachmentValue(Character, ESCARWeaponAttachmentCategory::Laser, ComboEnum);
				}
				else if (const uint8* Latched = LatchedLaserEnumByWeapon.Find(Weapon))
				{
					WriteWeaponLaserEnum(Weapon, *Latched);
					WriteAttachmentValue(Character, ESCARWeaponAttachmentCategory::Laser, *Latched);
				}
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
	if (!Enum)
	{
		return false;
	}

	if (Category == ESCARWeaponAttachmentCategory::Laser)
	{
		CurrentValue = NormalizeBodycamLaserEnum(CurrentValue);
	}

	const int32 EnumCount = GetValidEnumCount(Enum);
	if (EnumCount <= 0)
	{
		return false;
	}

	// ENUM_Laser is sparse (0=None, 3=Flash, 4=Laser). Cycle by index, not raw value.
	int32 CurrentIndex = Enum->GetIndexByValue(static_cast<int64>(CurrentValue));
	if (CurrentIndex == INDEX_NONE || CurrentIndex >= EnumCount)
	{
		CurrentIndex = 0;
	}

	const int32 NextIndex = (CurrentIndex + 1) % EnumCount;
	const uint8 NextValue = static_cast<uint8>(Enum->GetValueByIndex(NextIndex));
	if (!WriteAttachmentValue(Character, Category, NextValue))
	{
		return false;
	}

	UE_LOG(
		LogTemp,
		Log,
		TEXT("SCAR attachments: cycle %d -> %d (%s)"),
		static_cast<int32>(CurrentValue),
		static_cast<int32>(NextValue),
		*GetEnumDisplayName(Enum, NextValue).ToString());

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

	// Preserve latched FLASH/LASER after slot copy (Bodycam often stores Laser for FLASH picks).
	if (const uint8* Latched = LatchedLaserEnumByWeapon.Find(Weapon))
	{
		WriteWeaponLaserEnum(Weapon, *Latched);
		WriteAttachmentValue(Character, ESCARWeaponAttachmentCategory::Laser, *Latched);
	}

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
	using namespace SCARWeaponAttachmentInternal;

	AActor* Character = nullptr;
	if (Weapon)
	{
		if (APawn* OwnerPawn = Cast<APawn>(Weapon->GetOwner()))
		{
			Character = ResolveBodycamCharacter(OwnerPawn);
		}
		if (!Character)
		{
			if (APawn* InstigatorPawn = Cast<APawn>(Weapon->GetInstigator()))
			{
				Character = ResolveBodycamCharacter(InstigatorPawn);
			}
		}
	}

	EnsureWeaponLaserFlashEffectsDeferred(Character, Weapon);
}
