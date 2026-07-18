#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SCARRemoteAvatarAnchorComponent.generated.h"

class APawn;

/**
 * Lives on the LOCAL player controller (attached dynamically by
 * ASCARARMultiplayerPlayerController -- no Blueprint edits required).
 *
 * The local render camera deliberately ignores the physical phone's roll;
 * that is what keeps the FP arms/weapon glued to the screen. The side effect
 * is that every world-anchored actor, including remote players' avatars,
 * appears glued to the screen too and visually rotates with the phone.
 *
 * Each frame this component counter-rotates remote player pawns around the
 * local camera's view axis by exactly the roll the camera ignored, so their
 * avatars stay anchored to the real world seen in the AR passthrough -- like
 * a real subject filmed by a rolling camera. Purely local: nothing replicated
 * is modified, and the local camera / FP arms pipeline is untouched.
 *
 * Runs in TG_LastDemotable, after replication, character movement, and
 * gameplay ticks have written pawn transforms for the frame. Per pawn it
 * remembers both the un-rolled base pose and the rolled pose it wrote last
 * frame: if nothing else moved the pawn since, the remembered base is reused;
 * if another system did move it (replication update, movement simulation),
 * that fresh pose becomes the new base. Either way the roll is applied to an
 * un-rolled pose exactly once per frame and can never compound.
 */
UCLASS(ClassGroup = (SCAR))
class SCAR_API USCARRemoteAvatarAnchorComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	USCARRemoteAvatarAnchorComponent();

protected:
	virtual void TickComponent(
		float DeltaTime,
		ELevelTick TickType,
		FActorComponentTickFunction* ThisTickFunction) override;

private:
	struct FAnchorState
	{
		FTransform BaseWorld = FTransform::Identity;
		FTransform LastSetWorld = FTransform::Identity;
	};

	void RestoreAnchoredPawns();

	TMap<TWeakObjectPtr<APawn>, FAnchorState> AnchoredPawns;
};
