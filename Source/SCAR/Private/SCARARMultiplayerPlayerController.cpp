#include "SCARARMultiplayerPlayerController.h"

#include "ARBlueprintLibrary.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "HeadMountedDisplayFunctionLibrary.h"
#include "Kismet/GameplayStatics.h"
#include "SCARARMultiplayerBlueprintLibrary.h"
#include "SCARARMultiplayerMenuWidget.h"
#include "SCARARMultiplayerSlateMenu.h"
#include "SCARLocalFirstPersonArmsComponent.h"
#include "SCARWeaponModdingLauncherSlate.h"

namespace
{
	// Before AR multiplayer, FirstPersonCamera used bLockToHmd, which fed the
	// raw ARKit device pose straight into the render camera every frame --
	// zero Unreal-side smoothing lag at all (ARKit's own internal sensor
	// fusion is already clean). Switching to ControlRotation (needed so the
	// arm/weapon IK and multiplayer body orientation share the exact same
	// value the camera uses, instead of jittering against it) reintroduced a
	// small amount of lag via this smoothing step. 24 is tuned to be "high
	// but finite" -- filtering per-frame noise without *feeling* laggy.
	constexpr float ARRotationSmoothingSpeed = 24.f;
}

ASCARARMultiplayerPlayerController::ASCARARMultiplayerPlayerController()
{
	MultiplayerMenuWidgetClass = USCARARMultiplayerMenuWidget::StaticClass();
}

void ASCARARMultiplayerPlayerController::BeginPlay()
{
	Super::BeginPlay();

	UWorld* World = GetWorld();
	if (!World || !IsLocalController())
	{
		return;
	}

	const ENetMode NetMode = World->GetNetMode();
	if (NetMode == NM_Client)
	{
		HideMultiplayerMenu();
		NotifyMultiplayerConnectionStatus();
	}
	else if (bShowMultiplayerMenuOnBeginPlay)
	{
		if (USCARARMultiplayerBlueprintLibrary::ShouldShowMultiplayerMenu(this))
		{
			ShowMultiplayerMenu();
		}
		else if (NetMode == NM_ListenServer)
		{
			ShowMultiplayerMenu();
			if (MultiplayerMenuWidget)
			{
				MultiplayerMenuWidget->SetHostSessionMode(true);
			}
		}
	}

	FSCARWeaponModdingLauncherSlate::Show(this);
}

void ASCARARMultiplayerPlayerController::NotifyMultiplayerConnectionStatus()
{
	if (!GEngine || !IsLocalController())
	{
		return;
	}

	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	const FString NetModeText = USCARARMultiplayerBlueprintLibrary::GetNetModeDescription(this);
	const int32 PlayerCount = UGameplayStatics::GetNumPlayerControllers(World);
	const FString Message = FString::Printf(
		TEXT("Multiplayer active (%s) - %d player(s) connected"),
		*NetModeText,
		PlayerCount);

	GEngine->AddOnScreenDebugMessage(9001, 12.f, FColor::Green, Message);
	UE_LOG(LogTemp, Warning, TEXT("SCAR multiplayer: %s"), *Message);
}

void ASCARARMultiplayerPlayerController::HostARMultiplayer(const FString& MapOverride)
{
	HostARMultiplayerGame(MapOverride);
}

void ASCARARMultiplayerPlayerController::JoinARMultiplayer(const FString& Address)
{
	JoinARMultiplayerGame(Address);
}

void ASCARARMultiplayerPlayerController::HostARMultiplayerGame(const FString& MapOverride)
{
	const FString MapPath = MapOverride.IsEmpty() ? DefaultMapPath : MapOverride;

	if (UWorld* World = GetWorld())
	{
		const ENetMode NetMode = World->GetNetMode();
		if (NetMode == NM_Client)
		{
			return;
		}

		if (NetMode == NM_Standalone || NetMode == NM_ListenServer)
		{
			UGameplayStatics::OpenLevel(this, FName(*MapPath), true, TEXT("listen"));
			return;
		}
	}

	const FString TravelURL = FString::Printf(TEXT("%s?listen"), *MapPath);
	ClientTravel(TravelURL, ETravelType::TRAVEL_Absolute);
}

void ASCARARMultiplayerPlayerController::JoinARMultiplayerGame(const FString& Address)
{
	if (Address.IsEmpty())
	{
		return;
	}

	const FString TravelURL = USCARARMultiplayerBlueprintLibrary::BuildJoinAddress(Address, DefaultPort);
	ClientTravel(TravelURL, ETravelType::TRAVEL_Absolute);
}

void ASCARARMultiplayerPlayerController::ShowMultiplayerMenu()
{
	FSCARARMultiplayerSlateMenu::Show(this);
}

void ASCARARMultiplayerPlayerController::HideMultiplayerMenu()
{
	FSCARARMultiplayerSlateMenu::Hide();

	if (MultiplayerMenuWidget)
	{
		MultiplayerMenuWidget->SetVisibility(ESlateVisibility::Collapsed);
	}

	if (IsLocalController())
	{
		SetShowMouseCursor(false);
		SetInputMode(FInputModeGameOnly());
		bEnableClickEvents = false;
		bEnableMouseOverEvents = false;
	}
}

void ASCARARMultiplayerPlayerController::PlayerTick(float DeltaTime)
{
	Super::PlayerTick(DeltaTime);

	if (!IsLocalController())
	{
		return;
	}

	EnsureLocalFirstPersonArms();

	const FARSessionStatus SessionStatus = UARBlueprintLibrary::GetARSessionStatus();
	if (SessionStatus.Status != EARSessionStatus::Running)
	{
		return;
	}

	FRotator DeviceRotation;
	FVector DevicePosition;
	UHeadMountedDisplayFunctionLibrary::GetOrientationAndPosition(DeviceRotation, DevicePosition);

	if (!bHasSmoothedARRotation)
	{
		SmoothedARRotation = DeviceRotation;
		bHasSmoothedARRotation = true;
	}
	else
	{
		SmoothedARRotation = FMath::RInterpTo(SmoothedARRotation, DeviceRotation, DeltaTime, ARRotationSmoothingSpeed);
	}

	// Passthrough video rolls with the physical phone, but the rendered FP
	// arms/camera overlay must stay visually fixed on screen (zero roll). Pitch
	// and yaw still track where the player is looking for aim/world placement.
	FRotator ViewRotation = SmoothedARRotation;
	ViewRotation.Roll = 0.f;
	SetControlRotation(ViewRotation);
}

void ASCARARMultiplayerPlayerController::EnsureLocalFirstPersonArms()
{
	APawn* Pawn = GetPawn();
	if (!Pawn || Pawn->FindComponentByClass<USCARLocalFirstPersonArmsComponent>())
	{
		return;
	}

	if (USCARLocalFirstPersonArmsComponent* ArmsComponent =
			NewObject<USCARLocalFirstPersonArmsComponent>(Pawn, TEXT("SCAR_LocalFirstPersonArms")))
	{
		Pawn->AddInstanceComponent(ArmsComponent);
		ArmsComponent->RegisterComponent();
	}
}

bool ASCARARMultiplayerPlayerController::IsMultiplayerSession(const UObject* WorldContextObject)
{
	const UWorld* World = GEngine
		? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull)
		: nullptr;

	if (!World)
	{
		return false;
	}

	const ENetMode NetMode = World->GetNetMode();
	return NetMode == NM_ListenServer || NetMode == NM_Client || NetMode == NM_DedicatedServer;
}
