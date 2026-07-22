#include "SCARInventoryBlueprintLibrary.h"

#include "Animation/WidgetAnimation.h"
#include "Blueprint/UserWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/Image.h"
#include "Components/PanelWidget.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Components/TextBlock.h"
#include "Components/UniformGridSlot.h"
#include "Components/Widget.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "Framework/Application/IInputProcessor.h"
#include "Framework/Application/SlateApplication.h"
#include "Input/Events.h"
#include "GameFramework/HUD.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "Styling/CoreStyle.h"
#include "UObject/UObjectIterator.h"
#include "UObject/UnrealType.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/SNullWidget.h"

namespace SCARInventoryInternal
{
	static constexpr TCHAR InventoryHudClassPath[] =
		TEXT("/Game/InventorySystem_0_5/Core/HUD_InventoryGame.HUD_InventoryGame_C");
	static constexpr TCHAR InventoryComponentClassPath[] =
		TEXT("/Game/InventorySystem_0_5/Blueprints/Components/AC_Inventory.AC_Inventory_C");
	static constexpr TCHAR CharacterPreviewClassPath[] =
		TEXT("/Game/InventorySystem_0_5/Blueprints/Actors/BP_CharacterPreview.BP_CharacterPreview_C");
	static constexpr TCHAR WidgetGameClassPath[] =
		TEXT("/Game/InventorySystem_0_5/Blueprints/UserInterfaces/Game/WBP_Game.WBP_Game_C");

	static const FVector CharacterPreviewSpawnLocation(0.f, 0.f, -50000.f);

	static bool GBackpackOpen = false;
	static TSharedPtr<IInputProcessor> GTabProcessor;
	static TWeakObjectPtr<APlayerController> GTabPC;
	static TWeakObjectPtr<APawn> GInputBlockedPawn;
	static TSharedPtr<SWidget> GBlackBackdrop;
	static double GLastToggleTime = 0.0;

	static void SafeProcessEvent(UObject* Target, UFunction* Function)
	{
		if (!Target || !Function || !IsValid(Target))
		{
			return;
		}
		if (Function->ParmsSize <= 0)
		{
			Target->ProcessEvent(Function, nullptr);
			return;
		}
		uint8* Buffer = static_cast<uint8*>(FMemory_Alloca(Function->ParmsSize));
		FMemory::Memzero(Buffer, Function->ParmsSize);
		Target->ProcessEvent(Function, Buffer);
	}

	static UClass* LoadHudClass()
	{
		return StaticLoadClass(AHUD::StaticClass(), nullptr, InventoryHudClassPath);
	}

	static UClass* LoadInventoryComponentClass()
	{
		return StaticLoadClass(UActorComponent::StaticClass(), nullptr, InventoryComponentClassPath);
	}

	static UClass* LoadCharacterPreviewClass()
	{
		return StaticLoadClass(AActor::StaticClass(), nullptr, CharacterPreviewClassPath);
	}

	static UActorComponent* EnsureInventoryComponent(APlayerController* PC)
	{
		UClass* Class = LoadInventoryComponentClass();
		if (!PC || !Class)
		{
			return nullptr;
		}
		if (UActorComponent* Existing = PC->FindComponentByClass(Class))
		{
			return Existing;
		}
		UActorComponent* Comp = NewObject<UActorComponent>(PC, Class, TEXT("AC_Inventory"));
		if (!Comp)
		{
			return nullptr;
		}
		Comp->RegisterComponent();
		if (UFunction* Setup = Comp->FindFunction(TEXT("Setup")))
		{
			SafeProcessEvent(Comp, Setup);
		}
		return Comp;
	}

	static AHUD* EnsureHud(APlayerController* PC)
	{
		UClass* Class = LoadHudClass();
		if (!PC || !Class)
		{
			return nullptr;
		}
		if (AHUD* Existing = PC->GetHUD())
		{
			if (Existing->IsA(Class))
			{
				return Existing;
			}
			Existing->Destroy();
		}
		UWorld* World = PC->GetWorld();
		if (!World)
		{
			return nullptr;
		}
		FActorSpawnParameters Params;
		Params.Owner = PC;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		AHUD* Hud = World->SpawnActor<AHUD>(Class, Params);
		if (!Hud)
		{
			return nullptr;
		}
		PC->MyHUD = Hud;
		Hud->SetOwner(PC);
		if (UFunction* Setup = Hud->FindFunction(TEXT("Setup")))
		{
			SafeProcessEvent(Hud, Setup);
		}
		return Hud;
	}

	static UUserWidget* GetWidgetGame(APlayerController* PC)
	{
		AHUD* Hud = PC ? PC->GetHUD() : nullptr;
		if (Hud)
		{
			if (FObjectProperty* Prop = FindFProperty<FObjectProperty>(Hud->GetClass(), TEXT("Widget_Game")))
			{
				if (UUserWidget* WG = Cast<UUserWidget>(Prop->GetObjectPropertyValue_InContainer(Hud)))
				{
					return WG;
				}
			}
		}
		for (TObjectIterator<UUserWidget> It; It; ++It)
		{
			UUserWidget* Candidate = *It;
			if (!IsValid(Candidate) || !Candidate->GetClass())
			{
				continue;
			}
			if (!Candidate->GetClass()->GetName().StartsWith(TEXT("WBP_Game_C")))
			{
				continue;
			}
			if (Candidate->GetOwningPlayer() == PC || Candidate->IsInViewport())
			{
				return Candidate;
			}
		}
		return nullptr;
	}

	static UWidget* GetNamed(UUserWidget* Root, const TCHAR* Name)
	{
		if (!Root)
		{
			return nullptr;
		}
		if (FObjectProperty* Prop = FindFProperty<FObjectProperty>(Root->GetClass(), Name))
		{
			if (UWidget* Bound = Cast<UWidget>(Prop->GetObjectPropertyValue_InContainer(Root)))
			{
				return Bound;
			}
		}
		return Root->GetWidgetFromName(Name);
	}

	static void Hide(UWidget* W)
	{
		if (W)
		{
			W->SetVisibility(ESlateVisibility::Collapsed);
		}
	}

	static void Show(UWidget* W)
	{
		if (W)
		{
#if PLATFORM_IOS || PLATFORM_ANDROID
			W->SetVisibility(ESlateVisibility::Visible);
#else
			W->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
#endif
		}
	}

	static bool IsInventoryLauncherScreenPoint(
		const FVector2D& ScreenPos,
		const int32 ViewportSizeX,
		const int32 ViewportSizeY)
	{
		if (ViewportSizeX <= 0 || ViewportSizeY <= 0)
		{
			return false;
		}

		const float NormX = ScreenPos.X / static_cast<float>(ViewportSizeX);
		const float NormY = ScreenPos.Y / static_cast<float>(ViewportSizeY);

		// Top-right Inventory launcher (generous bounds for notches / DPI variance).
		return NormX >= 0.55f && NormX <= 1.05f && NormY >= 0.f && NormY <= 0.18f;
	}

	static bool TryGetPrimaryTouchScreenPoint(APlayerController* PC, FVector2D& OutScreenPos)
	{
		if (!PC)
		{
			return false;
		}

		float LocationX = 0.f;
		float LocationY = 0.f;
		bool bIsPressed = false;
		PC->GetInputTouchState(ETouchIndex::Touch1, LocationX, LocationY, bIsPressed);
		if (!bIsPressed)
		{
			return false;
		}

		OutScreenPos = FVector2D(LocationX, LocationY);
		return true;
	}

	static AActor* EnsureCharacterPreview(APlayerController* PC);

	static UUserWidget* CreateWidgetGameFallback(APlayerController* PC, AHUD* Hud)
	{
		UClass* WidgetClass = StaticLoadClass(UUserWidget::StaticClass(), nullptr, WidgetGameClassPath);
		if (!PC || !WidgetClass)
		{
			return nullptr;
		}

		UUserWidget* WidgetGame = CreateWidget<UUserWidget>(PC, WidgetClass);
		if (!WidgetGame)
		{
			return nullptr;
		}

		if (!WidgetGame->IsInViewport())
		{
			WidgetGame->AddToViewport(0);
		}

		if (Hud)
		{
			if (FObjectProperty* Prop = FindFProperty<FObjectProperty>(Hud->GetClass(), TEXT("Widget_Game")))
			{
				Prop->SetObjectPropertyValue_InContainer(Hud, WidgetGame);
			}
		}

		UE_LOG(LogTemp, Warning, TEXT("SCAR inventory: created WBP_Game fallback widget"));
		return WidgetGame;
	}

	static UUserWidget* EnsureWidgetGameReady(APlayerController* PC)
	{
		EnsureInventoryComponent(PC);
		AHUD* Hud = EnsureHud(PC);
		if (Hud)
		{
			if (UFunction* Setup = Hud->FindFunction(TEXT("Setup")))
			{
				SafeProcessEvent(Hud, Setup);
			}
		}

		UUserWidget* WidgetGame = GetWidgetGame(PC);
		if (!WidgetGame && Hud)
		{
			// HUD blueprint may finish Widget_Game on its next timer tick — try once more.
			if (UFunction* TrySetup = Hud->FindFunction(TEXT("Try to setup")))
			{
				SafeProcessEvent(Hud, TrySetup);
			}
			else if (UFunction* TrySetupAlt = Hud->FindFunction(TEXT("TryToSetup")))
			{
				SafeProcessEvent(Hud, TrySetupAlt);
			}
			WidgetGame = GetWidgetGame(PC);
		}

		if (!WidgetGame)
		{
			WidgetGame = CreateWidgetGameFallback(PC, Hud);
		}

		return WidgetGame;
	}

	/** Remove vitals / hotbar / help — never the backpack Content_Inventory. */
	static void HideGameplayChrome(UUserWidget* WidgetGame)
	{
		Hide(GetNamed(WidgetGame, TEXT("Content_HUD")));
		Hide(GetNamed(WidgetGame, TEXT("WBP_HelpKeysBox")));
		Hide(GetNamed(WidgetGame, TEXT("Content_Demo")));
		Hide(GetNamed(WidgetGame, TEXT("WBP_PlayerStatsHUD")));
		Hide(GetNamed(WidgetGame, TEXT("WBP_QuickUseBoxHUD")));
		Hide(GetNamed(WidgetGame, TEXT("WBP_PlayerStamina")));
		Hide(GetNamed(WidgetGame, TEXT("WBP_PlayerStatsBar")));
	}

	static constexpr TCHAR CraftingSlotClassPath[] =
		TEXT("/Game/InventorySystem_0_5/Blueprints/UserInterfaces/Game/Crafting/WBP_CraftingSlot.WBP_CraftingSlot_C");
	static constexpr int32 QuickCraftColumns = 5;
	static constexpr int32 QuickCraftSlotCount = 15;

	static void ForEachWidgetRecursive(UWidget* Widget, TFunctionRef<void(UWidget*)> Callback)
	{
		if (!Widget)
		{
			return;
		}

		Callback(Widget);

		if (UPanelWidget* Panel = Cast<UPanelWidget>(Widget))
		{
			const int32 ChildCount = Panel->GetChildrenCount();
			for (int32 ChildIndex = 0; ChildIndex < ChildCount; ++ChildIndex)
			{
				ForEachWidgetRecursive(Panel->GetChildAt(ChildIndex), Callback);
			}
		}
	}

	static UUserWidget* FindInventoryPanel(UUserWidget* WidgetGame)
	{
		if (UUserWidget* Bound = Cast<UUserWidget>(GetNamed(WidgetGame, TEXT("WBP_Inventory"))))
		{
			return Bound;
		}

		UUserWidget* Found = nullptr;
		ForEachWidgetRecursive(
			WidgetGame && WidgetGame->WidgetTree ? WidgetGame->WidgetTree->RootWidget : nullptr,
			[&Found](UWidget* Widget)
			{
				if (!Found && Widget && Widget->GetClass()->GetName().StartsWith(TEXT("WBP_Inventory_C")))
				{
					Found = Cast<UUserWidget>(Widget);
				}
			});
		return Found;
	}

	static UUserWidget* FindCraftingBox(UUserWidget* Inventory)
	{
		if (!Inventory)
		{
			return nullptr;
		}

		if (UUserWidget* Bound = Cast<UUserWidget>(GetNamed(Inventory, TEXT("CraftingBox"))))
		{
			return Bound;
		}
		if (UUserWidget* Bound = Cast<UUserWidget>(GetNamed(Inventory, TEXT("WBP_CraftingBox"))))
		{
			return Bound;
		}

		UUserWidget* Found = nullptr;
		ForEachWidgetRecursive(
			Inventory->WidgetTree ? Inventory->WidgetTree->RootWidget : nullptr,
			[&Found](UWidget* Widget)
			{
				if (!Found && Widget && Widget->GetClass()->GetName().StartsWith(TEXT("WBP_CraftingBox_C")))
				{
					Found = Cast<UUserWidget>(Widget);
				}
			});
		return Found;
	}

	static UPanelWidget* FindCraftingGrid(UUserWidget* CraftingBox)
	{
		if (!CraftingBox)
		{
			return nullptr;
		}

		if (UPanelWidget* Bound = Cast<UPanelWidget>(GetNamed(CraftingBox, TEXT("CraftingGrid"))))
		{
			return Bound;
		}

		UPanelWidget* Found = nullptr;
		ForEachWidgetRecursive(
			CraftingBox->WidgetTree ? CraftingBox->WidgetTree->RootWidget : nullptr,
			[&Found](UWidget* Widget)
			{
				if (!Found && Widget && Widget->GetFName() == TEXT("CraftingGrid"))
				{
					Found = Cast<UPanelWidget>(Widget);
				}
			});
		return Found;
	}

	static bool CraftingSlotHasDemoItem(UUserWidget* Slot)
	{
		if (!Slot)
		{
			return false;
		}

		if (FNameProperty* ItemNameProp = FindFProperty<FNameProperty>(Slot->GetClass(), TEXT("ItemName")))
		{
			if (ItemNameProp->GetPropertyValue_InContainer(Slot) != NAME_None)
			{
				return true;
			}
		}

		bool bHasVisibleIcon = false;
		ForEachWidgetRecursive(Slot, [&bHasVisibleIcon](UWidget* Widget)
		{
			if (bHasVisibleIcon || !Widget)
			{
				return;
			}
			if (UImage* Image = Cast<UImage>(Widget))
			{
				const FString Name = Widget->GetName();
				if (Name.Contains(TEXT("Icon"), ESearchCase::IgnoreCase)
					&& Widget->GetVisibility() != ESlateVisibility::Collapsed
					&& Widget->GetVisibility() != ESlateVisibility::Hidden)
				{
					const FSlateBrush& Brush = Image->GetBrush();
					if (Brush.GetResourceObject() != nullptr)
					{
						bHasVisibleIcon = true;
					}
				}
			}
		});
		return bHasVisibleIcon;
	}

	static void ClearCraftingSlotVisuals(UUserWidget* Slot)
	{
		if (!Slot)
		{
			return;
		}

		if (FNameProperty* ItemNameProp = FindFProperty<FNameProperty>(Slot->GetClass(), TEXT("ItemName")))
		{
			ItemNameProp->SetPropertyValue_InContainer(Slot, NAME_None);
		}
		if (FStrProperty* AmountProp = FindFProperty<FStrProperty>(Slot->GetClass(), TEXT("Amount")))
		{
			AmountProp->SetPropertyValue_InContainer(Slot, FString());
		}

		Hide(GetNamed(Slot, TEXT("Icon")));
		Hide(GetNamed(Slot, TEXT("ItemIcon")));
		Hide(GetNamed(Slot, TEXT("RarityBorder")));
		Hide(GetNamed(Slot, TEXT("Amount")));

		ForEachWidgetRecursive(Slot, [](UWidget* Widget)
		{
			if (!Widget)
			{
				return;
			}

			const FString Name = Widget->GetName();
			if (Name.Contains(TEXT("Icon"), ESearchCase::IgnoreCase))
			{
				Hide(Widget);
				if (UImage* Image = Cast<UImage>(Widget))
				{
					Image->SetBrushFromTexture(nullptr);
				}
			}
			if (Name.Contains(TEXT("Rarity"), ESearchCase::IgnoreCase))
			{
				Hide(Widget);
			}
			if (UTextBlock* Text = Cast<UTextBlock>(Widget))
			{
				if (Name.Contains(TEXT("Amount"), ESearchCase::IgnoreCase))
				{
					Text->SetText(FText::GetEmpty());
					Hide(Text);
				}
			}
		});
	}

	static void PopulateEmptyQuickCraftGrid(UPanelWidget* CraftingGrid, APlayerController* PC)
	{
		if (!CraftingGrid || !PC)
		{
			return;
		}

		UClass* SlotClass = StaticLoadClass(UUserWidget::StaticClass(), nullptr, CraftingSlotClassPath);
		if (!SlotClass)
		{
			return;
		}

		CraftingGrid->ClearChildren();

		for (int32 SlotIndex = 0; SlotIndex < QuickCraftSlotCount; ++SlotIndex)
		{
			UUserWidget* Slot = CreateWidget<UUserWidget>(PC, SlotClass);
			if (!Slot)
			{
				continue;
			}

			CraftingGrid->AddChild(Slot);
			ClearCraftingSlotVisuals(Slot);

			if (UUniformGridSlot* GridSlot = Cast<UUniformGridSlot>(Slot->Slot))
			{
				GridSlot->SetColumn(SlotIndex % QuickCraftColumns);
				GridSlot->SetRow(SlotIndex / QuickCraftColumns);
			}
		}
	}

	/** Replace demo DT_Inventory quick-craft entries with empty slot boxes. */
	static void StripDemoQuickCraftItems(UUserWidget* WidgetGame, APlayerController* PC)
	{
		UUserWidget* Inventory = FindInventoryPanel(WidgetGame);
		UUserWidget* CraftingBox = FindCraftingBox(Inventory);
		UPanelWidget* CraftingGrid = FindCraftingGrid(CraftingBox);
		if (!CraftingGrid)
		{
			return;
		}

		Show(CraftingBox);

		bool bHasDemoItems = false;
		const int32 ChildCount = CraftingGrid->GetChildrenCount();
		for (int32 ChildIndex = 0; ChildIndex < ChildCount; ++ChildIndex)
		{
			if (CraftingSlotHasDemoItem(Cast<UUserWidget>(CraftingGrid->GetChildAt(ChildIndex))))
			{
				bHasDemoItems = true;
				break;
			}
		}

		if (bHasDemoItems || ChildCount != QuickCraftSlotCount)
		{
			PopulateEmptyQuickCraftGrid(CraftingGrid, PC);
			return;
		}

		for (int32 ChildIndex = 0; ChildIndex < ChildCount; ++ChildIndex)
		{
			ClearCraftingSlotVisuals(Cast<UUserWidget>(CraftingGrid->GetChildAt(ChildIndex)));
		}
	}

	static UImage* FindCharacterPreviewImage(UUserWidget* WidgetGame)
	{
		if (!WidgetGame)
		{
			return nullptr;
		}
		if (UWidget* Named = GetNamed(WidgetGame, TEXT("CharacterPreview")))
		{
			return Cast<UImage>(Named);
		}
		if (UUserWidget* Inventory = Cast<UUserWidget>(GetNamed(WidgetGame, TEXT("WBP_Inventory"))))
		{
			if (UWidget* Named = Inventory->GetWidgetFromName(TEXT("CharacterPreview")))
			{
				return Cast<UImage>(Named);
			}
			if (FObjectProperty* Prop =
				FindFProperty<FObjectProperty>(Inventory->GetClass(), TEXT("CharacterPreview")))
			{
				return Cast<UImage>(Prop->GetObjectPropertyValue_InContainer(Inventory));
			}
		}
		return nullptr;
	}

	static AActor* EnsureCharacterPreview(APlayerController* PC)
	{
		UWorld* World = PC ? PC->GetWorld() : nullptr;
		UClass* PreviewClass = LoadCharacterPreviewClass();
		if (!World || !PreviewClass)
		{
			return nullptr;
		}

		TArray<AActor*> Existing;
		UGameplayStatics::GetAllActorsOfClass(World, PreviewClass, Existing);
		for (AActor* Actor : Existing)
		{
			if (IsValid(Actor))
			{
				// Ensure render-target / MaterialInstance exist (BeginPlay may have been skipped).
				if (UFunction* Setup = Actor->FindFunction(TEXT("Setup")))
				{
					if (FObjectProperty* MatProp =
						FindFProperty<FObjectProperty>(Actor->GetClass(), TEXT("MaterialInstance")))
					{
						if (!MatProp->GetObjectPropertyValue_InContainer(Actor))
						{
							SafeProcessEvent(Actor, Setup);
						}
					}
				}
				return Actor;
			}
		}

		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		AActor* Preview = World->SpawnActor<AActor>(
			PreviewClass, CharacterPreviewSpawnLocation, FRotator::ZeroRotator, Params);
		if (Preview)
		{
			UE_LOG(LogTemp, Warning, TEXT("SCAR inventory: spawned BP_CharacterPreview"));
			if (UFunction* Setup = Preview->FindFunction(TEXT("Setup")))
			{
				SafeProcessEvent(Preview, Setup);
			}
		}
		return Preview;
	}

	static void BindCharacterPreview(APlayerController* PC)
	{
		AActor* Preview = EnsureCharacterPreview(PC);
		UUserWidget* WidgetGame = GetWidgetGame(PC);
		UImage* Image = FindCharacterPreviewImage(WidgetGame);
		if (!Preview || !Image)
		{
			return;
		}

		UMaterialInterface* Material = nullptr;
		if (FObjectProperty* MatProp =
			FindFProperty<FObjectProperty>(Preview->GetClass(), TEXT("MaterialInstance")))
		{
			Material = Cast<UMaterialInterface>(MatProp->GetObjectPropertyValue_InContainer(Preview));
		}
		if (!Material)
		{
			if (FObjectProperty* MatProp =
				FindFProperty<FObjectProperty>(Preview->GetClass(), TEXT("Material")))
			{
				Material = Cast<UMaterialInterface>(MatProp->GetObjectPropertyValue_InContainer(Preview));
			}
		}
		if (Material)
		{
			Image->SetBrushFromMaterial(Material);
		}

		TArray<USceneCaptureComponent2D*> Captures;
		Preview->GetComponents<USceneCaptureComponent2D>(Captures);
		for (USceneCaptureComponent2D* Capture : Captures)
		{
			if (Capture)
			{
				Capture->bCaptureEveryFrame = GBackpackOpen;
				Capture->bCaptureOnMovement = GBackpackOpen;
				if (GBackpackOpen)
				{
					Capture->CaptureScene();
				}
			}
		}
	}

	/** Always drive WBP_Game::Set_ContentVisibility (HUD ToggleInventory is an interface event). */
	static void CallNativeToggle(UUserWidget* WidgetGame)
	{
		if (!WidgetGame)
		{
			return;
		}
		if (UFunction* Fn = WidgetGame->FindFunction(TEXT("Set_ContentVisibility")))
		{
			SafeProcessEvent(WidgetGame, Fn);
		}
	}

	static bool IsContentInventoryVisible(UWidget* ContentInventory)
	{
		if (!ContentInventory)
		{
			return false;
		}
		const ESlateVisibility Vis = ContentInventory->GetVisibility();
		return Vis != ESlateVisibility::Collapsed && Vis != ESlateVisibility::Hidden;
	}

	static void SetCanvasZOrder(UWidget* Widget, const int32 ZOrder)
	{
		if (!Widget)
		{
			return;
		}
		if (UCanvasPanelSlot* CanvasSlot = Cast<UCanvasPanelSlot>(Widget->Slot))
		{
			CanvasSlot->SetZOrder(ZOrder);
		}
	}

	/**
	 * Solid black behind inventory panels via FadeContent only.
	 * Do NOT add a separate Slate fullscreen overlay — on iOS that covers UMG entirely.
	 */
	static void ApplyBlackBackdrop(UUserWidget* WidgetGame, const bool bOpen)
	{
		// Always tear down any leftover Slate overlay from older builds.
		if (GBlackBackdrop.IsValid() && GEngine && GEngine->GameViewport)
		{
			GEngine->GameViewport->RemoveViewportWidgetContent(GBlackBackdrop.ToSharedRef());
			GBlackBackdrop.Reset();
		}

		UWidget* Fade = GetNamed(WidgetGame, TEXT("FadeContent"));
		UWidget* ContentInventory = GetNamed(WidgetGame, TEXT("Content_Inventory"));
		UWidget* InventoryWidget = GetNamed(WidgetGame, TEXT("WBP_Inventory"));

		if (bOpen)
		{
#if PLATFORM_IOS || PLATFORM_ANDROID
			// Fullscreen FadeContent covers inventory on mobile — hide it and rely on panel layout.
			Hide(Fade);
#else
			if (Fade)
			{
				Fade->SetVisibility(ESlateVisibility::HitTestInvisible);
				Fade->SetRenderOpacity(1.f);
				if (UImage* FadeImage = Cast<UImage>(Fade))
				{
					FadeImage->SetColorAndOpacity(FLinearColor::Black);
				}
				SetCanvasZOrder(Fade, 0);
			}
#endif

			// Inventory must paint above any backdrop.
			if (ContentInventory)
			{
				Show(ContentInventory);
				ContentInventory->SetRenderOpacity(1.f);
				SetCanvasZOrder(ContentInventory, 10);
			}
			if (InventoryWidget)
			{
				Show(InventoryWidget);
				InventoryWidget->SetRenderOpacity(1.f);
				SetCanvasZOrder(InventoryWidget, 11);
			}
			if (WidgetGame)
			{
				Show(WidgetGame);
				WidgetGame->SetRenderOpacity(1.f);
			}
		}
		else
		{
			Hide(Fade);
		}
	}

	/** Pause-menu input: UI only, pawn cannot move/shoot. */
	static void SetGameplayInputBlocked(APlayerController* PC, const bool bBlocked)
	{
		if (!PC)
		{
			return;
		}

		if (bBlocked)
		{
			if (APawn* Pawn = PC->GetPawn())
			{
				Pawn->DisableInput(PC);
				GInputBlockedPawn = Pawn;
			}
			PC->SetIgnoreMoveInput(true);
			PC->SetIgnoreLookInput(true);
			PC->bShowMouseCursor = true;
			PC->bEnableClickEvents = true;
			PC->bEnableTouchEvents = true;

			// GameAndUI keeps UMG painting correctly on iOS; pawn input stays disabled above.
			FInputModeGameAndUI Mode;
			Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
			Mode.SetHideCursorDuringCapture(false);
			if (UUserWidget* WidgetGame = GetWidgetGame(PC))
			{
				Mode.SetWidgetToFocus(WidgetGame->TakeWidget());
			}
			PC->SetInputMode(Mode);
		}
		else
		{
			if (APawn* PreviouslyBlocked = GInputBlockedPawn.Get())
			{
				PreviouslyBlocked->EnableInput(PC);
			}
			if (APawn* Pawn = PC->GetPawn())
			{
				Pawn->EnableInput(PC);
			}
			GInputBlockedPawn.Reset();
			PC->SetIgnoreMoveInput(false);
			PC->SetIgnoreLookInput(false);
			PC->bShowMouseCursor = false;
			// Keep touch/click enabled so top-right launcher buttons still work on iOS.
			PC->bEnableClickEvents = true;
			PC->bEnableTouchEvents = true;

			FInputModeGameOnly Mode;
			PC->SetInputMode(Mode);
		}
	}

	/**
	 * Drive the asset's Set_ContentVisibility so fade + layout stay correct, then always
	 * strip gameplay chrome (vitals/hotbar) so SCAR never shows the always-on HUD.
	 */
	static void SetBackpackOpen(APlayerController* PC, const bool bOpen)
	{
		UUserWidget* WidgetGame = GetWidgetGame(PC);
		UWidget* ContentInventory = GetNamed(WidgetGame, TEXT("Content_Inventory"));
		const bool bLooksOpen = IsContentInventoryVisible(ContentInventory);

		if (bOpen != bLooksOpen)
		{
			CallNativeToggle(WidgetGame);
		}

		WidgetGame = GetWidgetGame(PC);
		ContentInventory = GetNamed(WidgetGame, TEXT("Content_Inventory"));

		if (bOpen)
		{
			Show(ContentInventory);
			Show(GetNamed(WidgetGame, TEXT("WBP_Inventory")));
			if (UFunction* Update = WidgetGame ? WidgetGame->FindFunction(TEXT("Update_Inventory")) : nullptr)
			{
				SafeProcessEvent(WidgetGame, Update);
			}
			StripDemoQuickCraftItems(WidgetGame, PC);
		}
		else
		{
			Hide(ContentInventory);
			Hide(GetNamed(WidgetGame, TEXT("WBP_Inventory")));
		}

		// Native toggle restores Content_HUD on close — strip it every time.
		HideGameplayChrome(WidgetGame);
		GBackpackOpen = bOpen;
		BindCharacterPreview(PC);
		ApplyBlackBackdrop(WidgetGame, bOpen);
		SetGameplayInputBlocked(PC, bOpen);

		UE_LOG(
			LogTemp,
			Warning,
			TEXT("SCAR inventory: BACKPACK %s (game=%s inv=%s)"),
			bOpen ? TEXT("OPEN") : TEXT("CLOSED"),
			WidgetGame ? TEXT("ok") : TEXT("null"),
			ContentInventory ? TEXT("ok") : TEXT("null"));
	}

	class FInventoryInputProcessor final : public IInputProcessor
	{
	public:
		virtual void Tick(const float, FSlateApplication&, TSharedRef<ICursor>) override {}

		virtual bool HandleKeyDownEvent(FSlateApplication&, const FKeyEvent& Event) override
		{
			if (Event.IsRepeat() || Event.GetKey() != EKeys::Tab)
			{
				return false;
			}
			if (APlayerController* PC = GTabPC.Get())
			{
				USCARInventoryBlueprintLibrary::ToggleInventoryMenu(PC);
				return true;
			}
			return false;
		}

		/** iOS routes many touches through Slate pointer / LMB — same path as Tab. */
		virtual bool HandleMouseButtonDownEvent(FSlateApplication&, const FPointerEvent& Event) override
		{
			APlayerController* PC = GTabPC.Get();
			if (!PC)
			{
				return false;
			}

			int32 SizeX = 0;
			int32 SizeY = 0;
			PC->GetViewportSize(SizeX, SizeY);
			const FVector2D ScreenPos = Event.GetScreenSpacePosition();
			if (!IsInventoryLauncherScreenPoint(ScreenPos, SizeX, SizeY))
			{
				return false;
			}

			USCARInventoryBlueprintLibrary::ToggleInventoryMenu(PC);
			return true;
		}
	};

	static void EnsureTabHook(APlayerController* PC)
	{
		GTabPC = PC;
		if (GTabProcessor.IsValid() || !FSlateApplication::IsInitialized())
		{
			return;
		}
		GTabProcessor = MakeShared<FInventoryInputProcessor>();
		FSlateApplication::Get().RegisterInputPreProcessor(GTabProcessor, 0);
	}
}

bool USCARInventoryBlueprintLibrary::EnsureInventorySystem(APlayerController* PlayerController)
{
	if (!PlayerController || !PlayerController->IsLocalController())
	{
		return false;
	}
	SCARInventoryInternal::EnsureInventoryComponent(PlayerController);
	// Spawn preview BEFORE HUD/widgets so WBP_Inventory Construct's GetAllActors
	// (if still present) does not Array_Get a None and spam SetBrushFromMaterial errors.
	SCARInventoryInternal::EnsureCharacterPreview(PlayerController);
	SCARInventoryInternal::EnsureHud(PlayerController);
	SCARInventoryInternal::BindCharacterPreview(PlayerController);
	SCARInventoryInternal::EnsureTabHook(PlayerController);
	SCARInventoryInternal::HideGameplayChrome(SCARInventoryInternal::GetWidgetGame(PlayerController));
	return true;
}

void USCARInventoryBlueprintLibrary::TickInventoryPresentation(APlayerController* PlayerController)
{
	if (!PlayerController || !PlayerController->IsLocalController())
	{
		return;
	}
	EnsureInventorySystem(PlayerController);
	UUserWidget* WidgetGame = SCARInventoryInternal::GetWidgetGame(PlayerController);
	SCARInventoryInternal::HideGameplayChrome(WidgetGame);

	// Keep backpack panel matching our bool without touching its internal layout.
	UWidget* ContentInventory = SCARInventoryInternal::GetNamed(WidgetGame, TEXT("Content_Inventory"));
	if (SCARInventoryInternal::GBackpackOpen)
	{
		SCARInventoryInternal::Show(ContentInventory);
		SCARInventoryInternal::Show(SCARInventoryInternal::GetNamed(WidgetGame, TEXT("WBP_Inventory")));
		SCARInventoryInternal::StripDemoQuickCraftItems(WidgetGame, PlayerController);
		SCARInventoryInternal::ApplyBlackBackdrop(WidgetGame, true);
		SCARInventoryInternal::BindCharacterPreview(PlayerController);
	}
	else
	{
		SCARInventoryInternal::Hide(ContentInventory);
		SCARInventoryInternal::ApplyBlackBackdrop(WidgetGame, false);
	}
}

bool USCARInventoryBlueprintLibrary::ToggleInventoryMenu(APlayerController* PlayerController)
{
	if (!PlayerController || !PlayerController->IsLocalController())
	{
		return false;
	}

	const double Now = FPlatformTime::Seconds();
	if (Now - SCARInventoryInternal::GLastToggleTime < 0.2)
	{
		return SCARInventoryInternal::GBackpackOpen;
	}
	SCARInventoryInternal::GLastToggleTime = Now;

	SCARInventoryInternal::EnsureCharacterPreview(PlayerController);
	SCARInventoryInternal::EnsureTabHook(PlayerController);
	const UUserWidget* WidgetGame = SCARInventoryInternal::EnsureWidgetGameReady(PlayerController);
	if (!WidgetGame)
	{
		UE_LOG(LogTemp, Warning, TEXT("SCAR inventory: Widget_Game not ready — cannot toggle"));
		return false;
	}

	SCARInventoryInternal::SetBackpackOpen(PlayerController, !SCARInventoryInternal::GBackpackOpen);
	return true;
}

bool USCARInventoryBlueprintLibrary::IsInventoryMenuOpen(APlayerController* PlayerController)
{
	return PlayerController && SCARInventoryInternal::GBackpackOpen;
}
