#include "SCARARMultiplayerGameMode.h"

#include "Engine/Engine.h"
#include "GameFramework/Controller.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerStart.h"
#include "Kismet/GameplayStatics.h"
#include "SCARARMultiplayerPlayerController.h"
#include "SCARARMultiplayerPlayerState.h"
#include "SCARMultiplayerPawnSetup.h"

ASCARARMultiplayerGameMode::ASCARARMultiplayerGameMode()
{
	bUseSeamlessTravel = false;
	PlayerStateClass = ASCARARMultiplayerPlayerState::StaticClass();
	PlayerControllerClass = ASCARARMultiplayerPlayerController::StaticClass();
}

void ASCARARMultiplayerGameMode::InitGame(
	const FString& MapName,
	const FString& Options,
	FString& ErrorMessage)
{
	Super::InitGame(MapName, Options, ErrorMessage);

	UE_LOG(LogTemp, Warning, TEXT("SCAR-580 AR Multiplayer GameMode active on map %s"), *MapName);

	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(
			-1,
			20.f,
			FColor::Cyan,
			TEXT("SCAR-580 MULTIPLAYER MODE ACTIVE (ground+walk build)"));
	}
}

void ASCARARMultiplayerGameMode::StartPlay()
{
	Super::StartPlay();
	SCARMultiplayerPawnSetup::EnsureMultiplayerFloor(GetWorld());
}

void ASCARARMultiplayerGameMode::GenericPlayerInitialization(AController* NewPlayer)
{
	Super::GenericPlayerInitialization(NewPlayer);

	if (APawn* Pawn = NewPlayer ? NewPlayer->GetPawn() : nullptr)
	{
		SCARMultiplayerPawnSetup::EnsureMultiplayerPawnComponents(Pawn);
	}
}

void ASCARARMultiplayerGameMode::PostLogin(APlayerController* NewPlayer)
{
	Super::PostLogin(NewPlayer);

	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	const int32 PlayerCount = UGameplayStatics::GetNumPlayerControllers(World);
	const FString JoinMessage = FString::Printf(
		TEXT("Player joined - %d/%d connected"),
		PlayerCount,
		MaxPlayers);

	for (FConstPlayerControllerIterator Iterator = World->GetPlayerControllerIterator(); Iterator; ++Iterator)
	{
		APlayerController* PlayerController = Iterator->Get();
		if (!PlayerController || !PlayerController->IsLocalController())
		{
			continue;
		}

		if (ASCARARMultiplayerPlayerController* MultiplayerController =
			Cast<ASCARARMultiplayerPlayerController>(PlayerController))
		{
			MultiplayerController->HideMultiplayerMenu();
			MultiplayerController->NotifyMultiplayerConnectionStatus();
		}

		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(9002, 10.f, FColor::Yellow, JoinMessage);
		}
	}

	UE_LOG(LogTemp, Warning, TEXT("SCAR multiplayer: %s"), *JoinMessage);
}

AActor* ASCARARMultiplayerGameMode::ChoosePlayerStart_Implementation(AController* Player)
{
	AActor* Start = Super::ChoosePlayerStart_Implementation(Player);
	if (Start)
	{
		return Start;
	}

	UWorld* World = GetWorld();
	return World ? World->SpawnActor<APlayerStart>() : nullptr;
}
