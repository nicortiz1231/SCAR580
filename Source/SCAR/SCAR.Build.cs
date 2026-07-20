using UnrealBuildTool;
using System.IO;

public class SCAR : ModuleRules
{
	public SCAR(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"CoreUObject",
				"Engine",
				"AugmentedReality",
				"UMG",
				"Slate",
				"SlateCore",
				"Niagara",
				"EnhancedInput",
				"InputCore",
				"XRBase",
				"Sockets",
				"Networking",
				"ProceduralMeshComponent",
			});

		if (Target.Platform == UnrealTargetPlatform.IOS)
		{
			PrivateDependencyModuleNames.AddRange(
				new string[]
				{
					"AppleARKit",
					"AppleImageUtils",
					"XRBase",
				});

			PrivateIncludePaths.Add(
				Path.Combine(
					EngineDirectory,
					"Plugins/Runtime/AR/AppleAR/AppleARKit/Source/AppleARKit/Private"));

			PublicFrameworks.Add("Vision");
			PublicFrameworks.Add("CoreImage");
			PublicFrameworks.Add("AVFoundation");
		}
	}
}
