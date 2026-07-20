#include "SCARSharedARGround.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Net/UnrealNetwork.h"
#include "ProceduralMeshComponent.h"

ASCARSharedARGround::ASCARSharedARGround()
{
	PrimaryActorTick.bCanEverTick = false;
	bReplicates = true;

	FloorMesh = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("FloorMesh"));
	SetRootComponent(FloorMesh);
	FloorMesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	FloorMesh->SetCollisionObjectType(ECC_WorldStatic);
	FloorMesh->SetCollisionResponseToAllChannels(ECR_Block);
	FloorMesh->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
	FloorMesh->SetCastShadow(true);
	FloorMesh->SetHiddenInGame(false);
}

void ASCARSharedARGround::BeginPlay()
{
	Super::BeginPlay();
	BuildFloorMesh();
}

void ASCARSharedARGround::BuildFloorMesh()
{
	if (!FloorMesh)
	{
		return;
	}

	const float H = HalfExtentCm;
	const float Thickness = 20.f;

	TArray<FVector> Vertices;
	TArray<int32> Triangles;
	TArray<FVector> Normals;
	TArray<FVector2D> UVs;
	TArray<FColor> Colors;
	TArray<FProcMeshTangent> Tangents;

	// Top surface quad (visible green floor)
	Vertices.Add(FVector(-H, -H, Thickness));
	Vertices.Add(FVector(H, -H, Thickness));
	Vertices.Add(FVector(H, H, Thickness));
	Vertices.Add(FVector(-H, H, Thickness));

	Triangles.Append({0, 2, 1, 0, 3, 2});

	for (int32 i = 0; i < 4; ++i)
	{
		Normals.Add(FVector::UpVector);
		UVs.Add(FVector2D(0.f, 0.f));
		Colors.Add(FColor::Green);
		Tangents.Add(FProcMeshTangent(1.f, 0.f, 0.f));
	}

	FloorMesh->CreateMeshSection(
		0,
		Vertices,
		Triangles,
		Normals,
		UVs,
		Colors,
		Tangents,
		true);

	UMaterialInterface* BaseMat = LoadObject<UMaterialInterface>(
		nullptr,
		TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	if (BaseMat)
	{
		if (UMaterialInstanceDynamic* DynMat = UMaterialInstanceDynamic::Create(BaseMat, this))
		{
			DynMat->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.05f, 0.85f, 0.2f, 1.f));
			FloorMesh->SetMaterial(0, DynMat);
		}
	}

	FloorMesh->SetLightingChannels(true, true, true);
	FloorMesh->SetCastShadow(false);
	FloorMesh->SetReceivesDecals(false);
}

void ASCARSharedARGround::PlaceAt(const FVector& OriginXY, const float SurfaceWorldZ)
{
	GroundSurfaceZ = SurfaceWorldZ;
	const float Thickness = 20.f;
	SetActorLocation(FVector(OriginXY.X, OriginXY.Y, SurfaceWorldZ - Thickness));
}

void ASCARSharedARGround::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(ASCARSharedARGround, GroundSurfaceZ);
}

ASCARSharedARGround* ASCARSharedARGround::FindInWorld(const UWorld* World)
{
	if (!World)
	{
		return nullptr;
	}

	TActorIterator<ASCARSharedARGround> It(World);
	return It ? *It : nullptr;
}
