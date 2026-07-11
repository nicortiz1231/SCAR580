#pragma once

#include "CoreMinimal.h"
#include "SCARWeaponAttachmentTypes.generated.h"

UENUM(BlueprintType)
enum class ESCARWeaponAttachmentCategory : uint8
{
	Sight,
	Laser,
	Muzzle,
	Grip
};
