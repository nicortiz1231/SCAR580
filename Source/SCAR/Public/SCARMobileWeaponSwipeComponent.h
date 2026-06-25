#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SCARMobileWeaponSwipeComponent.generated.h"

class UInputAction;

/** Detects horizontal swipes on the FPS weapon band and cycles equipped weapons. */
UCLASS(ClassGroup = (SCAR), meta = (BlueprintSpawnableComponent))
class SCAR_API USCARMobileWeaponSwipeComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	USCARMobileWeaponSwipeComponent();

	/** Minimum horizontal swipe distance as a fraction of viewport width. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Weapon Swipe")
	float SwipeMinFraction = 0.03f;

	/** Normalized viewport X min (0 = left). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Weapon Swipe")
	float ZoneXMin = 0.05f;

	/** Normalized viewport X max (1 = right). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Weapon Swipe")
	float ZoneXMax = 0.95f;

	/** Normalized viewport Y min (0 = top). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Weapon Swipe")
	float ZoneYMin = 0.28f;

	/** Normalized viewport Y max (1 = bottom). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Weapon Swipe")
	float ZoneYMax = 0.88f;

	/** Seconds between accepted swipes. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Weapon Swipe")
	float SwapCooldownSeconds = 0.25f;

	/** Axis value injected for swipe-right (mouse wheel up / next weapon). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Weapon Swipe")
	float WheelNextValue = 1.f;

	/** Axis value injected for swipe-left (mouse wheel down / previous weapon). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Weapon Swipe")
	float WheelPreviousValue = -1.f;

protected:
	virtual void BeginPlay() override;
	virtual void TickComponent(
		float DeltaTime,
		ELevelTick TickType,
		FActorComponentTickFunction* ThisTickFunction) override;

private:
	struct FWeaponSwipeFingerState
	{
		bool bWasPressed = false;
		bool bTracking = false;
		float StartX = 0.f;
		float StartY = 0.f;
	};

	TMap<int32, FWeaponSwipeFingerState> FingerStates;
	double LastSwapWorldSeconds = -1000.0;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> MouseWheelAction;

	bool IsInWeaponZone(float NormX, float NormY) const;
	void ProcessFinger(class APlayerController* PC, int32 FingerIndex, int32 SizeX, int32 SizeY);
	bool TryCycleWeapon(class APlayerController* PC, float WheelAxis);
	void InjectWheelAxis(class APlayerController* PC, float WheelAxis);
};
