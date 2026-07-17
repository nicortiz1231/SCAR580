#include "SCARMultiplayerPresentationComponent.h"

#include "Animation/AnimInstance.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "DrawDebugHelpers.h"
#include "Engine/Engine.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Controller.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "SCARARMultiplayerPlayerController.h"
#include "SCARARPoseSyncComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "UObject/UnrealType.h"

namespace SCARMultiplayerPresentation
{
	static const TCHAR* MannequinMeshPath =
		TEXT("/Game/BodycamFPSKIT/Demo/Character/Mannequins/Meshes/SKM_Manny.SKM_Manny");

	static const TCHAR* FpArmsMeshPath =
		TEXT("/Game/BodycamFPSKIT/Blueprints/Camera/SKM_Camera.SKM_Camera");

	static const TCHAR* MirrorAnimClassPath =
		TEXT("/Game/BodycamFPSKIT/Demo/Character/Mannequins/Animations/ABP_Mirror.ABP_Mirror_C");

	static const TCHAR* PoseDriverAnimClassPath =
		TEXT("/Game/BodycamFPSKIT/Character/ABP_FP_ArmsProcedural.ABP_FP_ArmsProcedural_C");

	static const TCHAR* PistolMeshPath =
		TEXT("/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Weapon/SKM_Pistol.SKM_Pistol");
}

USCARMultiplayerPresentationComponent::USCARMultiplayerPresentationComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickGroup = TG_PostUpdateWork;
	OpponentMannequinMesh = TSoftObjectPtr<USkeletalMesh>(FSoftObjectPath(SCARMultiplayerPresentation::MannequinMeshPath));
	OpponentFpArmsMesh = TSoftObjectPtr<USkeletalMesh>(FSoftObjectPath(SCARMultiplayerPresentation::FpArmsMeshPath));
	OpponentFallbackPistolMesh = TSoftObjectPtr<USkeletalMesh>(FSoftObjectPath(SCARMultiplayerPresentation::PistolMeshPath));

	static ConstructorHelpers::FObjectFinder<USkeletalMesh> MannequinMeshFinder(SCARMultiplayerPresentation::MannequinMeshPath);
	if (MannequinMeshFinder.Succeeded())
	{
		CachedMannequinMesh = MannequinMeshFinder.Object;
	}

	static ConstructorHelpers::FObjectFinder<USkeletalMesh> FpArmsMeshFinder(SCARMultiplayerPresentation::FpArmsMeshPath);
	if (FpArmsMeshFinder.Succeeded())
	{
		CachedFpArmsMesh = FpArmsMeshFinder.Object;
	}
}

bool USCARMultiplayerPresentationComponent::IsUsingViewPlacementForLocalViewer() const
{
	return bPlaceOpponentInView && ShouldShowOpponentForLocalViewer(Cast<APawn>(GetOwner()));
}

void USCARMultiplayerPresentationComponent::BeginPlay()
{
	Super::BeginPlay();

	if (AActor* OwnerActor = GetOwner())
	{
		ConfigureNetworkVisibility(OwnerActor);
	}

	if (APawn* Pawn = Cast<APawn>(GetOwner()))
	{
		Pawn->ReceiveControllerChangedDelegate.AddDynamic(
			this,
			&USCARMultiplayerPresentationComponent::OnPawnControllerChanged);
	}

	RefreshPresentation();
	SetComponentTickEnabled(true);
}

void USCARMultiplayerPresentationComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (APawn* Pawn = Cast<APawn>(GetOwner()))
	{
		Pawn->ReceiveControllerChangedDelegate.RemoveDynamic(
			this,
			&USCARMultiplayerPresentationComponent::OnPawnControllerChanged);
	}

	Super::EndPlay(EndPlayReason);
}

void USCARMultiplayerPresentationComponent::ConfigureNetworkVisibility(AActor* OwnerActor) const
{
	if (!OwnerActor || !OwnerActor->HasAuthority())
	{
		return;
	}

	OwnerActor->bOnlyRelevantToOwner = false;
	OwnerActor->bAlwaysRelevant = true;
	OwnerActor->SetNetDormancy(DORM_Never);
}

void USCARMultiplayerPresentationComponent::OnPawnControllerChanged(
	APawn* Pawn,
	AController* OldController,
	AController* NewController)
{
	if (Pawn == GetOwner())
	{
		RefreshPresentation();
	}
}

void USCARMultiplayerPresentationComponent::TickComponent(
	const float DeltaTime,
	const ELevelTick TickType,
	FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	const bool bMultiplayer = ASCARARMultiplayerPlayerController::IsMultiplayerSession(GetWorld());
	if (!bMultiplayer && !bCachedIsOpponentView)
	{
		return;
	}

	OpponentRefreshAccumulator += DeltaTime;
	const bool bPoseDriverReady = OpponentPoseDriverMeshComponent && OpponentPoseDriverMeshComponent->GetSkeletalMeshAsset();
	const float RefreshInterval = bPoseDriverReady ? 0.1f : 0.05f;
	if (!bCachedIsOpponentView || OpponentRefreshAccumulator >= RefreshInterval)
	{
		OpponentRefreshAccumulator = 0.f;
		RefreshPresentation();
	}

	if (bCachedIsOpponentView)
	{
		UpdateOpponentViewPlacement();
	}
}

bool USCARMultiplayerPresentationComponent::ShouldShowOpponentForLocalViewer(const APawn* Pawn) const
{
	if (!Pawn || !Pawn->IsPlayerControlled() || !GetWorld())
	{
		return false;
	}

	const APlayerController* LocalPC = GetWorld()->GetFirstPlayerController();
	if (!LocalPC || !LocalPC->IsLocalController())
	{
		return false;
	}

	const APawn* LocalPawn = LocalPC->GetPawn();
	if (!LocalPawn || Pawn == LocalPawn)
	{
		return false;
	}

	return true;
}

USkeletalMeshComponent* USCARMultiplayerPresentationComponent::FindMeshByExactName(
	APawn* Pawn,
	const FName ComponentName) const
{
	if (!Pawn)
	{
		return nullptr;
	}

	const FString TargetName = ComponentName.ToString();
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

USkeletalMeshComponent* USCARMultiplayerPresentationComponent::EnsurePoseDriverMesh(APawn* Pawn)
{
	if (!Pawn)
	{
		return nullptr;
	}

	if (USkeletalMeshComponent* ExistingMesh = FindMeshByExactName(Pawn, FirstPersonMeshComponentName))
	{
		return ExistingMesh;
	}

	if (OpponentPoseDriverMeshComponent && IsValid(OpponentPoseDriverMeshComponent))
	{
		return OpponentPoseDriverMeshComponent;
	}

	USceneComponent* Root = Pawn->GetRootComponent();
	if (!Root)
	{
		return nullptr;
	}

	USkeletalMeshComponent* PoseDriverMesh = NewObject<USkeletalMeshComponent>(
		Pawn,
		FirstPersonMeshComponentName);
	if (!PoseDriverMesh)
	{
		return nullptr;
	}

	Pawn->AddInstanceComponent(PoseDriverMesh);
	PoseDriverMesh->SetupAttachment(Root);
	PoseDriverMesh->RegisterComponent();
	OpponentPoseDriverMeshComponent = PoseDriverMesh;
	bMirrorAnimInitialized = false;
	return PoseDriverMesh;
}

void USCARMultiplayerPresentationComponent::EnsurePawnEquippedGunSetForOpponentView(APawn* Pawn) const
{
	if (!Pawn)
	{
		return;
	}

	FProperty* EquippedGunSetProperty = Pawn->GetClass()->FindPropertyByName(TEXT("EquippedGunSet"));
	if (!EquippedGunSetProperty)
	{
		return;
	}

	if (const FEnumProperty* EnumProperty = CastField<FEnumProperty>(EquippedGunSetProperty))
	{
		if (const UEnum* Enum = EnumProperty->GetEnum())
		{
			int64 PistolValue = Enum->GetValueByNameString(TEXT("Pistol"));
			if (PistolValue == INDEX_NONE)
			{
				PistolValue = Enum->GetValueByNameString(TEXT("ENUM_Animset::Pistol"));
			}
			if (PistolValue == INDEX_NONE)
			{
				PistolValue = 1;
			}

			EnumProperty->GetUnderlyingProperty()->SetIntPropertyValue(
				EquippedGunSetProperty->ContainerPtrToValuePtr<void>(Pawn),
				PistolValue);
		}
	}
	else if (FByteProperty* ByteProperty = CastField<FByteProperty>(EquippedGunSetProperty))
	{
		ByteProperty->SetPropertyValue_InContainer(Pawn, static_cast<uint8>(1));
	}
}

void USCARMultiplayerPresentationComponent::RefreshPresentation()
{
	APawn* Pawn = Cast<APawn>(GetOwner());
	if (!Pawn)
	{
		return;
	}

	const bool bShowOpponent = ShouldShowOpponentForLocalViewer(Pawn);
	bCachedIsOpponentView = bShowOpponent;

	if (!bShowOpponent)
	{
		OpponentMannequinMeshComponent = nullptr;
		OpponentPoseDriverMeshComponent = nullptr;
		ReusedPistolItemMesh = nullptr;
		bMirrorAnimInitialized = false;

		if (OpponentWeaponMeshComponent)
		{
			OpponentWeaponMeshComponent->SetHiddenInGame(true);
		}

		return;
	}

	Pawn->SetActorHiddenInGame(false);
	EnsurePawnEquippedGunSetForOpponentView(Pawn);
	HideCameraAndLightComponents(Pawn);

	OpponentPoseDriverMeshComponent = EnsurePoseDriverMesh(Pawn);
	OpponentMannequinMeshComponent = FindMeshByExactName(Pawn, ThirdPersonMeshComponentName);

	// FP arms must be configured first — ABP_Mirror reads this pose for the visible mannequin.
	if (OpponentPoseDriverMeshComponent)
	{
		ConfigureFpPoseDriver(Pawn, OpponentPoseDriverMeshComponent);
	}

	if (OpponentMannequinMeshComponent)
	{
		ConfigureMirroredMannequin(OpponentMannequinMeshComponent);
		ReinitializeMirrorAnimIfNeeded(OpponentMannequinMeshComponent);
		EnsureOpponentWeaponOnMannequin(Pawn, OpponentMannequinMeshComponent);
	}

	if (UCapsuleComponent* Capsule = Pawn->FindComponentByClass<UCapsuleComponent>())
	{
		Capsule->SetHiddenInGame(true);
		Capsule->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
		Capsule->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
	}

	ShowOpponentDebug(Pawn);
}

TSubclassOf<UAnimInstance> USCARMultiplayerPresentationComponent::ResolveOpponentMirrorAnimClass() const
{
	if (OpponentMirrorAnimClass)
	{
		return OpponentMirrorAnimClass;
	}

	return TSoftClassPtr<UAnimInstance>(
		FSoftObjectPath(SCARMultiplayerPresentation::MirrorAnimClassPath)).Get();
}

TSubclassOf<UAnimInstance> USCARMultiplayerPresentationComponent::ResolveOpponentPoseDriverAnimClass() const
{
	if (OpponentPoseDriverAnimClass)
	{
		return OpponentPoseDriverAnimClass;
	}

	return TSoftClassPtr<UAnimInstance>(
		FSoftObjectPath(SCARMultiplayerPresentation::PoseDriverAnimClassPath)).Get();
}

void USCARMultiplayerPresentationComponent::ReparentPoseDriverToPawnRoot(
	APawn* Pawn,
	USkeletalMeshComponent* PoseDriverMesh) const
{
	if (!Pawn || !PoseDriverMesh)
	{
		return;
	}

	USceneComponent* Root = Pawn->GetRootComponent();
	if (!Root)
	{
		return;
	}

	if (PoseDriverMesh->GetAttachParent() != Root)
	{
		PoseDriverMesh->DetachFromComponent(FDetachmentTransformRules::KeepWorldTransform);
		PoseDriverMesh->AttachToComponent(Root, FAttachmentTransformRules::SnapToTargetIncludingScale);
	}

	PoseDriverMesh->SetRelativeLocation(PoseDriverRelativeLocation);
	PoseDriverMesh->SetRelativeRotation(PoseDriverRelativeRotation);
}

void USCARMultiplayerPresentationComponent::ConfigureFpPoseDriver(
	APawn* Pawn,
	USkeletalMeshComponent* PoseDriverMesh)
{
	if (!Pawn || !PoseDriverMesh)
	{
		return;
	}

	if (USkeletalMesh* MeshAsset = ResolveOpponentFpArmsMesh())
	{
		if (PoseDriverMesh->GetSkeletalMeshAsset() != MeshAsset)
		{
			PoseDriverMesh->SetSkeletalMesh(MeshAsset);
		}
	}

	if (TSubclassOf<UAnimInstance> AnimClass = ResolveOpponentPoseDriverAnimClass())
	{
		if (PoseDriverMesh->GetAnimClass() != AnimClass)
		{
			PoseDriverMesh->SetAnimInstanceClass(AnimClass);
		}
	}

	ReparentPoseDriverToPawnRoot(Pawn, PoseDriverMesh);

	PoseDriverMesh->SetComponentTickEnabled(true);
	PoseDriverMesh->bPauseAnims = false;
	PoseDriverMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	SetComponentHidden(PoseDriverMesh, true);
	PoseDriverMesh->MarkRenderStateDirty();
}

void USCARMultiplayerPresentationComponent::ConfigureMirroredMannequin(USkeletalMeshComponent* MannequinMesh)
{
	if (!MannequinMesh)
	{
		return;
	}

	if (USkeletalMesh* MeshAsset = ResolveOpponentMannequinMesh())
	{
		if (MannequinMesh->GetSkeletalMeshAsset() != MeshAsset)
		{
			MannequinMesh->SetSkeletalMesh(MeshAsset);
		}
	}

	if (TSubclassOf<UAnimInstance> MirrorClass = ResolveOpponentMirrorAnimClass())
	{
		if (MannequinMesh->GetAnimClass() != MirrorClass)
		{
			MannequinMesh->SetAnimInstanceClass(MirrorClass);
		}
	}

	MannequinMesh->SetComponentTickEnabled(true);
	MannequinMesh->bPauseAnims = false;
	MannequinMesh->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	MannequinMesh->SetCollisionResponseToAllChannels(ECR_Block);
	MannequinMesh->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
	MannequinMesh->SetGenerateOverlapEvents(false);
	MannequinMesh->SetCastShadow(true);
	SetComponentWorldVisible(MannequinMesh);
	MannequinMesh->MarkRenderStateDirty();
}

void USCARMultiplayerPresentationComponent::ReinitializeMirrorAnimIfNeeded(USkeletalMeshComponent* MannequinMesh)
{
	if (!MannequinMesh || bMirrorAnimInitialized)
	{
		return;
	}

	if (!OpponentPoseDriverMeshComponent ||
		!OpponentPoseDriverMeshComponent->GetSkeletalMeshAsset() ||
		!OpponentPoseDriverMeshComponent->GetAnimInstance())
	{
		return;
	}

	if (!ResolveOpponentMirrorAnimClass())
	{
		return;
	}

	MannequinMesh->InitAnim(true);
	bMirrorAnimInitialized = true;
}

void USCARMultiplayerPresentationComponent::UpdateOpponentViewPlacement()
{
	if (!bPlaceOpponentInView)
	{
		return;
	}

	APawn* Pawn = Cast<APawn>(GetOwner());
	if (!Pawn)
	{
		return;
	}

	const UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	const APlayerController* LocalPC = World->GetFirstPlayerController();
	if (!LocalPC || !LocalPC->IsLocalController())
	{
		return;
	}

	FVector ViewLocation;
	FRotator ViewRotation;
	LocalPC->GetPlayerViewPoint(ViewLocation, ViewRotation);

	const FVector FinalLocation = ComputeOpponentViewLocation(Pawn, ViewLocation, ViewRotation);

	FRotator TargetRotation(0.f, ViewRotation.Yaw + 180.f, 0.f);
	if (const USCARARPoseSyncComponent* PoseSync = Pawn->FindComponentByClass<USCARARPoseSyncComponent>())
	{
		if (PoseSync->HasValidARPose())
		{
			// Sanitized multiplayer body rotation (yaw/pitch, no roll) from the
			// opponent's replicated AR pose so awkward phone angles do not flip
			// the visible mannequin upside down.
			TargetRotation = PoseSync->GetCurrentARPose().Rotator();
		}
	}

	Pawn->SetActorLocationAndRotation(FinalLocation, TargetRotation, false, nullptr, ETeleportType::TeleportPhysics);

	if (ACharacter* Character = Cast<ACharacter>(Pawn))
	{
		if (UCharacterMovementComponent* Movement = Character->GetCharacterMovement())
		{
			Movement->StopMovementImmediately();
			Movement->Velocity = FVector::ZeroVector;
			Movement->SetMovementMode(MOVE_Walking);
		}
	}
}

FVector USCARMultiplayerPresentationComponent::ComputeOpponentViewLocation(
	const APawn* Pawn,
	const FVector& ViewLocation,
	const FRotator& ViewRotation) const
{
	float CapsuleHalfHeight = 88.f;
	if (Pawn)
	{
		if (const UCapsuleComponent* Capsule = Pawn->FindComponentByClass<UCapsuleComponent>())
		{
			CapsuleHalfHeight = Capsule->GetScaledCapsuleHalfHeight();
		}
	}

	const UWorld* World = GetWorld();
	const APlayerController* LocalPC = World ? World->GetFirstPlayerController() : nullptr;
	const APawn* LocalPawn = LocalPC ? LocalPC->GetPawn() : nullptr;

	const float StandingEyeHeightCm = 160.f;
	float FloorZ = ViewLocation.Z - StandingEyeHeightCm;

	if (LocalPawn)
	{
		float LocalCapsuleHalfHeight = 88.f;
		if (const UCapsuleComponent* LocalCapsule = LocalPawn->FindComponentByClass<UCapsuleComponent>())
		{
			LocalCapsuleHalfHeight = LocalCapsule->GetScaledCapsuleHalfHeight();
		}

		const float PawnFeetZ = LocalPawn->GetActorLocation().Z - LocalCapsuleHalfHeight;
		if (const ACharacter* LocalCharacter = Cast<ACharacter>(LocalPawn))
		{
			if (const UCharacterMovementComponent* Movement = LocalCharacter->GetCharacterMovement())
			{
				if (Movement->IsMovingOnGround())
				{
					FloorZ = PawnFeetZ;
				}
			}
		}
	}

	FVector HorizontalTarget = ViewLocation + ViewRotation.Vector() * OpponentViewDistanceCm;
	HorizontalTarget.Z = ViewLocation.Z;

	if (World)
	{
		const FVector TraceStart = HorizontalTarget + FVector(0.f, 0.f, 200.f);
		const FVector TraceEnd = HorizontalTarget - FVector(0.f, 0.f, 5000.f);
		FCollisionQueryParams Params(SCENE_QUERY_STAT(SCAROpponentFloor), false, Pawn);
		if (LocalPawn)
		{
			Params.AddIgnoredActor(LocalPawn);
		}
		FHitResult Hit;
		if (World->LineTraceSingleByChannel(Hit, TraceStart, TraceEnd, ECC_Visibility, Params))
		{
			FloorZ = Hit.ImpactPoint.Z;
		}
	}

	return FVector(HorizontalTarget.X, HorizontalTarget.Y, FloorZ + CapsuleHalfHeight);
}

void USCARMultiplayerPresentationComponent::ShowOpponentDebug(const APawn* Pawn) const
{
	if (!bShowOpponentDebug || !Pawn || !Pawn->GetWorld())
	{
		return;
	}

	const APlayerController* LocalPC = Pawn->GetWorld()->GetFirstPlayerController();
	if (!LocalPC || !LocalPC->IsLocalController())
	{
		return;
	}

	const USkeletalMeshComponent* VisualMesh = OpponentMannequinMeshComponent;
	const FVector Location = VisualMesh ? VisualMesh->GetComponentLocation() : Pawn->GetActorLocation();

	DrawDebugCapsule(
		Pawn->GetWorld(),
		Location,
		88.f,
		34.f,
		Pawn->GetActorQuat(),
		FColor::Green,
		false,
		0.1f,
		0,
		2.f);
}

void USCARMultiplayerPresentationComponent::HideCameraAndLightComponents(APawn* Pawn) const
{
	if (!Pawn)
	{
		return;
	}

	const FString FpMeshName = FirstPersonMeshComponentName.ToString();
	const FString TpMeshName = ThirdPersonMeshComponentName.ToString();

	TInlineComponentArray<UPrimitiveComponent*> PrimitiveComponents(Pawn);
	for (UPrimitiveComponent* Component : PrimitiveComponents)
	{
		if (!Component ||
			Component == OpponentMannequinMeshComponent ||
			Component == OpponentPoseDriverMeshComponent ||
			Component == OpponentWeaponMeshComponent ||
			Component == ReusedPistolItemMesh)
		{
			continue;
		}

		const FString Name = Component->GetName();
		if (Name == FpMeshName || Name == TpMeshName)
		{
			continue;
		}

		if (Name.Contains(TEXT("CameraFPS")) ||
			Name.Contains(TEXT("BodycamCamera")) ||
			Name.Contains(TEXT("WeaponLight")) ||
			Name.Contains(TEXT("FillLight")) ||
			Name.Contains(TEXT("AR_")))
		{
			SetComponentHidden(Component, true);
		}
	}
}

USkeletalMeshComponent* USCARMultiplayerPresentationComponent::FindExistingPistolItemMesh(APawn* Pawn) const
{
	if (!Pawn)
	{
		return nullptr;
	}

	TArray<USkeletalMeshComponent*> PawnMeshes;
	Pawn->GetComponents<USkeletalMeshComponent>(PawnMeshes, true);
	for (USkeletalMeshComponent* MeshComponent : PawnMeshes)
	{
		if (MeshComponent && MeshComponent->GetName() == TEXT("Item_Mesh"))
		{
			return MeshComponent;
		}
	}

	TArray<AActor*> AttachedActors;
	Pawn->GetAttachedActors(AttachedActors, true, true);
	for (AActor* AttachedActor : AttachedActors)
	{
		if (!AttachedActor)
		{
			continue;
		}

		TArray<USkeletalMeshComponent*> AttachedMeshes;
		AttachedActor->GetComponents<USkeletalMeshComponent>(AttachedMeshes, true);
		for (USkeletalMeshComponent* MeshComponent : AttachedMeshes)
		{
			if (MeshComponent && MeshComponent->GetName() == TEXT("Item_Mesh"))
			{
				return MeshComponent;
			}
		}
	}

	return nullptr;
}

FName USCARMultiplayerPresentationComponent::ResolveWeaponAttachSocket(
	const USkeletalMeshComponent* AttachMesh) const
{
	if (!AttachMesh)
	{
		return OpponentWeaponAttachSocketName;
	}

	const TArray<FName> SocketCandidates = {
		TEXT("ik_hand_gun"),
		TEXT("ik_hand_r"),
		OpponentWeaponAttachSocketName,
	};

	for (const FName SocketName : SocketCandidates)
	{
		if (AttachMesh->DoesSocketExist(SocketName))
		{
			return SocketName;
		}
	}

	return OpponentWeaponAttachSocketName;
}

void USCARMultiplayerPresentationComponent::EnsureOpponentWeaponOnMannequin(
	APawn* Pawn,
	USkeletalMeshComponent* MannequinMesh)
{
	if (!MannequinMesh || !Pawn)
	{
		return;
	}

	const FName SocketName = ResolveWeaponAttachSocket(MannequinMesh);

	if (USkeletalMeshComponent* ExistingItemMesh = FindExistingPistolItemMesh(Pawn))
	{
		ReusedPistolItemMesh = ExistingItemMesh;

		if (OpponentWeaponMeshComponent)
		{
			OpponentWeaponMeshComponent->SetHiddenInGame(true);
		}

		if (ExistingItemMesh->GetAttachParent() != MannequinMesh ||
			ExistingItemMesh->GetAttachSocketName() != SocketName)
		{
			ExistingItemMesh->AttachToComponent(
				MannequinMesh,
				FAttachmentTransformRules::SnapToTargetIncludingScale,
				SocketName);
		}

		SetComponentWorldVisible(ExistingItemMesh);
		ExistingItemMesh->MarkRenderStateDirty();
		return;
	}

	USkeletalMesh* PistolMesh = ResolveOpponentFallbackPistolMesh();
	if (!PistolMesh)
	{
		return;
	}

	if (!OpponentWeaponMeshComponent)
	{
		OpponentWeaponMeshComponent = NewObject<USkeletalMeshComponent>(Pawn, OpponentWeaponComponentName);
		if (!OpponentWeaponMeshComponent)
		{
			return;
		}

		Pawn->AddInstanceComponent(OpponentWeaponMeshComponent);
		OpponentWeaponMeshComponent->SetupAttachment(MannequinMesh, SocketName);
		OpponentWeaponMeshComponent->RegisterComponent();
	}

	if (OpponentWeaponMeshComponent->GetAttachParent() != MannequinMesh ||
		OpponentWeaponMeshComponent->GetAttachSocketName() != SocketName)
	{
		OpponentWeaponMeshComponent->AttachToComponent(
			MannequinMesh,
			FAttachmentTransformRules::SnapToTargetIncludingScale,
			SocketName);
	}

	OpponentWeaponMeshComponent->SetSkeletalMesh(PistolMesh);
	SetComponentWorldVisible(OpponentWeaponMeshComponent);
	OpponentWeaponMeshComponent->MarkRenderStateDirty();
}

USkeletalMesh* USCARMultiplayerPresentationComponent::ResolveOpponentMannequinMesh()
{
	if (CachedMannequinMesh)
	{
		return CachedMannequinMesh;
	}

	if (USkeletalMesh* MeshAsset = OpponentMannequinMesh.LoadSynchronous())
	{
		CachedMannequinMesh = MeshAsset;
		return MeshAsset;
	}

	if (USkeletalMesh* MeshAsset = LoadObject<USkeletalMesh>(nullptr, SCARMultiplayerPresentation::MannequinMeshPath))
	{
		CachedMannequinMesh = MeshAsset;
		return MeshAsset;
	}

	return nullptr;
}

USkeletalMesh* USCARMultiplayerPresentationComponent::ResolveOpponentFpArmsMesh()
{
	if (CachedFpArmsMesh)
	{
		return CachedFpArmsMesh;
	}

	if (USkeletalMesh* MeshAsset = OpponentFpArmsMesh.LoadSynchronous())
	{
		CachedFpArmsMesh = MeshAsset;
		return MeshAsset;
	}

	if (USkeletalMesh* MeshAsset = LoadObject<USkeletalMesh>(nullptr, SCARMultiplayerPresentation::FpArmsMeshPath))
	{
		CachedFpArmsMesh = MeshAsset;
		return MeshAsset;
	}

	return nullptr;
}

USkeletalMesh* USCARMultiplayerPresentationComponent::ResolveOpponentFallbackPistolMesh()
{
	if (CachedFallbackPistolMesh)
	{
		return CachedFallbackPistolMesh;
	}

	if (USkeletalMesh* MeshAsset = OpponentFallbackPistolMesh.LoadSynchronous())
	{
		CachedFallbackPistolMesh = MeshAsset;
		return MeshAsset;
	}

	if (USkeletalMesh* MeshAsset = LoadObject<USkeletalMesh>(nullptr, SCARMultiplayerPresentation::PistolMeshPath))
	{
		CachedFallbackPistolMesh = MeshAsset;
		return MeshAsset;
	}

	return nullptr;
}

void USCARMultiplayerPresentationComponent::SetComponentWorldVisible(UPrimitiveComponent* Component) const
{
	if (!Component)
	{
		return;
	}

	Component->SetHiddenInGame(false);
	Component->SetVisibility(true, true);
	Component->SetOwnerNoSee(false);
	Component->SetOnlyOwnerSee(false);
	Component->SetCastHiddenShadow(false);
	Component->SetFirstPersonPrimitiveType(EFirstPersonPrimitiveType::WorldSpaceRepresentation);
}

void USCARMultiplayerPresentationComponent::SetComponentHidden(
	UPrimitiveComponent* Component,
	const bool bHidden) const
{
	if (!Component)
	{
		return;
	}

	Component->SetHiddenInGame(bHidden);
	Component->SetVisibility(!bHidden, true);
	Component->SetOwnerNoSee(bHidden);
	if (bHidden)
	{
		Component->SetOnlyOwnerSee(false);
	}
}
