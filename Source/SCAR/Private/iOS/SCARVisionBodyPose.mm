#import <CoreGraphics/CoreGraphics.h>
#import <CoreImage/CoreImage.h>
#import <CoreVideo/CoreVideo.h>
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

static int SCARVisionWriteObservationsToOutput(
	NSArray<VNHumanBodyPoseObservation *> *Observations,
	const float MinConfidence,
	float *Output,
	const int OutputFloatCount,
	const int MaxBodies,
	const int MaxJoints)
{
	const int JointCount = MIN(MaxJoints, kJointCount);
	const int BodyStride = 5 + MaxJoints * 3;
	if (OutputFloatCount < BodyStride)
	{
		return 0;
	}

	NSArray<VNHumanBodyPoseObservationJointName> *JointNames = SCARVisionJointNames();
	int Written = 0;

	for (VNHumanBodyPoseObservation *Observation in Observations)
	{
		if (Written >= MaxBodies)
		{
			break;
		}

		const int Offset = Written * BodyStride;
		if (Offset + BodyStride > OutputFloatCount)
		{
			break;
		}

		float MinX = 1.0f;
		float MinY = 1.0f;
		float MaxX = 0.0f;
		float MaxY = 0.0f;
		float ConfidenceSum = 0.0f;
		int TrackedCount = 0;

		for (int Joint = 0; Joint < MaxJoints; Joint++)
		{
			const int JointOffset = Offset + 5 + Joint * 3;
			Output[JointOffset] = -1.0f;
			Output[JointOffset + 1] = -1.0f;
			Output[JointOffset + 2] = 0.0f;
		}

		for (int Joint = 0; Joint < JointCount; Joint++)
		{
			NSError *PointError = nil;
			VNRecognizedPoint *Point = [Observation recognizedPointForJointName:JointNames[Joint] error:&PointError];
			if (PointError != nil || Point == nil || Point.confidence < MinConfidence)
			{
				continue;
			}

			const float X = (float)Point.location.x;
			const float Y = (float)Point.location.y;
			const int JointOffset = Offset + 5 + Joint * 3;
			Output[JointOffset] = X;
			Output[JointOffset + 1] = Y;
			Output[JointOffset + 2] = (float)Point.confidence;

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

		Output[Offset] = ConfidenceSum / TrackedCount;
		Output[Offset + 1] = MAX(0.0f, MinX);
		Output[Offset + 2] = MAX(0.0f, MinY);
		Output[Offset + 3] = MIN(1.0f, MaxX);
		Output[Offset + 4] = MIN(1.0f, MaxY);
		Written++;
	}

	return Written;
}

static int SCARVisionPerformPixelBufferRequest(
	CVPixelBufferRef PixelBuffer,
	const int Orientation,
	const float MinConfidence,
	float *Output,
	const int OutputFloatCount,
	const int MaxBodies,
	const int MaxJoints)
{
	if (@available(iOS 14.0, *))
	{
		if (PixelBuffer == NULL || Output == NULL || MaxBodies <= 0)
		{
			return 0;
		}

		VNDetectHumanBodyPoseRequest *Request = [[VNDetectHumanBodyPoseRequest alloc] init];
		VNImageRequestHandler *Handler = [[VNImageRequestHandler alloc]
			initWithCVPixelBuffer:PixelBuffer
			orientation:(CGImagePropertyOrientation)Orientation
			options:@{}];

		NSError *Error = nil;
		const BOOL Ok = [Handler performRequests:@[Request] error:&Error];
		if (!Ok || Error != nil)
		{
			return 0;
		}

		return SCARVisionWriteObservationsToOutput(
			Request.results,
			MinConfidence,
			Output,
			OutputFloatCount,
			MaxBodies,
			MaxJoints);
	}

	return 0;
}

static int SCARVisionPerformCGImageRequest(
	CGImageRef Image,
	const int Orientation,
	const float MinConfidence,
	float *Output,
	const int OutputFloatCount,
	const int MaxBodies,
	const int MaxJoints)
{
	if (@available(iOS 14.0, *))
	{
		if (Image == NULL || Output == NULL || MaxBodies <= 0)
		{
			return 0;
		}

		VNDetectHumanBodyPoseRequest *Request = [[VNDetectHumanBodyPoseRequest alloc] init];
		VNImageRequestHandler *Handler = [[VNImageRequestHandler alloc]
			initWithCGImage:Image
			orientation:(CGImagePropertyOrientation)Orientation
			options:@{}];

		NSError *Error = nil;
		const BOOL Ok = [Handler performRequests:@[Request] error:&Error];
		if (!Ok || Error != nil)
		{
			return 0;
		}

		return SCARVisionWriteObservationsToOutput(
			Request.results,
			MinConfidence,
			Output,
			OutputFloatCount,
			MaxBodies,
			MaxJoints);
	}

	return 0;
}

extern "C" int SCARVisionDetectHumanBodyPose2DFromPixelBuffer(
	void *PixelBuffer,
	int Orientation,
	float MinConfidence,
	float *Output,
	int OutputFloatCount,
	int MaxBodies,
	int MaxJoints)
{
	SCARVisionClearOutput(Output, OutputFloatCount);
	if (PixelBuffer == NULL)
	{
		return 0;
	}

	return SCARVisionPerformPixelBufferRequest(
		static_cast<CVPixelBufferRef>(PixelBuffer),
		Orientation,
		MinConfidence,
		Output,
		OutputFloatCount,
		MaxBodies,
		MaxJoints);
}

extern "C" int SCARVisionDetectHumanBodyPose2D(
	const uint8_t *RgbaBytes,
	int Width,
	int Height,
	int Orientation,
	float MinConfidence,
	float *Output,
	int OutputFloatCount,
	int MaxBodies,
	int MaxJoints)
{
	SCARVisionClearOutput(Output, OutputFloatCount);

	if (RgbaBytes == NULL || Width <= 0 || Height <= 0 || MaxBodies <= 0)
	{
		return 0;
	}

	CGDataProviderRef Provider = CGDataProviderCreateWithData(NULL, RgbaBytes, Width * Height * 4, NULL);
	if (Provider == NULL)
	{
		return 0;
	}

	CGColorSpaceRef ColorSpace = CGColorSpaceCreateDeviceRGB();
	const CGBitmapInfo BitmapInfo = kCGBitmapByteOrder32Big | kCGImageAlphaPremultipliedLast;
	CGImageRef Image = CGImageCreate(
		Width,
		Height,
		8,
		32,
		Width * 4,
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

	const int Written = SCARVisionPerformCGImageRequest(
		Image,
		Orientation,
		MinConfidence,
		Output,
		OutputFloatCount,
		MaxBodies,
		MaxJoints);

	CGImageRelease(Image);
	return Written;
}

/** Unity parity: downscale AR camera frame to max dimension, convert to CGImage, run Vision on RGBA. */
extern "C" int SCARVisionDetectHumanBodyPose2DFromPixelBufferDownscaled(
	void *PixelBuffer,
	int MaxImageDimension,
	int Orientation,
	float MinConfidence,
	float *Output,
	int OutputFloatCount,
	int MaxBodies,
	int MaxJoints)
{
	SCARVisionClearOutput(Output, OutputFloatCount);
	if (PixelBuffer == NULL || MaxImageDimension <= 0)
	{
		return 0;
	}

	CVPixelBufferRef Buffer = static_cast<CVPixelBufferRef>(PixelBuffer);
	const size_t SourceWidth = CVPixelBufferGetWidth(Buffer);
	const size_t SourceHeight = CVPixelBufferGetHeight(Buffer);
	if (SourceWidth == 0 || SourceHeight == 0)
	{
		return 0;
	}

	const float MaxSource = static_cast<float>(MAX(SourceWidth, SourceHeight));
	const float Scale = MaxSource <= static_cast<float>(MaxImageDimension)
		? 1.0f
		: static_cast<float>(MaxImageDimension) / MaxSource;

	CIImage *SourceImage = [CIImage imageWithCVPixelBuffer:Buffer];
	if (SourceImage == nil)
	{
		return 0;
	}

	CIImage *ScaledImage = SourceImage;
	if (Scale < 0.999f)
	{
		CIFilter *ScaleFilter = [CIFilter filterWithName:@"CILanczosScaleTransform"];
		if (ScaleFilter != nil)
		{
			[ScaleFilter setValue:SourceImage forKey:kCIInputImageKey];
			[ScaleFilter setValue:@(Scale) forKey:kCIInputScaleKey];
			[ScaleFilter setValue:@(1.0) forKey:kCIInputAspectRatioKey];
			ScaledImage = ScaleFilter.outputImage;
		}
	}

	if (ScaledImage == nil)
	{
		return 0;
	}

	static CIContext *SharedContext = nil;
	static dispatch_once_t ContextOnce;
	dispatch_once(&ContextOnce, ^{
		SharedContext = [CIContext contextWithOptions:@{kCIContextUseSoftwareRenderer : @NO}];
	});

	const CGRect Extent = ScaledImage.extent;
	CGImageRef Image = [SharedContext createCGImage:ScaledImage fromRect:Extent];
	if (Image == NULL)
	{
		return 0;
	}

	const int Written = SCARVisionPerformCGImageRequest(
		Image,
		Orientation,
		MinConfidence,
		Output,
		OutputFloatCount,
		MaxBodies,
		MaxJoints);

	CGImageRelease(Image);
	return Written;
}
