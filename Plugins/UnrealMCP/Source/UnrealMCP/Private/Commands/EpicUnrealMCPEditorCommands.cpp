#include "Commands/EpicUnrealMCPEditorCommands.h"
#include "Commands/EpicUnrealMCPCommonUtils.h"
#include "Editor.h"
#include "EditorViewportClient.h"
#include "LevelEditorViewport.h"
#include "ImageUtils.h"
#include "HighResScreenshot.h"
#include "Engine/GameViewportClient.h"
#include "Misc/FileHelper.h"
#include "GameFramework/Actor.h"
#include "Engine/Selection.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/DirectionalLight.h"
#include "Engine/PointLight.h"
#include "Engine/SpotLight.h"
#include "Camera/CameraActor.h"
#include "Components/StaticMeshComponent.h"
#include "EditorSubsystem.h"
#include "Subsystems/EditorActorSubsystem.h"
#include "Engine/Blueprint.h"
#include "Engine/BlueprintGeneratedClass.h"
#include "EditorAssetLibrary.h"
#include "Commands/EpicUnrealMCPBlueprintCommands.h"
#include "InputMappingContext.h"
#include "InputAction.h"
#include "FileHelpers.h"
#include "Engine/SkyLight.h"
#include "Components/SkyLightComponent.h"
#include "Engine/DirectionalLight.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/PointLightComponent.h"
#include "Engine/SimpleConstructionScript.h"
#include "Engine/SCS_Node.h"
#include "Kismet2/KismetEditorUtilities.h"

FEpicUnrealMCPEditorCommands::FEpicUnrealMCPEditorCommands()
{
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params)
{
    // Actor manipulation commands
    if (CommandType == TEXT("get_actors_in_level"))
    {
        return HandleGetActorsInLevel(Params);
    }
    else if (CommandType == TEXT("find_actors_by_name"))
    {
        return HandleFindActorsByName(Params);
    }
    else if (CommandType == TEXT("spawn_actor"))
    {
        return HandleSpawnActor(Params);
    }
    else if (CommandType == TEXT("delete_actor"))
    {
        return HandleDeleteActor(Params);
    }
    else if (CommandType == TEXT("set_actor_transform"))
    {
        return HandleSetActorTransform(Params);
    }
    // Blueprint actor spawning
    else if (CommandType == TEXT("spawn_blueprint_actor"))
    {
        return HandleSpawnBlueprintActor(Params);
    }
    // Input mapping modification
    else if (CommandType == TEXT("modify_input_mapping"))
    {
        return HandleModifyInputMapping(Params);
    }
    // Component property setter (e.g. light intensity on BP_FPCharacter lights)
    else if (CommandType == TEXT("set_component_property"))
    {
        return HandleSetComponentProperty(Params);
    }
    
    return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Unknown editor command: %s"), *CommandType));
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleGetActorsInLevel(const TSharedPtr<FJsonObject>& Params)
{
    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(GWorld, AActor::StaticClass(), AllActors);
    
    TArray<TSharedPtr<FJsonValue>> ActorArray;
    for (AActor* Actor : AllActors)
    {
        if (Actor)
        {
            ActorArray.Add(FEpicUnrealMCPCommonUtils::ActorToJson(Actor));
        }
    }
    
    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetArrayField(TEXT("actors"), ActorArray);
    
    return ResultObj;
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleFindActorsByName(const TSharedPtr<FJsonObject>& Params)
{
    FString Pattern;
    if (!Params->TryGetStringField(TEXT("pattern"), Pattern))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'pattern' parameter"));
    }
    
    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(GWorld, AActor::StaticClass(), AllActors);
    
    TArray<TSharedPtr<FJsonValue>> MatchingActors;
    for (AActor* Actor : AllActors)
    {
        if (Actor && Actor->GetName().Contains(Pattern))
        {
            MatchingActors.Add(FEpicUnrealMCPCommonUtils::ActorToJson(Actor));
        }
    }
    
    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetArrayField(TEXT("actors"), MatchingActors);
    
    return ResultObj;
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleSpawnActor(const TSharedPtr<FJsonObject>& Params)
{
    // Get required parameters
    FString ActorType;
    if (!Params->TryGetStringField(TEXT("type"), ActorType))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'type' parameter"));
    }

    // Get actor name (required parameter)
    FString ActorName;
    if (!Params->TryGetStringField(TEXT("name"), ActorName))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
    }

    // Get optional transform parameters
    FVector Location(0.0f, 0.0f, 0.0f);
    FRotator Rotation(0.0f, 0.0f, 0.0f);
    FVector Scale(1.0f, 1.0f, 1.0f);

    if (Params->HasField(TEXT("location")))
    {
        Location = FEpicUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("location"));
    }
    if (Params->HasField(TEXT("rotation")))
    {
        Rotation = FEpicUnrealMCPCommonUtils::GetRotatorFromJson(Params, TEXT("rotation"));
    }
    if (Params->HasField(TEXT("scale")))
    {
        Scale = FEpicUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("scale"));
    }

    // Create the actor based on type
    AActor* NewActor = nullptr;
    UWorld* World = GEditor->GetEditorWorldContext().World();

    if (!World)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get editor world"));
    }

    // Check if an actor with this name already exists
    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(World, AActor::StaticClass(), AllActors);
    for (AActor* Actor : AllActors)
    {
        if (Actor && Actor->GetName() == ActorName)
        {
            return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Actor with name '%s' already exists"), *ActorName));
        }
    }

    FActorSpawnParameters SpawnParams;
    SpawnParams.Name = *ActorName;

    if (ActorType == TEXT("StaticMeshActor"))
    {
        AStaticMeshActor* NewMeshActor = World->SpawnActor<AStaticMeshActor>(AStaticMeshActor::StaticClass(), Location, Rotation, SpawnParams);
        if (NewMeshActor)
        {
            // Check for an optional static_mesh parameter to assign a mesh
            FString MeshPath;
            if (Params->TryGetStringField(TEXT("static_mesh"), MeshPath))
            {
                UStaticMesh* Mesh = Cast<UStaticMesh>(UEditorAssetLibrary::LoadAsset(MeshPath));
                if (Mesh)
                {
                    NewMeshActor->GetStaticMeshComponent()->SetStaticMesh(Mesh);
                }
                else
                {
                    UE_LOG(LogTemp, Warning, TEXT("Could not find static mesh at path: %s"), *MeshPath);
                }
            }
        }
        NewActor = NewMeshActor;
    }
    else if (ActorType == TEXT("PointLight"))
    {
        NewActor = World->SpawnActor<APointLight>(APointLight::StaticClass(), Location, Rotation, SpawnParams);
    }
    else if (ActorType == TEXT("SpotLight"))
    {
        NewActor = World->SpawnActor<ASpotLight>(ASpotLight::StaticClass(), Location, Rotation, SpawnParams);
    }
    else if (ActorType == TEXT("DirectionalLight"))
    {
        NewActor = World->SpawnActor<ADirectionalLight>(ADirectionalLight::StaticClass(), Location, Rotation, SpawnParams);
    }
    else if (ActorType == TEXT("CameraActor"))
    {
        NewActor = World->SpawnActor<ACameraActor>(ACameraActor::StaticClass(), Location, Rotation, SpawnParams);
    }
    else if (ActorType == TEXT("SkyLight"))
    {
        ASkyLight* SkyLightActor = World->SpawnActor<ASkyLight>(ASkyLight::StaticClass(), Location, Rotation, SpawnParams);
        if (SkyLightActor && SkyLightActor->GetLightComponent())
        {
            // Default to a modest intensity suitable for AR character lighting
            double Intensity = 1.0;
            Params->TryGetNumberField(TEXT("intensity"), Intensity);
            SkyLightActor->GetLightComponent()->Intensity = (float)Intensity;
        }
        NewActor = SkyLightActor;
    }
    else
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Unknown actor type: %s"), *ActorType));
    }

    if (NewActor)
    {
        // Set scale (since SpawnActor only takes location and rotation)
        FTransform Transform = NewActor->GetTransform();
        Transform.SetScale3D(Scale);
        NewActor->SetActorTransform(Transform);

        // Return the created actor's details
        return FEpicUnrealMCPCommonUtils::ActorToJsonObject(NewActor, true);
    }

    return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to create actor"));
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleDeleteActor(const TSharedPtr<FJsonObject>& Params)
{
    FString ActorName;
    if (!Params->TryGetStringField(TEXT("name"), ActorName))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
    }

    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(GWorld, AActor::StaticClass(), AllActors);
    
    for (AActor* Actor : AllActors)
    {
        if (Actor && Actor->GetName() == ActorName)
        {
            // Store actor info before deletion for the response
            TSharedPtr<FJsonObject> ActorInfo = FEpicUnrealMCPCommonUtils::ActorToJsonObject(Actor);
            
            // Delete the actor
            Actor->Destroy();
            
            TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
            ResultObj->SetObjectField(TEXT("deleted_actor"), ActorInfo);
            return ResultObj;
        }
    }
    
    return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Actor not found: %s"), *ActorName));
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleSetActorTransform(const TSharedPtr<FJsonObject>& Params)
{
    // Get actor name
    FString ActorName;
    if (!Params->TryGetStringField(TEXT("name"), ActorName))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
    }

    // Find the actor
    AActor* TargetActor = nullptr;
    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(GWorld, AActor::StaticClass(), AllActors);
    
    for (AActor* Actor : AllActors)
    {
        if (Actor && Actor->GetName() == ActorName)
        {
            TargetActor = Actor;
            break;
        }
    }

    if (!TargetActor)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Actor not found: %s"), *ActorName));
    }

    // Get transform parameters
    FTransform NewTransform = TargetActor->GetTransform();

    if (Params->HasField(TEXT("location")))
    {
        NewTransform.SetLocation(FEpicUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("location")));
    }
    if (Params->HasField(TEXT("rotation")))
    {
        NewTransform.SetRotation(FQuat(FEpicUnrealMCPCommonUtils::GetRotatorFromJson(Params, TEXT("rotation"))));
    }
    if (Params->HasField(TEXT("scale")))
    {
        NewTransform.SetScale3D(FEpicUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("scale")));
    }

    // Set the new transform
    TargetActor->SetActorTransform(NewTransform);

    // Return updated actor info
    return FEpicUnrealMCPCommonUtils::ActorToJsonObject(TargetActor, true);
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleSpawnBlueprintActor(const TSharedPtr<FJsonObject>& Params)
{
    // This function will now correctly call the implementation in BlueprintCommands
    FEpicUnrealMCPBlueprintCommands BlueprintCommands;
    return BlueprintCommands.HandleCommand(TEXT("spawn_blueprint_actor"), Params);
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleModifyInputMapping(const TSharedPtr<FJsonObject>& Params)
{
    // Required params: imc_path, action_path, new_key
    // Optional: old_key (to match a specific binding; if omitted, replaces first match)
    FString IMCPath, ActionPath, NewKeyName;
    if (!Params->TryGetStringField(TEXT("imc_path"), IMCPath))
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing required param: imc_path"));
    if (!Params->TryGetStringField(TEXT("action_path"), ActionPath))
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing required param: action_path"));
    if (!Params->TryGetStringField(TEXT("new_key"), NewKeyName))
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing required param: new_key"));

    FString OldKeyName;
    bool bFilterByOldKey = Params->TryGetStringField(TEXT("old_key"), OldKeyName);

    // Load the Input Mapping Context asset
    UInputMappingContext* IMC = LoadObject<UInputMappingContext>(nullptr, *IMCPath);
    if (!IMC)
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Could not load IMC asset: %s"), *IMCPath));

    // Load the Input Action asset
    UInputAction* Action = LoadObject<UInputAction>(nullptr, *ActionPath);
    if (!Action)
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Could not load InputAction asset: %s"), *ActionPath));

    FName NewKeyFName(*NewKeyName);
    FKey NewKey = FKey(NewKeyFName);
    if (!NewKey.IsValid())
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Invalid key name: %s"), *NewKeyName));

    // Access Mappings via reflection to avoid const limitations
    FArrayProperty* MappingsProp = CastField<FArrayProperty>(
        UInputMappingContext::StaticClass()->FindPropertyByName(TEXT("Mappings")));
    if (!MappingsProp)
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Could not find Mappings property on UInputMappingContext"));

    FStructProperty* ElemProp = CastField<FStructProperty>(MappingsProp->Inner);
    if (!ElemProp)
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Unexpected Mappings inner property type"));

    FObjectProperty* ActionProp = CastField<FObjectProperty>(
        ElemProp->Struct->FindPropertyByName(TEXT("Action")));
    FStructProperty* KeyProp = CastField<FStructProperty>(
        ElemProp->Struct->FindPropertyByName(TEXT("Key")));

    if (!ActionProp || !KeyProp)
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Could not find Action or Key property on FEnhancedActionKeyMapping"));

    FScriptArrayHelper ArrayHelper(MappingsProp, MappingsProp->ContainerPtrToValuePtr<void>(IMC));

    int32 ChangedCount = 0;
    for (int32 i = 0; i < ArrayHelper.Num(); i++)
    {
        void* ElemPtr = ArrayHelper.GetRawPtr(i);

        // Check action match
        UObject* MappedAction = ActionProp->GetObjectPropertyValue_InContainer(ElemPtr);
        if (MappedAction != Action)
            continue;

        // Optionally filter by old key
        if (bFilterByOldKey)
        {
            FKey* KeyPtr = KeyProp->ContainerPtrToValuePtr<FKey>(ElemPtr);
            if (KeyPtr->GetFName() != FName(*OldKeyName))
                continue;
        }

        // Modify key in-place
        FKey* KeyPtr = KeyProp->ContainerPtrToValuePtr<FKey>(ElemPtr);
        *KeyPtr = NewKey;
        ChangedCount++;
    }

    if (ChangedCount == 0)
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(
            FString::Printf(TEXT("No mapping found for action '%s'%s in IMC '%s'"),
                *ActionPath,
                bFilterByOldKey ? *FString::Printf(TEXT(" with key '%s'"), *OldKeyName) : TEXT(""),
                *IMCPath));

    // Mark package dirty and save
    IMC->MarkPackageDirty();
    TArray<UPackage*> PackagesToSave;
    PackagesToSave.Add(IMC->GetPackage());
    UEditorLoadingAndSavingUtils::SavePackages(PackagesToSave, /*bOnlyDirty=*/false);

    TSharedPtr<FJsonObject> Result = MakeShareable(new FJsonObject);
    Result->SetStringField(TEXT("status"), TEXT("success"));
    Result->SetNumberField(TEXT("mappings_changed"), (double)ChangedCount);
    Result->SetStringField(TEXT("new_key"), NewKeyName);
    Result->SetStringField(TEXT("imc_path"), IMCPath);
    return Result;
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleSetComponentProperty(const TSharedPtr<FJsonObject>& Params)
{
    // Required params: blueprint_path, component_name, property_name
    // Value params (at least one required): float_value, bool_value, int_value, string_value
    FString BlueprintPath, ComponentName, PropertyName;
    if (!Params->TryGetStringField(TEXT("blueprint_path"), BlueprintPath))
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing required param: blueprint_path"));
    if (!Params->TryGetStringField(TEXT("component_name"), ComponentName))
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing required param: component_name"));
    if (!Params->TryGetStringField(TEXT("property_name"), PropertyName))
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing required param: property_name"));

    UBlueprint* BP = LoadObject<UBlueprint>(nullptr, *BlueprintPath);
    if (!BP)
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Could not load Blueprint: %s"), *BlueprintPath));

    if (!BP->SimpleConstructionScript)
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Blueprint has no SimpleConstructionScript"));

    // Find the SCS node for the component
    UActorComponent* ComponentTemplate = nullptr;
    TArray<USCS_Node*> AllNodes = BP->SimpleConstructionScript->GetAllNodes();
    for (USCS_Node* Node : AllNodes)
    {
        if (Node && Node->GetVariableName().ToString() == ComponentName)
        {
            ComponentTemplate = Node->ComponentTemplate;
            break;
        }
    }

    if (!ComponentTemplate)
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(
            FString::Printf(TEXT("Component '%s' not found in Blueprint '%s'"), *ComponentName, *BlueprintPath));

    // Find the property by name
    FProperty* Prop = ComponentTemplate->GetClass()->FindPropertyByName(FName(*PropertyName));
    if (!Prop)
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(
            FString::Printf(TEXT("Property '%s' not found on component '%s'"), *PropertyName, *ComponentName));

    FString SetResult;

    // Handle float
    double FloatVal;
    if (Params->TryGetNumberField(TEXT("float_value"), FloatVal))
    {
        if (FFloatProperty* FProp = CastField<FFloatProperty>(Prop))
        {
            FProp->SetPropertyValue_InContainer(ComponentTemplate, (float)FloatVal);
            SetResult = FString::Printf(TEXT("Set float '%s' = %f"), *PropertyName, FloatVal);
        }
        else if (FDoubleProperty* DProp = CastField<FDoubleProperty>(Prop))
        {
            DProp->SetPropertyValue_InContainer(ComponentTemplate, FloatVal);
            SetResult = FString::Printf(TEXT("Set double '%s' = %f"), *PropertyName, FloatVal);
        }
        else
        {
            return FEpicUnrealMCPCommonUtils::CreateErrorResponse(
                FString::Printf(TEXT("Property '%s' is not a float/double"), *PropertyName));
        }
    }
    // Handle bool
    else if (Params->HasField(TEXT("bool_value")))
    {
        bool BoolVal = Params->GetBoolField(TEXT("bool_value"));
        if (FBoolProperty* BProp = CastField<FBoolProperty>(Prop))
        {
            BProp->SetPropertyValue_InContainer(ComponentTemplate, BoolVal);
            SetResult = FString::Printf(TEXT("Set bool '%s' = %s"), *PropertyName, BoolVal ? TEXT("true") : TEXT("false"));
        }
        else
        {
            return FEpicUnrealMCPCommonUtils::CreateErrorResponse(
                FString::Printf(TEXT("Property '%s' is not a bool"), *PropertyName));
        }
    }
    // Handle int
    else if (Params->HasField(TEXT("int_value")))
    {
        int64 IntVal = (int64)Params->GetNumberField(TEXT("int_value"));
        if (FIntProperty* IProp = CastField<FIntProperty>(Prop))
        {
            IProp->SetPropertyValue_InContainer(ComponentTemplate, (int32)IntVal);
            SetResult = FString::Printf(TEXT("Set int '%s' = %lld"), *PropertyName, IntVal);
        }
        else
        {
            return FEpicUnrealMCPCommonUtils::CreateErrorResponse(
                FString::Printf(TEXT("Property '%s' is not an int"), *PropertyName));
        }
    }
    else
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(
            TEXT("Must provide one of: float_value, bool_value, int_value"));
    }

    // Mark blueprint dirty and compile
    BP->MarkPackageDirty();
    FKismetEditorUtilities::CompileBlueprint(BP);

    // Save the blueprint package
    TArray<UPackage*> PackagesToSave;
    PackagesToSave.Add(BP->GetPackage());
    UEditorLoadingAndSavingUtils::SavePackages(PackagesToSave, false);

    TSharedPtr<FJsonObject> Res = MakeShareable(new FJsonObject);
    Res->SetStringField(TEXT("status"), TEXT("success"));
    Res->SetStringField(TEXT("result"), SetResult);
    Res->SetStringField(TEXT("blueprint"), BlueprintPath);
    Res->SetStringField(TEXT("component"), ComponentName);
    return Res;
}
