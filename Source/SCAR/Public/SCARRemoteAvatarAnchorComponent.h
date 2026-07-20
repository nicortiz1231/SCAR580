#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SCARRemoteAvatarAnchorComponent.generated.h"

class APawn;
class USkeletalMeshComponent;

/**
 * Lives on the LOCAL player controller (attached dynamically by
 * ASCARARMultiplayerPlayerController -- no Blueprint edits required).
 *
 * The local render camera deliberately ignores the physical phone's roll;
 * that is what keeps the FP arms/weapon glued to the screen. The side effect
 * is that every world-anchored actor, including remote players' avatars,
 * appears glued to the screen too and visually rotates with the phone.
 *
 * Each frame this component counter-rotates remote player avatars around the
 * local camera's view axis by exactly the roll the camera ignored, so they
 * stay anchored to the real world seen in the AR passthrough -- like a real
 * subject filmed by a rolling camera.
 *
 * Position stays on the replicated pawn transform (feet grounded by pose sync).
 * Only rotation receives counter-roll; re-projecting mesh position around the
 * camera caused avatars to float when the viewer pitched/yawed to look around.
 */
UCLASS(ClassGroup = (SCAR))
class SCAR_API USCARRemoteAvatarAnchorComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	USCARRemoteAvatarAnchorComponent();

	/** Body mesh (full-body avatar other players see) component name. */
	UPROPERTY(EditAnywhere, Category = "SCAR|AvatarAnchor")
	FName BodyMeshComponentName = TEXT("CharacterMesh0");

protected:
	virtual void TickComponent(
		float DeltaTime,
		ELevelTick TickType,
		FActorComponentTickFunction* ThisTickFunction) override;

private:
	struct FMeshAnchorState
	{
		TWeakObjectPtr<USkeletalMeshComponent> Mesh;
		FTransform DefaultRelative = FTransform::Identity;
	};

	USkeletalMeshComponent* FindBodyMesh(APawn* Pawn) const;
	void RestoreAnchoredMeshes();

	TMap<TWeakObjectPtr<APawn>, FMeshAnchorState> AnchoredMeshes;
};
