#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SCARArLaserPresentationComponent.generated.h"

/** Keeps Bodycam laser/flash attachments visible in AR passthrough during hipfire and ADS. */
UCLASS(ClassGroup = (SCAR), meta = (BlueprintSpawnableComponent))
class SCAR_API USCARArLaserPresentationComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	USCARArLaserPresentationComponent();

protected:
	virtual void BeginPlay() override;
	virtual void TickComponent(
		float DeltaTime,
		ELevelTick TickType,
		FActorComponentTickFunction* ThisTickFunction) override;
};
