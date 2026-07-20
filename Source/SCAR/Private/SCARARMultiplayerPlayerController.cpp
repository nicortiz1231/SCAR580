#include "SCARARMultiplayerPlayerController.h"

#include "ARBlueprintLibrary.h"
#include "ARSessionConfig.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "HeadMountedDisplayFunctionLibrary.h"
#include "Kismet/GameplayStatics.h"
#include "SCARARMultiplayerBlueprintLibrary.h"
#include "SCARARMultiplayerMenuWidget.h"
#include "SCARARMultiplayerSlateMenu.h"
#include "SCARAvatarWeaponSyncComponent.h"
#include "SCARLocalFirstPersonArmsComponent.h"
#include "SCARRemoteAvatarAnchorComponent.h"
#include "SCARMultiplayerPawnSetup.h"
#include "SCARWeaponModdingLauncherSlate.h"
#include "TimerManager.h"
#include "UObject/UnrealType.h"

namespace
{
	constexpr float ARRotationSmoothingSpeed = 24.f;

	bool ShouldUseDeviceARSession()
	{
#if PLATFORM_IOS
		return true;
#else
		return false;
#endif
	}
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

	if (ShouldUseDeviceARSession())
	{
		ScheduleWorldTrackingCheck();
	}
}

void ASCARARMultiplayerPlayerController::OnPossess(APawn* InPawn)
{
	Super::OnPossess(InPawn);

	if (InPawn)
	{
		SCARMultiplayerPawnSetup::EnsureMultiplayerPawnComponents(InPawn);
	}

	if (IsLocalController() && ShouldUseDeviceARSession())
	{
		ScheduleWorldTrackingCheck();
	}
}

void ASCARARMultiplayerPlayerController::ScheduleWorldTrackingCheck()
{
	if (!IsLocalController() || !ShouldUseDeviceARSession() || bWorldTrackingReady)
	{
		return;
	}

	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	World->GetTimerManager().SetTimer(
		WorldTrackingTimer,
		this,
		&ASCARARMultiplayerPlayerController::EnsureWorldTrackingARSession,
		2.f,
		false);
}

void ASCARARMultiplayerPlayerController::EnsureWorldTrackingARSession()
{
	if (!IsLocalController() || !ShouldUseDeviceARSession() || bWorldTrackingReady)
	{
		return;
	}

	if (WorldTrackingAttempts >= 2)
	{
		return;
	}

	++WorldTrackingAttempts;

	static const TCHAR* ConfigPaths[] = {
		TEXT("/Game/SCAR580/D_ARSessionConfig_BodyTracking.D_ARSessionConfig_BodyTracking"),
		TEXT("/Game/HandheldAR/D_ARSessionConfig.D_ARSessionConfig"),
	};

	UARSessionConfig* SourceConfig = nullptr;
	for (const TCHAR* Path : ConfigPaths)
	{
		SourceConfig = LoadObject<UARSessionConfig>(nullptr, Path);
		if (SourceConfig)
		{
			break;
		}
	}

	const FARSessionStatus Status = UARBlueprintLibrary::GetARSessionStatus();
	const bool bRunning = Status.Status == EARSessionStatus::Running;
	const bool bAlreadyWorld = SourceConfig && SourceConfig->GetSessionType() == EARSessionType::World;

	if (bRunning && bAlreadyWorld)
	{
		bWorldTrackingReady = true;
		return;
	}

	UARSessionConfig* RuntimeConfig = SourceConfig
		? DuplicateObject<UARSessionConfig>(SourceConfig, GetTransientPackage())
		: NewObject<UARSessionConfig>(GetTransientPackage());
	if (!RuntimeConfig)
	{
		return;
	}

	auto SetBool = [](UObject* Obj, FName Name, bool bVal)
	{
		if (FBoolProperty* Prop = FindFProperty<FBoolProperty>(Obj->GetClass(), Name))
		{
			Prop->SetPropertyValue_InContainer(Obj, bVal);
		}
	};
	auto SetSessionType = [](UObject* Obj, EARSessionType Type)
	{
		if (FEnumProperty* EnumProp = FindFProperty<FEnumProperty>(Obj->GetClass(), TEXT("SessionType")))
		{
			void* Ptr = EnumProp->ContainerPtrToValuePtr<void>(Obj);
			EnumProp->GetUnderlyingProperty()->SetIntPropertyValue(Ptr, static_cast<int64>(Type));
		}
		else if (FByteProperty* ByteProp = FindFProperty<FByteProperty>(Obj->GetClass(), TEXT("SessionType")))
		{
			ByteProp->SetPropertyValue_InContainer(Obj, static_cast<uint8>(Type));
		}
	};

	SetSessionType(RuntimeConfig, EARSessionType::World);
	SetBool(RuntimeConfig, TEXT("bEnableAutomaticCameraTracking"), true);
	SetBool(RuntimeConfig, TEXT("bEnableAutomaticCameraOverlay"), true);
	SetBool(RuntimeConfig, TEXT("bHorizontalPlaneDetection"), true);
	SetBool(RuntimeConfig, TEXT("bVerticalPlaneDetection"), false);
	RuntimeConfig->SetEnableAutoFocus(true);

	const bool bNeedsRestart = bRunning && !bAlreadyWorld;
	if (bNeedsRestart)
	{
		UARBlueprintLibrary::StopARSession();
	}

	UARBlueprintLibrary::StartARSession(RuntimeConfig);
	bWorldTrackingReady = true;

	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(
			9101,
			5.f,
			FColor::Cyan,
			bNeedsRestart
				? TEXT("SCAR AR: World tracking enabled (walk)")
				: TEXT("SCAR AR: World tracking session started"));
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

void ASCARARMultiplayerPlayerController::PlayerTick(float DeltaTime)
{
	Super::PlayerTick(DeltaTime);

	if (!IsLocalController())
	{
		return;
	}

	EnsureLocalFirstPersonArms();
	EnsureRemoteAvatarAnchor();
	EnsureAvatarWeaponSync();

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

void ASCARARMultiplayerPlayerController::EnsureRemoteAvatarAnchor()
{
	if (FindComponentByClass<USCARRemoteAvatarAnchorComponent>())
	{
		return;
	}

	if (USCARRemoteAvatarAnchorComponent* AnchorComponent =
			NewObject<USCARRemoteAvatarAnchorComponent>(this, TEXT("SCAR_RemoteAvatarAnchor")))
	{
		AddInstanceComponent(AnchorComponent);
		AnchorComponent->RegisterComponent();
	}
}

void ASCARARMultiplayerPlayerController::EnsureAvatarWeaponSync()
{
	if (FindComponentByClass<USCARAvatarWeaponSyncComponent>())
	{
		return;
	}

	if (USCARAvatarWeaponSyncComponent* WeaponSyncComponent =
			NewObject<USCARAvatarWeaponSyncComponent>(this, TEXT("SCAR_AvatarWeaponSync")))
	{
		AddInstanceComponent(WeaponSyncComponent);
		WeaponSyncComponent->RegisterComponent();
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
