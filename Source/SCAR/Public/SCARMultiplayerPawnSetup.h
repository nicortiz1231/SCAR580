#pragma once

#include "CoreMinimal.h"

class APawn;
class UWorld;

/** Runtime wiring so multiplayer AR works without re-running editor Python setup scripts. */
namespace SCARMultiplayerPawnSetup
{
	void EnsureMultiplayerFloor(UWorld* World);
	void EnsureMultiplayerPawnComponents(APawn* Pawn);
	void SnapPawnToGround(APawn* Pawn);
}
