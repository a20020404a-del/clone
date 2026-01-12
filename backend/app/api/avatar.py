"""Avatar API endpoints"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path

from ..models.schemas import (
    ImageUploadResponse,
    AvatarGenerateRequest,
    AvatarGenerateResponse,
    AvatarStatusResponse,
    ProcessingStatus,
    ErrorResponse
)
from ..services.avatar_gen import AvatarGeneratorService
from ..utils.file_handler import FileHandler

router = APIRouter()

# Service instances
avatar_service = AvatarGeneratorService()
file_handler = FileHandler()


@router.post(
    "/upload-image",
    response_model=ImageUploadResponse,
    responses={400: {"model": ErrorResponse}}
)
async def upload_reference_image(
    file: UploadFile = File(..., description="Reference image with a clear face")
):
    """
    Upload a reference image for avatar generation.

    The image should be:
    - A clear, front-facing photo
    - Minimum 256x256 pixels
    - Supported formats: JPG, PNG
    """
    # Validate file type
    is_valid, msg = file_handler.validate_file_type(file.filename, "image")
    if not is_valid:
        raise HTTPException(status_code=400, detail=msg)

    # Read file content
    content = await file.read()

    # Validate file size
    is_valid, msg = file_handler.validate_file_size(len(content), "image")
    if not is_valid:
        raise HTTPException(status_code=400, detail=msg)

    # Save the file
    image_id, file_path = await avatar_service.save_upload(content, file.filename)

    # Validate image
    is_valid, metadata, msg = await avatar_service.validate_image(file_path)
    if not is_valid:
        await file_handler.delete_file(file_path)
        raise HTTPException(status_code=400, detail=msg)

    # Preprocess image
    processed_path, process_metadata = await avatar_service.preprocess_image(file_path, image_id)

    # Register the image
    avatar_service.register_image(image_id, processed_path, {**metadata, **process_metadata})

    return ImageUploadResponse(
        image_id=image_id,
        filename=file.filename,
        width=metadata.get("width", 0),
        height=metadata.get("height", 0),
        face_detected=metadata.get("face_detected", False),
        status=ProcessingStatus.COMPLETED,
        message=msg
    )


@router.post(
    "/generate",
    response_model=AvatarGenerateResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
)
async def generate_avatar(
    request: AvatarGenerateRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate a talking avatar video.

    Combines the reference image with synthesized audio to create
    a lip-synced video of the avatar speaking.
    """
    # Get image path
    image_path = avatar_service.get_image_path(request.image_id)
    if not image_path:
        raise HTTPException(status_code=404, detail="Reference image not found")

    # Get audio path
    audio_path = await file_handler.get_output_file(request.audio_id, "voice")
    if not audio_path:
        raise HTTPException(status_code=404, detail="Audio file not found")

    # Start generation (this could be done in background for long processes)
    video_id, status, message = await avatar_service.generate_avatar(
        request.image_id,
        image_path,
        audio_path,
        request.expression_scale
    )

    return AvatarGenerateResponse(
        video_id=video_id,
        image_id=request.image_id,
        audio_id=request.audio_id,
        status=status,
        progress=0 if status == ProcessingStatus.PROCESSING else 100,
        message=message
    )


@router.get(
    "/{video_id}/status",
    response_model=AvatarStatusResponse
)
async def get_generation_status(video_id: str):
    """
    Get the status of avatar video generation.
    """
    task_status = await avatar_service.get_task_status(video_id)
    if not task_status:
        raise HTTPException(status_code=404, detail="Task not found")

    video_url = None
    if task_status["status"] == ProcessingStatus.COMPLETED:
        video_url = f"/api/v1/avatar/{video_id}/video"

    return AvatarStatusResponse(
        video_id=video_id,
        status=task_status["status"],
        progress=task_status.get("progress", 0),
        video_url=video_url,
        error=task_status.get("error")
    )


@router.get("/{video_id}/video")
async def get_video_file(video_id: str):
    """
    Download the generated avatar video.
    """
    video_path = await avatar_service.get_video_path(video_id)
    if not video_path:
        raise HTTPException(status_code=404, detail="Video not found or not ready")

    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=f"{video_id}.mp4"
    )


@router.get("/{image_id}/info")
async def get_image_info(image_id: str):
    """
    Get information about an uploaded image.
    """
    info = avatar_service.get_image_info(image_id)
    if not info:
        raise HTTPException(status_code=404, detail="Image not found")

    return {"image_id": image_id, **info}


@router.get("/{image_id}/preview")
async def get_image_preview(image_id: str):
    """
    Get the preprocessed image preview.
    """
    image_path = avatar_service.get_image_path(image_id)
    if not image_path:
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(
        image_path,
        media_type="image/png",
        filename=f"{image_id}.png"
    )
