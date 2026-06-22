#import <CoreGraphics/CoreGraphics.h>
#import <Foundation/Foundation.h>
#import <ImageIO/ImageIO.h>
#import <Vision/Vision.h>

static const int kJointCount = 19;

static NSArray<VNHumanBodyPoseObservationJointName> *SCARVisionJointNames(void)
{
	static NSArray<VNHumanBodyPoseObservationJointName> *Names = nil;
	static dispatch_once_t OnceToken;
	dispatch_once(&OnceToken, ^{
		Names = @[
			VNHumanBodyPoseObservationJointNameNose,
			VNHumanBodyPoseObservationJointNameLeftEye,
			VNHumanBodyPoseObservationJointNameRightEye,
			VNHumanBodyPoseObservationJointNameLeftEar,
			VNHumanBodyPoseObservationJointNameRightEar,
			VNHumanBodyPoseObservationJointNameLeftShoulder,
			VNHumanBodyPoseObservationJointNameRightShoulder,
			VNHumanBodyPoseObservationJointNameNeck,
			VNHumanBodyPoseObservationJointNameLeftElbow,
			VNHumanBodyPoseObservationJointNameRightElbow,
			VNHumanBodyPoseObservationJointNameLeftWrist,
			VNHumanBodyPoseObservationJointNameRightWrist,
			VNHumanBodyPoseObservationJointNameLeftHip,
			VNHumanBodyPoseObservationJointNameRightHip,
			VNHumanBodyPoseObservationJointNameRoot,
			VNHumanBodyPoseObservationJointNameLeftKnee,
			VNHumanBodyPoseObservationJointNameRightKnee,
			VNHumanBodyPoseObservationJointNameLeftAnkle,
			VNHumanBodyPoseObservationJointNameRightAnkle
		];
	});
	return Names;
}

static void SCARVisionClearOutput(float *Output, int OutputFloatCount)
{
	if (Output == NULL || OutputFloatCount <= 0)
	{
		return;
	}

	for (int Index = 0; Index < OutputFloatCount; Index++)
	{
		Output[Index] = 0.0f;
	}
}

extern "C" int SCARVisionDetectHumanBodyPose2D(
	const uint8_t *rgbaBytes,
	int width,
	int height,
	int orientation,
	float minConfidence,
	float *output,
	int outputFloatCount,
	int maxBodies,
	int maxJoints)
{
	SCARVisionClearOutput(output, outputFloatCount);

	if (@available(iOS 14.0, *))
	{
		if (rgbaBytes == NULL || output == NULL || width <= 0 || height <= 0 || maxBodies <= 0)
		{
			return 0;
		}

		const int jointCount = MIN(maxJoints, kJointCount);
		const int bodyStride = 5 + maxJoints * 3;
		if (outputFloatCount < bodyStride)
		{
			return 0;
		}

		CGDataProviderRef Provider = CGDataProviderCreateWithData(NULL, rgbaBytes, width * height * 4, NULL);
		if (Provider == NULL)
		{
			return 0;
		}

		CGColorSpaceRef ColorSpace = CGColorSpaceCreateDeviceRGB();
		const CGBitmapInfo BitmapInfo = kCGBitmapByteOrder32Big | kCGImageAlphaPremultipliedLast;
		CGImageRef Image = CGImageCreate(
			width,
			height,
			8,
			32,
			width * 4,
			ColorSpace,
			BitmapInfo,
			Provider,
			NULL,
			false,
			kCGRenderingIntentDefault);

		CGColorSpaceRelease(ColorSpace);
		CGDataProviderRelease(Provider);

		if (Image == NULL)
		{
			return 0;
		}

		VNDetectHumanBodyPoseRequest *Request = [[VNDetectHumanBodyPoseRequest alloc] init];
		VNImageRequestHandler *Handler = [[VNImageRequestHandler alloc]
			initWithCGImage:Image
			orientation:(CGImagePropertyOrientation)orientation
			options:@{}];

		NSError *Error = nil;
		const BOOL Ok = [Handler performRequests:@[Request] error:&Error];
		CGImageRelease(Image);

		if (!Ok || Error != nil)
		{
			return 0;
		}

		NSArray<VNHumanBodyPoseObservation *> *Observations = Request.results;
		NSArray<VNHumanBodyPoseObservationJointName> *JointNames = SCARVisionJointNames();

		int Written = 0;
		for (VNHumanBodyPoseObservation *Observation in Observations)
		{
			if (Written >= maxBodies)
			{
				break;
			}

			const int Offset = Written * bodyStride;
			if (Offset + bodyStride > outputFloatCount)
			{
				break;
			}

			float MinX = 1.0f;
			float MinY = 1.0f;
			float MaxX = 0.0f;
			float MaxY = 0.0f;
			float ConfidenceSum = 0.0f;
			int TrackedCount = 0;

			for (int Joint = 0; Joint < maxJoints; Joint++)
			{
				const int JointOffset = Offset + 5 + Joint * 3;
				output[JointOffset] = -1.0f;
				output[JointOffset + 1] = -1.0f;
				output[JointOffset + 2] = 0.0f;
			}

			for (int Joint = 0; Joint < jointCount; Joint++)
			{
				NSError *PointError = nil;
				VNRecognizedPoint *Point = [Observation recognizedPointForJointName:JointNames[Joint] error:&PointError];
				if (PointError != nil || Point == nil || Point.confidence < minConfidence)
				{
					continue;
				}

				const float X = (float)Point.location.x;
				const float Y = (float)Point.location.y;
				const int JointOffset = Offset + 5 + Joint * 3;
				output[JointOffset] = X;
				output[JointOffset + 1] = Y;
				output[JointOffset + 2] = (float)Point.confidence;

				MinX = MIN(MinX, X);
				MinY = MIN(MinY, Y);
				MaxX = MAX(MaxX, X);
				MaxY = MAX(MaxY, Y);
				ConfidenceSum += (float)Point.confidence;
				TrackedCount++;
			}

			if (TrackedCount < 4)
			{
				continue;
			}

			output[Offset] = ConfidenceSum / TrackedCount;
			output[Offset + 1] = MAX(0.0f, MinX);
			output[Offset + 2] = MAX(0.0f, MinY);
			output[Offset + 3] = MIN(1.0f, MaxX);
			output[Offset + 4] = MIN(1.0f, MaxY);
			Written++;
		}

		return Written;
	}

	return 0;
}
