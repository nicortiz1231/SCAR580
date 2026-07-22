#include "SCARHorrorKitZombieDirector.h"

#include "AIController.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequence.h"
#include "BrainComponent.h"
#include "Components/ActorComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Perception/AIPerceptionComponent.h"
#include "SCARSharedARGround.h"
#include "TimerManager.h"

namespace SCARHorrorKitZombieDirectorPrivate
{
	static constexpr float EnemyCapsuleHalfHeightCm = 88.f;
	static constexpr float AttackCooldownSeconds = 1.6f;
	static constexpr float PackAttackRecoverySeconds = 0.45f;
	static constexpr float AIStripDelaySeconds = 0.2f;
	static constexpr float ProneMeshExtraDropCm = 58.f;
	static constexpr float ProneDamageStunSeconds = 0.35f;
	static constexpr int32 DamageAnimCount = 6;

	static const TCHAR* DamageAnimAssets[DamageAnimCount] = {
		TEXT("anim_Taking_Damage_A"),
		TEXT("anim_Taking_Damage_B"),
		TEXT("anim_Taking_Damage_C"),
		TEXT("anim_Taking_Damage_D"),
		TEXT("anim_Taking_Damage_E"),
		TEXT("anim_Taking_Damage_F"),
	};

	/** Horror Kit–embedded pack clips share the kit mannequin skeleton. */
	static constexpr const TCHAR* PackAnimRoot =
		TEXT("/Game/FirstPersonHorrorKit/Demo/ZombieAnimationPack/Animations/Mannequin_UE5/");

	static constexpr const TCHAR* KitAnimClassPath =
		TEXT("/Game/FirstPersonHorrorKit/Characters/Enemy/ABP_Enemy.ABP_Enemy_C");

	/** Same slot ABP_Enemy uses for anim_Attack_A_Montage. */
	static const FName PackAnimSlot(TEXT("DefaultSlot"));

	struct FPackGait
	{
		const TCHAR* Name;
		const TCHAR* LocomotionAsset;
		const TCHAR* IdleAsset;
		const TCHAR* AttackAsset;
		float WalkSpeed;
		/** If true, never play standing clips (idle/attack) — stay on crawl/prone anims only. */
		bool bAlwaysProne;
	};

	/**
	 * One of each distinct locomotion style from the pack.
	 * PackEnemyCount indexes into this (wrapping if higher).
	 */
	static const FPackGait PackGaits[] = {
		// Crawl must never use standing idle/attack — that pops them upright then "falls" back down.
		{TEXT("Crawl"), TEXT("anim_Belly_Crawling_A"), TEXT("anim_Belly_Crawling_A"), TEXT("anim_Belly_Crawling_B"), 95.f, true},
		{TEXT("WalkA"), TEXT("anim_Walk_A"), TEXT("anim_Idle_A"), TEXT("anim_Attack_B"), 165.f, false},
		{TEXT("WalkB"), TEXT("anim_Walk_B"), TEXT("anim_Idle_B"), TEXT("anim_Attack_C"), 175.f, false},
		{TEXT("WalkC"), TEXT("anim_Walk_C"), TEXT("anim_Idle_A"), TEXT("anim_Attack_D"), 190.f, false},
		{TEXT("Run"), TEXT("anim_Run_A"), TEXT("anim_Idle_A"), TEXT("anim_Attack_A"), 380.f, false},
	};

	static constexpr int32 PackGaitCount = UE_ARRAY_COUNT(PackGaits);

	static FSoftObjectPath MakePackAnimPath(const TCHAR* AssetName)
	{
		return FSoftObjectPath(FString(PackAnimRoot) + AssetName + TEXT(".") + AssetName);
	}

	static UAnimSequence* LoadPackAnim(const TCHAR* AssetName)
	{
		return Cast<UAnimSequence>(MakePackAnimPath(AssetName).TryLoad());
	}

	static int32 ResolvePackGaitIndex(const int32 PackVariantIndex)
	{
		if (PackGaitCount <= 0)
		{
			return 0;
		}
		return ((PackVariantIndex % PackGaitCount) + PackGaitCount) % PackGaitCount;
	}

	static bool IsProneGait(const int32 PackVariantIndex)
	{
		return PackGaits[ResolvePackGaitIndex(PackVariantIndex)].bAlwaysProne;
	}

	static void ApplyProneMeshOffset(ACharacter* Enemy)
	{
		USkeletalMeshComponent* Mesh = Enemy ? Enemy->GetMesh() : nullptr;
		UCapsuleComponent* Capsule = Enemy ? Enemy->GetCapsuleComponent() : nullptr;
		if (!Mesh || !Capsule)
		{
			return;
		}

		const float HalfH = Capsule->GetScaledCapsuleHalfHeight();
		FVector Rel = Mesh->GetRelativeLocation();
		Rel.Z = -HalfH - ProneMeshExtraDropCm;
		Mesh->SetRelativeLocation(Rel);
	}

	static UClass* LoadKitAnimClass()
	{
		return LoadClass<UAnimInstance>(nullptr, KitAnimClassPath);
	}

	static UAnimInstance* EnsureKitAnimInstance(USkeletalMeshComponent* Mesh)
	{
		if (!Mesh)
		{
			return nullptr;
		}

		Mesh->bPauseAnims = false;
		Mesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;

		UClass* KitAnimClass = LoadKitAnimClass();
		if (!KitAnimClass)
		{
			return Mesh->GetAnimInstance();
		}

		// Keep kit ABP — never clear AnimClass (that caused T-pose when mode flipped back).
		if (Mesh->GetAnimClass() != KitAnimClass)
		{
			Mesh->SetAnimInstanceClass(KitAnimClass);
		}
		Mesh->SetAnimationMode(EAnimationMode::AnimationBlueprint);
		if (!Mesh->GetAnimInstance())
		{
			Mesh->InitAnim(/*bForceReinit=*/true);
		}

		if (UAnimInstance* Anim = Mesh->GetAnimInstance())
		{
			// Pack loco montages often carry root-motion tracks (in-place or authored).
			// Default RootMotionFromMontagesOnly then overrides CMC → walk-in-place.
			Anim->SetRootMotionMode(ERootMotionMode::IgnoreRootMotion);
			return Anim;
		}
		return nullptr;
	}

	static void ConfigurePackMovement(ACharacter* Enemy, const float WalkSpeed)
	{
		if (!Enemy)
		{
			return;
		}

		// Never apply anim root-motion translation — chase is CMC-driven.
		Enemy->SetAnimRootMotionTranslationScale(0.f);

		if (UCharacterMovementComponent* Move = Enemy->GetCharacterMovement())
		{
			Move->MaxWalkSpeed = WalkSpeed;
			Move->MaxAcceleration = 250.f;
			Move->bOrientRotationToMovement = true;
			Move->RotationRate = FRotator(0.f, 480.f, 0.f);
			Move->bUseControllerDesiredRotation = false;
			Move->bUseRVOAvoidance = false;
			Move->GravityScale = 1.f;
			Move->SetMovementMode(MOVE_Walking);
			Move->SetActive(true);
		}
	}
}

ASCARHorrorKitZombieDirector::ASCARHorrorKitZombieDirector()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.f;
	bReplicates = false;
}

void ASCARHorrorKitZombieDirector::BeginPlay()
{
	Super::BeginPlay();

	AttackMontage = Cast<UAnimMontage>(AttackMontagePath.TryLoad());
	PackAttackMontage = Cast<UAnimMontage>(PackAttackMontagePath.TryLoad());
	AttackRangeCmSq = FMath::Square(AttackRangeCm);

	if (ASCARSharedARGround* Ground = ASCARSharedARGround::FindInWorld(GetWorld()))
	{
		SyncToGround(Ground);
	}
}

void ASCARHorrorKitZombieDirector::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (!bEnemiesSpawned)
	{
		if (ASCARSharedARGround* Ground = ASCARSharedARGround::FindInWorld(GetWorld()))
		{
			SyncToGround(Ground);
		}
		return;
	}

	DriveEnemies(DeltaSeconds);
}

void ASCARHorrorKitZombieDirector::SyncToGround(ASCARSharedARGround* Ground)
{
	UWorld* World = GetWorld();
	if (!Ground || !World || World->GetNetMode() == NM_Client)
	{
		return;
	}

	const FVector GroundCenter = Ground->GetActorLocation();
	if (bEnemiesSpawned && bHasCachedGroundCenter
		&& FVector::Dist2D(GroundCenter, CachedGroundCenter) > 250.f)
	{
		ClearAllSpawnedEnemies();
	}

	CachedGroundCenter = GroundCenter;
	bHasCachedGroundCenter = true;
	SpawnEnemiesIfNeeded(Ground);
}

FVector ASCARHorrorKitZombieDirector::GetSpawnLocation(
	const ASCARSharedARGround* Ground,
	const int32 Index,
	const int32 Count,
	const float RadiusCm,
	const float PhaseRadians) const
{
	const float SurfaceZ = Ground->GetGroundSurfaceZ();
	const FVector Center = Ground->GetActorLocation();
	const float Angle =
		PhaseRadians + (2.f * PI * static_cast<float>(Index)) / static_cast<float>(FMath::Max(Count, 1));
	const float Radius = FMath::Min(RadiusCm, Ground->HalfExtentCm * 0.75f);

	return FVector(
		Center.X + FMath::Cos(Angle) * Radius,
		Center.Y + FMath::Sin(Angle) * Radius,
		SurfaceZ + SCARHorrorKitZombieDirectorPrivate::EnemyCapsuleHalfHeightCm);
}

APawn* ASCARHorrorKitZombieDirector::GetPlayerPawn() const
{
	return UGameplayStatics::GetPlayerPawn(GetWorld(), 0);
}

void ASCARHorrorKitZombieDirector::ApplyPackProneCrawl(
	ACharacter* Enemy,
	const int32 PackVariantIndex,
	const float WalkSpeed)
{
	if (!Enemy)
	{
		return;
	}

	USkeletalMeshComponent* Mesh = Enemy->GetMesh();
	if (!Mesh)
	{
		return;
	}

	using namespace SCARHorrorKitZombieDirectorPrivate;
	const int32 GaitIndex = ResolvePackGaitIndex(PackVariantIndex);
	const FPackGait& Gait = PackGaits[GaitIndex];

	UAnimSequence* Crawl = LoadPackAnim(Gait.LocomotionAsset);
	if (!Crawl)
	{
		return;
	}

	// Bypass kit ABP entirely — its standing Idle/Run blendspace was bleeding through the slot montage.
	Mesh->bPauseAnims = false;
	Mesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
	Mesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);
	Mesh->PlayAnimation(Crawl, /*bLooping=*/true);

	Enemy->SetAnimRootMotionTranslationScale(0.f);
	ConfigurePackMovement(Enemy, WalkSpeed);
	ApplyProneMeshOffset(Enemy);
	SnapEnemyToGround(Enemy);

	const int32 SpawnIndex = SpawnedEnemies.IndexOfByKey(Enemy);
	if (SpawnedEnemies.IsValidIndex(SpawnIndex))
	{
		if (!PackInMelee.IsValidIndex(SpawnIndex))
		{
			PackInMelee.SetNum(SpawnedEnemies.Num());
		}
		PackLocoMontages[SpawnIndex] = nullptr;
		PackInMelee[SpawnIndex] = WalkSpeed <= KINDA_SMALL_NUMBER;
	}
}

void ASCARHorrorKitZombieDirector::ApplyPackLocomotion(ACharacter* Enemy, const int32 PackVariantIndex)
{
	if (!Enemy)
	{
		return;
	}

	USkeletalMeshComponent* Mesh = Enemy->GetMesh();
	if (!Mesh)
	{
		return;
	}

	using namespace SCARHorrorKitZombieDirectorPrivate;
	const int32 GaitIndex = ResolvePackGaitIndex(PackVariantIndex);
	const FPackGait& Gait = PackGaits[GaitIndex];

	if (Gait.bAlwaysProne)
	{
		ApplyPackProneCrawl(Enemy, PackVariantIndex, Gait.WalkSpeed);
		return;
	}

	UAnimSequence* Locomotion = LoadPackAnim(Gait.LocomotionAsset);
	if (!Locomotion)
	{
		UE_LOG(
			LogTemp,
			Error,
			TEXT("SCAR HorrorKit: failed to load pack locomotion %s for gait %s"),
			Gait.LocomotionAsset,
			Gait.Name);
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(
				9210 + GaitIndex,
				8.f,
				FColor::Red,
				FString::Printf(TEXT("SCAR pack: missing anim %s"), Gait.LocomotionAsset));
		}
		return;
	}

	UAnimInstance* Anim = EnsureKitAnimInstance(Mesh);
	if (!Anim)
	{
		UE_LOG(LogTemp, Error, TEXT("SCAR HorrorKit: no AnimInstance on pack zombie %s"), *GetNameSafe(Enemy));
		return;
	}

	ConfigurePackMovement(Enemy, Gait.WalkSpeed);

	Anim->StopSlotAnimation(0.05f, PackAnimSlot);
	UAnimMontage* LocoMontage = Anim->PlaySlotAnimationAsDynamicMontage(
		Locomotion,
		PackAnimSlot,
		0.15f,
		0.15f,
		1.f,
		/*LoopCount=*/100000);

	const int32 SpawnIndex = SpawnedEnemies.IndexOfByKey(Enemy);
	if (SpawnedEnemies.IsValidIndex(SpawnIndex))
	{
		if (!PackLocoMontages.IsValidIndex(SpawnIndex))
		{
			PackLocoMontages.SetNum(SpawnedEnemies.Num());
		}
		if (!PackInMelee.IsValidIndex(SpawnIndex))
		{
			PackInMelee.SetNum(SpawnedEnemies.Num());
		}
		PackLocoMontages[SpawnIndex] = LocoMontage;
		PackInMelee[SpawnIndex] = false;
	}

	if (UCapsuleComponent* Capsule = Enemy->GetCapsuleComponent())
	{
		const float HalfH = Capsule->GetScaledCapsuleHalfHeight();
		FVector Rel = Mesh->GetRelativeLocation();
		Rel.Z = -HalfH;
		Mesh->SetRelativeLocation(Rel);
	}

	SnapEnemyToGround(Enemy);
}

void ASCARHorrorKitZombieDirector::ApplyPackIdle(ACharacter* Enemy, const int32 PackVariantIndex)
{
	if (!Enemy)
	{
		return;
	}

	USkeletalMeshComponent* Mesh = Enemy->GetMesh();
	if (!Mesh)
	{
		return;
	}

	using namespace SCARHorrorKitZombieDirectorPrivate;
	const int32 GaitIndex = ResolvePackGaitIndex(PackVariantIndex);
	const FPackGait& Gait = PackGaits[GaitIndex];

	if (Gait.bAlwaysProne)
	{
		// Stay on the same crawl loop — never swap to standing idle.
		ApplyPackProneCrawl(Enemy, PackVariantIndex, 0.f);
		return;
	}

	UAnimInstance* Anim = EnsureKitAnimInstance(Mesh);
	if (!Anim)
	{
		return;
	}

	// Stop chase motion so they plant instead of crawling/walking in place with translation.
	if (UCharacterMovementComponent* Move = Enemy->GetCharacterMovement())
	{
		Move->StopMovementImmediately();
		Move->Velocity = FVector::ZeroVector;
		Move->MaxWalkSpeed = 0.f;
	}
	Enemy->SetAnimRootMotionTranslationScale(0.f);
	Anim->SetRootMotionMode(ERootMotionMode::IgnoreRootMotion);

	const int32 SpawnIndex = SpawnedEnemies.IndexOfByKey(Enemy);

	// Prone crawler: keep the crawl loop forever — standing idle/attack pops them upright.
	const TCHAR* IdleName = Gait.bAlwaysProne ? Gait.LocomotionAsset : Gait.IdleAsset;
	UAnimSequence* Idle = LoadPackAnim(IdleName);
	if (!Idle && !Gait.bAlwaysProne)
	{
		Idle = LoadPackAnim(TEXT("anim_Idle_A"));
	}
	if (!Idle)
	{
		return;
	}

	if (SpawnedEnemies.IsValidIndex(SpawnIndex))
	{
		UAnimMontage* Current = PackLocoMontages.IsValidIndex(SpawnIndex) ? PackLocoMontages[SpawnIndex].Get() : nullptr;
		if (Current && Anim->Montage_IsPlaying(Current))
		{
			if (PackInMelee.IsValidIndex(SpawnIndex))
			{
				PackInMelee[SpawnIndex] = true;
			}
			return;
		}
	}

	Anim->StopSlotAnimation(Gait.bAlwaysProne ? 0.02f : 0.1f, PackAnimSlot);
	UAnimMontage* IdleMontage = Anim->PlaySlotAnimationAsDynamicMontage(
		Idle,
		PackAnimSlot,
		Gait.bAlwaysProne ? 0.05f : 0.2f,
		Gait.bAlwaysProne ? 0.05f : 0.2f,
		1.f,
		/*LoopCount=*/100000);

	if (SpawnedEnemies.IsValidIndex(SpawnIndex))
	{
		if (!PackLocoMontages.IsValidIndex(SpawnIndex))
		{
			PackLocoMontages.SetNum(SpawnedEnemies.Num());
		}
		if (!PackInMelee.IsValidIndex(SpawnIndex))
		{
			PackInMelee.SetNum(SpawnedEnemies.Num());
		}
		PackLocoMontages[SpawnIndex] = IdleMontage;
		PackInMelee[SpawnIndex] = true;
	}
}

void ASCARHorrorKitZombieDirector::ResumePackStance(ACharacter* Enemy, const int32 PackVariantIndex)
{
	if (!IsValid(Enemy))
	{
		return;
	}

	if (SCARHorrorKitZombieDirectorPrivate::IsProneGait(PackVariantIndex))
	{
		APawn* Player = GetPlayerPawn();
		const bool bInMelee = Player
			&& (Player->GetActorLocation() - Enemy->GetActorLocation()).SizeSquared2D() <= AttackRangeCmSq;
		const float Speed = bInMelee
			? 0.f
			: SCARHorrorKitZombieDirectorPrivate::PackGaits[
				SCARHorrorKitZombieDirectorPrivate::ResolvePackGaitIndex(PackVariantIndex)].WalkSpeed;
		ApplyPackProneCrawl(Enemy, PackVariantIndex, Speed);
		return;
	}

	APawn* Player = GetPlayerPawn();
	if (!Player)
	{
		ApplyPackLocomotion(Enemy, PackVariantIndex);
		return;
	}

	FVector ToPlayer = Player->GetActorLocation() - Enemy->GetActorLocation();
	ToPlayer.Z = 0.f;
	if (ToPlayer.SizeSquared() <= AttackRangeCmSq)
	{
		ApplyPackIdle(Enemy, PackVariantIndex);
	}
	else
	{
		ApplyPackLocomotion(Enemy, PackVariantIndex);
	}
}

void ASCARHorrorKitZombieDirector::SnapEnemyToGround(ACharacter* Enemy) const
{
	if (!IsValid(Enemy))
	{
		return;
	}

	float HalfH = SCARHorrorKitZombieDirectorPrivate::EnemyCapsuleHalfHeightCm;
	if (UCapsuleComponent* Capsule = Enemy->GetCapsuleComponent())
	{
		HalfH = Capsule->GetScaledCapsuleHalfHeight();
	}

	FVector Loc = Enemy->GetActorLocation();
	const float TargetZ = CachedGroundSurfaceZ + HalfH;
	if (!FMath::IsNearlyEqual(Loc.Z, TargetZ, 1.f))
	{
		Loc.Z = TargetZ;
		Enemy->SetActorLocation(Loc, false, nullptr, ETeleportType::TeleportPhysics);
	}

	if (UCharacterMovementComponent* Move = Enemy->GetCharacterMovement())
	{
		Move->Velocity = FVector(Move->Velocity.X, Move->Velocity.Y, 0.f);
		if (Move->MovementMode == MOVE_None || Move->MovementMode == MOVE_Falling)
		{
			Move->SetMovementMode(MOVE_Walking);
		}
	}
}

bool ASCARHorrorKitZombieDirector::IsManagedEnemy(const ACharacter* Enemy) const
{
	return IsValid(Enemy) && SpawnedEnemies.Contains(Enemy);
}

bool ASCARHorrorKitZombieDirector::TryResolveEnemyIndex(ACharacter* Enemy, int32& OutIndex) const
{
	OutIndex = SpawnedEnemies.IndexOfByKey(Enemy);
	return SpawnedEnemies.IsValidIndex(OutIndex) && IsValid(SpawnedEnemies[OutIndex]);
}

FSCARZombieHitResult ASCARHorrorKitZombieDirector::NotifyEnemyShot(ACharacter* Enemy, const float Damage)
{
	FSCARZombieHitResult Result;

	int32 Index = INDEX_NONE;
	if (!TryResolveEnemyIndex(Enemy, Index) || Damage <= 0.f)
	{
		return Result;
	}

	if (!EnemyHealthRemaining.IsValidIndex(Index))
	{
		EnemyHealthRemaining.SetNum(SpawnedEnemies.Num());
		for (int32 HealthIndex = 0; HealthIndex < EnemyHealthRemaining.Num(); ++HealthIndex)
		{
			if (EnemyHealthRemaining[HealthIndex] <= 0.f)
			{
				EnemyHealthRemaining[HealthIndex] = ZombieMaxHealth;
			}
		}
	}

	float& Health = EnemyHealthRemaining[Index];
	if (Health <= 0.f)
	{
		return Result;
	}

	const float Applied = FMath::Min(Damage, Health);
	Health = FMath::Max(0.f, Health - Applied);

	Result.bHit = true;
	Result.AppliedDamage = Applied;
	Result.RemainingHealth = Health;
	Result.HitEnemy = Enemy;

	TriggerDamageReaction(Enemy, Index);

	if (Health <= 0.f)
	{
		Result.bKilled = true;
		DestroyManagedEnemyAtIndex(Index);
	}

	return Result;
}

void ASCARHorrorKitZombieDirector::TriggerDamageReaction(ACharacter* Enemy, const int32 EnemyIndex)
{
	if (!IsValid(Enemy) || !SpawnedEnemies.IsValidIndex(EnemyIndex))
	{
		return;
	}

	using namespace SCARHorrorKitZombieDirectorPrivate;

	const bool bPack = SpawnedEnemyIsPack.IsValidIndex(EnemyIndex) && SpawnedEnemyIsPack[EnemyIndex];
	const int32 PackVariant =
		SpawnedEnemyPackVariant.IsValidIndex(EnemyIndex) ? SpawnedEnemyPackVariant[EnemyIndex] : 0;

	if (bPack && IsProneGait(PackVariant))
	{
		if (UCharacterMovementComponent* Move = Enemy->GetCharacterMovement())
		{
			Move->StopMovementImmediately();
			Move->Velocity = FVector::ZeroVector;
			Move->MaxWalkSpeed = 0.f;
		}
		if (PackAttackLockRemaining.IsValidIndex(EnemyIndex))
		{
			PackAttackLockRemaining[EnemyIndex] = ProneDamageStunSeconds;
		}
		return;
	}

	if (!DamageAnimVariant.IsValidIndex(EnemyIndex))
	{
		DamageAnimVariant.SetNum(SpawnedEnemies.Num());
	}

	const int32 AnimPick = DamageAnimVariant[EnemyIndex] % DamageAnimCount;
	DamageAnimVariant[EnemyIndex] = AnimPick + 1;

	UAnimSequence* DamageSeq = LoadPackAnim(DamageAnimAssets[AnimPick]);
	USkeletalMeshComponent* Mesh = Enemy->GetMesh();
	if (!DamageSeq || !Mesh)
	{
		return;
	}

	UAnimInstance* Anim = EnsureKitAnimInstance(Mesh);
	if (!Anim)
	{
		return;
	}

	Enemy->SetAnimRootMotionTranslationScale(0.f);
	Anim->SetRootMotionMode(ERootMotionMode::IgnoreRootMotion);

	const float Duration = FMath::Max(0.35f, DamageSeq->GetPlayLength());
	Anim->StopSlotAnimation(0.02f, PackAnimSlot);
	UAnimMontage* DamageMontage = Anim->PlaySlotAnimationAsDynamicMontage(
		DamageSeq,
		PackAnimSlot,
		0.05f,
		0.05f,
		1.f,
		/*LoopCount=*/1,
		/*BlendOutTriggerTime=*/-1.f,
		/*InTimeToStartMontageAt=*/0.f);

	if (PackAttackLockRemaining.IsValidIndex(EnemyIndex))
	{
		PackAttackLockRemaining[EnemyIndex] = Duration;
	}

	if (PackLocoMontages.IsValidIndex(EnemyIndex) && DamageMontage)
	{
		PackLocoMontages[EnemyIndex] = DamageMontage;
	}
	if (PackInMelee.IsValidIndex(EnemyIndex))
	{
		PackInMelee[EnemyIndex] = true;
	}

	if (bPack)
	{
		if (UWorld* World = GetWorld())
		{
			FTimerHandle ResumeHandle;
			TWeakObjectPtr<ACharacter> WeakEnemy(Enemy);
			const int32 Variant = PackVariant;
			World->GetTimerManager().SetTimer(
				ResumeHandle,
				FTimerDelegate::CreateLambda([this, WeakEnemy, Variant]()
				{
					if (ACharacter* Alive = WeakEnemy.Get())
					{
						ResumePackStance(Alive, Variant);
					}
				}),
				Duration,
				false);
		}
	}
}

ACharacter* ASCARHorrorKitZombieDirector::FindManagedEnemyUnderCrosshair(
	const FVector& ViewOrigin,
	const FVector& ViewDirection,
	const float MaxDistanceCm,
	const float MaxAngleDegrees) const
{
	const FVector ViewDir = ViewDirection.GetSafeNormal();
	if (ViewDir.IsNearlyZero() || MaxDistanceCm <= 0.f)
	{
		return nullptr;
	}

	const float MaxAngle = FMath::Max(1.f, MaxAngleDegrees);
	const float MaxAngleCos = FMath::Cos(FMath::DegreesToRadians(MaxAngle));
	const float MaxLineDistCm = 55.f;

	ACharacter* BestEnemy = nullptr;
	float BestScore = TNumericLimits<float>::Max();

	for (const TObjectPtr<ACharacter>& EnemyPtr : SpawnedEnemies)
	{
		ACharacter* Enemy = EnemyPtr.Get();
		if (!IsValid(Enemy))
		{
			continue;
		}

		float CapsuleRadius = 42.f;
		if (const UCapsuleComponent* Capsule = Enemy->GetCapsuleComponent())
		{
			CapsuleRadius = Capsule->GetScaledCapsuleRadius();
		}

		const FVector ToEnemy = Enemy->GetActorLocation() - ViewOrigin;
		const float Distance = ToEnemy.Size();
		if (Distance <= KINDA_SMALL_NUMBER || Distance > MaxDistanceCm)
		{
			continue;
		}

		const FVector ToEnemyDir = ToEnemy / Distance;
		const float Dot = FVector::DotProduct(ViewDir, ToEnemyDir);
		if (Dot < MaxAngleCos)
		{
			continue;
		}

		const float LineDist = FMath::PointDistToLine(Enemy->GetActorLocation(), ViewOrigin, ViewDir);
		if (LineDist > CapsuleRadius + MaxLineDistCm)
		{
			continue;
		}

		const float Score = Distance + (1.f - Dot) * 250.f + LineDist * 2.f;
		if (Score < BestScore)
		{
			BestScore = Score;
			BestEnemy = Enemy;
		}
	}

	return BestEnemy;
}

void ASCARHorrorKitZombieDirector::DestroyManagedEnemyAtIndex(const int32 EnemyIndex)
{
	if (!SpawnedEnemies.IsValidIndex(EnemyIndex))
	{
		return;
	}

	if (ACharacter* Enemy = SpawnedEnemies[EnemyIndex])
	{
		Enemy->Destroy();
	}

	SpawnedEnemies[EnemyIndex] = nullptr;
	if (EnemyHealthRemaining.IsValidIndex(EnemyIndex))
	{
		EnemyHealthRemaining[EnemyIndex] = 0.f;
	}
}

void ASCARHorrorKitZombieDirector::ClearAllSpawnedEnemies()
{
	for (ACharacter* Enemy : SpawnedEnemies)
	{
		if (IsValid(Enemy))
		{
			Enemy->Destroy();
		}
	}

	SpawnedEnemies.Reset();
	SpawnedEnemyIsPack.Reset();
	SpawnedEnemyPackVariant.Reset();
	AttackCooldownRemaining.Reset();
	PendingAIStrip.Reset();
	PendingAIStripIsPack.Reset();
	PendingAIStripPackVariant.Reset();
	PackLocoMontages.Reset();
	PackAttackLockRemaining.Reset();
	PackInMelee.Reset();
	EnemyHealthRemaining.Reset();
	DamageAnimVariant.Reset();
	bEnemiesSpawned = false;
}

void ASCARHorrorKitZombieDirector::PrepareEnemyForDirectChase(
	ACharacter* Enemy,
	const bool bPackEnemy,
	const int32 PackVariantIndex)
{
	if (!Enemy)
	{
		return;
	}

	Enemy->bUseControllerRotationYaw = false;

	if (UCharacterMovementComponent* Move = Enemy->GetCharacterMovement())
	{
		// Kit keep natural Horror Kit walk; pack overrides speed in ApplyPackLocomotion.
		Move->MaxWalkSpeed = ChaseWalkSpeed;
		Move->MaxAcceleration = 250.f;
		Move->bOrientRotationToMovement = true;
		Move->RotationRate = FRotator(0.f, 480.f, 0.f);
		Move->bUseControllerDesiredRotation = false;
		Move->bUseRVOAvoidance = false;
		Move->SetMovementMode(MOVE_Walking);
	}

	if (USkeletalMeshComponent* Mesh = Enemy->GetMesh())
	{
		Mesh->SetAllBodiesSimulatePhysics(false);
		Mesh->SetSimulatePhysics(false);

		if (bPackEnemy)
		{
			ApplyPackLocomotion(Enemy, PackVariantIndex);
		}
		else if (!Mesh->GetAnimInstance())
		{
			if (UClass* AnimClass = SCARHorrorKitZombieDirectorPrivate::LoadKitAnimClass())
			{
				Mesh->SetAnimInstanceClass(AnimClass);
			}
		}
	}

	// Perception is unused for direct chase — disable tick only, do not DestroyComponent.
	TArray<UActorComponent*> Components;
	Enemy->GetComponents(Components);
	for (UActorComponent* Comp : Components)
	{
		if (Comp && Comp->IsA<UAIPerceptionComponent>())
		{
			Comp->Deactivate();
			Comp->SetComponentTickEnabled(false);
		}
	}
}

void ASCARHorrorKitZombieDirector::FinalizeEnemyAIStrip(
	ACharacter* Enemy,
	const bool bPackEnemy,
	const int32 PackVariantIndex)
{
	if (!IsValid(Enemy))
	{
		return;
	}

	// Keep the AIController possessed — destroying it made chase feel sluggish.
	// Only stop the kit Behavior Tree / pathfollowing.
	if (AAIController* AIController = Cast<AAIController>(Enemy->GetController()))
	{
		AIController->StopMovement();
		if (UBrainComponent* Brain = AIController->GetBrainComponent())
		{
			Brain->StopLogic(TEXT("SCAR direct chase"));
		}
	}

	PrepareEnemyForDirectChase(Enemy, bPackEnemy, PackVariantIndex);
	SnapEnemyToGround(Enemy);
}

void ASCARHorrorKitZombieDirector::TriggerKitAttack(
	ACharacter* Enemy,
	const bool bPackEnemy,
	const int32 PackVariantIndex)
{
	if (!Enemy)
	{
		return;
	}

	if (bPackEnemy)
	{
		using namespace SCARHorrorKitZombieDirectorPrivate;
		const int32 GaitIndex = ResolvePackGaitIndex(PackVariantIndex);
		const FPackGait& Gait = PackGaits[GaitIndex];
		const int32 SpawnIndex = SpawnedEnemies.IndexOfByKey(Enemy);

		// Crawler: never touch standing attack/idle — keep SingleNode belly crawl only.
		if (Gait.bAlwaysProne)
		{
			if (AttackCooldownRemaining.IsValidIndex(SpawnIndex))
			{
				AttackCooldownRemaining[SpawnIndex] = AttackCooldownSeconds;
			}
			return;
		}

		UAnimSequence* AttackSeq = LoadPackAnim(Gait.AttackAsset);
		USkeletalMeshComponent* Mesh = Enemy->GetMesh();
		UAnimInstance* Anim = EnsureKitAnimInstance(Mesh);
		if (!AttackSeq || !Anim)
		{
			return;
		}

		const float Duration = FMath::Max(0.35f, AttackSeq->GetPlayLength());

		// Full clip: short blends, no early interrupt from idle/loco re-assert.
		Anim->StopSlotAnimation(0.02f, PackAnimSlot);
		UAnimMontage* AttackMontageDynamic = Anim->PlaySlotAnimationAsDynamicMontage(
			AttackSeq,
			PackAnimSlot,
			0.05f,
			0.05f,
			1.f,
			/*LoopCount=*/1,
			/*BlendOutTriggerTime=*/-1.f,
			/*InTimeToStartMontageAt=*/0.f);

		if (SpawnedEnemies.IsValidIndex(SpawnIndex))
		{
			if (PackAttackLockRemaining.IsValidIndex(SpawnIndex))
			{
				PackAttackLockRemaining[SpawnIndex] = Duration;
			}
			// Cooldown must cover the full attack — fixed 1.6s was cutting longer clips short.
			if (AttackCooldownRemaining.IsValidIndex(SpawnIndex))
			{
				AttackCooldownRemaining[SpawnIndex] = Duration + PackAttackRecoverySeconds;
			}
			if (PackLocoMontages.IsValidIndex(SpawnIndex) && AttackMontageDynamic)
			{
				PackLocoMontages[SpawnIndex] = AttackMontageDynamic;
			}
			if (PackInMelee.IsValidIndex(SpawnIndex))
			{
				PackInMelee[SpawnIndex] = true;
			}
		}

		if (UWorld* World = GetWorld())
		{
			FTimerHandle ResumeHandle;
			TWeakObjectPtr<ACharacter> WeakEnemy(Enemy);
			const int32 Variant = PackVariantIndex;
			World->GetTimerManager().SetTimer(
				ResumeHandle,
				FTimerDelegate::CreateLambda([this, WeakEnemy, Variant]()
				{
					if (ACharacter* Alive = WeakEnemy.Get())
					{
						ResumePackStance(Alive, Variant);
					}
				}),
				Duration,
				false);
		}
		return;
	}

	if (UFunction* AtackFn = Enemy->FindFunction(FName(TEXT("Atack"))))
	{
		Enemy->ProcessEvent(AtackFn, nullptr);
		return;
	}

	if (!AttackMontage)
	{
		AttackMontage = Cast<UAnimMontage>(AttackMontagePath.TryLoad());
	}
	if (AttackMontage)
	{
		if (UAnimInstance* Anim = Enemy->GetMesh() ? Enemy->GetMesh()->GetAnimInstance() : nullptr)
		{
			Anim->Montage_Play(AttackMontage);
		}
	}
}

void ASCARHorrorKitZombieDirector::DriveEnemies(float DeltaSeconds)
{
	APawn* Player = GetPlayerPawn();
	if (!Player)
	{
		return;
	}

	const FVector PlayerLoc = Player->GetActorLocation();
	const int32 Count = SpawnedEnemies.Num();

	for (int32 Index = 0; Index < Count; ++Index)
	{
		ACharacter* Enemy = SpawnedEnemies[Index];
		if (!IsValid(Enemy))
		{
			continue;
		}

		float& Cooldown = AttackCooldownRemaining[Index];
		Cooldown = FMath::Max(0.f, Cooldown - DeltaSeconds);

		if (PackAttackLockRemaining.IsValidIndex(Index))
		{
			PackAttackLockRemaining[Index] = FMath::Max(0.f, PackAttackLockRemaining[Index] - DeltaSeconds);
		}

		FVector ToPlayer = PlayerLoc - Enemy->GetActorLocation();
		ToPlayer.Z = 0.f;
		const float DistSq = ToPlayer.SizeSquared();
		if (DistSq < KINDA_SMALL_NUMBER)
		{
			continue;
		}

		const FVector Dir = ToPlayer.GetSafeNormal();
		Enemy->SetActorRotation(FRotator(0.f, Dir.Rotation().Yaw, 0.f));

		const bool bPack = SpawnedEnemyIsPack.IsValidIndex(Index) && SpawnedEnemyIsPack[Index];
		const int32 PackVariant =
			SpawnedEnemyPackVariant.IsValidIndex(Index) ? SpawnedEnemyPackVariant[Index] : 0;

		// Keep everyone on the AR floor — pack montages / spawn adjust can sink them under it.
		{
			float HalfH = SCARHorrorKitZombieDirectorPrivate::EnemyCapsuleHalfHeightCm;
			if (UCapsuleComponent* Capsule = Enemy->GetCapsuleComponent())
			{
				HalfH = Capsule->GetScaledCapsuleHalfHeight();
			}
			const float MinCenterZ = CachedGroundSurfaceZ + HalfH - 2.f;
			if (Enemy->GetActorLocation().Z < MinCenterZ)
			{
				SnapEnemyToGround(Enemy);
			}
		}

		// Pack stance: prone crawler uses SingleNode crawl only; others use slot montages.
		if (bPack && SCARHorrorKitZombieDirectorPrivate::IsProneGait(PackVariant))
		{
			USkeletalMeshComponent* Mesh = Enemy->GetMesh();
			const bool bInMelee = DistSq <= AttackRangeCmSq;
			const float Speed = bInMelee
				? 0.f
				: SCARHorrorKitZombieDirectorPrivate::PackGaits[
					SCARHorrorKitZombieDirectorPrivate::ResolvePackGaitIndex(PackVariant)].WalkSpeed;

			if (Mesh && Mesh->GetAnimationMode() != EAnimationMode::AnimationSingleNode)
			{
				ApplyPackProneCrawl(Enemy, PackVariant, Speed);
			}
			else if (UCharacterMovementComponent* Move = Enemy->GetCharacterMovement())
			{
				Move->MaxWalkSpeed = Speed;
			}
		}
		else if (bPack && (!PackAttackLockRemaining.IsValidIndex(Index) || PackAttackLockRemaining[Index] <= 0.f))
		{
			UAnimInstance* Anim = Enemy->GetMesh() ? Enemy->GetMesh()->GetAnimInstance() : nullptr;
			if (Anim)
			{
				Anim->SetRootMotionMode(ERootMotionMode::IgnoreRootMotion);
			}
			Enemy->SetAnimRootMotionTranslationScale(0.f);

			const bool bInMelee = DistSq <= AttackRangeCmSq;
			if (bInMelee)
			{
				if (!PackInMelee.IsValidIndex(Index) || !PackInMelee[Index])
				{
					ApplyPackIdle(Enemy, PackVariant);
				}
				else
				{
					UAnimMontage* Stance = PackLocoMontages.IsValidIndex(Index) ? PackLocoMontages[Index].Get() : nullptr;
					if (!Anim || !Stance || !Anim->Montage_IsPlaying(Stance))
					{
						ApplyPackIdle(Enemy, PackVariant);
					}
				}
			}
			else
			{
				if (PackInMelee.IsValidIndex(Index) && PackInMelee[Index])
				{
					ApplyPackLocomotion(Enemy, PackVariant);
				}
				else
				{
					UAnimMontage* Loco = PackLocoMontages.IsValidIndex(Index) ? PackLocoMontages[Index].Get() : nullptr;
					if (!Anim || !Loco || !Anim->Montage_IsPlaying(Loco))
					{
						ApplyPackLocomotion(Enemy, PackVariant);
					}
				}
			}
		}

		if (DistSq > AttackRangeCmSq)
		{
			if (bPack && SCARHorrorKitZombieDirectorPrivate::IsProneGait(PackVariant))
			{
				if (UCharacterMovementComponent* Move = Enemy->GetCharacterMovement())
				{
					Move->MaxWalkSpeed = SCARHorrorKitZombieDirectorPrivate::PackGaits[
						SCARHorrorKitZombieDirectorPrivate::ResolvePackGaitIndex(PackVariant)].WalkSpeed;
				}
			}
			Enemy->AddMovementInput(Dir, 1.f);
		}
		else
		{
			// Plant feet while attacking — no residual walk slide.
			if (bPack && !SCARHorrorKitZombieDirectorPrivate::IsProneGait(PackVariant))
			{
				if (UCharacterMovementComponent* Move = Enemy->GetCharacterMovement())
				{
					Move->StopMovementImmediately();
					Move->Velocity = FVector::ZeroVector;
				}
			}
			else if (bPack && SCARHorrorKitZombieDirectorPrivate::IsProneGait(PackVariant))
			{
				if (UCharacterMovementComponent* Move = Enemy->GetCharacterMovement())
				{
					Move->StopMovementImmediately();
					Move->Velocity = FVector::ZeroVector;
					Move->MaxWalkSpeed = 0.f;
				}
			}
			if (Cooldown <= 0.f)
			{
				const bool bPackAttackReady =
					!bPack
					|| !PackAttackLockRemaining.IsValidIndex(Index)
					|| PackAttackLockRemaining[Index] <= 0.f;
				if (bPackAttackReady)
				{
					TriggerKitAttack(Enemy, bPack, PackVariant);
					// Pack cooldown is set inside TriggerKitAttack to the full anim length.
					if (!bPack)
					{
						Cooldown = SCARHorrorKitZombieDirectorPrivate::AttackCooldownSeconds;
					}
				}
			}
		}
	}
}

void ASCARHorrorKitZombieDirector::SpawnEnemiesIfNeeded(const ASCARSharedARGround* Ground)
{
	if (bEnemiesSpawned || !Ground)
	{
		return;
	}

	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	AttackRangeCmSq = FMath::Square(AttackRangeCm);
	CachedGroundSurfaceZ = Ground->GetGroundSurfaceZ();

	const bool bNeedEnemyClass = EnemyCount > 0 || PackEnemyCount > 0;
	UClass* EnemyClass = bNeedEnemyClass ? EnemyClassPath.TryLoadClass<ACharacter>() : nullptr;
	if (bNeedEnemyClass && !EnemyClass)
	{
		UE_LOG(LogTemp, Error, TEXT("SCAR HorrorKit: failed to load enemy class %s"), *EnemyClassPath.ToString());
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(
				9201,
				12.f,
				FColor::Red,
				TEXT("SCAR: Failed to load FirstPersonHorrorKit BP_Enemy"));
		}
		return;
	}

	// Pack zombies spawn as kit BP_Enemy; distinct pack gaits are applied in ApplyPackLocomotion.
	(void)PackEnemyClassPath;

	if (!AttackMontage)
	{
		AttackMontage = Cast<UAnimMontage>(AttackMontagePath.TryLoad());
	}
	if (!PackAttackMontage)
	{
		PackAttackMontage = Cast<UAnimMontage>(PackAttackMontagePath.TryLoad());
	}

	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
	SpawnParams.Owner = this;

	SpawnedEnemies.Reset();
	SpawnedEnemyIsPack.Reset();
	SpawnedEnemyPackVariant.Reset();
	AttackCooldownRemaining.Reset();
	PendingAIStrip.Reset();
	PendingAIStripIsPack.Reset();
	PendingAIStripPackVariant.Reset();
	PackLocoMontages.Reset();
	PackAttackLockRemaining.Reset();
	PackInMelee.Reset();
	EnemyHealthRemaining.Reset();
	DamageAnimVariant.Reset();

	auto SpawnRing = [&](UClass* Class, const int32 Count, const float RadiusCm, const float Phase, const bool bPack)
	{
		if (!Class || Count <= 0)
		{
			return;
		}

		for (int32 Index = 0; Index < Count; ++Index)
		{
			const FVector Location = GetSpawnLocation(Ground, Index, Count, RadiusCm, Phase);
			const FVector ToCenter = Ground->GetActorLocation() - Location;
			const FRotator FaceCenter = ToCenter.IsNearlyZero()
				? FRotator::ZeroRotator
				: ToCenter.Rotation();

			ACharacter* Enemy = World->SpawnActor<ACharacter>(
				Class,
				Location,
				FRotator(0.f, FaceCenter.Yaw, 0.f),
				SpawnParams);
			if (!Enemy)
			{
				continue;
			}

			const int32 PackVariant = bPack ? Index : 0;
			SpawnedEnemies.Add(Enemy);
			SpawnedEnemyIsPack.Add(bPack);
			SpawnedEnemyPackVariant.Add(PackVariant);
			AttackCooldownRemaining.Add(0.f);
			PackLocoMontages.Add(nullptr);
			PackAttackLockRemaining.Add(0.f);
			PackInMelee.Add(false);
			EnemyHealthRemaining.Add(ZombieMaxHealth);
			DamageAnimVariant.Add(0);
			// Apply after registration so pack loco montage can be stored by index.
			PrepareEnemyForDirectChase(Enemy, bPack, PackVariant);
			SnapEnemyToGround(Enemy);
			PendingAIStrip.Add(Enemy);
			PendingAIStripIsPack.Add(bPack);
			PendingAIStripPackVariant.Add(PackVariant);
		}
	};

	SpawnRing(EnemyClass, EnemyCount, SpawnRadiusCm, 0.f, false);
	SpawnRing(EnemyClass, PackEnemyCount, PackSpawnRadiusCm, PackSpawnPhaseRadians, true);

	bEnemiesSpawned = SpawnedEnemies.Num() > 0;

	if (bEnemiesSpawned)
	{
		FTimerHandle StripHandle;
		World->GetTimerManager().SetTimer(
			StripHandle,
			FTimerDelegate::CreateLambda([this]()
			{
				const int32 PendingCount = PendingAIStrip.Num();
				for (int32 Index = 0; Index < PendingCount; ++Index)
				{
					const bool bPack = PendingAIStripIsPack.IsValidIndex(Index) && PendingAIStripIsPack[Index];
					const int32 PackVariant =
						PendingAIStripPackVariant.IsValidIndex(Index) ? PendingAIStripPackVariant[Index] : 0;
					FinalizeEnemyAIStrip(PendingAIStrip[Index], bPack, PackVariant);
				}
				PendingAIStrip.Reset();
				PendingAIStripIsPack.Reset();
				PendingAIStripPackVariant.Reset();
			}),
			SCARHorrorKitZombieDirectorPrivate::AIStripDelaySeconds,
			false);
	}

	int32 KitSpawned = 0;
	int32 PackSpawned = 0;
	for (const bool bPack : SpawnedEnemyIsPack)
	{
		if (bPack)
		{
			++PackSpawned;
		}
		else
		{
			++KitSpawned;
		}
	}

	if (GEngine && bEnemiesSpawned)
	{
		using namespace SCARHorrorKitZombieDirectorPrivate;
		FString GaitSummary;
		for (int32 Index = 0; Index < PackSpawned; ++Index)
		{
			const FPackGait& Gait = PackGaits[ResolvePackGaitIndex(Index)];
			if (!GaitSummary.IsEmpty())
			{
				GaitSummary += TEXT(", ");
			}
			GaitSummary += Gait.Name;
		}

		GEngine->AddOnScreenDebugMessage(
			9200,
			16.f,
			FColor::Green,
			FString::Printf(
				TEXT("SCAR zombies: kit %d + pack %d [%s]"),
				KitSpawned,
				PackSpawned,
				*GaitSummary));
	}

	UE_LOG(
		LogTemp,
		Warning,
		TEXT("SCAR HorrorKit: spawned kit %d/%d + pack %d/%d (one gait each)"),
		KitSpawned,
		EnemyCount,
		PackSpawned,
		PackEnemyCount);
}

ASCARHorrorKitZombieDirector* ASCARHorrorKitZombieDirector::FindInWorld(const UWorld* World)
{
	if (!World)
	{
		return nullptr;
	}

	TActorIterator<ASCARHorrorKitZombieDirector> It(World);
	return It ? *It : nullptr;
}

ASCARHorrorKitZombieDirector* ASCARHorrorKitZombieDirector::EnsureInWorld(UWorld* World)
{
	if (!World)
	{
		return nullptr;
	}

	if (ASCARHorrorKitZombieDirector* Existing = FindInWorld(World))
	{
		return Existing;
	}

	if (World->GetNetMode() == NM_Client)
	{
		return nullptr;
	}

	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

	return World->SpawnActor<ASCARHorrorKitZombieDirector>(
		ASCARHorrorKitZombieDirector::StaticClass(),
		FVector::ZeroVector,
		FRotator::ZeroRotator,
		SpawnParams);
}
