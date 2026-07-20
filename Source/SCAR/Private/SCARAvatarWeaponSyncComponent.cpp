#include "SCARAvatarWeaponSyncComponent.h"

#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequenceBase.h"
#include "Animation/AnimationAsset.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "SCARARMultiplayerPlayerState.h"
#include "UObject/ConstructorHelpers.h"
#include "UObject/EnumProperty.h"
#include "UObject/SoftObjectPath.h"
#include "UObject/UnrealType.h"

DEFINE_LOG_CATEGORY_STATIC(LogSCARAvatarWeapon, Log, All);

namespace
{
	UObject* GetObjectProperty(UObject* Object, const FName PropertyName)
	{
		if (!Object)
		{
			return nullptr;
		}

		if (const FObjectProperty* Property =
				CastField<FObjectProperty>(Object->GetClass()->FindPropertyByName(PropertyName)))
		{
			return Property->GetObjectPropertyValue_InContainer(Object);
		}

		return nullptr;
	}

	bool GetByteProperty(UObject* Object, const FName PropertyName, uint8& OutValue)
	{
		if (!Object)
		{
			return false;
		}

		if (const FByteProperty* Property =
				CastField<FByteProperty>(Object->GetClass()->FindPropertyByName(PropertyName)))
		{
			OutValue = Property->GetPropertyValue_InContainer(Object);
			return true;
		}

		return false;
	}

	bool GetBoolProperty(UObject* Object, const FName PropertyName, bool& OutValue)
	{
		if (!Object)
		{
			return false;
		}

		if (const FBoolProperty* Property =
				CastField<FBoolProperty>(Object->GetClass()->FindPropertyByName(PropertyName)))
		{
			OutValue = Property->GetPropertyValue_InContainer(Object);
			return true;
		}

		return false;
	}

	bool GetFloatProperty(UObject* Object, const FName PropertyName, float& OutValue)
	{
		if (!Object)
		{
			return false;
		}

		if (const FFloatProperty* Property =
				CastField<FFloatProperty>(Object->GetClass()->FindPropertyByName(PropertyName)))
		{
			OutValue = Property->GetPropertyValue_InContainer(Object);
			return true;
		}

		return false;
	}

	void SetByteProperty(UObject* Object, const FName PropertyName, const uint8 Value)
	{
		if (!Object)
		{
			return;
		}

		FProperty* Property = Object->GetClass()->FindPropertyByName(PropertyName);
		if (!Property)
		{
			return;
		}

		if (const FByteProperty* ByteProperty = CastField<FByteProperty>(Property))
		{
			ByteProperty->SetPropertyValue_InContainer(Object, Value);
			return;
		}

		if (const FEnumProperty* EnumProperty = CastField<FEnumProperty>(Property))
		{
			EnumProperty->GetUnderlyingProperty()->SetIntPropertyValue(
				EnumProperty->ContainerPtrToValuePtr<void>(Object),
				static_cast<int64>(Value));
		}
	}

	void SetBoolProperty(UObject* Object, const FName PropertyName, const bool bValue)
	{
		if (!Object)
		{
			return;
		}

		if (const FBoolProperty* Property =
				CastField<FBoolProperty>(Object->GetClass()->FindPropertyByName(PropertyName)))
		{
			Property->SetPropertyValue_InContainer(Object, bValue);
		}
	}

	void ForceAnimsetProperty(UObject* Object, const uint8 AnimsetValue)
	{
		if (!Object)
		{
			return;
		}

		for (TFieldIterator<FProperty> It(Object->GetClass()); It; ++It)
		{
			FProperty* Property = *It;
			if (!Property)
			{
				continue;
			}

			const FString PropertyName = Property->GetName();
			const bool bLooksLikeAnimset =
				PropertyName.Contains(TEXT("Animset"), ESearchCase::IgnoreCase) ||
				PropertyName.Contains(TEXT("GunSet"), ESearchCase::IgnoreCase);
			if (!bLooksLikeAnimset)
			{
				continue;
			}

			if (FEnumProperty* EnumProperty = CastField<FEnumProperty>(Property))
			{
				EnumProperty->GetUnderlyingProperty()->SetIntPropertyValue(
					EnumProperty->ContainerPtrToValuePtr<void>(Object),
					static_cast<int64>(AnimsetValue));
			}
			else if (FByteProperty* ByteProperty = CastField<FByteProperty>(Property))
			{
				ByteProperty->SetPropertyValue_InContainer(Object, AnimsetValue);
			}
		}
	}

	static const TCHAR* DefaultPistolMeshPath =
		TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Weapon/SKM_Pistol.SKM_Pistol");

	constexpr uint8 AnimsetPistol = 0;
	constexpr uint8 AnimsetRifle = 1;
	constexpr uint8 AnimsetShotgun = 2;
	constexpr uint8 AnimsetSniper = 3;
	constexpr uint8 AnimsetHands = 7;

	USkeletalMeshComponent* FindItemMeshOnActor(const AActor* Actor)
	{
		if (!Actor)
		{
			return nullptr;
		}

		TArray<USkeletalMeshComponent*> Meshes;
		Actor->GetComponents<USkeletalMeshComponent>(Meshes);
		for (USkeletalMeshComponent* Mesh : Meshes)
		{
			if (Mesh && Mesh->GetName() == TEXT("Item_Mesh"))
			{
				return Mesh;
			}
		}

		return nullptr;
	}

	const TCHAR* ResolveHoldAnimPath(const FString& WeaponMeshPath, const bool bAiming)
	{
		if (WeaponMeshPath.Contains(TEXT("Rifle")))
		{
			return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Rifle/Anim_Arms_AmericanRifle_Pose.Anim_Arms_AmericanRifle_Pose");
		}
		if (WeaponMeshPath.Contains(TEXT("Shotgun")))
		{
			return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Shotgun/Anim_Arms_Shotgun_Idle.Anim_Arms_Shotgun_Idle");
		}
		if (WeaponMeshPath.Contains(TEXT("Sniper")))
		{
			return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Sniper/Anim_Arms_Sniper__Idle.Anim_Arms_Sniper__Idle");
		}

		if (bAiming)
		{
			return TEXT("/Game/SCAR580/Animations/Anim_Arms_Pistol_ADS.Anim_Arms_Pistol_ADS");
		}

		return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Anim_Arms_Pistol_Idle.Anim_Arms_Pistol_Idle");
	}

	const TCHAR* ResolveActionAnimPath(const FString& WeaponMeshPath, const ESCARAvatarAnimAction Action)
	{
		const bool bPistol = WeaponMeshPath.IsEmpty() || WeaponMeshPath.Contains(TEXT("Pistol"));
		const bool bRifle = WeaponMeshPath.Contains(TEXT("Rifle"));
		const bool bShotgun = WeaponMeshPath.Contains(TEXT("Shotgun"));
		const bool bSniper = WeaponMeshPath.Contains(TEXT("Sniper"));

		switch (Action)
		{
		case ESCARAvatarAnimAction::Fire:
			if (bRifle)
			{
				return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Rifle/Anim_Arms_AmericanRifle_Fire.Anim_Arms_AmericanRifle_Fire");
			}
			if (bShotgun)
			{
				return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Shotgun/Anim_Arms_Shotgun_Fire.Anim_Arms_Shotgun_Fire");
			}
			if (bSniper)
			{
				return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Sniper/Anim_Arms_Sniper_FireShort.Anim_Arms_Sniper_FireShort");
			}
			return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Anim_Arms_Pistol_Fire.Anim_Arms_Pistol_Fire");

		case ESCARAvatarAnimAction::ReloadEmpty:
			if (bRifle)
			{
				return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Rifle/Anim_Arms_AmericanRifle_ReloadEmpty.Anim_Arms_AmericanRifle_ReloadEmpty");
			}
			if (bSniper)
			{
				return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Sniper/Anim_Arms_Sniper_Reload_Empty.Anim_Arms_Sniper_Reload_Empty");
			}
			if (bPistol || (!bRifle && !bShotgun && !bSniper))
			{
				return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Anim_Arms_Pistol_ReloadEmpty.Anim_Arms_Pistol_ReloadEmpty");
			}
			// fall through
		case ESCARAvatarAnimAction::Reload:
			if (bRifle)
			{
				return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Rifle/Anim_Arms_AmericanRifle_Reload.Anim_Arms_AmericanRifle_Reload");
			}
			if (bShotgun)
			{
				return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Shotgun/Anim_Arms_Shotgun_ReloadBegin.Anim_Arms_Shotgun_ReloadBegin");
			}
			if (bSniper)
			{
				return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Sniper/Anim_Arms_Sniper_Reload.Anim_Arms_Sniper_Reload");
			}
			return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Anim_Arms_Pistol_Reload.Anim_Arms_Pistol_Reload");

		default:
			return nullptr;
		}
	}
}

USCARAvatarWeaponSyncComponent::USCARAvatarWeaponSyncComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickGroup = TG_PrePhysics;

	static const TCHAR* PrecachePaths[] = {
		TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Anim_Arms_Pistol_Idle.Anim_Arms_Pistol_Idle"),
		TEXT("/Game/SCAR580/Animations/Anim_Arms_Pistol_ADS.Anim_Arms_Pistol_ADS"),
		TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Anim_Arms_Pistol_Fire.Anim_Arms_Pistol_Fire"),
		TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Anim_Arms_Pistol_Reload.Anim_Arms_Pistol_Reload"),
		TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Anim_Arms_Pistol_ReloadEmpty.Anim_Arms_Pistol_ReloadEmpty"),
		TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Rifle/Anim_Arms_AmericanRifle_Pose.Anim_Arms_AmericanRifle_Pose"),
		TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Shotgun/Anim_Arms_Shotgun_Idle.Anim_Arms_Shotgun_Idle"),
		TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Sniper/Anim_Arms_Sniper__Idle.Anim_Arms_Sniper__Idle"),
		TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Weapon/SKM_Pistol.SKM_Pistol"),
	};

	for (const TCHAR* Path : PrecachePaths)
	{
		if (FString(Path).Contains(TEXT("SKM_Pistol")))
		{
			ConstructorHelpers::FObjectFinder<USkeletalMesh> MeshFinder(Path);
			if (MeshFinder.Succeeded())
			{
				WeaponMeshCache.Add(Path, MeshFinder.Object);
			}
			continue;
		}

		ConstructorHelpers::FObjectFinder<UAnimSequenceBase> AnimFinder(Path);
		if (AnimFinder.Succeeded())
		{
			HoldAnimCache.Add(Path, AnimFinder.Object);
		}
	}
}

void USCARAvatarWeaponSyncComponent::TickComponent(
	const float DeltaTime,
	const ELevelTick TickType,
	FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	const APlayerController* LocalPC = Cast<APlayerController>(GetOwner());
	UWorld* World = GetWorld();
	if (!World || !LocalPC || !LocalPC->IsLocalController())
	{
		return;
	}

	APawn* LocalPawn = LocalPC->GetPawn();
	if (!LocalPawn)
	{
		return;
	}

	const double Now = World->GetTimeSeconds();
	const double SampleInterval = 1.0 / static_cast<double>(FMath::Max(SampleRateHz, 1.f));
	if (Now - LastSampleSeconds >= SampleInterval)
	{
		LastSampleSeconds = Now;
		SampleAndSendLocalLoadout(LocalPawn);
	}

	// Fire / reload must be sampled every tick — a 10Hz loadout poll misses short
	// CrosshairFireAlpha spikes and HandsSlot montages.
	SampleAndSendLocalAnimActions(LocalPawn);

	UpdateRemoteAvatarWeapons(LocalPC, LocalPawn);
}

void USCARAvatarWeaponSyncComponent::SampleAndSendLocalLoadout(APawn* LocalPawn)
{
	ASCARARMultiplayerPlayerState* LoadoutState =
		LocalPawn->GetPlayerState<ASCARARMultiplayerPlayerState>();
	if (!LoadoutState)
	{
		return;
	}

	FLocalLoadoutSample Sample;
	if (!ReadLocalLoadout(LocalPawn, Sample))
	{
		return;
	}

	const bool bLoadoutChanged =
		!bHasSentLoadout ||
		Sample.WeaponMeshPath != LastSentSample.WeaponMeshPath ||
		Sample.WeaponId != LastSentSample.WeaponId ||
		Sample.bAiming != LastSentSample.bAiming ||
		Sample.AttachSocket != LastSentSample.AttachSocket ||
		!Sample.RelativeLocation.Equals(LastSentSample.RelativeLocation, 0.01f) ||
		!Sample.RelativeRotation.Equals(LastSentSample.RelativeRotation, 0.01f);

	if (bLoadoutChanged)
	{
		LoadoutState->Server_UpdateAvatarLoadout(
			Sample.WeaponMeshPath,
			Sample.WeaponId,
			Sample.bAiming,
			Sample.AttachSocket,
			Sample.RelativeLocation,
			Sample.RelativeRotation);
		LastSentSample = Sample;
		bHasSentLoadout = true;
	}
}

void USCARAvatarWeaponSyncComponent::SampleAndSendLocalAnimActions(APawn* LocalPawn)
{
	ASCARARMultiplayerPlayerState* LoadoutState =
		LocalPawn->GetPlayerState<ASCARARMultiplayerPlayerState>();
	if (!LoadoutState)
	{
		return;
	}

	const ESCARAvatarAnimAction Action = DetectLocalAnimAction(LocalPawn);
	const UWorld* World = GetWorld();
	const double Now = World ? World->GetTimeSeconds() : 0.0;

	if (Action == ESCARAvatarAnimAction::Fire)
	{
		if (Now - LastFireNotifySeconds >= 0.07)
		{
			LastFireNotifySeconds = Now;
			LoadoutState->Server_NotifyAvatarAnimAction(static_cast<uint8>(Action));
		}
	}
	else if (
		Action == ESCARAvatarAnimAction::Reload ||
		Action == ESCARAvatarAnimAction::ReloadEmpty)
	{
		if (!bReloadActionLatched && Now - LastReloadNotifySeconds >= 0.2)
		{
			bReloadActionLatched = true;
			LastReloadNotifySeconds = Now;
			LoadoutState->Server_NotifyAvatarAnimAction(static_cast<uint8>(Action));
		}
	}
	else
	{
		bReloadActionLatched = false;
	}

	LastDetectedAction = Action;
}

bool USCARAvatarWeaponSyncComponent::ReadLocalLoadout(
	APawn* LocalPawn,
	FLocalLoadoutSample& OutSample) const
{
	OutSample = FLocalLoadoutSample();

	GetByteProperty(LocalPawn, TEXT("EquippedWeapon"), OutSample.WeaponId);
	GetBoolProperty(LocalPawn, TEXT("IsAim"), OutSample.bAiming);

	bool bEquipped = false;
	bool bIsWeapon = false;
	GetBoolProperty(LocalPawn, TEXT("Equipped"), bEquipped);
	GetBoolProperty(LocalPawn, TEXT("IsWeapon"), bIsWeapon);

	if (const USkeletalMeshComponent* ItemMesh = FindHeldItemMesh(LocalPawn))
	{
		if (const USkeletalMesh* MeshAsset = ItemMesh->GetSkeletalMeshAsset())
		{
			OutSample.WeaponMeshPath = MeshAsset->GetPathName();
		}

		OutSample.AttachSocket = ItemMesh->GetAttachSocketName();
		OutSample.RelativeLocation = ItemMesh->GetRelativeLocation();
		OutSample.RelativeRotation = ItemMesh->GetRelativeRotation();
	}

	if (OutSample.WeaponMeshPath.IsEmpty() && (bEquipped || bIsWeapon || OutSample.bAiming))
	{
		OutSample.WeaponMeshPath = DefaultPistolMeshPath;
	}

	return true;
}

ESCARAvatarAnimAction USCARAvatarWeaponSyncComponent::DetectLocalAnimAction(APawn* LocalPawn)
{
	if (!LocalPawn)
	{
		return ESCARAvatarAnimAction::None;
	}

	// Prefer FP arm / weapon montages — the kit plays Fire/Reload there.
	if (IsLocalAnimInstancePlayingAction(LocalPawn, ESCARAvatarAnimAction::ReloadEmpty))
	{
		return ESCARAvatarAnimAction::ReloadEmpty;
	}
	if (IsLocalAnimInstancePlayingAction(LocalPawn, ESCARAvatarAnimAction::Reload))
	{
		return ESCARAvatarAnimAction::Reload;
	}
	if (IsLocalAnimInstancePlayingAction(LocalPawn, ESCARAvatarAnimAction::Fire))
	{
		return ESCARAvatarAnimAction::Fire;
	}

	float FireAlpha = 0.f;
	if (GetFloatProperty(LocalPawn, TEXT("CrosshairFireAlpha"), FireAlpha))
	{
		const bool bRisingEdge = FireAlpha > 0.08f && LastFireAlpha <= 0.08f;
		LastFireAlpha = FireAlpha;
		if (bRisingEdge)
		{
			return ESCARAvatarAnimAction::Fire;
		}
	}

	const int32 Ammo = ReadHeldWeaponAmmo(LocalPawn);
	if (Ammo >= 0)
	{
		if (bHasKnownAmmo)
		{
			if (Ammo < LastKnownAmmo)
			{
				LastKnownAmmo = Ammo;
				return ESCARAvatarAnimAction::Fire;
			}
			if (Ammo > LastKnownAmmo)
			{
				LastKnownAmmo = Ammo;
				return ESCARAvatarAnimAction::Reload;
			}
		}
		LastKnownAmmo = Ammo;
		bHasKnownAmmo = true;
	}

	return ESCARAvatarAnimAction::None;
}

bool USCARAvatarWeaponSyncComponent::IsLocalAnimInstancePlayingAction(
	APawn* LocalPawn,
	const ESCARAvatarAnimAction Action) const
{
	if (!LocalPawn)
	{
		return false;
	}

	FString WeaponPath;
	if (const USkeletalMeshComponent* ItemMesh = FindHeldItemMesh(LocalPawn))
	{
		if (const USkeletalMesh* MeshAsset = ItemMesh->GetSkeletalMeshAsset())
		{
			WeaponPath = MeshAsset->GetPathName();
		}
	}

	UAnimSequenceBase* ActionAnim = const_cast<USCARAvatarWeaponSyncComponent*>(this)
										->ResolveActionAnimation(WeaponPath, Action);
	if (!ActionAnim)
	{
		return false;
	}

	static const FName SlotNames[] = {
		FName(TEXT("DefaultSlot")),
		FName(TEXT("UpperBody")),
		FName(TEXT("Hands")),
		FName(TEXT("Weapon")),
		FName(TEXT("FullBody")),
	};

	TArray<UAnimInstance*> AnimInstances;

	if (UAnimInstance* Hands = Cast<UAnimInstance>(GetObjectProperty(LocalPawn, TEXT("HandsSlot"))))
	{
		AnimInstances.Add(Hands);
	}
	if (UAnimInstance* AnimBP = Cast<UAnimInstance>(GetObjectProperty(LocalPawn, TEXT("AnimBP"))))
	{
		AnimInstances.Add(AnimBP);
	}

	TArray<USkeletalMeshComponent*> Meshes;
	LocalPawn->GetComponents<USkeletalMeshComponent>(Meshes);
	for (USkeletalMeshComponent* Mesh : Meshes)
	{
		if (Mesh && Mesh->GetAnimInstance())
		{
			AnimInstances.AddUnique(Mesh->GetAnimInstance());
		}
	}

	if (const USkeletalMeshComponent* ItemMesh = FindHeldItemMesh(LocalPawn))
	{
		if (UAnimInstance* ItemAnim = ItemMesh->GetAnimInstance())
		{
			AnimInstances.AddUnique(ItemAnim);
		}
	}

	for (UAnimInstance* AnimInstance : AnimInstances)
	{
		if (!AnimInstance)
		{
			continue;
		}

		if (const UAnimMontage* Montage = AnimInstance->GetCurrentActiveMontage())
		{
			const FString MontageName = Montage->GetName();
			if (Action == ESCARAvatarAnimAction::Fire && MontageName.Contains(TEXT("Fire")))
			{
				return true;
			}
			if ((Action == ESCARAvatarAnimAction::Reload || Action == ESCARAvatarAnimAction::ReloadEmpty) &&
				MontageName.Contains(TEXT("Reload")))
			{
				return true;
			}
		}

		for (const FName SlotName : SlotNames)
		{
			if (AnimInstance->IsPlayingSlotAnimation(ActionAnim, SlotName))
			{
				return true;
			}
		}
	}

	return false;
}

int32 USCARAvatarWeaponSyncComponent::ReadHeldWeaponAmmo(APawn* LocalPawn) const
{
	AActor* WeaponActor = nullptr;
	for (const FName PropertyName : {FName(TEXT("SpawnedItemRef")), FName(TEXT("SpawnedItem"))})
	{
		WeaponActor = Cast<AActor>(GetObjectProperty(LocalPawn, PropertyName));
		if (WeaponActor)
		{
			break;
		}
	}

	if (!WeaponActor)
	{
		return -1;
	}

	static const TCHAR* AmmoHints[] = {
		TEXT("Ammo"),
		TEXT("CurrentAmmo"),
		TEXT("MagazineAmmo"),
		TEXT("ClipAmmo"),
		TEXT("Bullets"),
		TEXT("Rounds"),
	};

	for (TFieldIterator<FProperty> It(WeaponActor->GetClass()); It; ++It)
	{
		FProperty* Property = *It;
		if (!Property)
		{
			continue;
		}

		const FString Name = Property->GetName();
		bool bMatch = false;
		for (const TCHAR* Hint : AmmoHints)
		{
			if (Name.Contains(Hint))
			{
				bMatch = true;
				break;
			}
		}
		if (!bMatch || Name.Contains(TEXT("Max")) || Name.Contains(TEXT("Reserve")))
		{
			continue;
		}

		if (const FIntProperty* IntProperty = CastField<FIntProperty>(Property))
		{
			return IntProperty->GetPropertyValue_InContainer(WeaponActor);
		}
		if (const FByteProperty* ByteProperty = CastField<FByteProperty>(Property))
		{
			return static_cast<int32>(ByteProperty->GetPropertyValue_InContainer(WeaponActor));
		}
		if (const FFloatProperty* FloatProperty = CastField<FFloatProperty>(Property))
		{
			return FMath::RoundToInt(FloatProperty->GetPropertyValue_InContainer(WeaponActor));
		}
	}

	return -1;
}

USkeletalMeshComponent* USCARAvatarWeaponSyncComponent::FindHeldItemMesh(APawn* Pawn) const
{
	for (const FName PropertyName : {FName(TEXT("SpawnedItemRef")), FName(TEXT("SpawnedItem"))})
	{
		if (const AActor* ItemActor = Cast<AActor>(GetObjectProperty(Pawn, PropertyName)))
		{
			if (USkeletalMeshComponent* ItemMesh = FindItemMeshOnActor(ItemActor))
			{
				if (ItemMesh->GetSkeletalMeshAsset())
				{
					return ItemMesh;
				}
			}
		}
	}

	TArray<AActor*> AttachedActors;
	Pawn->GetAttachedActors(AttachedActors, true, true);
	for (const AActor* AttachedActor : AttachedActors)
	{
		if (!AttachedActor || AttachedActor->IsHidden())
		{
			continue;
		}

		if (USkeletalMeshComponent* ItemMesh = FindItemMeshOnActor(AttachedActor))
		{
			if (ItemMesh->GetSkeletalMeshAsset() && ItemMesh->IsVisible())
			{
				return ItemMesh;
			}
		}
	}

	return nullptr;
}

void USCARAvatarWeaponSyncComponent::UpdateRemoteAvatarWeapons(
	const APlayerController* LocalPC,
	const APawn* LocalPawn)
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	for (TActorIterator<APawn> It(World); It; ++It)
	{
		APawn* Pawn = *It;
		if (!Pawn || Pawn == LocalPawn || Pawn->IsLocallyControlled())
		{
			continue;
		}

		const ASCARARMultiplayerPlayerState* LoadoutState =
			Pawn->GetPlayerState<ASCARARMultiplayerPlayerState>();
		if (!LoadoutState)
		{
			continue;
		}

		if (LocalPC->PlayerState && LoadoutState == LocalPC->PlayerState)
		{
			continue;
		}

		ApplyLoadoutToRemotePawn(Pawn, LoadoutState);
	}
}

void USCARAvatarWeaponSyncComponent::ApplyLoadoutToRemotePawn(
	APawn* Pawn,
	const ASCARARMultiplayerPlayerState* LoadoutState)
{
	FString WeaponMeshPath = LoadoutState->HeldWeaponMeshPath;
	if (WeaponMeshPath.IsEmpty() &&
		(LoadoutState->bAvatarAiming || LoadoutState->EquippedWeaponId != 0))
	{
		WeaponMeshPath = DefaultPistolMeshPath;
	}

	const bool bArmed = !WeaponMeshPath.IsEmpty();
	const bool bAiming = LoadoutState->bAvatarAiming;

	SetPawnStanceVariables(Pawn, LoadoutState->EquippedWeaponId, bAiming, bArmed);
	DestroyLeftoverAdsDrivers(Pawn);

	USkeletalMeshComponent* BodyMesh = nullptr;
	TArray<USkeletalMeshComponent*> Meshes;
	Pawn->GetComponents<USkeletalMeshComponent>(Meshes);
	for (USkeletalMeshComponent* Mesh : Meshes)
	{
		if (Mesh && Mesh->GetName() == BodyMeshComponentName.ToString())
		{
			BodyMesh = Mesh;
			break;
		}
	}

	if (!BodyMesh)
	{
		return;
	}

	EnsureMannyAnimBP(Pawn, BodyMesh);
	ApplyWeaponStance(Pawn, BodyMesh, WeaponMeshPath, bArmed, bAiming);
	ApplyAvatarAction(
		Pawn,
		BodyMesh,
		static_cast<ESCARAvatarAnimAction>(LoadoutState->AvatarAnimAction),
		LoadoutState->AvatarAnimActionSerial,
		WeaponMeshPath);

	USkeletalMeshComponent* WeaponComponent = EnsureAvatarWeaponComponent(Pawn, BodyMesh);
	if (!WeaponComponent)
	{
		return;
	}

	if (!bArmed)
	{
		WeaponComponent->SetHiddenInGame(true);
		WeaponComponent->SetVisibility(false, true);
		return;
	}

	const FName DesiredSocket = FName(TEXT("ik_hand_gun"));
	const FName SocketToUse = BodyMesh->DoesSocketExist(DesiredSocket)
		? DesiredSocket
		: ResolveHandSocket(BodyMesh);

	WeaponComponent->SetUsingAbsoluteLocation(false);
	WeaponComponent->SetUsingAbsoluteRotation(false);
	WeaponComponent->SetUsingAbsoluteScale(false);
	WeaponComponent->AttachToComponent(
		BodyMesh,
		FAttachmentTransformRules::SnapToTargetIncludingScale,
		SocketToUse);
	WeaponComponent->SetRelativeLocation(FVector::ZeroVector);
	WeaponComponent->SetRelativeRotation(FRotator::ZeroRotator);
	WeaponComponent->SetRelativeScale3D(FVector::OneVector);

	if (USkeletalMesh* WeaponMesh = ResolveWeaponMesh(WeaponMeshPath))
	{
		if (WeaponComponent->GetSkeletalMeshAsset() != WeaponMesh)
		{
			WeaponComponent->SetSkeletalMesh(WeaponMesh);
		}

		WeaponComponent->SetHiddenInGame(false);
		WeaponComponent->SetVisibility(true, true);
		WeaponComponent->SetOwnerNoSee(false);
		WeaponComponent->SetOnlyOwnerSee(false);
	}

	HideDuplicatePresentationWeapons(Pawn);
}

void USCARAvatarWeaponSyncComponent::EnsureMannyAnimBP(
	APawn* Pawn,
	USkeletalMeshComponent* BodyMesh)
{
	if (!OriginalBodyAnimClasses.Contains(Pawn))
	{
		if (UClass* CurrentClass = BodyMesh->GetAnimClass())
		{
			OriginalBodyAnimClasses.Add(Pawn, CurrentClass);
		}
	}

	TSubclassOf<UAnimInstance> MannyClass = nullptr;
	if (const TSubclassOf<UAnimInstance>* OriginalClass = OriginalBodyAnimClasses.Find(Pawn))
	{
		MannyClass = *OriginalClass;
	}
	if (!MannyClass)
	{
		MannyClass = LoadClass<UAnimInstance>(
			nullptr,
			TEXT("/Game/BodycamFPSKIT/Demo/Character/Mannequins/Animations/ABP_Manny.ABP_Manny_C"));
		if (MannyClass)
		{
			OriginalBodyAnimClasses.Add(Pawn, MannyClass);
		}
	}

	if (!MannyClass)
	{
		return;
	}

	const bool bWrongMode = BodyMesh->GetAnimationMode() != EAnimationMode::AnimationBlueprint;
	const bool bWrongClass = BodyMesh->GetAnimClass() != MannyClass.Get();
	if (bWrongMode || bWrongClass || BodyMesh->GetAnimInstance() == nullptr)
	{
		BodyMesh->SetAnimationMode(EAnimationMode::AnimationBlueprint);
		BodyMesh->SetAnimInstanceClass(MannyClass);
		UE_LOG(
			LogSCARAvatarWeapon,
			Log,
			TEXT("Remote %s: restored ABP_Manny (look/aim/turn alive)"),
			*Pawn->GetName());
	}

	BodyMesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
	BodyMesh->bPauseAnims = false;
	BodyMesh->SetComponentTickEnabled(true);
}

void USCARAvatarWeaponSyncComponent::ApplyWeaponStance(
	APawn* Pawn,
	USkeletalMeshComponent* BodyMesh,
	const FString& WeaponMeshPath,
	const bool bArmed,
	const bool bAiming)
{
	const uint8 Animset = bArmed ? ResolveAnimsetForWeapon(WeaponMeshPath) : AnimsetHands;

	ForceAnimsetProperty(Pawn, Animset);
	SetByteProperty(Pawn, TEXT("EquippedGunSet"), Animset);

	UAnimInstance* AnimInstance = BodyMesh->GetAnimInstance();
	if (!AnimInstance)
	{
		return;
	}

	ForceAnimsetProperty(AnimInstance, Animset);
	SetByteProperty(AnimInstance, TEXT("EquippedAnimset"), Animset);
	SetBoolProperty(AnimInstance, TEXT("IsAiming"), bAiming);
	SetBoolProperty(AnimInstance, TEXT("IsAim"), bAiming);

	// Continuous UpperBody hold: ADS when aiming, kit idle otherwise.
	// Re-apply if Manny's turn logic StopSlotAnimation clears the slot.
	if (!bArmed)
	{
		return;
	}

	UAnimSequenceBase* HoldAnim = ResolveHoldAnimation(WeaponMeshPath, bAiming);
	if (!HoldAnim)
	{
		return;
	}

	const bool bActionPlaying = [&]()
	{
		if (UAnimSequenceBase* FireAnim = ResolveActionAnimation(WeaponMeshPath, ESCARAvatarAnimAction::Fire))
		{
			if (AnimInstance->IsPlayingSlotAnimation(FireAnim, UpperBodySlotName))
			{
				return true;
			}
		}
		if (UAnimSequenceBase* ReloadAnim = ResolveActionAnimation(WeaponMeshPath, ESCARAvatarAnimAction::Reload))
		{
			if (AnimInstance->IsPlayingSlotAnimation(ReloadAnim, UpperBodySlotName))
			{
				return true;
			}
		}
		if (UAnimSequenceBase* ReloadEmptyAnim =
				ResolveActionAnimation(WeaponMeshPath, ESCARAvatarAnimAction::ReloadEmpty))
		{
			if (AnimInstance->IsPlayingSlotAnimation(ReloadEmptyAnim, UpperBodySlotName))
			{
				return true;
			}
		}
		return false;
	}();

	if (bActionPlaying)
	{
		return;
	}

	if (!AnimInstance->IsPlayingSlotAnimation(HoldAnim, UpperBodySlotName))
	{
		AnimInstance->PlaySlotAnimationAsDynamicMontage(
			HoldAnim,
			UpperBodySlotName,
			0.15f,
			0.15f,
			1.f,
			1000);
	}
}

void USCARAvatarWeaponSyncComponent::ApplyAvatarAction(
	APawn* Pawn,
	USkeletalMeshComponent* BodyMesh,
	const ESCARAvatarAnimAction Action,
	const uint8 Serial,
	const FString& WeaponMeshPath)
{
	if (Action == ESCARAvatarAnimAction::None || Serial == 0)
	{
		return;
	}

	if (LastPlayedActionSerial.FindRef(Pawn) == Serial)
	{
		return;
	}

	// Fire/reload visuals (weapon mesh anim + muzzle FX) are played by
	// ASCARARMultiplayerPlayerState::Multicast_PlayAvatarAnimAction.
	// Do NOT play Anim_Arms_* Fire on UpperBody — that contorts Manny's hold.
	LastPlayedActionSerial.Add(Pawn, Serial);
}

void USCARAvatarWeaponSyncComponent::DestroyLeftoverAdsDrivers(APawn* Pawn)
{
	if (!Pawn)
	{
		return;
	}

	TArray<USkeletalMeshComponent*> Meshes;
	Pawn->GetComponents<USkeletalMeshComponent>(Meshes);
	for (USkeletalMeshComponent* Mesh : Meshes)
	{
		if (!Mesh)
		{
			continue;
		}

		const FString Name = Mesh->GetName();
		if (Name.Contains(TEXT("SCAR_ADSPoseDriver")) || Name.Contains(TEXT("ADSPoseDriver")))
		{
			Mesh->DestroyComponent();
		}
	}
}

void USCARAvatarWeaponSyncComponent::HideDuplicatePresentationWeapons(APawn* Pawn)
{
	if (!Pawn)
	{
		return;
	}

	TArray<USkeletalMeshComponent*> Meshes;
	Pawn->GetComponents<USkeletalMeshComponent>(Meshes);
	for (USkeletalMeshComponent* Mesh : Meshes)
	{
		if (!Mesh)
		{
			continue;
		}

		const FString Name = Mesh->GetName();
		if (Name.Contains(TEXT("OpponentWeapon")) || Name.Contains(TEXT("SCAR_OpponentWeapon")))
		{
			Mesh->SetHiddenInGame(true);
			Mesh->SetVisibility(false, true);
		}
	}
}

USkeletalMeshComponent* USCARAvatarWeaponSyncComponent::EnsureAvatarWeaponComponent(
	APawn* Pawn,
	USkeletalMeshComponent* BodyMesh)
{
	if (const TObjectPtr<USkeletalMeshComponent>* Existing = AvatarWeaponComponents.Find(Pawn))
	{
		if (*Existing && IsValid(*Existing))
		{
			return *Existing;
		}
	}

	const FName SocketName = ResolveHandSocket(BodyMesh);

	USkeletalMeshComponent* WeaponComponent =
		NewObject<USkeletalMeshComponent>(Pawn, TEXT("SCAR_AvatarWeapon"));
	if (!WeaponComponent)
	{
		return nullptr;
	}

	Pawn->AddInstanceComponent(WeaponComponent);
	WeaponComponent->SetupAttachment(BodyMesh, SocketName);
	WeaponComponent->RegisterComponent();
	WeaponComponent->AttachToComponent(
		BodyMesh,
		FAttachmentTransformRules::SnapToTargetIncludingScale,
		SocketName);

	WeaponComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	WeaponComponent->SetGenerateOverlapEvents(false);
	WeaponComponent->SetOwnerNoSee(false);
	WeaponComponent->SetOnlyOwnerSee(false);
	WeaponComponent->SetCastShadow(true);
	WeaponComponent->SetFirstPersonPrimitiveType(EFirstPersonPrimitiveType::WorldSpaceRepresentation);

	AvatarWeaponComponents.Add(Pawn, WeaponComponent);
	return WeaponComponent;
}

UAnimSequenceBase* USCARAvatarWeaponSyncComponent::ResolveHoldAnimation(
	const FString& WeaponMeshPath,
	const bool bAiming)
{
	const FString AnimPath = ResolveHoldAnimPath(WeaponMeshPath, bAiming);
	if (const TObjectPtr<UAnimSequenceBase>* Cached = HoldAnimCache.Find(AnimPath))
	{
		return *Cached;
	}

	UAnimSequenceBase* Anim = Cast<UAnimSequenceBase>(FSoftObjectPath(AnimPath).TryLoad());
	if (Anim)
	{
		HoldAnimCache.Add(AnimPath, Anim);
	}
	else
	{
		UE_LOG(LogSCARAvatarWeapon, Warning, TEXT("Failed to load hold animation '%s'"), *AnimPath);
	}

	return Anim;
}

UAnimSequenceBase* USCARAvatarWeaponSyncComponent::ResolveActionAnimation(
	const FString& WeaponMeshPath,
	const ESCARAvatarAnimAction Action)
{
	const TCHAR* AnimPath = ResolveActionAnimPath(WeaponMeshPath, Action);
	if (!AnimPath)
	{
		return nullptr;
	}

	if (const TObjectPtr<UAnimSequenceBase>* Cached = HoldAnimCache.Find(AnimPath))
	{
		return *Cached;
	}

	UAnimSequenceBase* Anim = Cast<UAnimSequenceBase>(FSoftObjectPath(AnimPath).TryLoad());
	if (Anim)
	{
		HoldAnimCache.Add(AnimPath, Anim);
	}

	return Anim;
}

USkeletalMesh* USCARAvatarWeaponSyncComponent::ResolveWeaponMesh(const FString& MeshPath)
{
	if (const TObjectPtr<USkeletalMesh>* Cached = WeaponMeshCache.Find(MeshPath))
	{
		return *Cached;
	}

	USkeletalMesh* MeshAsset = Cast<USkeletalMesh>(FSoftObjectPath(MeshPath).TryLoad());
	if (MeshAsset)
	{
		WeaponMeshCache.Add(MeshPath, MeshAsset);
	}
	else
	{
		UE_LOG(LogSCARAvatarWeapon, Warning, TEXT("Failed to load avatar weapon mesh '%s'"), *MeshPath);
	}

	return MeshAsset;
}

uint8 USCARAvatarWeaponSyncComponent::ResolveAnimsetForWeapon(const FString& WeaponMeshPath)
{
	if (WeaponMeshPath.Contains(TEXT("Rifle")))
	{
		return AnimsetRifle;
	}
	if (WeaponMeshPath.Contains(TEXT("Shotgun")))
	{
		return AnimsetShotgun;
	}
	if (WeaponMeshPath.Contains(TEXT("Sniper")))
	{
		return AnimsetSniper;
	}
	return AnimsetPistol;
}

FName USCARAvatarWeaponSyncComponent::ResolveHandSocket(const USkeletalMeshComponent* BodyMesh)
{
	static const FName SocketCandidates[] = {
		FName(TEXT("ik_hand_gun")),
		FName(TEXT("ik_hand_r")),
		FName(TEXT("hand_r")),
	};

	if (BodyMesh)
	{
		for (const FName SocketName : SocketCandidates)
		{
			if (BodyMesh->DoesSocketExist(SocketName))
			{
				return SocketName;
			}
		}
	}

	return FName(TEXT("hand_r"));
}

void USCARAvatarWeaponSyncComponent::SetPawnStanceVariables(
	APawn* Pawn,
	const uint8 WeaponId,
	const bool bAiming,
	const bool bArmed)
{
	SetByteProperty(Pawn, TEXT("EquippedWeapon"), WeaponId);
	SetBoolProperty(Pawn, TEXT("IsAim"), bAiming);
	SetBoolProperty(Pawn, TEXT("Equipped"), bArmed);
	SetBoolProperty(Pawn, TEXT("IsWeapon"), bArmed);
}
