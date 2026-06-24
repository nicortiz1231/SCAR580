#include "SCARBodyHitMarkerWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Image.h"
#include "Engine/GameViewportClient.h"
#include "Engine/Texture2D.h"
#include "GameFramework/PlayerController.h"

void USCARBodyHitMarkerWidget::NativeConstruct()
{
	Super::NativeConstruct();

	SetAnchorsInViewport(FAnchors(0.f, 0.f, 0.f, 0.f));
	SetAlignmentInViewport(FVector2D(0.f, 0.f));

	if (!MarkerImage && WidgetTree)
	{
		MarkerImage = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("HitMarkerImage"));
		if (MarkerImage)
		{
			WidgetTree->RootWidget = MarkerImage;
		}
	}
}

void USCARBodyHitMarkerWidget::ApplyMarkerTexture(UTexture2D* Texture, const float SizePx)
{
	if (!WidgetTree)
	{
		return;
	}

	if (!MarkerImage)
	{
		MarkerImage = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("HitMarkerImage"));
		if (MarkerImage)
		{
			WidgetTree->RootWidget = MarkerImage;
		}
	}

	if (!MarkerImage || !Texture)
	{
		return;
	}

	const float ClampedSize = FMath::Max(12.f, SizePx);
	FSlateBrush Brush;
	Brush.SetResourceObject(Texture);
	Brush.ImageSize = FVector2D(ClampedSize, ClampedSize);
	Brush.DrawAs = ESlateBrushDrawType::Image;
	MarkerImage->SetBrush(Brush);
	MarkerImage->SetColorAndOpacity(FLinearColor::White);
}

void USCARBodyHitMarkerWidget::SetMarkerTexture(UTexture2D* Texture)
{
	ApplyMarkerTexture(Texture, 32.f);
}

bool USCARBodyHitMarkerWidget::GetViewportPixelSize(FVector2D& OutViewportPixels) const
{
	if (const APlayerController* PlayerController = GetOwningPlayer())
	{
		int32 ScreenWidth = 0;
		int32 ScreenHeight = 0;
		PlayerController->GetViewportSize(ScreenWidth, ScreenHeight);
		if (ScreenWidth > 0 && ScreenHeight > 0)
		{
			OutViewportPixels = FVector2D(static_cast<float>(ScreenWidth), static_cast<float>(ScreenHeight));
			return true;
		}
	}

	if (const ULocalPlayer* LocalPlayer = GetOwningLocalPlayer())
	{
		if (LocalPlayer->ViewportClient)
		{
			FVector2D ViewportSize;
			LocalPlayer->ViewportClient->GetViewportSize(ViewportSize);
			if (ViewportSize.X > 0.f && ViewportSize.Y > 0.f)
			{
				OutViewportPixels = ViewportSize;
				return true;
			}
		}
	}

	return false;
}

void USCARBodyHitMarkerWidget::SetScreenMarkerLayout(const FVector2D& Viewport01Center, const float SizePx)
{
	const float ClampedSize = FMath::Max(12.f, SizePx);

	FVector2D ViewportPixels;
	if (!GetViewportPixelSize(ViewportPixels))
	{
		return;
	}

	SetDesiredSizeInViewport(FVector2D(ClampedSize, ClampedSize));

	const FVector2D TopLeft(
		Viewport01Center.X * ViewportPixels.X - ClampedSize * 0.5f,
		Viewport01Center.Y * ViewportPixels.Y - ClampedSize * 0.5f);
	SetPositionInViewport(TopLeft, false);

	if (MarkerImage)
	{
		MarkerImage->SetVisibility(ESlateVisibility::HitTestInvisible);
		FSlateBrush Brush = MarkerImage->GetBrush();
		Brush.ImageSize = FVector2D(ClampedSize, ClampedSize);
		MarkerImage->SetBrush(Brush);
	}
}
