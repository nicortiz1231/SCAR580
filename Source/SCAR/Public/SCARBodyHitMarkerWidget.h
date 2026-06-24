#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SCARBodyHitMarkerWidget.generated.h"

class UImage;
class UTexture2D;

UCLASS()
class SCAR_API USCARBodyHitMarkerWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	void SetMarkerTexture(UTexture2D* Texture);
	void ApplyMarkerTexture(UTexture2D* Texture, float SizePx);
	void SetScreenMarkerLayout(const FVector2D& Viewport01Center, float SizePx);

protected:
	virtual void NativeConstruct() override;

private:
	bool GetViewportPixelSize(FVector2D& OutViewportPixels) const;
	UPROPERTY()
	TObjectPtr<UImage> MarkerImage;
};
