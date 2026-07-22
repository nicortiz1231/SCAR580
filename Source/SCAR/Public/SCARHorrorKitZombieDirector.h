#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SCARHorrorKitZombieTypes.h"
#include "SCARHorrorKitZombieDirector.generated.h"

class ASCARSharedARGround;
class ACharacter;
class UAnimMontage;
class UAnimSequence;

	/**
 * Spawns FirstPersonHorrorKit BP_Enemy zombies (kit AnimBP) plus optional extra
 * pack-animated zombies that each play a distinct locomotion clip from the
 * Zombie Animation Pack (crawl / walk styles / run).
 *
 * Pack pawns use kit BP_Enemy + kit ABP_Enemy (DefaultSlot), and override the
 * pose with a looping dynamic montage of the pack clip. Clearing AnimClass /
 * AnimationSingleNode caused T-pose when the mesh fell back to AnimBlueprint
 * with no instance.
 */
UCLASS()
class SCAR_API ASCARHorrorKitZombieDirector : public AActor
{
	GENERATED_BODY()

public:
	ASCARHorrorKitZombieDirector();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|HorrorKit", meta = (ClampMin = "0", ClampMax = "20"))
	int32 EnemyCount = 4;

	/**
	 * Extra kit BP_Enemy instances that use pack locomotion clips.
	 * Keep equal to EnemyCount so both waves match; indexes into crawl/walk/run gaits.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|HorrorKit", meta = (ClampMin = "0", ClampMax = "20"))
	int32 PackEnemyCount = 4;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|HorrorKit", meta = (ClampMin = "100"))
	float SpawnRadiusCm = 900.f;

	/** Pack ring radius (slightly tighter than kit so groups don't stack). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|HorrorKit", meta = (ClampMin = "100"))
	float PackSpawnRadiusCm = 750.f;

	/** Radians phase offset for the pack ring so pack zombies sit between kit ones. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|HorrorKit")
	float PackSpawnPhaseRadians = 0.628319f; // ~36 deg = PI/5

	/** Kit BP_Enemy CharacterMovement default (300). Keep this for the natural walk pace. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|HorrorKit", meta = (ClampMin = "50"))
	float ChaseWalkSpeed = 300.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|HorrorKit", meta = (ClampMin = "50"))
	float AttackRangeCm = 160.f;

	/** Health for each spawned zombie (kit + pack). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|HorrorKit", meta = (ClampMin = "1"))
	float ZombieMaxHealth = 100.f;

	/** Default per-shot damage when the weapon does not supply a value. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|HorrorKit", meta = (ClampMin = "1"))
	float ZombieShotDamage = 25.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|HorrorKit")
	FSoftClassPath EnemyClassPath =
		FSoftClassPath(TEXT("/Game/FirstPersonHorrorKit/Blueprints/Enemy/BP_Enemy.BP_Enemy_C"));

	/** Unused for spawn (kept for compatibility). Pack zombies spawn as EnemyClassPath. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|HorrorKit")
	FSoftClassPath PackEnemyClassPath =
		FSoftClassPath(TEXT("/Game/SCAR580/Zombies/BP_Enemy_ZombiePack.BP_Enemy_ZombiePack_C"));

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|HorrorKit")
	FSoftObjectPath AttackMontagePath = FSoftObjectPath(
		TEXT("/Game/FirstPersonHorrorKit/Demo/ZombieAnimationPack/Animations/Mannequin_UE5/anim_Attack_A_Montage.anim_Attack_A_Montage"));

	/** Legacy path — pack attacks now use AnimSequences (SingleNode), not this montage. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|HorrorKit")
	FSoftObjectPath PackAttackMontagePath = FSoftObjectPath(
		TEXT("/Game/SCAR580/Zombies/anim_Attack_A_Montage_Pack.anim_Attack_A_Montage_Pack"));

	UFUNCTION(BlueprintCallable, Category = "SCAR|HorrorKit")
	void SyncToGround(ASCARSharedARGround* Ground);

	/** True if this pawn is one of the zombies spawned/tracked by the director. */
	UFUNCTION(BlueprintPure, Category = "SCAR|HorrorKit")
	bool IsManagedEnemy(const ACharacter* Enemy) const;

	/** Apply weapon damage and play a taking-damage reaction when allowed. */
	UFUNCTION(BlueprintCallable, Category = "SCAR|HorrorKit")
	FSCARZombieHitResult NotifyEnemyShot(ACharacter* Enemy, float Damage);

	/** Aim-cone fallback when line traces miss zombie mesh collision. */
	ACharacter* FindManagedEnemyUnderCrosshair(
		const FVector& ViewOrigin,
		const FVector& ViewDirection,
		float MaxDistanceCm,
		float MaxAngleDegrees = 6.f) const;

	static ASCARHorrorKitZombieDirector* FindInWorld(const UWorld* World);
	static ASCARHorrorKitZombieDirector* EnsureInWorld(UWorld* World);

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	void SpawnEnemiesIfNeeded(const ASCARSharedARGround* Ground);
	void DriveEnemies(float DeltaSeconds);
	void PrepareEnemyForDirectChase(ACharacter* Enemy, bool bPackEnemy, int32 PackVariantIndex);
	void FinalizeEnemyAIStrip(ACharacter* Enemy, bool bPackEnemy, int32 PackVariantIndex);
	void ApplyPackLocomotion(ACharacter* Enemy, int32 PackVariantIndex);
	void ApplyPackIdle(ACharacter* Enemy, int32 PackVariantIndex);
	void ApplyPackProneCrawl(ACharacter* Enemy, int32 PackVariantIndex, float WalkSpeed);
	void TriggerKitAttack(ACharacter* Enemy, bool bPackEnemy, int32 PackVariantIndex);
	void TriggerDamageReaction(ACharacter* Enemy, int32 EnemyIndex);
	void ResumePackStance(ACharacter* Enemy, int32 PackVariantIndex);
	void DestroyManagedEnemyAtIndex(int32 EnemyIndex);
	void ClearAllSpawnedEnemies();
	bool TryResolveEnemyIndex(ACharacter* Enemy, int32& OutIndex) const;
	void SnapEnemyToGround(ACharacter* Enemy) const;
	FVector GetSpawnLocation(const ASCARSharedARGround* Ground, int32 Index, int32 Count, float RadiusCm, float PhaseRadians) const;
	APawn* GetPlayerPawn() const;

	UPROPERTY()
	TArray<TObjectPtr<ACharacter>> SpawnedEnemies;

	/** Parallel to SpawnedEnemies: true = pack locomotion variant. */
	TArray<bool> SpawnedEnemyIsPack;

	/** Parallel to SpawnedEnemies: pack gait index (ignored for kit). */
	TArray<int32> SpawnedEnemyPackVariant;

	UPROPERTY()
	TObjectPtr<UAnimMontage> AttackMontage;

	UPROPERTY()
	TObjectPtr<UAnimMontage> PackAttackMontage;

	/** Parallel cooldown timers (same index as SpawnedEnemies). */
	TArray<float> AttackCooldownRemaining;

	/** Enemies that still need a one-shot AI strip after possession. */
	UPROPERTY()
	TArray<TObjectPtr<ACharacter>> PendingAIStrip;

	TArray<bool> PendingAIStripIsPack;
	TArray<int32> PendingAIStripPackVariant;

	/** Parallel: true while pack enemy is in melee (idle/attack, not locomotion). */
	TArray<bool> PackInMelee;

	/** Parallel: active looping stance montage for pack enemies (loco or idle). */
	UPROPERTY()
	TArray<TObjectPtr<UAnimMontage>> PackLocoMontages;

	/** Parallel: seconds remaining before pack loco may be re-asserted (attack/damage lockout). */
	TArray<float> PackAttackLockRemaining;

	/** Parallel health pool for spawned zombies. */
	TArray<float> EnemyHealthRemaining;

	/** Round-robin picker for anim_Taking_Damage_A..F. */
	TArray<int32> DamageAnimVariant;

	/** Cached AR floor surface Z used for spawn / re-snap. */
	float CachedGroundSurfaceZ = 0.f;

	float AttackRangeCmSq = 0.f;
	bool bEnemiesSpawned = false;
	bool bHasCachedGroundCenter = false;
	FVector CachedGroundCenter = FVector::ZeroVector;
};
