#include "SCARHorrorKitZombieDirector.h"

#include "AIController.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "BrainComponent.h"
#include "Components/ActorComponent.h"
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
	static constexpr float AIStripDelaySeconds = 0.2f;
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

	SpawnEnemiesIfNeeded(Ground);
}

FVector ASCARHorrorKitZombieDirector::GetSpawnLocation(const ASCARSharedARGround* Ground, const int32 Index) const
{
	const float SurfaceZ = Ground->GetGroundSurfaceZ();
	const FVector Center = Ground->GetActorLocation();
	const float Angle = (2.f * PI * static_cast<float>(Index)) / static_cast<float>(FMath::Max(EnemyCount, 1));
	const float Radius = FMath::Min(SpawnRadiusCm, Ground->HalfExtentCm * 0.75f);

	return FVector(
		Center.X + FMath::Cos(Angle) * Radius,
		Center.Y + FMath::Sin(Angle) * Radius,
		SurfaceZ + SCARHorrorKitZombieDirectorPrivate::EnemyCapsuleHalfHeightCm);
}

APawn* ASCARHorrorKitZombieDirector::GetPlayerPawn() const
{
	return UGameplayStatics::GetPlayerPawn(GetWorld(), 0);
}

void ASCARHorrorKitZombieDirector::PrepareEnemyForDirectChase(ACharacter* Enemy)
{
	if (!Enemy)
	{
		return;
	}

	Enemy->bUseControllerRotationYaw = false;

	if (UCharacterMovementComponent* Move = Enemy->GetCharacterMovement())
	{
		// Match FirstPersonHorrorKit BP_Enemy CDO: MaxWalkSpeed=300, MaxAcceleration=250.
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
		// Soften kit physical-anim side effects without destroying the component
		// (BP BeginPlay Physical_Animation still needs it alive).
		Mesh->SetAllBodiesSimulatePhysics(false);
		Mesh->SetSimulatePhysics(false);

		if (!Mesh->GetAnimInstance())
		{
			if (UClass* AnimClass = LoadClass<UAnimInstance>(
					nullptr,
					TEXT("/Game/FirstPersonHorrorKit/Characters/Enemy/ABP_Enemy.ABP_Enemy_C")))
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

void ASCARHorrorKitZombieDirector::FinalizeEnemyAIStrip(ACharacter* Enemy)
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

	PrepareEnemyForDirectChase(Enemy);
}

void ASCARHorrorKitZombieDirector::TriggerKitAttack(ACharacter* Enemy)
{
	if (!Enemy)
	{
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

		FVector ToPlayer = PlayerLoc - Enemy->GetActorLocation();
		ToPlayer.Z = 0.f;
		const float DistSq = ToPlayer.SizeSquared();
		if (DistSq < KINDA_SMALL_NUMBER)
		{
			continue;
		}

		const FVector Dir = ToPlayer.GetSafeNormal();
		Enemy->SetActorRotation(FRotator(0.f, Dir.Rotation().Yaw, 0.f));

		if (DistSq > AttackRangeCmSq)
		{
			Enemy->AddMovementInput(Dir, 1.f);
		}
		else if (Cooldown <= 0.f)
		{
			TriggerKitAttack(Enemy);
			Cooldown = SCARHorrorKitZombieDirectorPrivate::AttackCooldownSeconds;
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

	UClass* EnemyClass = EnemyClassPath.TryLoadClass<ACharacter>();
	if (!EnemyClass)
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

	if (!AttackMontage)
	{
		AttackMontage = Cast<UAnimMontage>(AttackMontagePath.TryLoad());
	}

	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
	SpawnParams.Owner = this;

	SpawnedEnemies.Reset();
	AttackCooldownRemaining.Reset();
	PendingAIStrip.Reset();

	for (int32 Index = 0; Index < EnemyCount; ++Index)
	{
		const FVector Location = GetSpawnLocation(Ground, Index);
		const FVector ToCenter = Ground->GetActorLocation() - Location;
		const FRotator FaceCenter = ToCenter.IsNearlyZero()
			? FRotator::ZeroRotator
			: ToCenter.Rotation();

		ACharacter* Enemy = World->SpawnActor<ACharacter>(
			EnemyClass,
			Location,
			FRotator(0.f, FaceCenter.Yaw, 0.f),
			SpawnParams);
		if (!Enemy)
		{
			continue;
		}

		PrepareEnemyForDirectChase(Enemy);
		SpawnedEnemies.Add(Enemy);
		AttackCooldownRemaining.Add(0.f);
		PendingAIStrip.Add(Enemy);
	}

	bEnemiesSpawned = SpawnedEnemies.Num() > 0;

	if (bEnemiesSpawned)
	{
		FTimerHandle StripHandle;
		World->GetTimerManager().SetTimer(
			StripHandle,
			FTimerDelegate::CreateLambda([this]()
			{
				for (ACharacter* Enemy : PendingAIStrip)
				{
					FinalizeEnemyAIStrip(Enemy);
				}
				PendingAIStrip.Reset();
			}),
			SCARHorrorKitZombieDirectorPrivate::AIStripDelaySeconds,
			false);
	}

	if (GEngine && bEnemiesSpawned)
	{
		GEngine->AddOnScreenDebugMessage(
			9200,
			12.f,
			FColor::Green,
			FString::Printf(
				TEXT("SCAR zombies: kit walk speed %.0f cm/s (restart editor if still fast)"),
				ChaseWalkSpeed));
	}

	UE_LOG(
		LogTemp,
		Warning,
		TEXT("SCAR HorrorKit: spawned %d/%d zombies — kit default walk %.0f cm/s"),
		SpawnedEnemies.Num(),
		EnemyCount,
		ChaseWalkSpeed);
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
