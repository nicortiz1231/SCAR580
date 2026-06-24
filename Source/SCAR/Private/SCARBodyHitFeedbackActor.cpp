#include "SCARBodyHitFeedbackActor.h"

#include "NiagaraComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "TimerManager.h"

ASCARBodyHitFeedbackActor::ASCARBodyHitFeedbackActor()
{
	PrimaryActorTick.bCanEverTick = false;

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	BloodEffect = CreateDefaultSubobject<UNiagaraComponent>(TEXT("BloodEffect"));
	BloodEffect->SetupAttachment(Root);
	BloodEffect->SetAutoActivate(false);
	BloodEffect->SetVisibility(false);

	static ConstructorHelpers::FObjectFinder<UNiagaraSystem> BloodFinder(
		TEXT("/Game/BodycamFPSKIT/ParticleEffects/NS_Smoke_Blood_System.NS_Smoke_Blood_System"));
	if (BloodFinder.Succeeded())
	{
		BloodNiagaraSystem = BloodFinder.Object;
	}
}

void ASCARBodyHitFeedbackActor::BeginPlay()
{
	Super::BeginPlay();
}

void ASCARBodyHitFeedbackActor::ActivateAtLocation(const FVector& WorldLocation)
{
	SetActorLocation(WorldLocation);
	SpawnBloodEffect();
}

void ASCARBodyHitFeedbackActor::SpawnBloodEffect()
{
	if (!BloodNiagaraSystem)
	{
		return;
	}

	if (BloodEffect)
	{
		if (BloodEffect->GetAsset() != BloodNiagaraSystem)
		{
			BloodEffect->SetAsset(BloodNiagaraSystem);
		}

		BloodEffect->DeactivateImmediate();
		BloodEffect->ResetSystem();
		BloodEffect->SetVisibility(true);
		BloodEffect->Activate(true);
		return;
	}

	UNiagaraComponent* SpawnedEffect = UNiagaraFunctionLibrary::SpawnSystemAtLocation(
		this,
		BloodNiagaraSystem,
		GetActorLocation(),
		GetActorRotation(),
		FVector::OneVector,
		true,
		true,
		ENCPoolMethod::AutoRelease);
	if (!SpawnedEffect)
	{
		return;
	}

	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(BloodDestroyTimerHandle);
		World->GetTimerManager().SetTimer(
			BloodDestroyTimerHandle,
			[SpawnedEffect]()
			{
				if (IsValid(SpawnedEffect))
				{
					SpawnedEffect->DeactivateImmediate();
				}
			},
			BloodLifetimeSeconds,
			false);
	}
}
