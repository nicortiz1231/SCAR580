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
		}
	}
}
