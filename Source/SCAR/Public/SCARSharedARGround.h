#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SCARSharedARGround.generated.h"

class UBoxComponent;
class UProceduralMeshComponent;

/** Visible virtual floor for AR multiplayer — spawned once per session at the origin. */
UCLASS()
class SCAR_API ASCARSharedARGround : public AActor
{
	GENERATED_BODY()

public:
	ASCARSharedARGround();

	/** Half-extent of the floor plane in cm (15 m = 1500). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "SCAR|AR Ground")
	float HalfExtentCm = 1500.f;

	void PlaceAt(const FVector& OriginXY, float SurfaceWorldZ);

	UFUNCTION(BlueprintPure, Category = "SCAR|AR Ground")
	float GetGroundSurfaceZ() const { return GroundSurfaceZ; }

	/** Walkable collision used by Recast (ProceduralMesh reports empty nav bounds). */
	UFUNCTION(BlueprintPure, Category = "SCAR|AR Ground")
	UBoxComponent* GetNavFloor() const { return NavFloor; }

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	static ASCARSharedARGround* FindInWorld(const UWorld* World);

protected:
	virtual void BeginPlay() override;

private:
	void BuildFloorMesh();
	void UpdateNavFloor();

	UPROPERTY(VisibleAnywhere, Category = "SCAR|AR Ground")
	TObjectPtr<UProceduralMeshComponent> FloorMesh;

	/** Invisible box with valid bounds so HorrorKit AI MoveTo can path on AR ground. */
	UPROPERTY(VisibleAnywhere, Category = "SCAR|AR Ground")
	TObjectPtr<UBoxComponent> NavFloor;

	UPROPERTY(Replicated)
	float GroundSurfaceZ = 0.f;
};
