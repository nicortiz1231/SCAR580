#include "SCARWeaponAttachmentComponent.h"

#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "SCARWeaponAttachmentBlueprintLibrary.h"
#include "SCARWeaponModdingLauncherSlate.h"

USCARWeaponAttachmentComponent::USCARWeaponAttachmentComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;
	PrimaryComponentTick.TickGroup = TG_PostUpdateWork;
}

void USCARWeaponAttachmentComponent::BeginPlay()
{
	Super::BeginPlay();

	if (bShowAttachmentBar)
	{
		EnsureLauncher();
	}
}

void USCARWeaponAttachmentComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	Super::EndPlay(EndPlayReason);
}

void USCARWeaponAttachmentComponent::EnsureLauncher()
{
	APawn* Pawn = Cast<APawn>(GetOwner());
	if (!Pawn)
	{
		return;
	}

	APlayerController* PlayerController = Cast<APlayerController>(Pawn->GetController());
	if (!PlayerController && GetWorld())
	{
		PlayerController = GetWorld()->GetFirstPlayerController();
	}

	if (PlayerController && PlayerController->IsLocalController())
	{
		FSCARWeaponModdingLauncherSlate::Show(PlayerController);
	}
}

void USCARWeaponAttachmentComponent::TickComponent(
	const float DeltaTime,
	const ELevelTick TickType,
	FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	APawn* Pawn = Cast<APawn>(GetOwner());
	if (Pawn && Pawn->IsLocallyControlled())
	{
		USCARWeaponAttachmentBlueprintLibrary::EnsureWeaponLaserFlashEffectsForPawn(Pawn);
	}

	if (!bShowAttachmentBar)
	{
		return;
	}

	if (!FSCARWeaponModdingLauncherSlate::IsVisible())
	{
		EnsureLauncher();
	}
}
