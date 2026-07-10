#include "SCARARMultiplayerPlayerController.h"

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "SCARARMultiplayerBlueprintLibrary.h"
#include "SCARARMultiplayerMenuWidget.h"
#include "SCARARMultiplayerSlateMenu.h"

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
		return;
	}

	if (!bShowMultiplayerMenuOnBeginPlay)
	{
		return;
	}

	if (USCARARMultiplayerBlueprintLibrary::ShouldShowMultiplayerMenu(this))
	{
		ShowMultiplayerMenu();
		return;
	}

	if (NetMode == NM_ListenServer)
	{
		ShowMultiplayerMenu();
		if (MultiplayerMenuWidget)
		{
			MultiplayerMenuWidget->SetHostSessionMode(true);
		}
	}
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
