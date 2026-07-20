#pragma once

#include "CoreMinimal.h"

class APawn;
class USkeletalMeshComponent;

namespace SCARAvatarGrounding
{
	/** Find the visible body mesh used for opponent mannequins. */
	USkeletalMeshComponent* FindBodyMesh(APawn* Pawn, FName MeshName = TEXT("CharacterMesh0"));

	/** Lowest world-space Z of the mesh bounds (approximate sole height). */
	bool GetMeshFeetWorldZ(const USkeletalMeshComponent* Mesh, float& OutFeetWorldZ);

	/** Trace straight down at XY and return the highest blocking surface Z, if any. */
	bool TraceGroundWorldZ(const UWorld* World, const FVector& WorldXY, float ReferenceWorldZ, float& OutGroundZ, const AActor* IgnoreActor = nullptr);

	/** Move pawn vertically so mesh feet sit on the traced ground surface. Returns true if adjusted. */
	bool SnapPawnFeetToGround(APawn* Pawn, FName MeshName = TEXT("CharacterMesh0"));

	/** Move a world-space point vertically so feet sit on ground (for detached mesh rendering). */
	bool SnapWorldFeetToGround(
		const UWorld* World,
		const FVector& CurrentWorldLocation,
		float FeetWorldZ,
		FVector& OutWorldLocation,
		const AActor* IgnoreActor = nullptr);
}
