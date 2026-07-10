#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SCARARMultiplayerMenuSubsystem.generated.h"

UCLASS()
class SCAR_API USCARARMultiplayerMenuSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;

	void TryShowMenuForLocalPlayer();
};
