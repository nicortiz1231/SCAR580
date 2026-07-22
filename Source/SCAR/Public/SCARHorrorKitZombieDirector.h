#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SCARHorrorKitZombieDirector.generated.h"

class ASCARSharedARGround;
class ACharacter;
class UAnimMontage;

/**
 * Spawns FirstPersonHorrorKit BP_Enemy zombies and drives a cheap direct chase.
 * Kit ABP_Enemy / BS_Walk_Speed handles locomotion anims from movement speed.
 */
UCLASS()
class SCAR_API ASCARHorrorKitZombieDirector : public AActor
{
	GENERATED_BODY()

public:
	ASCARHorrorKitZombieDirector();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|HorrorKit", meta = (ClampMin = "1", ClampMax = "20"))
	int32 EnemyCount = 5;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|HorrorKit", meta = (ClampMin = "100"))
	float SpawnRadiusCm = 900.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|HorrorKit", meta = (ClampMin = "50"))
	float ChaseWalkSpeed = 650.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|HorrorKit", meta = (ClampMin = "50"))
	float AttackRangeCm = 160.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|HorrorKit")
	FSoftClassPath EnemyClassPath =
		FSoftClassPath(TEXT("/Game/FirstPersonHorrorKit/Blueprints/Enemy/BP_Enemy.BP_Enemy_C"));

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|HorrorKit")
	FSoftObjectPath AttackMontagePath = FSoftObjectPath(
		TEXT("/Game/FirstPersonHorrorKit/Demo/ZombieAnimationPack/Animations/Mannequin_UE5/anim_Attack_A_Montage.anim_Attack_A_Montage"));

	UFUNCTION(BlueprintCallable, Category = "SCAR|HorrorKit")
	void SyncToGround(ASCARSharedARGround* Ground);

	static ASCARHorrorKitZombieDirector* FindInWorld(const UWorld* World);
	static ASCARHorrorKitZombieDirector* EnsureInWorld(UWorld* World);

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	void SpawnEnemiesIfNeeded(const ASCARSharedARGround* Ground);
	void DriveEnemies(float DeltaSeconds);
	void PrepareEnemyForDirectChase(ACharacter* Enemy);
	void FinalizeEnemyAIStrip(ACharacter* Enemy);
	void TriggerKitAttack(ACharacter* Enemy);
	FVector GetSpawnLocation(const ASCARSharedARGround* Ground, int32 Index) const;
	APawn* GetPlayerPawn() const;

	UPROPERTY()
	TArray<TObjectPtr<ACharacter>> SpawnedEnemies;

	UPROPERTY()
	TObjectPtr<UAnimMontage> AttackMontage;

	/** Parallel cooldown timers (same index as SpawnedEnemies). */
	TArray<float> AttackCooldownRemaining;

	/** Enemies that still need a one-shot AI strip after possession. */
	UPROPERTY()
	TArray<TObjectPtr<ACharacter>> PendingAIStrip;

	float AttackRangeCmSq = 0.f;
	bool bEnemiesSpawned = false;
};
