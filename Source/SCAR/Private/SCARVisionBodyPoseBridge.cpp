#include "SCARVisionBodyPoseBridge.h"

#if PLATFORM_IOS && !UE_EDITOR
extern "C" int SCARVisionDetectHumanBodyPose2D(
	const uint8* rgbaBytes,
	int width,
	int height,
	int orientation,
	float minConfidence,
	float* output,
	int outputFloatCount,
	int maxBodies,
	int maxJoints);
#endif

bool FSCARVisionBodyPoseBridge::IsSupported()
{
#if PLATFORM_IOS && !UE_EDITOR
	return true;
#else
	return false;
#endif
}

int32 FSCARVisionBodyPoseBridge::DetectFromRgba(
	const uint8* RgbaBytes,
	const int32 Width,
	const int32 Height,
	const int32 Orientation,
	const float MinConfidence,
	TArray<float>& OutBuffer,
	const int32 InMaxBodies,
	const int32 InMaxJoints)
{
#if PLATFORM_IOS && !UE_EDITOR
	const int32 OutputFloatCount = InMaxBodies * BodyStride;
	OutBuffer.SetNumZeroed(OutputFloatCount);

	return SCARVisionDetectHumanBodyPose2D(
		RgbaBytes,
		Width,
		Height,
		Orientation,
		MinConfidence,
		OutBuffer.GetData(),
		OutputFloatCount,
		InMaxBodies,
		InMaxJoints);
#else
	(void)RgbaBytes;
	(void)Width;
	(void)Height;
	(void)Orientation;
	(void)MinConfidence;
	(void)OutBuffer;
	(void)InMaxBodies;
	(void)InMaxJoints;
	return 0;
#endif
}
