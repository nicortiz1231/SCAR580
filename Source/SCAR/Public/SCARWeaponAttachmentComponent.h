#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SCARWeaponAttachmentComponent.generated.h"

/** Ensures the Bodycam weapon-modding launcher button is visible during play. */
UCLASS(ClassGroup = (SCAR), meta = (BlueprintSpawnableComponent))
class SCAR_API USCARWeaponAttachmentComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	USCARWeaponAttachmentComponent();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Attachments")
	bool bShowAttachmentBar = true;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(
		float DeltaTime,
		ELevelTick TickType,
		FActorComponentTickFunction* ThisTickFunction) override;

private:
	void EnsureLauncher();
};
