#include "SCARAvatarGrounding.h"

#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/Pawn.h"
#include "SCARSharedARGround.h"

namespace SCARAvatarGrounding
{
	USkeletalMeshComponent* FindBodyMesh(APawn* Pawn, const FName MeshName)
	{
		if (!Pawn)
		{
			return nullptr;
		}

		const FString TargetName = MeshName.ToString();
		TArray<USkeletalMeshComponent*> Meshes;
		Pawn->GetComponents<USkeletalMeshComponent>(Meshes);
		for (USkeletalMeshComponent* Mesh : Meshes)
		{
			if (Mesh && Mesh->GetName() == TargetName)
			{
				return Mesh;
			}
		}

		return nullptr;
	}

	bool GetMeshFeetWorldZ(const USkeletalMeshComponent* Mesh, float& OutFeetWorldZ)
	{
		if (!Mesh || !Mesh->GetSkeletalMeshAsset())
		{
			return false;
		}

		const FBoxSphereBounds Bounds = Mesh->CalcBounds(Mesh->GetComponentTransform());
		OutFeetWorldZ = Bounds.Origin.Z - Bounds.BoxExtent.Z;
		return true;
	}

	bool TraceGroundWorldZ(
		const UWorld* World,
		const FVector& WorldXY,
		const float ReferenceWorldZ,
		float& OutGroundZ,
		const AActor* IgnoreActor)
	{
		if (!World)
		{
			return false;
		}

		const FVector TraceStart(WorldXY.X, WorldXY.Y, ReferenceWorldZ + 250.f);
		const FVector TraceEnd(WorldXY.X, WorldXY.Y, ReferenceWorldZ - 5000.f);

		FCollisionQueryParams Params(SCENE_QUERY_STAT(SCARAvatarFeetGround), false, IgnoreActor);
		if (IgnoreActor)
		{
			Params.AddIgnoredActor(IgnoreActor);
		}

		FHitResult Hit;
		if (World->LineTraceSingleByChannel(Hit, TraceStart, TraceEnd, ECC_Visibility, Params))
		{
			OutGroundZ = Hit.ImpactPoint.Z;
			return true;
		}

		if (World->LineTraceSingleByChannel(Hit, TraceStart, TraceEnd, ECC_WorldStatic, Params))
		{
			OutGroundZ = Hit.ImpactPoint.Z;
			return true;
		}

		if (const ASCARSharedARGround* Ground = ASCARSharedARGround::FindInWorld(World))
		{
			OutGroundZ = Ground->GetGroundSurfaceZ();
			return true;
		}

		OutGroundZ = 0.f;
		return true;
	}

	bool SnapWorldFeetToGround(
		const UWorld* World,
		const FVector& CurrentWorldLocation,
		const float FeetWorldZ,
		FVector& OutWorldLocation,
		const AActor* IgnoreActor)
	{
		float GroundZ = 0.f;
		if (!TraceGroundWorldZ(World, CurrentWorldLocation, FeetWorldZ, GroundZ, IgnoreActor))
		{
			return false;
		}

		const float DeltaZ = GroundZ - FeetWorldZ;
		if (FMath::Abs(DeltaZ) < 0.5f)
		{
			return false;
		}

		OutWorldLocation = CurrentWorldLocation + FVector(0.f, 0.f, DeltaZ);
		return true;
	}

	bool SnapPawnFeetToGround(APawn* Pawn, const FName MeshName)
	{
		if (!Pawn)
		{
			return false;
		}

		USkeletalMeshComponent* BodyMesh = FindBodyMesh(Pawn, MeshName);
		if (!BodyMesh)
		{
			// Fallback: snap capsule bottom to ground.
			float CapsuleHalfHeight = 88.f;
			if (const UCapsuleComponent* Capsule = Pawn->FindComponentByClass<UCapsuleComponent>())
			{
				CapsuleHalfHeight = Capsule->GetScaledCapsuleHalfHeight();
			}

			float GroundZ = 0.f;
			const FVector PawnLocation = Pawn->GetActorLocation();
			const float FeetZ = PawnLocation.Z - CapsuleHalfHeight;
			if (!TraceGroundWorldZ(Pawn->GetWorld(), PawnLocation, FeetZ, GroundZ, Pawn))
			{
				return false;
			}

			const float TargetCenterZ = GroundZ + CapsuleHalfHeight;
			if (FMath::IsNearlyEqual(PawnLocation.Z, TargetCenterZ, 0.5f))
			{
				return false;
			}

			Pawn->SetActorLocation(
				FVector(PawnLocation.X, PawnLocation.Y, TargetCenterZ),
				false,
				nullptr,
				ETeleportType::TeleportPhysics);
			return true;
		}

		// Ensure mannequin mesh uses standard UE foot offset when possible.
		if (ACharacter* Character = Cast<ACharacter>(Pawn))
		{
			if (UCapsuleComponent* Capsule = Character->GetCapsuleComponent())
			{
				const float DesiredMeshZ = -Capsule->GetScaledCapsuleHalfHeight();
				const FVector RelativeLocation = BodyMesh->GetRelativeLocation();
				if (!FMath::IsNearlyEqual(RelativeLocation.Z, DesiredMeshZ, 1.f))
				{
					BodyMesh->SetRelativeLocation(FVector(RelativeLocation.X, RelativeLocation.Y, DesiredMeshZ));
				}
			}
		}

		float FeetWorldZ = 0.f;
		if (!GetMeshFeetWorldZ(BodyMesh, FeetWorldZ))
		{
			return false;
		}

		FVector AdjustedLocation = Pawn->GetActorLocation();
		if (!SnapWorldFeetToGround(Pawn->GetWorld(), AdjustedLocation, FeetWorldZ, AdjustedLocation, Pawn))
		{
			return false;
		}

		Pawn->SetActorLocation(AdjustedLocation, false, nullptr, ETeleportType::TeleportPhysics);
		return true;
	}
}
