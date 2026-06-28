#include "iOS/SCARBodyScreenMappingIOS.h"

#include "AppleARKitCamera.h"
#include "AppleARKitFrame.h"
#include "AppleARKitModule.h"
#include "AppleARKitSystem.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"

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

	const FAppleARKitCamera* GetCurrentARKitCamera()
	{
		const TSharedPtr<FAppleARKitSystem, ESPMode::ThreadSafe> ArkitSystem = FAppleARKitModule::GetARKitSystem();
		if (!ArkitSystem.IsValid())
		{
			return nullptr;
		}

		void* RawFrame = ArkitSystem->GetGameThreadARFrameRawPointer();
		if (!RawFrame)
		{
			return nullptr;
		}

		const FAppleARKitFrame* Frame = static_cast<const FAppleARKitFrame*>(RawFrame);
		return &Frame->Camera;
	}

	bool MapImageToViewportUsingARKitCamera(
		const FAppleARKitCamera& Camera,
		const FVector2D& ImageNormalized,
		FVector2D& OutViewport01)
	{
		FVector2D ViewportSize;
		if (!GetViewportSize(ViewportSize))
		{
			return false;
		}

		const EAppleARKitBackgroundFitMode FitMode = EAppleARKitBackgroundFitMode::Fit;
		const int32 GridSteps = 48;
		FVector2D BestScreen = FVector2D::ZeroVector;
		float BestDistSq = TNumericLimits<float>::Max();

		for (int32 GridX = 0; GridX <= GridSteps; ++GridX)
		{
			for (int32 GridY = 0; GridY <= GridSteps; ++GridY)
			{
				const FVector2D TestScreen(
					(static_cast<float>(GridX) / GridSteps) * ViewportSize.X,
					(static_cast<float>(GridY) / GridSteps) * ViewportSize.Y);

				const FVector2D MappedImage = Camera.GetImageCoordinateForScreenPosition(
					TestScreen,
					FitMode,
					ViewportSize.X,
					ViewportSize.Y);

				const float DistSq = FVector2D::DistSquared(MappedImage, ImageNormalized);
				if (DistSq < BestDistSq)
				{
					BestDistSq = DistSq;
					BestScreen = TestScreen;
				}
			}
		}

		float RefineStep = FMath::Min(ViewportSize.X, ViewportSize.Y) / static_cast<float>(GridSteps);
		for (int32 RefineIter = 0; RefineIter < 12; ++RefineIter)
		{
			bool bImproved = false;
			static const FVector2D Deltas[] = {
				FVector2D(1.f, 0.f),
				FVector2D(-1.f, 0.f),
				FVector2D(0.f, 1.f),
				FVector2D(0.f, -1.f),
			};

			for (const FVector2D& Delta : Deltas)
			{
				const FVector2D TestScreen(
					FMath::Clamp(BestScreen.X + Delta.X * RefineStep, 0.f, ViewportSize.X),
					FMath::Clamp(BestScreen.Y + Delta.Y * RefineStep, 0.f, ViewportSize.Y));

				const FVector2D MappedImage = Camera.GetImageCoordinateForScreenPosition(
					TestScreen,
					FitMode,
					ViewportSize.X,
					ViewportSize.Y);

				const float DistSq = FVector2D::DistSquared(MappedImage, ImageNormalized);
				if (DistSq < BestDistSq)
				{
					BestDistSq = DistSq;
					BestScreen = TestScreen;
					bImproved = true;
				}
			}

			RefineStep *= 0.5f;
			if (!bImproved && RefineIter > 3)
			{
				break;
			}
		}

		OutViewport01.X = BestScreen.X / ViewportSize.X;
		OutViewport01.Y = BestScreen.Y / ViewportSize.Y;
		return true;
	}
}

bool SCAR_MapImageNormalizedToViewport01_IOS(const FVector2D& ImageNormalized, FVector2D& OutViewport01)
{
	if (const FAppleARKitCamera* Camera = GetCurrentARKitCamera())
	{
		return MapImageToViewportUsingARKitCamera(*Camera, ImageNormalized, OutViewport01);
	}

	return false;
}

bool SCAR_MapViewport01ToImageNormalized_IOS(const FVector2D& Viewport01, FVector2D& OutImageNormalized)
{
	if (const FAppleARKitCamera* Camera = GetCurrentARKitCamera())
	{
		FVector2D ViewportSize;
		if (!GetViewportSize(ViewportSize))
		{
			return false;
		}

		const FVector2D Screen(
			Viewport01.X * ViewportSize.X,
			Viewport01.Y * ViewportSize.Y);
		OutImageNormalized = Camera->GetImageCoordinateForScreenPosition(
			Screen,
			EAppleARKitBackgroundFitMode::Fit,
			ViewportSize.X,
			ViewportSize.Y);
		return OutImageNormalized.X >= 0.f
			&& OutImageNormalized.X <= 1.f
			&& OutImageNormalized.Y >= 0.f
			&& OutImageNormalized.Y <= 1.f;
	}

	return false;
}

bool SCAR_GetCameraImageResolution_IOS(FVector2D& OutImageResolution)
{
	if (const FAppleARKitCamera* Camera = GetCurrentARKitCamera())
	{
		if (Camera->ImageResolution.X > 0.f && Camera->ImageResolution.Y > 0.f)
		{
			OutImageResolution = Camera->ImageResolution;
			return true;
		}
	}

	return false;
}
