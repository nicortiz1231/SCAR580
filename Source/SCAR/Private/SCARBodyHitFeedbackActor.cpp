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
		BloodEffect->SetVisibility(true);
		BloodEffect->SetAsset(BloodNiagaraSystem);
		BloodEffect->Activate(true);
	}
	else
	{
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(
			this,
			BloodNiagaraSystem,
			GetActorLocation(),
			GetActorRotation());
	}

	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(BloodDestroyTimerHandle);
		World->GetTimerManager().SetTimer(
			BloodDestroyTimerHandle,
			[this]()
			{
				if (BloodEffect)
				{
					BloodEffect->Deactivate();
					BloodEffect->SetVisibility(false);
				}
			},
			BloodLifetimeSeconds,
			false);
	}
}
