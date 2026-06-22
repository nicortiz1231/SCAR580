#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SCARBodyDebugDrawComponent.generated.h"

class UCanvas;
class APlayerController;

UENUM(BlueprintType)
enum class ESCARBodyDebugSourceMode : uint8
{
	Auto UMETA(ToolTip = "Prefer ARKit Pose2D screen overlay, then 3D projected to screen, then Vision."),
	ARKit3D UMETA(ToolTip = "Draw only ARKit 3D body skeleton."),
	Pose2D UMETA(ToolTip = "Draw only ARKit Pose2D skeleton."),
	Vision UMETA(ToolTip = "Draw only Apple Vision skeleton."),
	All UMETA(ToolTip = "Draw all available skeleton sources.")
};

USTRUCT()
struct FSCARBodyDebugScreenJoint
{
	GENERATED_BODY()

	UPROPERTY()
	FVector2D GuiPosition = FVector2D::ZeroVector;

	UPROPERTY()
	bool bIsValid = false;
};

UCLASS(ClassGroup = (SCAR), meta = (BlueprintSpawnableComponent))
class SCAR_API USCARBodyDebugDrawComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	USCARBodyDebugDrawComponent();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection|Debug")
	ESCARBodyDebugSourceMode SourceMode = ESCARBodyDebugSourceMode::Auto;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection|Debug")
	bool bDraw3DSkeleton = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection|Debug")
	bool bDrawPose2D = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection|Debug")
	bool bDrawVisionSkeleton = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection|Debug")
	bool bFlipPose2DY = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection|Debug")
	bool bUseImageSpacePose2DMapping = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection|Debug")
	bool bDrawJointMarkers = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection|Debug")
	float ScreenJointPixelSize = 18.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection|Debug")
	FLinearColor JointMarkerColor = FLinearColor(1.f, 0.95f, 0.2f, 0.95f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection|Debug")
	bool bFlipVisionY = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection|Debug")
	float ScreenOverlayDistance = 150.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection|Debug")
	float LineThickness = 3.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection|Debug")
	float JointPointSize = 6.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection|Debug")
	FLinearColor SkeletonColor3D = FLinearColor::Green;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection|Debug")
	FLinearColor SkeletonColorPose2D = FLinearColor(0.2f, 1.f, 0.35f, 0.85f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SCAR|Body Detection|Debug")
	FLinearColor SkeletonColorVision = FLinearColor(0.1f, 0.9f, 1.f);

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	FDelegateHandle DebugDrawDelegateHandle;

	UPROPERTY(Transient)
	TArray<FSCARBodyDebugScreenJoint> CachedScreenJoints;

	UPROPERTY(Transient)
	TArray<FIntPoint> CachedBonePairs;

	UPROPERTY(Transient)
	FLinearColor CachedBoneColor = FLinearColor::Green;

	UPROPERTY(Transient)
	FLinearColor CachedJointColor = FLinearColor::Yellow;

	UPROPERTY(Transient)
	bool bHasScreenOverlay = false;

	void OnDebugDraw(UCanvas* Canvas, APlayerController* PlayerController);
	void UpdateScreenOverlayCache(const class USCARBodyDetectionSubsystem* Subsystem);
	void CachePose2DScreenOverlay(const class USCARBodyDetectionSubsystem* Subsystem);
	void CacheVisionScreenOverlay(const class USCARBodyDetectionSubsystem* Subsystem);
	void CachePose3DProjectedScreenOverlay(const class USCARBodyDetectionSubsystem* Subsystem);
	void DrawScreenOverlay(UCanvas* Canvas) const;
	void DrawGuiLine(UCanvas* Canvas, const FVector2D& Start, const FVector2D& End, float Thickness, const FLinearColor& Color) const;
	void DrawGuiJoint(UCanvas* Canvas, const FVector2D& Center, float Size, const FLinearColor& Color) const;

	void DrawPose3D(const class USCARBodyDetectionSubsystem* Subsystem) const;
	int32 FindPrimaryVisionTargetIndex(const TArray<struct FSCARScreenSpaceBodyTarget>& Targets) const;
	bool VisionJointToGuiPixels(const struct FSCARVisionBodyJoint& Joint, int32 ScreenWidth, int32 ScreenHeight, FVector2D& OutGuiPixels) const;
};
