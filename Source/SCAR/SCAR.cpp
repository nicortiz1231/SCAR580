#include "SCAR.h"
#include "CoreGlobals.h"
#include "Modules/ModuleManager.h"

class FSCARModule : public IModuleInterface
{
public:
	virtual void StartupModule() override
	{
		// Engine ini NearClipPlane is often ignored on mobile; set global fallback early.
		GNearClippingPlane = 0.0001f;
	}
};

IMPLEMENT_PRIMARY_GAME_MODULE(FSCARModule, SCAR, "SCAR");
