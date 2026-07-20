#include "SCARARMultiplayerPlayerState.h"

#include "Animation/AnimSequenceBase.h"
#include "Animation/AnimationAsset.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Net/UnrealNetwork.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "Particles/ParticleSystem.h"
#include "Sound/SoundBase.h"
#include "UObject/SoftObjectPath.h"

namespace
{
	const TCHAR* ResolveWeaponMeshActionAnimPath(const FString& WeaponMeshPath, const uint8 Action)
	{
		const bool bRifle = WeaponMeshPath.Contains(TEXT("Rifle"));
		const bool bShotgun = WeaponMeshPath.Contains(TEXT("Shotgun"));
		const bool bSniper = WeaponMeshPath.Contains(TEXT("Sniper"));

		if (Action == 1) // Fire
		{
			if (bRifle)
			{
				return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Rifle/Weapon/Anim_Weapon_AmericanRifle_Fire.Anim_Weapon_AmericanRifle_Fire");
			}
			if (bShotgun)
			{
				return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Shotgun/Weapon/Anim_Weapon_Shotgun_Fire.Anim_Weapon_Shotgun_Fire");
			}
			if (bSniper)
			{
				return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Sniper/Weapon/Anim_Weapon_Sniper_FireLong.Anim_Weapon_Sniper_FireLong");
			}
			return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Weapon/Anim_Weapon_Pistol_Fire.Anim_Weapon_Pistol_Fire");
		}

		// Reload / ReloadEmpty — weapon mesh cycles
		if (bRifle)
		{
			return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Rifle/Weapon/Anim_Weapon_AmericanRifle_Reload.Anim_Weapon_AmericanRifle_Reload");
		}
		if (bShotgun)
		{
			return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Shotgun/Weapon/Anim_Weapon_Shotgun_Reload.Anim_Weapon_Shotgun_Reload");
		}
		if (bSniper)
		{
			return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Sniper/Weapon/Anim_Weapon_Sniper_Reload.Anim_Weapon_Sniper_Reload");
		}
		if (Action == 3)
		{
			return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Weapon/Anim_Weapon_Pistol_ReloadEmpty.Anim_Weapon_Pistol_ReloadEmpty");
		}
		return TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Weapon/Anim_Weapon_Pistol_Reload.Anim_Weapon_Pistol_Reload");
	}

	const TCHAR* ResolveMuzzleFxPath(const FString& WeaponMeshPath)
	{
		if (WeaponMeshPath.Contains(TEXT("Rifle")) || WeaponMeshPath.Contains(TEXT("Sniper")))
		{
			return TEXT("/Game/BodycamFPSKIT/Demo/Lyra_Content/Effects/Particles/Weapons/NS_WeaponFire_MuzzleFlash_Rifle.NS_WeaponFire_MuzzleFlash_Rifle");
		}
		if (WeaponMeshPath.Contains(TEXT("Shotgun")))
		{
			return TEXT("/Game/BodycamFPSKIT/Demo/Lyra_Content/Effects/Particles/Weapons/NS_WeaponFire_Shotgun.NS_WeaponFire_Shotgun");
		}
		if (WeaponMeshPath.Contains(TEXT("Heavy")))
		{
			return TEXT("/Game/BodycamFPSKIT/Demo/Lyra_Content/Effects/Particles/Weapons/NS_WeaponHeavyPistolFire.NS_WeaponHeavyPistolFire");
		}
		return TEXT("/Game/BodycamFPSKIT/Demo/Lyra_Content/Effects/Particles/Weapons/NS_WeaponPistolFire.NS_WeaponPistolFire");
	}

	const TCHAR* ResolveFireSoundPath(const FString& WeaponMeshPath)
	{
		if (WeaponMeshPath.Contains(TEXT("Rifle")))
		{
			return TEXT("/Game/BodycamFPSKIT/Demo/Lyra_Content/Audio/Sounds/Weapons/Rifle2/MS_Weapons_Rifle2_Fire.MS_Weapons_Rifle2_Fire");
		}
		if (WeaponMeshPath.Contains(TEXT("Shotgun")))
		{
			return TEXT("/Game/BodycamFPSKIT/Demo/Lyra_Content/Audio/Sounds/Weapons/Shotgun/MS_Weapons_Shotgun_Fire.MS_Weapons_Shotgun_Fire");
		}
		if (WeaponMeshPath.Contains(TEXT("Heavy")))
		{
			return TEXT("/Game/BodycamFPSKIT/Audio/HeavyPistol/MS_HeavyPistolShoot.MS_HeavyPistolShoot");
		}
		return TEXT("/Game/BodycamFPSKIT/Audio/Pistol_Audio/MS_PistolShoot.MS_PistolShoot");
	}

	USkeletalMeshComponent* FindAvatarWeaponMesh(APawn* Pawn)
	{
		if (!Pawn)
		{
			return nullptr;
		}

		TArray<USkeletalMeshComponent*> Meshes;
		Pawn->GetComponents<USkeletalMeshComponent>(Meshes);
		for (USkeletalMeshComponent* Mesh : Meshes)
		{
			if (Mesh && Mesh->GetName().Contains(TEXT("SCAR_AvatarWeapon")))
			{
				return Mesh;
			}
		}
		return nullptr;
	}

	FName ResolveMuzzleSocket(const USkeletalMeshComponent* WeaponMesh)
	{
		static const FName Candidates[] = {
			FName(TEXT("MuzzleFlash")),
			FName(TEXT("Muzzle")),
			FName(TEXT("muzzle")),
			FName(TEXT("Barrel")),
			FName(TEXT("barrel")),
			FName(TEXT("Flash")),
			FName(TEXT("tip")),
		};

		if (WeaponMesh)
		{
			for (const FName SocketName : Candidates)
			{
				if (WeaponMesh->DoesSocketExist(SocketName))
				{
					return SocketName;
				}
			}
		}

		return NAME_None;
	}
}

ASCARARMultiplayerPlayerState::ASCARARMultiplayerPlayerState()
{
	bReplicates = true;
	SetNetUpdateFrequency(30.f);
}

void ASCARARMultiplayerPlayerState::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(ASCARARMultiplayerPlayerState, Kills);
	DOREPLIFETIME(ASCARARMultiplayerPlayerState, Deaths);
	DOREPLIFETIME(ASCARARMultiplayerPlayerState, HeldWeaponMeshPath);
	DOREPLIFETIME(ASCARARMultiplayerPlayerState, EquippedWeaponId);
	DOREPLIFETIME(ASCARARMultiplayerPlayerState, bAvatarAiming);
	DOREPLIFETIME(ASCARARMultiplayerPlayerState, HeldWeaponAttachSocket);
	DOREPLIFETIME(ASCARARMultiplayerPlayerState, HeldWeaponRelativeLocation);
	DOREPLIFETIME(ASCARARMultiplayerPlayerState, HeldWeaponRelativeRotation);
	DOREPLIFETIME(ASCARARMultiplayerPlayerState, AvatarAnimAction);
	DOREPLIFETIME(ASCARARMultiplayerPlayerState, AvatarAnimActionSerial);
}

void ASCARARMultiplayerPlayerState::Server_UpdateAvatarLoadout_Implementation(
	const FString& WeaponMeshPath,
	const uint8 WeaponId,
	const bool bAiming,
	const FName AttachSocket,
	const FVector RelativeLocation,
	const FRotator RelativeRotation)
{
	HeldWeaponMeshPath = WeaponMeshPath;
	EquippedWeaponId = WeaponId;
	bAvatarAiming = bAiming;
	HeldWeaponAttachSocket = AttachSocket;
	HeldWeaponRelativeLocation = RelativeLocation;
	HeldWeaponRelativeRotation = RelativeRotation;
}

void ASCARARMultiplayerPlayerState::Server_NotifyAvatarAnimAction_Implementation(const uint8 Action)
{
	if (Action == 0)
	{
		return;
	}

	const UWorld* World = GetWorld();
	const double Now = World ? World->GetTimeSeconds() : 0.0;
	if (Action == LastServerAvatarAction && Now - LastServerAvatarActionSeconds < 0.08)
	{
		return;
	}
	LastServerAvatarAction = Action;
	LastServerAvatarActionSeconds = Now;

	AvatarAnimAction = Action;
	++AvatarAnimActionSerial;
	if (AvatarAnimActionSerial == 0)
	{
		AvatarAnimActionSerial = 1;
	}

	Multicast_PlayAvatarAnimAction(Action, AvatarAnimActionSerial);
}

void ASCARARMultiplayerPlayerState::Multicast_PlayAvatarAnimAction_Implementation(
	const uint8 Action,
	const uint8 Serial)
{
	AvatarAnimAction = Action;
	AvatarAnimActionSerial = Serial;
	PlayAvatarActionOnPawn(Action);
}

void ASCARARMultiplayerPlayerState::PlayAvatarActionOnPawn(const uint8 Action) const
{
	APawn* Pawn = GetPawn();
	if (!Pawn || Action == 0)
	{
		return;
	}

	// Local player already sees FP weapon fire / muzzle FX.
	if (Pawn->IsLocallyControlled())
	{
		return;
	}

	USkeletalMeshComponent* WeaponMesh = FindAvatarWeaponMesh(Pawn);
	if (!WeaponMesh || !WeaponMesh->GetSkeletalMeshAsset())
	{
		return;
	}

	const FString& WeaponPath = HeldWeaponMeshPath;

	// Weapon mesh fire/reload — do NOT play full-body arm Fire montages on Manny
	// (those fight the hold pose and twist the arms).
	if (const TCHAR* WeaponAnimPath = ResolveWeaponMeshActionAnimPath(WeaponPath, Action))
	{
		if (UAnimationAsset* WeaponAnim =
				Cast<UAnimationAsset>(FSoftObjectPath(WeaponAnimPath).TryLoad()))
		{
			WeaponMesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);
			WeaponMesh->SetAnimation(WeaponAnim);
			WeaponMesh->Play(false);
		}
	}

	if (Action != 1) // Fire only for muzzle FX / sound
	{
		return;
	}

	const FName MuzzleSocket = ResolveMuzzleSocket(WeaponMesh);
	const FTransform SpawnTransform = MuzzleSocket.IsNone()
		? WeaponMesh->GetComponentTransform()
		: WeaponMesh->GetSocketTransform(MuzzleSocket);

	if (UNiagaraSystem* MuzzleFx = Cast<UNiagaraSystem>(
			FSoftObjectPath(ResolveMuzzleFxPath(WeaponPath)).TryLoad()))
	{
		if (MuzzleSocket.IsNone())
		{
			UNiagaraFunctionLibrary::SpawnSystemAtLocation(
				Pawn,
				MuzzleFx,
				SpawnTransform.GetLocation(),
				SpawnTransform.Rotator());
		}
		else
		{
			UNiagaraFunctionLibrary::SpawnSystemAttached(
				MuzzleFx,
				WeaponMesh,
				MuzzleSocket,
				FVector::ZeroVector,
				FRotator::ZeroRotator,
				EAttachLocation::SnapToTarget,
				true);
		}
	}
	else if (UParticleSystem* CascadeFlash = Cast<UParticleSystem>(FSoftObjectPath(
				 TEXT("/Game/BodycamFPSKIT/ParticleEffects/P_MuzzleFlash.P_MuzzleFlash"))
				 .TryLoad()))
	{
		UGameplayStatics::SpawnEmitterAttached(
			CascadeFlash,
			WeaponMesh,
			MuzzleSocket,
			FVector::ZeroVector,
			FRotator::ZeroRotator,
			EAttachLocation::SnapToTarget,
			true);
	}

	if (USoundBase* FireSound =
			Cast<USoundBase>(FSoftObjectPath(ResolveFireSoundPath(WeaponPath)).TryLoad()))
	{
		UGameplayStatics::PlaySoundAtLocation(Pawn, FireSound, SpawnTransform.GetLocation());
	}
}

void ASCARARMultiplayerPlayerState::RegisterKill()
{
	if (HasAuthority())
	{
		++Kills;
	}
}

void ASCARARMultiplayerPlayerState::RegisterDeath()
{
	if (HasAuthority())
	{
		++Deaths;
	}
}

void ASCARARMultiplayerPlayerState::OnRep_Kills()
{
}

void ASCARARMultiplayerPlayerState::OnRep_Deaths()
{
}
