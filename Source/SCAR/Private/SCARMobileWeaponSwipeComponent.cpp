#include "SCARMobileWeaponSwipeComponent.h"

#include "EnhancedInputSubsystems.h"
#include "GameFramework/PlayerController.h"
#include "InputAction.h"
#include "InputActionValue.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"

namespace SCARMobileWeaponSwipe
{
	static const TCHAR* MouseWheelActionPath =
		TEXT("/Game/BodycamFPSKIT/Input/Actions/IA_MouseWheel.IA_MouseWheel");
}

USCARMobileWeaponSwipeComponent::USCARMobileWeaponSwipeComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;
}

void USCARMobileWeaponSwipeComponent::BeginPlay()
{
	Super::BeginPlay();

	MouseWheelAction = LoadObject<UInputAction>(nullptr, SCARMobileWeaponSwipe::MouseWheelActionPath);
	if (!MouseWheelAction)
	{
		UE_LOG(LogTemp, Warning, TEXT("SCARMobileWeaponSwipe: missing IA_MouseWheel"));
	}
}

bool USCARMobileWeaponSwipeComponent::IsInWeaponZone(const float NormX, const float NormY) const
{
	return NormX >= ZoneXMin && NormX <= ZoneXMax && NormY >= ZoneYMin && NormY <= ZoneYMax;
}

void USCARMobileWeaponSwipeComponent::InjectWheelAxis(APlayerController* PC, const float WheelAxis)
{
	if (!PC || !MouseWheelAction)
	{
		return;
	}

	const ULocalPlayer* LocalPlayer = PC->GetLocalPlayer();
	if (!LocalPlayer)
	{
		return;
	}

	UEnhancedInputLocalPlayerSubsystem* InputSubsystem =
		LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>();
	if (!InputSubsystem)
	{
		return;
	}

	InputSubsystem->InjectInputForAction(
		MouseWheelAction,
		FInputActionValue(WheelAxis),
		TArray<UInputModifier*>(),
		TArray<UInputTrigger*>());
}

bool USCARMobileWeaponSwipeComponent::TryCycleWeapon(APlayerController* PC, const float WheelAxis)
{
	const UWorld* World = GetWorld();
	if (!World || !PC || FMath::IsNearlyZero(WheelAxis))
	{
		return false;
	}

	if (World->GetTimeSeconds() - LastSwapWorldSeconds < SwapCooldownSeconds)
	{
		return false;
	}

	LastSwapWorldSeconds = World->GetTimeSeconds();
	InjectWheelAxis(PC, WheelAxis);
	UE_LOG(
		LogTemp,
		Log,
		TEXT("SCARMobileWeaponSwipe: cycle weapon wheel=%.2f"),
		WheelAxis);
	return true;
}

void USCARMobileWeaponSwipeComponent::ProcessFinger(
	APlayerController* PC,
	const int32 FingerIndex,
	const int32 SizeX,
	const int32 SizeY)
{
	float LocationX = 0.f;
	float LocationY = 0.f;
	bool bIsPressed = false;
	PC->GetInputTouchState(static_cast<ETouchIndex::Type>(FingerIndex), LocationX, LocationY, bIsPressed);

	const float NormX = LocationX / static_cast<float>(SizeX);
	const float NormY = LocationY / static_cast<float>(SizeY);
	const bool bInZone = IsInWeaponZone(NormX, NormY);

	FWeaponSwipeFingerState& State = FingerStates.FindOrAdd(FingerIndex);

	if (!State.bWasPressed && bIsPressed && bInZone)
	{
		State.bTracking = true;
		State.StartX = LocationX;
		State.StartY = LocationY;
	}
	else if (State.bTracking && State.bWasPressed && !bIsPressed)
	{
		const float Dx = LocationX - State.StartX;
		const float Dy = LocationY - State.StartY;
		const float MinSwipe = static_cast<float>(SizeX) * SwipeMinFraction;

		if (FMath::Abs(Dx) >= MinSwipe && FMath::Abs(Dx) > FMath::Abs(Dy) * 0.5f)
		{
			const float WheelAxis = Dx < 0.f ? WheelPreviousValue : WheelNextValue;
			TryCycleWeapon(PC, WheelAxis);
		}

		State.bTracking = false;
	}
	else if (!bIsPressed)
	{
		State.bTracking = false;
	}

	State.bWasPressed = bIsPressed;
}

void USCARMobileWeaponSwipeComponent::TickComponent(
	const float DeltaTime,
	const ELevelTick TickType,
	FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	const APawn* Pawn = Cast<APawn>(GetOwner());
	if (!Pawn || !Pawn->IsLocallyControlled())
	{
		return;
	}

	APlayerController* PC = Cast<APlayerController>(Pawn->GetController());
	if (!PC)
	{
		return;
	}

	int32 SizeX = 0;
	int32 SizeY = 0;
	PC->GetViewportSize(SizeX, SizeY);
	if (SizeX <= 0 || SizeY <= 0)
	{
		return;
	}

	static constexpr int32 MaxFingers = 5;
	for (int32 Finger = 0; Finger < MaxFingers; ++Finger)
	{
		ProcessFinger(PC, Finger, SizeX, SizeY);
	}
}
