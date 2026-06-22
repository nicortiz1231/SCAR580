#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SCARBodyDetectionTypes.h"
#include "SCARBodyDetectionBlueprintLibrary.generated.h"

class USCARBodyDetectionSubsystem;
class USCARVisionBodyPoseProvider;

UCLASS()
class SCAR_API USCARBodyDetectionBlueprintLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category = "SCAR|Body Detection", meta = (WorldContext = "WorldContextObject"))
	static USCARBodyDetectionSubsystem* GetBodyDetectionSubsystem(const UObject* WorldContextObject);

	UFUNCTION(BlueprintPure, Category = "SCAR|Body Detection", meta = (WorldContext = "WorldContextObject"))
	static bool IsPersonInCameraPreview(const UObject* WorldContextObject);

	UFUNCTION(BlueprintPure, Category = "SCAR|Body Detection", meta = (WorldContext = "WorldContextObject"))
	static FSCARBodyDetectionSnapshot GetBodyDetectionSnapshot(const UObject* WorldContextObject);

	UFUNCTION(BlueprintPure, Category = "SCAR|Body Detection")
	static bool IsVisionBodyPoseSupported();
};
