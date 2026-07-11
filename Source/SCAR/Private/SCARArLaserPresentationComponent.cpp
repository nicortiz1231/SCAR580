#include "SCARArLaserPresentationComponent.h"

#include "GameFramework/Pawn.h"
#include "SCARWeaponAttachmentBlueprintLibrary.h"

USCARArLaserPresentationComponent::USCARArLaserPresentationComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;
	PrimaryComponentTick.TickGroup = TG_PostUpdateWork;
}

void USCARArLaserPresentationComponent::BeginPlay()
{
	Super::BeginPlay();

	if (APawn* Pawn = Cast<APawn>(GetOwner()))
	{
		if (Pawn->IsLocallyControlled())
		{
			USCARWeaponAttachmentBlueprintLibrary::EnsureWeaponLaserFlashEffectsForPawn(Pawn);
		}
	}
}

void USCARArLaserPresentationComponent::TickComponent(
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
}
