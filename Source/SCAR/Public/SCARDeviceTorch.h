#pragma once

#include "CoreMinimal.h"

/** Controls the physical iPhone LED torch (rear camera flash). No-op on non-iOS. */
namespace SCARDeviceTorch
{
	bool IsSupported();

	/** Turn the device torch on/off. Safe to call repeatedly; implementation is idempotent. */
	void SetEnabled(bool bEnabled);
}
