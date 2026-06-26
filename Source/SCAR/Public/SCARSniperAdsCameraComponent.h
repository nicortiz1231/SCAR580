#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SCARSniperAdsCameraComponent.generated.h"

class USCARNearClipCameraModifier;
class UCameraComponent;

/** Installs a near-clip camera modifier and tags weapon meshes for first-person rendering. */
UCLASS(ClassGroup = (SCAR), meta = (BlueprintSpawnableComponent))
class SCAR_API USCARSniperAdsCameraComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	USCARSniperAdsCameraComponent();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Sniper ADS")
	float NearClipPlane = 0.0001f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Sniper ADS")
	float AdsFirstPersonFov = 18.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Sniper ADS")
	float AdsFirstPersonScale = 2.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Sniper ADS")
	float AdsFovThreshold = 50.f;

protected:
	virtual void BeginPlay() override;
	virtual void TickComponent(
		float DeltaTime,
		ELevelTick TickType,
		FActorComponentTickFunction* ThisTickFunction) override;

private:
	UPROPERTY(Transient)
	TObjectPtr<USCARNearClipCameraModifier> NearClipModifier;

	bool bCameraConfigured = false;
	bool bMeshesTagged = false;

	void EnsureNearClipModifier();
	void ConfigureFirstPersonCamera();
	void TagWeaponMeshesFirstPerson();
	UCameraComponent* FindFirstPersonCamera() const;
	void TagActorPrimitives(class AActor* Actor) const;
	void UpdateFirstPersonScaleForAds();
};
