#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "SCARPlayerController.generated.h"

/** Uses ASCARPlayerCameraManager for forced near-clip and ADS first-person scale. */
UCLASS()
class SCAR_API ASCARPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	ASCARPlayerController();
};
