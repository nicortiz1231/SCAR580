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
#include "SCARInventoryBlueprintLibrary.h"
#include "SCARInventoryLauncherSlate.h"
#include "SCARWeaponModdingLauncherSlate.h"
#include "GameFramework/TouchInterface.h"
#include "Components/InputComponent.h"
#include "InputCoreTypes.h"
#include "InputKeyEventArgs.h"
#include "TimerManager.h"
#include "UObject/UnrealType.h"

namespace
{
	constexpr float ARRotationSmoothingSpeed = 24.f;

#if PLATFORM_IOS || PLATFORM_ANDROID
	static const TCHAR* MobileTouchInterfacePath =
		TEXT("/Game/SCAR580/Input/TI_MobileCombat.TI_MobileCombat");
#endif

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
	FSCARInventoryLauncherSlate::Show(this);

	// Mobile Slate launcher buttons require touch routing while in GameOnly mode.
	bEnableClickEvents = true;
	bEnableTouchEvents = true;

	EnsureMobileTouchInterface();

	if (ShouldUseDeviceARSession())
	{
		ScheduleWorldTrackingCheck();
	}
}

void ASCARARMultiplayerPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();
	// Tab / B are handled in InputKey so they still work while the inventory
	// menu is open (GameAndUI), which can swallow normal BindKey callbacks.
}

bool ASCARARMultiplayerPlayerController::InputKey(const FInputKeyEventArgs& Params)
{
	if (IsLocalController() && Params.Event == IE_Pressed && Params.Key == EKeys::Tab)
	{
		OnToggleInventoryPressed();
		return true;
	}

#if PLATFORM_IOS || PLATFORM_ANDROID
	// iOS routes screen taps through LeftMouseButton — treat top-right launcher as Tab.
	if (IsLocalController() && Params.Event == IE_Pressed && Params.Key == EKeys::LeftMouseButton)
	{
		float TouchX = 0.f;
		float TouchY = 0.f;
		bool bTouchDown = false;
		GetInputTouchState(ETouchIndex::Touch1, TouchX, TouchY, bTouchDown);
		if (bTouchDown)
		{
			int32 SizeX = 0;
			int32 SizeY = 0;
			GetViewportSize(SizeX, SizeY);
			if (FSCARInventoryLauncherSlate::HitTestScreenPoint(FVector2D(TouchX, TouchY), SizeX, SizeY))
			{
				OnToggleInventoryPressed();
				return true;
			}
		}
	}
#endif

	// Pause menu: swallow gameplay keys so clicks/keys don't fire weapons or move pawn.
	if (IsLocalController() && USCARInventoryBlueprintLibrary::IsInventoryMenuOpen(this))
	{
		if (Params.Key.IsMouseButton())
		{
			return true;
		}
	}

	return Super::InputKey(Params);
}

bool ASCARARMultiplayerPlayerController::InputTouch(
	const FTouchId TouchId,
	const ETouchType::Type Type,
	const FVector2D& TouchLocation,
	const float Force,
	const uint64 Timestamp)
{
	if (IsLocalController() && Type == ETouchType::Began)
	{
		int32 SizeX = 0;
		int32 SizeY = 0;
		GetViewportSize(SizeX, SizeY);
		if (FSCARInventoryLauncherSlate::HitTestScreenPoint(TouchLocation, SizeX, SizeY))
		{
			OnToggleInventoryPressed();
			return true;
		}
	}

	return Super::InputTouch(TouchId, Type, TouchLocation, Force, Timestamp);
}

void ASCARARMultiplayerPlayerController::OnToggleInventoryPressed()
{
	if (!IsLocalController() || !FSCARInventoryLauncherSlate::ShouldAcceptToggleHotkey())
	{
		return;
	}

	USCARInventoryBlueprintLibrary::ToggleInventoryMenu(this);
}

void ASCARARMultiplayerPlayerController::EnsureMobileTouchInterface()
{
#if PLATFORM_IOS || PLATFORM_ANDROID
	if (bMobileTouchInterfaceReady)
	{
		return;
	}

	UTouchInterface* BaseTI = LoadObject<UTouchInterface>(nullptr, MobileTouchInterfacePath);
	if (!BaseTI)
	{
		return;
	}

	UTouchInterface* TI = DuplicateObject<UTouchInterface>(BaseTI, this);
	if (!TI)
	{
		return;
	}

	bool bHasTabZone = false;
	for (const FTouchInputControl& Control : TI->Controls)
	{
		if (Control.MainInputKey == EKeys::Tab)
		{
			bHasTabZone = true;
			break;
		}
	}

	if (!bHasTabZone)
	{
		FTouchInputControl TabZone;
		TabZone.bTreatAsButton = true;
		TabZone.Center = FVector2D(0.88f, 0.10f);
		TabZone.VisualSize = FVector2D(0.16f, 0.16f);
		TabZone.ThumbSize = FVector2D(0.16f, 0.16f);
		TabZone.InteractionSize = FVector2D(0.20f, 0.20f);
		TabZone.InputScale = FVector2D(1.f, 1.f);
		TabZone.MainInputKey = EKeys::Tab;
		TI->Controls.Add(TabZone);
	}

	ActivateTouchInterface(TI);
	bMobileTouchInterfaceReady = true;
#endif
}

void ASCARARMultiplayerPlayerController::PollMobileInventoryLauncher()
{
#if PLATFORM_IOS || PLATFORM_ANDROID
	if (!IsLocalController())
	{
		return;
	}

	int32 SizeX = 0;
	int32 SizeY = 0;
	GetViewportSize(SizeX, SizeY);

	for (int32 FingerIndex = 0; FingerIndex < MaxInventoryTouchFingers; ++FingerIndex)
	{
		float LocationX = 0.f;
		float LocationY = 0.f;
		bool bIsPressed = false;
		GetInputTouchState(static_cast<ETouchIndex::Type>(FingerIndex), LocationX, LocationY, bIsPressed);

		const bool bWasPressed = InventoryTouchWasDown[FingerIndex];
		if (bIsPressed && !bWasPressed)
		{
			if (FSCARInventoryLauncherSlate::HitTestScreenPoint(FVector2D(LocationX, LocationY), SizeX, SizeY))
			{
				OnToggleInventoryPressed();
			}
		}

		InventoryTouchWasDown[FingerIndex] = bIsPressed;
	}
#endif
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

	if (IsLocalController())
	{
		EnsureMobileTouchInterface();
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

	// Keep vitals/hotbar removed and pause-backpack visibility in sync every frame.
	USCARInventoryBlueprintLibrary::TickInventoryPresentation(this);

	PollMobileInventoryLauncher();

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
