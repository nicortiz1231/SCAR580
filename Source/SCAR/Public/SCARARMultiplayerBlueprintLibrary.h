#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SCARARMultiplayerBlueprintLibrary.generated.h"

UCLASS()
class SCAR_API USCARARMultiplayerBlueprintLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category = "SCAR|Multiplayer")
	static bool GetLocalLanIPv4(FString& OutAddress);

	UFUNCTION(BlueprintPure, Category = "SCAR|Multiplayer")
	static FString BuildJoinAddress(const FString& HostAddress, int32 Port = 7777);

	UFUNCTION(BlueprintPure, Category = "SCAR|Multiplayer", meta = (WorldContext = "WorldContextObject"))
	static FString GetNetModeDescription(const UObject* WorldContextObject);

	UFUNCTION(BlueprintPure, Category = "SCAR|Multiplayer", meta = (WorldContext = "WorldContextObject"))
	static bool ShouldShowMultiplayerMenu(const UObject* WorldContextObject);

	UFUNCTION(BlueprintCallable, Category = "SCAR|Multiplayer", meta = (WorldContext = "WorldContextObject"))
	static void HostARMultiplayerSession(UObject* WorldContextObject, const FString& MapOverride = TEXT(""));

	UFUNCTION(BlueprintCallable, Category = "SCAR|Multiplayer")
	static void JoinARMultiplayerSession(APlayerController* PlayerController, const FString& Address, int32 Port = 7777);

	UFUNCTION(BlueprintCallable, Category = "SCAR|Multiplayer", meta = (WorldContext = "WorldContextObject"))
	static void ShowARMultiplayerMenu(UObject* WorldContextObject);

	UFUNCTION(BlueprintCallable, Category = "SCAR|Multiplayer")
	static void ShowARMultiplayerMenuForActor(AActor* Actor);
};
