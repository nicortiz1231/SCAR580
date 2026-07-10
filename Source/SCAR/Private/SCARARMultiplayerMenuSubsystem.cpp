#include "SCARARMultiplayerMenuSubsystem.h"

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "SCARARMultiplayerBlueprintLibrary.h"
#include "SCARARMultiplayerPlayerController.h"
#include "SCARARMultiplayerSlateMenu.h"

bool USCARARMultiplayerMenuSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	if (const UWorld* World = Cast<UWorld>(Outer))
	{
		return World->IsGameWorld() && World->GetNetMode() != NM_DedicatedServer;
	}

	return false;
}

void USCARARMultiplayerMenuSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);

	InWorld.GetTimerManager().SetTimerForNextTick([this]()
	{
		TryShowMenuForLocalPlayer();
	});
}

void USCARARMultiplayerMenuSubsystem::TryShowMenuForLocalPlayer()
{
	UWorld* World = GetWorld();
	if (!World || World->GetNetMode() == NM_DedicatedServer)
	{
		return;
	}

	APlayerController* PlayerController = World->GetFirstPlayerController();
	if (!PlayerController || !PlayerController->IsLocalController())
	{
		return;
	}

	const bool bStandaloneMenu = USCARARMultiplayerBlueprintLibrary::ShouldShowMultiplayerMenu(World);
	const bool bListenHostMenu = World->GetNetMode() == NM_ListenServer;
	if (!bStandaloneMenu && !bListenHostMenu)
	{
		return;
	}

	if (ASCARARMultiplayerPlayerController* MultiplayerController = Cast<ASCARARMultiplayerPlayerController>(PlayerController))
	{
		MultiplayerController->ShowMultiplayerMenu();
		return;
	}

	FSCARARMultiplayerSlateMenu::Show(PlayerController);
}
