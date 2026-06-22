#include "SCARBodyScreenMapping.h"

#include "ARBlueprintLibrary.h"
#include "ARTextures.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/PlayerController.h"

#if PLATFORM_IOS
#include "iOS/SCARBodyScreenMappingIOS.h"
#include "AppleARKitTextures.h"
#endif

namespace
{
	bool GetViewportSize(FVector2D& OutViewportSize)
	{
		if (GEngine && GEngine->GameViewport)
		{
			GEngine->GameViewport->GetViewportSize(OutViewportSize);
			return OutViewportSize.X > 0.f && OutViewportSize.Y > 0.f;
		}

		return false;
	}

	bool MapImageToViewportUsingAspectFit(const FVector2D& ImageNormalized, FVector2D& OutViewport01)
	{
		FVector2D ViewportSize;
		if (!GetViewportSize(ViewportSize))
		{
			return false;
		}

		FVector2D ImageResolution(1920.f, 1440.f);
		SCARBodyScreenMapping::GetCameraImageResolution(ImageResolution);

		const float ImageAspect = ImageResolution.X / FMath::Max(ImageResolution.Y, 1.f);
		const float ScreenAspect = ViewportSize.X / FMath::Max(ViewportSize.Y, 1.f);

		float ScreenX = 0.f;
		float ScreenY = 0.f;

		if (ScreenAspect > ImageAspect)
		{
			const float VisibleWidth = ViewportSize.Y * ImageAspect;
			const float OffsetX = (ViewportSize.X - VisibleWidth) * 0.5f;
			ScreenX = OffsetX + ImageNormalized.X * VisibleWidth;
			ScreenY = ImageNormalized.Y * ViewportSize.Y;
		}
		else
		{
			const float VisibleHeight = ViewportSize.X / ImageAspect;
			const float OffsetY = (ViewportSize.Y - VisibleHeight) * 0.5f;
			ScreenX = ImageNormalized.X * ViewportSize.X;
			ScreenY = OffsetY + ImageNormalized.Y * VisibleHeight;
		}

		OutViewport01.X = ScreenX / ViewportSize.X;
		OutViewport01.Y = ScreenY / ViewportSize.Y;
		return true;
	}
}

bool SCARBodyScreenMapping::GetCameraImageResolution(FVector2D& OutImageResolution)
{
#if PLATFORM_IOS
	if (SCAR_GetCameraImageResolution_IOS(OutImageResolution))
	{
		return true;
	}
#endif

	if (UARTexture* CameraTexture = UARBlueprintLibrary::GetARTexture(EARTextureType::CameraImage))
	{
#if PLATFORM_IOS
		if (const UAppleARKitTextureCameraImage* AppleTexture = Cast<UAppleARKitTextureCameraImage>(CameraTexture))
		{
			OutImageResolution = FVector2D(AppleTexture->Size.X, AppleTexture->Size.Y);
			return OutImageResolution.X > 0.f && OutImageResolution.Y > 0.f;
		}
#endif
		OutImageResolution = FVector2D(CameraTexture->Size.X, CameraTexture->Size.Y);
		return OutImageResolution.X > 0.f && OutImageResolution.Y > 0.f;
	}

	return false;
}

bool SCARBodyScreenMapping::MapImageNormalizedToViewport01(
	const FVector2D& ImageNormalized,
	FVector2D& OutViewport01)
{
#if PLATFORM_IOS
	if (SCAR_MapImageNormalizedToViewport01_IOS(ImageNormalized, OutViewport01))
	{
		return true;
	}
#endif

	return MapImageToViewportUsingAspectFit(ImageNormalized, OutViewport01);
}

bool SCARBodyScreenMapping::ImageNormalizedToWorldAtDistance(
	APlayerController* PlayerController,
	const FVector2D& ImageNormalized,
	const float Distance,
	FVector& OutWorldLocation)
{
	if (!PlayerController)
	{
		return false;
	}

	FVector2D Viewport01;
	if (!MapImageNormalizedToViewport01(ImageNormalized, Viewport01))
	{
		return false;
	}

	int32 SizeX = 0;
	int32 SizeY = 0;
	PlayerController->GetViewportSize(SizeX, SizeY);
	if (SizeX <= 0 || SizeY <= 0)
	{
		return false;
	}

	FVector WorldLocation;
	FVector WorldDirection;
	if (!PlayerController->DeprojectScreenPositionToWorld(
		Viewport01.X * SizeX,
		Viewport01.Y * SizeY,
		WorldLocation,
		WorldDirection))
	{
		return false;
	}

	OutWorldLocation = WorldLocation + WorldDirection * Distance;
	return true;
}
