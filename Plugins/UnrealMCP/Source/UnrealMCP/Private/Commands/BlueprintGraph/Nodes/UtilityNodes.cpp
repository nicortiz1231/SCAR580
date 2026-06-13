#include "Commands/BlueprintGraph/Nodes/UtilityNodes.h"
#include "Commands/BlueprintGraph/Nodes/NodeCreatorUtils.h"
#include "K2Node_CallFunction.h"
#include "K2Node_Select.h"
#include "K2Node_SpawnActorFromClass.h"
#include "EdGraphSchema_K2.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetMathLibrary.h"
#include "Engine/Blueprint.h"
#include "EditorAssetLibrary.h"
#include "Json.h"

UK2Node* FUtilityNodeCreator::CreatePrintNode(UEdGraph* Graph, const TSharedPtr<FJsonObject>& Params)
{
	if (!Graph || !Params.IsValid())
	{
		return nullptr;
	}

	UK2Node_CallFunction* PrintNode = NewObject<UK2Node_CallFunction>(Graph);
	if (!PrintNode)
	{
		return nullptr;
	}

	UFunction* PrintFunc = UKismetSystemLibrary::StaticClass()->FindFunctionByName(
		GET_FUNCTION_NAME_CHECKED(UKismetSystemLibrary, PrintString)
	);

	if (!PrintFunc)
	{
		return nullptr;
	}

	// Set function reference BEFORE initialization
	PrintNode->SetFromFunction(PrintFunc);

	double PosX, PosY;
	FNodeCreatorUtils::ExtractNodePosition(Params, PosX, PosY);
	PrintNode->NodePosX = static_cast<int32>(PosX);
	PrintNode->NodePosY = static_cast<int32>(PosY);

	Graph->AddNode(PrintNode, true, false);
	FNodeCreatorUtils::InitializeK2Node(PrintNode, Graph);

	// Set message if provided AFTER initialization
	FString Message;
	if (Params->TryGetStringField(TEXT("message"), Message))
	{
		UEdGraphPin* InStringPin = PrintNode->FindPin(TEXT("InString"));
		if (InStringPin)
		{
			InStringPin->DefaultValue = Message;
		}
	}

	return PrintNode;
}

UK2Node* FUtilityNodeCreator::CreateCallFunctionNode(UEdGraph* Graph, const TSharedPtr<FJsonObject>& Params)
{
	if (!Graph || !Params.IsValid())
	{
		return nullptr;
	}

	// Get target function name
	FString TargetFunction;
	if (!Params->TryGetStringField(TEXT("target_function"), TargetFunction))
	{
		return nullptr;
	}

	UK2Node_CallFunction* CallNode = NewObject<UK2Node_CallFunction>(Graph);
	if (!CallNode)
	{
		return nullptr;
	}

	// Find the function to call
	UFunction* TargetFunc = nullptr;
	FString ClassName;
	if (Params->TryGetStringField(TEXT("target_class"), ClassName))
	{
		UClass* TargetClass = nullptr;

		// First try StaticFindObject (works for loaded UObjects including Blueprint Generated Classes)
		TargetClass = Cast<UClass>(StaticFindObject(UClass::StaticClass(), nullptr, *ClassName));

		// If not found, try loading a Blueprint asset and getting its generated class
		if (!TargetClass)
		{
			FString BlueprintPath = ClassName;
			// Strip _C suffix to get the Blueprint asset path
			if (BlueprintPath.EndsWith(TEXT("_C")))
			{
				BlueprintPath = BlueprintPath.LeftChop(2);
			}
			// Add .Blueprint suffix if not present
			if (!BlueprintPath.Contains(TEXT(".")))
			{
				BlueprintPath += TEXT(".") + FPaths::GetBaseFilename(BlueprintPath);
			}
			UBlueprint* BP = LoadObject<UBlueprint>(nullptr, *BlueprintPath);
			if (!BP && UEditorAssetLibrary::DoesAssetExist(BlueprintPath))
			{
				UObject* Asset = UEditorAssetLibrary::LoadAsset(BlueprintPath);
				BP = Cast<UBlueprint>(Asset);
			}
			if (BP && BP->GeneratedClass)
			{
				TargetClass = BP->GeneratedClass;
			}
		}

		if (TargetClass)
		{
			TargetFunc = TargetClass->FindFunctionByName(FName(*TargetFunction));
		}
	}
	else
	{
		// Search common Unreal Blueprint function libraries in order
		TArray<UClass*> SearchClasses = {
			UKismetSystemLibrary::StaticClass(),
			UGameplayStatics::StaticClass(),
			UKismetMathLibrary::StaticClass()
		};

		for (UClass* SearchClass : SearchClasses)
		{
			if (SearchClass)
			{
				TargetFunc = SearchClass->FindFunctionByName(FName(*TargetFunction));
				if (TargetFunc) break;
			}
		}
	}

	if (!TargetFunc)
	{
		return nullptr;
	}

	// Set function reference BEFORE initialization
	CallNode->SetFromFunction(TargetFunc);

	double PosX, PosY;
	FNodeCreatorUtils::ExtractNodePosition(Params, PosX, PosY);
	CallNode->NodePosX = static_cast<int32>(PosX);
	CallNode->NodePosY = static_cast<int32>(PosY);

	Graph->AddNode(CallNode, true, false);
	FNodeCreatorUtils::InitializeK2Node(CallNode, Graph);

	return CallNode;
}

UK2Node* FUtilityNodeCreator::CreateSelectNode(UEdGraph* Graph, const TSharedPtr<FJsonObject>& Params)
{
	if (!Graph || !Params.IsValid())
	{
		return nullptr;
	}

	UK2Node_Select* SelectNode = NewObject<UK2Node_Select>(Graph);
	if (!SelectNode)
	{
		return nullptr;
	}

	double PosX, PosY;
	FNodeCreatorUtils::ExtractNodePosition(Params, PosX, PosY);
	SelectNode->NodePosX = static_cast<int32>(PosX);
	SelectNode->NodePosY = static_cast<int32>(PosY);

	Graph->AddNode(SelectNode, true, false);
	FNodeCreatorUtils::InitializeK2Node(SelectNode, Graph);

	return SelectNode;
}

UK2Node* FUtilityNodeCreator::CreateSpawnActorNode(UEdGraph* Graph, const TSharedPtr<FJsonObject>& Params)
{
	if (!Graph || !Params.IsValid())
	{
		return nullptr;
	}

	UK2Node_SpawnActorFromClass* SpawnActorNode = NewObject<UK2Node_SpawnActorFromClass>(Graph);
	if (!SpawnActorNode)
	{
		return nullptr;
	}

	double PosX, PosY;
	FNodeCreatorUtils::ExtractNodePosition(Params, PosX, PosY);
	SpawnActorNode->NodePosX = static_cast<int32>(PosX);
	SpawnActorNode->NodePosY = static_cast<int32>(PosY);

	Graph->AddNode(SpawnActorNode, true, false);
	FNodeCreatorUtils::InitializeK2Node(SpawnActorNode, Graph);

	// Optionally set the spawn class via target_blueprint or spawn_class parameter
	FString SpawnClassName;
	bool bFoundClass = Params->TryGetStringField(TEXT("spawn_class"), SpawnClassName);
	if (!bFoundClass)
	{
		bFoundClass = Params->TryGetStringField(TEXT("target_blueprint"), SpawnClassName);
	}
	if (bFoundClass && !SpawnClassName.IsEmpty())
	{
		UClass* SpawnClass = nullptr;
		SpawnClass = Cast<UClass>(StaticFindObject(UClass::StaticClass(), nullptr, *SpawnClassName));

		if (!SpawnClass)
		{
			FString BlueprintPath = SpawnClassName;
			if (BlueprintPath.EndsWith(TEXT("_C")))
			{
				BlueprintPath = BlueprintPath.LeftChop(2);
			}
			if (!BlueprintPath.Contains(TEXT(".")))
			{
				BlueprintPath += TEXT(".") + FPaths::GetBaseFilename(BlueprintPath);
			}
			UBlueprint* BP = LoadObject<UBlueprint>(nullptr, *BlueprintPath);
			if (!BP && UEditorAssetLibrary::DoesAssetExist(BlueprintPath))
			{
				UObject* Asset = UEditorAssetLibrary::LoadAsset(BlueprintPath);
				BP = Cast<UBlueprint>(Asset);
			}
			if (BP && BP->GeneratedClass)
			{
				SpawnClass = BP->GeneratedClass;
			}
		}

		if (SpawnClass)
		{
			// Set the class pin default value
			UEdGraphPin* ClassPin = SpawnActorNode->GetClassPin();
			if (ClassPin)
			{
				ClassPin->DefaultObject = SpawnClass;
			}
		}
	}

	return SpawnActorNode;
}

