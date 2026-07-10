#include "SCARSniperAdsCameraComponent.h"

#include "SCARNearClipCameraModifier.h"
#include "SCARPhonePreviewParity.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/PrimitiveComponent.h"
#include "Engine/Engine.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"

USCARSniperAdsCameraComponent::USCARSniperAdsCameraComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;
}

void USCARSniperAdsCameraComponent::BeginPlay()
{
	Super::BeginPlay();
	EnsureNearClipModifier();
	ConfigureFirstPersonCamera();
	TagWeaponMeshesFirstPerson();
}

UCameraComponent* USCARSniperAdsCameraComponent::FindFirstPersonCamera() const
{
	const APawn* Pawn = Cast<APawn>(GetOwner());
	if (!Pawn)
	{
		return nullptr;
	}

	TArray<UCameraComponent*> Cameras;
	Pawn->GetComponents<UCameraComponent>(Cameras);
	for (UCameraComponent* Camera : Cameras)
	{
		if (Camera && Camera->GetName().Contains(TEXT("FirstPersonCamera")))
		{
			return Camera;
		}
	}

	return Cameras.Num() > 0 ? Cameras[0] : nullptr;
}

void USCARSniperAdsCameraComponent::EnsureNearClipModifier()
{
	if (NearClipModifier)
	{
		return;
	}

	APawn* Pawn = Cast<APawn>(GetOwner());
	if (!Pawn || !Pawn->IsLocallyControlled())
	{
		return;
	}

	APlayerController* PC = Cast<APlayerController>(Pawn->GetController());
	if (!PC || !PC->PlayerCameraManager)
	{
		return;
	}

	NearClipModifier = Cast<USCARNearClipCameraModifier>(
		PC->PlayerCameraManager->AddNewCameraModifier(USCARNearClipCameraModifier::StaticClass()));
	if (NearClipModifier)
	{
		NearClipModifier->NearClipPlane = NearClipPlane;
		NearClipModifier->AdsFirstPersonFov = AdsFirstPersonFov;
		NearClipModifier->AdsFirstPersonScale = AdsFirstPersonScale;
		NearClipModifier->AdsFovThreshold = AdsFovThreshold;
		NearClipModifier->EnableModifier();
	}
}

void USCARSniperAdsCameraComponent::ConfigureFirstPersonCamera()
{
	if (bCameraConfigured)
	{
		return;
	}

	UCameraComponent* Camera = FindFirstPersonCamera();
	if (!Camera)
	{
		return;
	}

	if (SCARPhonePreviewParity::ShouldUseMobileCameraPath(GetWorld()))
	{
		Camera->SetEnableFirstPersonFieldOfView(false);
		Camera->SetEnableFirstPersonScale(false);
		Camera->SetFirstPersonScale(1.f);
	}
	else
	{
		Camera->SetEnableFirstPersonFieldOfView(true);
		Camera->SetEnableFirstPersonScale(true);
		Camera->SetFirstPersonFieldOfView(AdsFirstPersonFov);
		Camera->SetFirstPersonScale(1.f);
	}
	bCameraConfigured = true;
}

void USCARSniperAdsCameraComponent::UpdateFirstPersonScaleForAds()
{
	UCameraComponent* Camera = FindFirstPersonCamera();
	if (!Camera)
	{
		return;
	}

	const APawn* Pawn = Cast<APawn>(GetOwner());
	if (!Pawn || !Pawn->IsLocallyControlled())
	{
		return;
	}

	const APlayerController* PC = Cast<APlayerController>(Pawn->GetController());
	if (!PC || !PC->PlayerCameraManager)
	{
		return;
	}

	if (SCARPhonePreviewParity::ShouldUseMobileCameraPath(GetWorld()))
	{
		Camera->SetFirstPersonScale(1.f);
		return;
	}

	const float CurrentFov = PC->PlayerCameraManager->GetFOVAngle();
	const float Scale = CurrentFov <= AdsFovThreshold ? AdsFirstPersonScale : 1.f;
	Camera->SetFirstPersonScale(Scale);
}

void USCARSniperAdsCameraComponent::TagActorPrimitives(AActor* Actor) const
{
	if (!Actor)
	{
		return;
	}

	TArray<UPrimitiveComponent*> Primitives;
	Actor->GetComponents<UPrimitiveComponent>(Primitives);
	for (UPrimitiveComponent* Prim : Primitives)
	{
		if (!Prim)
		{
			continue;
		}

		const FString Name = Prim->GetName();
		if (Name.Contains(TEXT("Optic"))
			|| Name.Contains(TEXT("Weapon"))
			|| Name.Contains(TEXT("Scope"))
			|| Name.Contains(TEXT("Skeletal"))
			|| Name.Contains(TEXT("StaticMesh"))
			|| Name.Contains(TEXT("Mesh")))
		{
			Prim->SetFirstPersonPrimitiveType(EFirstPersonPrimitiveType::FirstPerson);
			Prim->SetBoundsScale(1.5f);
		}
	}

	TArray<AActor*> Attached;
	Actor->GetAttachedActors(Attached);
	for (AActor* Child : Attached)
	{
		TagActorPrimitives(Child);
	}
}

void USCARSniperAdsCameraComponent::TagWeaponMeshesFirstPerson()
{
	APawn* Pawn = Cast<APawn>(GetOwner());
	if (!Pawn)
	{
		return;
	}

	TagActorPrimitives(Pawn);

	TArray<AActor*> Attached;
	Pawn->GetAttachedActors(Attached, true, true);
	for (AActor* Actor : Attached)
	{
		TagActorPrimitives(Actor);
	}

	bMeshesTagged = true;
}

void USCARSniperAdsCameraComponent::TickComponent(
	const float DeltaTime,
	const ELevelTick TickType,
	FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	EnsureNearClipModifier();
	ConfigureFirstPersonCamera();
	UpdateFirstPersonScaleForAds();

	// Re-tag when weapon is spawned/swapped.
	if (!bMeshesTagged)
	{
		TagWeaponMeshesFirstPerson();
	}
}
