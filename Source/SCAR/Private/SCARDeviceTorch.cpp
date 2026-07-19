#include "SCARDeviceTorch.h"

#if !PLATFORM_IOS

bool SCARDeviceTorch::IsSupported()
{
	return false;
}

void SCARDeviceTorch::SetEnabled(bool bEnabled)
{
	(void)bEnabled;
}

#endif
