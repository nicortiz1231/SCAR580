#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SCARBodyDebugActor.generated.h"

class USCARBodyDebugDrawComponent;

/** Debug actor that draws ARKit + Vision body skeleton overlays (Unity ARHumanBodyDebugOverlay parity). */
UCLASS(Blueprintable)
class SCAR_API ASCARBodyDebugActor : public AActor
{
	GENERATED_BODY()

public:
	ASCARBodyDebugActor();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "SCAR|Body Detection")
	TObjectPtr<USCARBodyDebugDrawComponent> DebugDrawComponent;
};
