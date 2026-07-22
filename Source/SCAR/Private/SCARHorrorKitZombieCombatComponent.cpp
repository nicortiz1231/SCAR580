#include "SCARHorrorKitZombieCombatComponent.h"

#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "SCARHorrorKitZombieBlueprintLibrary.h"
#include "SCARHorrorKitZombieDirector.h"
#include "SCARHorrorKitZombieTypes.h"
#include "UObject/UnrealType.h"

USCARHorrorKitZombieCombatComponent::USCARHorrorKitZombieCombatComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickGroup = TG_PostUpdateWork;
}

void USCARHorrorKitZombieCombatComponent::BeginPlay()
{
	Super::BeginPlay();

	if (UWorld* World = GetWorld())
	{
		ASCARHorrorKitZombieDirector::EnsureInWorld(World);
	}
}

void USCARHorrorKitZombieCombatComponent::TickComponent(
	const float DeltaTime,
	const ELevelTick TickType,
	FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	APawn* Pawn = Cast<APawn>(GetOwner());
	if (!Pawn || !Pawn->IsLocallyControlled())
	{
		return;
	}

	TryProcessLocalFire(Pawn);
}

namespace SCARHorrorKitZombieCombatComponentPrivate
{
	static bool GetFloatProperty(const UObject* Object, const FName PropertyName, float& OutValue)
	{
		if (!Object)
		{
			return false;
		}

		if (const FFloatProperty* Property =
				CastField<FFloatProperty>(Object->GetClass()->FindPropertyByName(PropertyName)))
		{
			OutValue = Property->GetPropertyValue_InContainer(Object);
			return true;
		}

		return false;
	}

	static bool GetIntProperty(const UObject* Object, const FName PropertyName, int32& OutValue)
	{
		if (!Object)
		{
			return false;
		}

		if (const FIntProperty* Property =
				CastField<FIntProperty>(Object->GetClass()->FindPropertyByName(PropertyName)))
		{
			OutValue = Property->GetPropertyValue_InContainer(Object);
			return true;
		}

		if (const FInt64Property* Property =
				CastField<FInt64Property>(Object->GetClass()->FindPropertyByName(PropertyName)))
		{
			OutValue = static_cast<int32>(Property->GetPropertyValue_InContainer(Object));
			return true;
		}

		return false;
	}

	static UObject* GetObjectProperty(const UObject* Object, const FName PropertyName)
	{
		if (!Object)
		{
			return nullptr;
		}

		if (const FObjectProperty* Property =
				CastField<FObjectProperty>(Object->GetClass()->FindPropertyByName(PropertyName)))
		{
			return Property->GetObjectPropertyValue_InContainer(Object);
		}

		return nullptr;
	}

	static UObject* GetHeldWeaponActor(const UObject* Pawn)
	{
		for (const FName PropertyName :
			{FName(TEXT("SpawnedItemRef")), FName(TEXT("SpawnedItem")), FName(TEXT("HeldItem"))})
		{
			if (UObject* Weapon = GetObjectProperty(Pawn, PropertyName))
			{
				return Weapon;
			}
		}

		return nullptr;
	}

	static int32 ReadHeldWeaponAmmo(const UObject* Pawn)
	{
		UObject* WeaponActor = GetHeldWeaponActor(Pawn);
		if (!WeaponActor)
		{
			return -1;
		}

		static const TCHAR* AmmoHints[] = {
			TEXT("Ammo"),
			TEXT("CurrentAmmo"),
			TEXT("MagazineAmmo"),
			TEXT("ClipAmmo"),
			TEXT("Bullets"),
			TEXT("Rounds"),
		};

		for (TFieldIterator<FProperty> It(WeaponActor->GetClass()); It; ++It)
		{
			FProperty* Property = *It;
			if (!Property)
			{
				continue;
			}

			const FString Name = Property->GetName();
			bool bMatch = false;
			for (const TCHAR* Hint : AmmoHints)
			{
				if (Name.Contains(Hint))
				{
					bMatch = true;
					break;
				}
			}
			if (!bMatch || Name.Contains(TEXT("Max")) || Name.Contains(TEXT("Reserve")))
			{
				continue;
			}

			if (const FIntProperty* IntProperty = CastField<FIntProperty>(Property))
			{
				return IntProperty->GetPropertyValue_InContainer(WeaponActor);
			}

			if (const FInt64Property* Int64Property = CastField<FInt64Property>(Property))
			{
				return static_cast<int32>(Int64Property->GetPropertyValue_InContainer(WeaponActor));
			}
		}

		return -1;
	}
}

bool USCARHorrorKitZombieCombatComponent::DetectFireEdge(APawn* LocalPawn)
{
	if (!LocalPawn)
	{
		return false;
	}

	using namespace SCARHorrorKitZombieCombatComponentPrivate;

	float FireAlpha = 0.f;
	if (GetFloatProperty(LocalPawn, TEXT("CrosshairFireAlpha"), FireAlpha))
	{
		const bool bRisingEdge = FireAlpha > 0.08f && LastFireAlpha <= 0.08f;
		LastFireAlpha = FireAlpha;
		if (bRisingEdge)
		{
			return true;
		}
	}

	int32 Ammo = ReadHeldWeaponAmmo(LocalPawn);
	if (Ammo < 0)
	{
		GetIntProperty(LocalPawn, TEXT("Ammo"), Ammo);
	}

	if (Ammo >= 0)
	{
		if (bHasKnownAmmo && Ammo < LastKnownAmmo)
		{
			LastKnownAmmo = Ammo;
			return true;
		}
		LastKnownAmmo = Ammo;
		bHasKnownAmmo = true;
	}

	return false;
}

float USCARHorrorKitZombieCombatComponent::ReadWeaponDamage(APawn* LocalPawn) const
{
	using namespace SCARHorrorKitZombieCombatComponentPrivate;

	float Damage = DefaultShotDamage;
	if (UObject* HeldItem = GetHeldWeaponActor(LocalPawn))
	{
		float ItemDamage = Damage;
		if (GetFloatProperty(HeldItem, TEXT("Damage"), ItemDamage) && ItemDamage > 0.f)
		{
			Damage = ItemDamage;
		}
	}

	float PawnDamage = Damage;
	if (GetFloatProperty(LocalPawn, TEXT("Damage"), PawnDamage) && PawnDamage > 0.f)
	{
		Damage = PawnDamage;
	}

	return Damage;
}

void USCARHorrorKitZombieCombatComponent::TryProcessLocalFire(APawn* LocalPawn)
{
	if (!DetectFireEdge(LocalPawn))
	{
		return;
	}

	const UWorld* World = GetWorld();
	const double Now = World ? World->GetTimeSeconds() : 0.0;
	if (Now - LastShotProcessedSeconds < 0.05)
	{
		return;
	}
	LastShotProcessedSeconds = Now;

	const float Damage = ReadWeaponDamage(LocalPawn);
	(void)USCARHorrorKitZombieBlueprintLibrary::TryApplyZombieHitScan(this, Damage, TraceDistanceCm);
}
