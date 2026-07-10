#include "SCARARMultiplayerBlueprintLibrary.h"

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "GameFramework/PlayerController.h"
#include "IPAddress.h"
#include "Kismet/GameplayStatics.h"
#include "SCARARMultiplayerMenuSubsystem.h"
#include "SCARARMultiplayerPlayerController.h"
#include "SCARARMultiplayerSlateMenu.h"
#include "SocketSubsystem.h"

namespace
{
	const TCHAR* DefaultMapPath = TEXT("/Game/SCAR580/Maps/Map_AR");
}

bool USCARARMultiplayerBlueprintLibrary::GetLocalLanIPv4(FString& OutAddress)
{
	ISocketSubsystem* SocketSubsystem = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM);
	if (!SocketSubsystem)
	{
		return false;
	}

	TArray<TSharedPtr<FInternetAddr>> Addresses;
	SocketSubsystem->GetLocalAdapterAddresses(Addresses);

	for (const TSharedPtr<FInternetAddr>& Address : Addresses)
	{
		if (!Address.IsValid() || !Address->IsValid())
		{
			continue;
		}

		const FString Candidate = Address->ToString(false);
		if (Candidate.StartsWith(TEXT("127.")) || Candidate == TEXT("localhost"))
		{
			continue;
		}
		if (Candidate.StartsWith(TEXT("10.")) ||
			Candidate.StartsWith(TEXT("192.168.")) ||
			Candidate.StartsWith(TEXT("172.")))
		{
			OutAddress = Candidate;
			return true;
		}
	}

	return false;
}

FString USCARARMultiplayerBlueprintLibrary::BuildJoinAddress(const FString& HostAddress, const int32 Port)
{
	if (HostAddress.IsEmpty())
	{
		return FString();
	}

	if (HostAddress.Contains(TEXT(":")))
	{
		return HostAddress;
	}

	return FString::Printf(TEXT("%s:%d"), *HostAddress, Port);
}

FString USCARARMultiplayerBlueprintLibrary::GetNetModeDescription(const UObject* WorldContextObject)
{
	const UWorld* World = GEngine
		? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull)
		: nullptr;

	if (!World)
	{
		return TEXT("No world");
	}

	switch (World->GetNetMode())
	{
	case NM_Standalone:
		return TEXT("Standalone");
	case NM_ListenServer:
		return TEXT("Listen Server");
	case NM_Client:
		return TEXT("Client");
	case NM_DedicatedServer:
		return TEXT("Dedicated Server");
	default:
		return TEXT("Unknown");
	}
}

bool USCARARMultiplayerBlueprintLibrary::ShouldShowMultiplayerMenu(const UObject* WorldContextObject)
{
	const UWorld* World = GEngine
		? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull)
		: nullptr;

	if (!World)
	{
		return false;
	}

	return World->GetNetMode() == NM_Standalone;
}

void USCARARMultiplayerBlueprintLibrary::HostARMultiplayerSession(UObject* WorldContextObject, const FString& MapOverride)
{
	UWorld* World = GEngine
		? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull)
		: nullptr;

	if (!World)
	{
		return;
	}

	const FString MapPath = MapOverride.IsEmpty() ? DefaultMapPath : MapOverride;

	if (APlayerController* PlayerController = World->GetFirstPlayerController())
	{
		if (ASCARARMultiplayerPlayerController* MultiplayerController = Cast<ASCARARMultiplayerPlayerController>(PlayerController))
		{
			MultiplayerController->HostARMultiplayerGame(MapOverride);
			return;
		}
	}

	const ENetMode NetMode = World->GetNetMode();
	if (NetMode == NM_Client)
	{
		return;
	}

	if (NetMode == NM_Standalone || NetMode == NM_ListenServer)
	{
		UGameplayStatics::OpenLevel(WorldContextObject, FName(*MapPath), true, TEXT("listen"));
		return;
	}

	const FString TravelURL = FString::Printf(TEXT("%s?listen"), *MapPath);
	if (APlayerController* PlayerController = World->GetFirstPlayerController())
	{
		PlayerController->ClientTravel(TravelURL, ETravelType::TRAVEL_Absolute);
	}
}

void USCARARMultiplayerBlueprintLibrary::JoinARMultiplayerSession(
	APlayerController* PlayerController,
	const FString& Address,
	const int32 Port)
{
	if (!PlayerController || Address.IsEmpty())
	{
		return;
	}

	if (ASCARARMultiplayerPlayerController* MultiplayerController = Cast<ASCARARMultiplayerPlayerController>(PlayerController))
	{
		MultiplayerController->JoinARMultiplayerGame(Address);
		return;
	}

	const FString TravelURL = BuildJoinAddress(Address, Port);
	PlayerController->ClientTravel(TravelURL, ETravelType::TRAVEL_Absolute);
}

void USCARARMultiplayerBlueprintLibrary::ShowARMultiplayerMenu(UObject* WorldContextObject)
{
	UWorld* World = GEngine
		? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull)
		: nullptr;

	if (!World || !ShouldShowMultiplayerMenu(World))
	{
		return;
	}

	if (APlayerController* PlayerController = World->GetFirstPlayerController())
	{
		if (ASCARARMultiplayerPlayerController* MultiplayerController = Cast<ASCARARMultiplayerPlayerController>(PlayerController))
		{
			MultiplayerController->ShowMultiplayerMenu();
			return;
		}

		FSCARARMultiplayerSlateMenu::Show(PlayerController);
		return;
	}

	if (USCARARMultiplayerMenuSubsystem* MenuSubsystem = World->GetSubsystem<USCARARMultiplayerMenuSubsystem>())
	{
		MenuSubsystem->TryShowMenuForLocalPlayer();
	}
}

void USCARARMultiplayerBlueprintLibrary::ShowARMultiplayerMenuForActor(AActor* Actor)
{
	ShowARMultiplayerMenu(Actor);
}
