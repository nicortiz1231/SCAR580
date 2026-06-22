#pragma once

#include "SCARVisionBodyPoseBridge.h"

/** Platform bridge for Apple Vision 2D multi-body pose (Unity ARVisionBodyPose.mm parity). */
class SCAR_API FSCARVisionBodyPoseBridge
{
public:
	static constexpr int32 MaxBodies = 8;
	static constexpr int32 JointCount = 19;
	static constexpr int32 BodyStride = 5 + JointCount * 3;

	static bool IsSupported();
	static int32 DetectFromRgba(
		const uint8* RgbaBytes,
		int32 Width,
		int32 Height,
		int32 Orientation,
		float MinConfidence,
		TArray<float>& OutBuffer,
		int32 InMaxBodies,
		int32 InMaxJoints);
};
