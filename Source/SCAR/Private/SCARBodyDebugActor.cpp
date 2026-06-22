#include "SCARBodyDebugActor.h"

#include "Components/SceneComponent.h"
#include "SCARBodyDebugDrawComponent.h"

ASCARBodyDebugActor::ASCARBodyDebugActor()
{
	PrimaryActorTick.bCanEverTick = false;

	USceneComponent* SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(SceneRoot);

	DebugDrawComponent = CreateDefaultSubobject<USCARBodyDebugDrawComponent>(TEXT("BodyDebugDraw"));
}
