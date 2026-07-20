#include "SCARLocalFirstPersonArmsComponent.h"

#include "ARBlueprintLibrary.h"
#include "Animation/AnimInstance.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Engine/Engine.h"
#include "GameFramework/Actor.h"
#include "GameFramework/Pawn.h"
#include "SCARMultiplayerPawnSetup.h"
#include "UObject/UnrealType.h"

DEFINE_LOG_CATEGORY_STATIC(LogSCARLocalArms, Log, All);

USCARLocalFirstPersonArmsComponent::USCARLocalFirstPersonArmsComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	// Run after Bodycam procedural ADS / aim logic has written mesh transforms.
	PrimaryComponentTick.TickGroup = TG_LastDemotable;
}

void USCARLocalFirstPersonArmsComponent::BeginPlay()
{
	Super::BeginPlay();

	if (APawn* Pawn = Cast<APawn>(GetOwner()))
	{
		TrySetup(Pawn);
	}
}

bool USCARLocalFirstPersonArmsComponent::IsARRunning() const
{
	const FARSessionStatus SessionStatus = UARBlueprintLibrary::GetARSessionStatus();
	return SessionStatus.Status == EARSessionStatus::Running;
}

void USCARLocalFirstPersonArmsComponent::TrySetup(APawn* Pawn)
{
	if (!Pawn || !Pawn->IsLocallyControlled() || bLocalViewConfigured)
	{
		return;
	}

	if (!CachedFirstPersonCamera)
	{
		CachedFirstPersonCamera = FindFirstPersonCamera(Pawn);
	}

	if (!CachedSpringArm)
	{
		CachedSpringArm = FindSpringArm(Pawn);
	}

	if (!CachedFirstPersonMesh)
	{
		CachedFirstPersonMesh = FindMeshByExactName(Pawn, FirstPersonMeshComponentName);
	}

	if (!CachedThirdPersonMesh)
	{
		CachedThirdPersonMesh = FindMeshByExactName(Pawn, ThirdPersonMeshComponentName);
	}

	if (!CachedFirstPersonCamera || !CachedFirstPersonMesh)
	{
		return;
	}

	ConfigureLocalView(Pawn);
	bLocalViewConfigured = true;
	UE_LOG(
		LogSCARLocalArms,
		Log,
		TEXT("Configured camera-locked FP arms on %s (FP=%s relLoc=%s relRot=%s)"),
		*Pawn->GetName(),
		*CachedFirstPersonMesh->GetName(),
		*CameraAttachRelativeLocation.ToString(),
		*CameraAttachRelativeRotation.ToString());
}

void USCARLocalFirstPersonArmsComponent::ConfigureLocalView(APawn* Pawn)
{
	ConfigureSpringArmForAR();
	DisableCameraLookSwayForAR(Pawn);
	EnsureFirstPersonMeshOnCamera(Pawn);
	if (IsARRunning())
	{
		ConfigureMultiplayerBodyMesh(Pawn);
	}
	else
	{
		ConfigureEditorDesktopBodyMesh(Pawn);
	}
}

void USCARLocalFirstPersonArmsComponent::ConfigureSpringArmForAR()
{
	if (!CachedSpringArm || !IsARRunning() || bSpringArmConfiguredForAR)
	{
		return;
	}

	// Keep pitch/yaw tracking for aim, but strip roll so FP arms stay upright on
	// screen while the AR passthrough alone tilts with the physical phone.
	CachedSpringArm->bUsePawnControlRotation = true;
	CachedSpringArm->bInheritPitch = true;
	CachedSpringArm->bInheritYaw = true;
	CachedSpringArm->bInheritRoll = false;
	CachedSpringArm->bEnableCameraLag = false;
	CachedSpringArm->bEnableCameraRotationLag = false;

	if (CachedFirstPersonCamera)
	{
		CachedFirstPersonCamera->bUsePawnControlRotation = true;
	}

	bSpringArmConfiguredForAR = true;
}

void USCARLocalFirstPersonArmsComponent::DisableCameraLookSwayForAR(APawn* Pawn)
{
	if (!Pawn || !IsARRunning() || bCameraLookSwayDisabled)
	{
		return;
	}

	for (UActorComponent* Component : Pawn->GetComponents())
	{
		if (!Component || !Component->GetClass()->GetName().Contains(TEXT("ProceduralAnimation")))
		{
			continue;
		}

		if (FProperty* SwayProperty = Component->GetClass()->FindPropertyByName(TEXT("MouseSwayAmplitude")))
		{
			if (FStructProperty* StructProperty = CastField<FStructProperty>(SwayProperty))
			{
				if (StructProperty->Struct == TBaseStructure<FVector>::Get())
				{
					*StructProperty->ContainerPtrToValuePtr<FVector>(Component) = FVector::ZeroVector;
					bCameraLookSwayDisabled = true;
					UE_LOG(LogSCARLocalArms, Log, TEXT("Zeroed MouseSwayAmplitude on %s for AR"), *Component->GetName());
					return;
				}
			}
		}
	}
}

void USCARLocalFirstPersonArmsComponent::EnsureFirstPersonMeshOnCamera(APawn* Pawn)
{
	if (!Pawn || !CachedFirstPersonCamera || !CachedFirstPersonMesh)
	{
		return;
	}

	const bool bNeedsAttach = CachedFirstPersonMesh->GetAttachParent() != CachedFirstPersonCamera;
	if (bNeedsAttach)
	{
		CachedFirstPersonMesh->DetachFromComponent(FDetachmentTransformRules::KeepWorldTransform);
		CachedFirstPersonMesh->AttachToComponent(
			CachedFirstPersonCamera,
			FAttachmentTransformRules::KeepRelativeTransform);

		CameraAttachRelativeLocation = CachedFirstPersonMesh->GetRelativeLocation();
		CameraAttachRelativeRotation = CachedFirstPersonMesh->GetRelativeRotation();
		CameraAttachRelativeScale = CachedFirstPersonMesh->GetRelativeScale3D();
	}

	CachedFirstPersonMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	CachedFirstPersonMesh->SetHiddenInGame(false);
	CachedFirstPersonMesh->SetVisibility(true, true);
	CachedFirstPersonMesh->SetOwnerNoSee(false);
	CachedFirstPersonMesh->SetOnlyOwnerSee(true);
	CachedFirstPersonMesh->SetCastHiddenShadow(false);
	CachedFirstPersonMesh->SetFirstPersonPrimitiveType(EFirstPersonPrimitiveType::FirstPerson);
}

void USCARLocalFirstPersonArmsComponent::LockFirstPersonMeshToCamera()
{
	if (!CachedFirstPersonCamera || !CachedFirstPersonMesh)
	{
		return;
	}

	// Bodycam ADS writes component pitch/offset each frame. Reset it so the
	// mesh stays fixed to the camera; ADS pose continues via bone animation.
	CachedFirstPersonMesh->SetRelativeLocation(CameraAttachRelativeLocation);
	CachedFirstPersonMesh->SetRelativeRotation(CameraAttachRelativeRotation);
	CachedFirstPersonMesh->SetRelativeScale3D(CameraAttachRelativeScale);
}

void USCARLocalFirstPersonArmsComponent::ConfigureMultiplayerBodyMesh(APawn* Pawn)
{
	if (!CachedThirdPersonMesh)
	{
		return;
	}

	CachedThirdPersonMesh->SetHiddenInGame(false);
	CachedThirdPersonMesh->SetVisibility(true, true);
	CachedThirdPersonMesh->SetOwnerNoSee(true);
	CachedThirdPersonMesh->SetOnlyOwnerSee(false);
	CachedThirdPersonMesh->SetFirstPersonPrimitiveType(EFirstPersonPrimitiveType::WorldSpaceRepresentation);
}

void USCARLocalFirstPersonArmsComponent::ConfigureEditorDesktopBodyMesh(APawn* Pawn)
{
	if (IsARRunning() || !Pawn || !CachedThirdPersonMesh)
	{
		return;
	}

	ACharacter* Character = Cast<ACharacter>(Pawn);
	UCapsuleComponent* Capsule = Character ? Character->GetCapsuleComponent() : nullptr;
	if (!Capsule)
	{
		return;
	}

	SCARMultiplayerPawnSetup::EnsureMultiplayerFloor(Pawn->GetWorld());

	if (CachedThirdPersonMesh->GetAttachParent() != Capsule)
	{
		CachedThirdPersonMesh->AttachToComponent(
			Capsule,
			FAttachmentTransformRules::SnapToTargetNotIncludingScale);
	}

	const float MeshZ = -Capsule->GetScaledCapsuleHalfHeight();
	CachedThirdPersonMesh->SetRelativeLocation(FVector(0.f, 0.f, MeshZ));
	CachedThirdPersonMesh->SetRelativeRotation(FRotator::ZeroRotator);
	CachedThirdPersonMesh->SetRelativeScale3D(FVector::OneVector);

	static const TCHAR* MannyAnimBP =
		TEXT("/Game/BodycamFPSKIT/Demo/Character/Mannequins/Animations/ABP_Manny.ABP_Manny_C");
	if (TSubclassOf<UAnimInstance> MannyClass = LoadClass<UAnimInstance>(nullptr, MannyAnimBP))
	{
		if (CachedThirdPersonMesh->GetAnimClass() != MannyClass)
		{
			CachedThirdPersonMesh->SetAnimInstanceClass(MannyClass);
		}
	}

	CachedThirdPersonMesh->SetHiddenInGame(false);
	CachedThirdPersonMesh->SetVisibility(true, true);
	CachedThirdPersonMesh->SetOwnerNoSee(false);
	CachedThirdPersonMesh->SetOnlyOwnerSee(false);
	CachedThirdPersonMesh->SetCastHiddenShadow(false);
	CachedThirdPersonMesh->SetComponentTickEnabled(true);
	CachedThirdPersonMesh->bPauseAnims = false;

	if (Character)
	{
		if (UCharacterMovementComponent* Movement = Character->GetCharacterMovement())
		{
			Movement->GravityScale = 1.f;
			Movement->SetMovementMode(MOVE_Walking);
			Movement->MaxWalkSpeed = FMath::Max(Movement->MaxWalkSpeed, 300.f);
		}

		SCARMultiplayerPawnSetup::SnapPawnToGround(Pawn);
	}

	bEditorDesktopBodyConfigured = true;
}

void USCARLocalFirstPersonArmsComponent::TickComponent(
	const float DeltaTime,
	const ELevelTick TickType,
	FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	APawn* Pawn = Cast<APawn>(GetOwner());
	if (!Pawn || !Pawn->IsLocallyControlled())
	{
		return;
	}

	if (!bLocalViewConfigured)
	{
		TrySetup(Pawn);
	}

	if (!bLocalViewConfigured)
	{
		return;
	}

	if (IsARRunning())
	{
		if (!bSpringArmConfiguredForAR)
		{
			ConfigureSpringArmForAR();
		}

		if (!bCameraLookSwayDisabled)
		{
			DisableCameraLookSwayForAR(Pawn);
		}
	}

	EnsureFirstPersonMeshOnCamera(Pawn);
	LockFirstPersonMeshToCamera();

	if (!IsARRunning() && bEditorDesktopBodyConfigured && CachedThirdPersonMesh)
	{
		if (ACharacter* Character = Cast<ACharacter>(Pawn))
		{
			if (UCapsuleComponent* Capsule = Character->GetCapsuleComponent())
			{
				const float MeshZ = -Capsule->GetScaledCapsuleHalfHeight();
				CachedThirdPersonMesh->SetRelativeLocation(FVector(0.f, 0.f, MeshZ));
				CachedThirdPersonMesh->SetRelativeRotation(FRotator::ZeroRotator);
			}
		}
	}
}

UCameraComponent* USCARLocalFirstPersonArmsComponent::FindFirstPersonCamera(const APawn* Pawn) const
{
	if (!Pawn)
	{
		return nullptr;
	}

	TArray<UCameraComponent*> Cameras;
	Pawn->GetComponents<UCameraComponent>(Cameras);

	for (UCameraComponent* Camera : Cameras)
	{
		if (Camera && Camera->GetName() == FirstPersonCameraComponentName.ToString())
		{
			return Camera;
		}
	}

	for (UCameraComponent* Camera : Cameras)
	{
		if (Camera && Camera->GetName().Contains(TEXT("FirstPersonCamera")))
		{
			return Camera;
		}
	}

	return Cameras.Num() > 0 ? Cameras[0] : nullptr;
}

USpringArmComponent* USCARLocalFirstPersonArmsComponent::FindSpringArm(const APawn* Pawn) const
{
	if (!Pawn)
	{
		return nullptr;
	}

	TArray<USpringArmComponent*> SpringArms;
	Pawn->GetComponents<USpringArmComponent>(SpringArms);

	for (USpringArmComponent* SpringArm : SpringArms)
	{
		if (SpringArm && SpringArm->GetName() == SpringArmComponentName.ToString())
		{
			return SpringArm;
		}
	}

	return SpringArms.Num() > 0 ? SpringArms[0] : nullptr;
}

USkeletalMeshComponent* USCARLocalFirstPersonArmsComponent::FindMeshByExactName(
	const APawn* Pawn,
	const FName Name) const
{
	if (!Pawn)
	{
		return nullptr;
	}

	const FString TargetName = Name.ToString();
	TArray<USkeletalMeshComponent*> SkeletalMeshes;
	Pawn->GetComponents<USkeletalMeshComponent>(SkeletalMeshes);

	for (USkeletalMeshComponent* MeshComponent : SkeletalMeshes)
	{
		if (MeshComponent && MeshComponent->GetName() == TargetName)
		{
			return MeshComponent;
		}
	}

	return nullptr;
}
