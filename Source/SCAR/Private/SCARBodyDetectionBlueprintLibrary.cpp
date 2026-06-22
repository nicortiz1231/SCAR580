#include "SCARBodyDetectionBlueprintLibrary.h"

#include "Engine/World.h"
#include "SCARBodyDetectionSubsystem.h"
#include "SCARVisionBodyPoseBridge.h"
#include "SCARVisionBodyPoseProvider.h"

USCARBodyDetectionSubsystem* USCARBodyDetectionBlueprintLibrary::GetBodyDetectionSubsystem(const UObject* WorldContextObject)
{
	if (const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull) : nullptr)
	{
		return World->GetSubsystem<USCARBodyDetectionSubsystem>();
	}

	return nullptr;
}

bool USCARBodyDetectionBlueprintLibrary::IsPersonInCameraPreview(const UObject* WorldContextObject)
{
	if (const USCARBodyDetectionSubsystem* Subsystem = GetBodyDetectionSubsystem(WorldContextObject))
	{
		return Subsystem->IsPersonInCameraPreview();
	}

	return false;
}

FSCARBodyDetectionSnapshot USCARBodyDetectionBlueprintLibrary::GetBodyDetectionSnapshot(const UObject* WorldContextObject)
{
	if (const USCARBodyDetectionSubsystem* Subsystem = GetBodyDetectionSubsystem(WorldContextObject))
	{
		return Subsystem->GetSnapshot();
	}

	return FSCARBodyDetectionSnapshot();
}

bool USCARBodyDetectionBlueprintLibrary::IsVisionBodyPoseSupported()
{
	return FSCARVisionBodyPoseBridge::IsSupported();
}
