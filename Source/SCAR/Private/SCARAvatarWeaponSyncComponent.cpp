#include "SCARAvatarWeaponSyncComponent.h"

#include "Animation/AnimInstance.h"
#include "Animation/AnimSequenceBase.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "SCARARMultiplayerPlayerState.h"
#include "UObject/ConstructorHelpers.h"
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

	void SetByteProperty(UObject* Object, const FName PropertyName, const uint8 Value)
	{
		if (!Object)
		{
			return;
		}

		if (const FByteProperty* Property =
				CastField<FByteProperty>(Object->GetClass()->FindPropertyByName(PropertyName)))
		{
			Property->SetPropertyValue_InContainer(Object, Value);
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

	// Full-body true-FPS hold animations. Pistol uses a generated ADS variant
	// of the kit's idle (Scripts/make_pistol_ads_anim.py): same grip and aim
	// orientation, but arms IK-extended forward. Others are kit anims on
	// SK_Mannequin, the same skeleton as the SKM_Manny avatar body.
	const TCHAR* ResolveHoldAnimPath(const FString& WeaponMeshPath)
	{
		if (WeaponMeshPath.Contains(TEXT("Pistol")))
		{
			return TEXT("/Game/SCAR580/Animations/Anim_Arms_Pistol_ADS.Anim_Arms_Pistol_ADS");
		}
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

		// Knife/grenade/unknown: default to the pistol hold rather than the
		// unarmed boxing idle so the item is at least gripped believably.
		return TEXT("/Game/SCAR580/Animations/Anim_Arms_Pistol_ADS.Anim_Arms_Pistol_ADS");
	}
}

USCARAvatarWeaponSyncComponent::USCARAvatarWeaponSyncComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	// After gameplay/anim ticks so stance variables written here are stable
	// for next frame's anim evaluation and never race the kit's own logic.
	PrimaryComponentTick.TickGroup = TG_PostUpdateWork;

	// Hard-reference the hold animations so they are always cooked into
	// device builds even though gameplay only loads them by path.
	static const TCHAR* HoldAnimPaths[] = {
		TEXT("/Game/SCAR580/Animations/Anim_Arms_Pistol_ADS.Anim_Arms_Pistol_ADS"),
		TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Rifle/Anim_Arms_AmericanRifle_Pose.Anim_Arms_AmericanRifle_Pose"),
		TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Shotgun/Anim_Arms_Shotgun_Idle.Anim_Arms_Shotgun_Idle"),
		TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Sniper/Anim_Arms_Sniper__Idle.Anim_Arms_Sniper__Idle"),
	};

	for (const TCHAR* AnimPath : HoldAnimPaths)
	{
		ConstructorHelpers::FObjectFinder<UAnimSequenceBase> AnimFinder(AnimPath);
		if (AnimFinder.Succeeded())
		{
			HoldAnimCache.Add(AnimPath, AnimFinder.Object);
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

	// During the join window our own pawn exists but is not possessed yet and
	// would look "remote"; never touch any pawn until possession completes.
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

	if (bHasSentLoadout && Sample == LastSentSample)
	{
		return;
	}

	LoadoutState->Server_UpdateAvatarLoadout(
		Sample.WeaponMeshPath,
		Sample.WeaponId,
		Sample.bAiming,
		Sample.AttachSocket,
		Sample.RelativeLocation,
		Sample.RelativeRotation);
	LastSentSample = Sample;
	bHasSentLoadout = true;

	UE_LOG(
		LogSCARAvatarWeapon,
		Log,
		TEXT("Sent avatar loadout: weapon='%s' id=%d aiming=%d socket='%s' relLoc=%s relRot=%s"),
		*Sample.WeaponMeshPath,
		Sample.WeaponId,
		Sample.bAiming ? 1 : 0,
		*Sample.AttachSocket.ToString(),
		*Sample.RelativeLocation.ToString(),
		*Sample.RelativeRotation.ToString());
}

bool USCARAvatarWeaponSyncComponent::ReadLocalLoadout(
	APawn* LocalPawn,
	FLocalLoadoutSample& OutSample) const
{
	OutSample = FLocalLoadoutSample();

	GetByteProperty(LocalPawn, TEXT("EquippedWeapon"), OutSample.WeaponId);
	GetBoolProperty(LocalPawn, TEXT("IsAim"), OutSample.bAiming);

	if (const USkeletalMeshComponent* ItemMesh = FindHeldItemMesh(LocalPawn))
	{
		if (const USkeletalMesh* MeshAsset = ItemMesh->GetSkeletalMeshAsset())
		{
			OutSample.WeaponMeshPath = MeshAsset->GetPathName();
		}

		// The kit's ChangeWeaponSocket/SocketOffset already placed this mesh
		// perfectly on the owner's body; capture that placement verbatim so
		// remote machines can reproduce the exact grip.
		OutSample.AttachSocket = ItemMesh->GetAttachSocketName();
		OutSample.RelativeLocation = ItemMesh->GetRelativeLocation();
		OutSample.RelativeRotation = ItemMesh->GetRelativeRotation();
	}

	return true;
}

USkeletalMeshComponent* USCARAvatarWeaponSyncComponent::FindHeldItemMesh(APawn* Pawn) const
{
	// The kit stores the currently held item actor in SpawnedItemRef /
	// SpawnedItem; prefer those over scanning so weapon swaps are exact.
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

	// Fallback: first visible Item_Mesh among attached item actors.
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

		// Extra identity check: never treat a pawn owned by the local player
		// state as remote (covers possession races during join).
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
	const bool bArmed = !LoadoutState->HeldWeaponMeshPath.IsEmpty();

	// Keep the remote pawn's kit variables mirroring its owner so any kit
	// logic keying off them behaves consistently.
	SetPawnStanceVariables(Pawn, LoadoutState->EquippedWeaponId, LoadoutState->bAvatarAiming, bArmed);

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

	ApplyHoldAnimationToBody(Pawn, BodyMesh, LoadoutState->HeldWeaponMeshPath, bArmed);

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

	// Reproduce the owner's exact attachment: same socket on the same body
	// skeleton, same per-weapon grip offset applied by the kit.
	const FName DesiredSocket = (LoadoutState->HeldWeaponAttachSocket != NAME_None &&
			BodyMesh->DoesSocketExist(LoadoutState->HeldWeaponAttachSocket))
		? LoadoutState->HeldWeaponAttachSocket
		: ResolveHandSocket(BodyMesh);

	if (WeaponComponent->GetAttachParent() != BodyMesh ||
		WeaponComponent->GetAttachSocketName() != DesiredSocket)
	{
		WeaponComponent->AttachToComponent(
			BodyMesh,
			FAttachmentTransformRules::SnapToTargetIncludingScale,
			DesiredSocket);
	}

	WeaponComponent->SetRelativeLocation(LoadoutState->HeldWeaponRelativeLocation);
	WeaponComponent->SetRelativeRotation(LoadoutState->HeldWeaponRelativeRotation);

	if (USkeletalMesh* WeaponMesh = ResolveWeaponMesh(LoadoutState->HeldWeaponMeshPath))
	{
		if (WeaponComponent->GetSkeletalMeshAsset() != WeaponMesh)
		{
			WeaponComponent->SetSkeletalMesh(WeaponMesh);
		}

		WeaponComponent->SetHiddenInGame(false);
		WeaponComponent->SetVisibility(true, true);
	}
}

void USCARAvatarWeaponSyncComponent::ApplyHoldAnimationToBody(
	APawn* Pawn,
	USkeletalMeshComponent* BodyMesh,
	const FString& WeaponMeshPath,
	const bool bArmed)
{
	if (!bArmed)
	{
		// Restore the kit's locomotion anim blueprint when unarmed.
		if (const TObjectPtr<UAnimSequenceBase>* Applied = AppliedHoldAnims.Find(Pawn))
		{
			if (*Applied)
			{
				if (const TSubclassOf<UAnimInstance>* OriginalClass = OriginalBodyAnimClasses.Find(Pawn))
				{
					BodyMesh->SetAnimationMode(EAnimationMode::AnimationBlueprint);
					BodyMesh->SetAnimInstanceClass(*OriginalClass);
				}
				AppliedHoldAnims.Add(Pawn, nullptr);
			}
		}
		return;
	}

	UAnimSequenceBase* HoldAnim = ResolveHoldAnimation(WeaponMeshPath);
	if (!HoldAnim)
	{
		return;
	}

	const TObjectPtr<UAnimSequenceBase>* Applied = AppliedHoldAnims.Find(Pawn);
	if (Applied && *Applied == HoldAnim)
	{
		return;
	}

	if (!OriginalBodyAnimClasses.Contains(Pawn))
	{
		OriginalBodyAnimClasses.Add(Pawn, BodyMesh->GetAnimClass());
	}

	// The default ABP_Manny on this body only knows unarmed locomotion, so
	// override it with the ADS weapon-hold pose (same skeleton/data the FPS
	// player's own pose uses).
	BodyMesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);
	BodyMesh->PlayAnimation(HoldAnim, true);
	AppliedHoldAnims.Add(Pawn, HoldAnim);

	UE_LOG(
		LogSCARAvatarWeapon,
		Log,
		TEXT("Applied hold animation '%s' to %s"),
		*HoldAnim->GetName(),
		*Pawn->GetName());
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

	UE_LOG(
		LogSCARAvatarWeapon,
		Log,
		TEXT("Attached avatar weapon to %s at socket '%s'"),
		*Pawn->GetName(),
		*SocketName.ToString());

	return WeaponComponent;
}

UAnimSequenceBase* USCARAvatarWeaponSyncComponent::ResolveHoldAnimation(const FString& WeaponMeshPath)
{
	const FString AnimPath = ResolveHoldAnimPath(WeaponMeshPath);
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

USkeletalMesh* USCARAvatarWeaponSyncComponent::ResolveWeaponMesh(const FString& MeshPath)
{
	if (const TObjectPtr<USkeletalMesh>* Cached = WeaponMeshCache.Find(MeshPath))
	{
		return *Cached;
	}

	USkeletalMesh* MeshAsset = Cast<USkeletalMesh>(
		FSoftObjectPath(MeshPath).TryLoad());
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
