"""Voice API endpoints"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from pathlib import Path

from ..models.schemas import (
    VoiceUploadResponse,
    VoiceCloneRequest,
    VoiceCloneResponse,
    VoiceSynthesizeRequest,
    VoiceSynthesizeResponse,
    ProcessingStatus,
    ErrorResponse
)
from ..services.voice_clone import VoiceCloneService
from ..utils.file_handler import FileHandler

router = APIRouter()

# Service instances
voice_service = VoiceCloneService()
file_handler = FileHandler()


@router.post(
    "/upload",
    response_model=VoiceUploadResponse,
    responses={400: {"model": ErrorResponse}}
)
async def upload_voice_sample(
    file: UploadFile = File(..., description="Voice sample audio file (10-300 seconds)")
):
    """
    Upload a voice sample for cloning.

    The audio file should be:
    - At least 10 seconds long (20+ seconds recommended)
    - Clear speech with minimal background noise
    - Supported formats: MP3, WAV, M4A, OGG
    """
    # Validate file type
    is_valid, msg = file_handler.validate_file_type(file.filename, "voice")
    if not is_valid:
        raise HTTPException(status_code=400, detail=msg)

    # Read file content
    content = await file.read()

    # Validate file size
    is_valid, msg = file_handler.validate_file_size(len(content), "voice")
    if not is_valid:
        raise HTTPException(status_code=400, detail=msg)

    # Save the file
    voice_id, file_path = await voice_service.save_upload(content, file.filename)

    # Validate audio
    is_valid, duration, msg = await voice_service.validate_audio(file_path)
    if not is_valid:
        # Clean up invalid file
        await file_handler.delete_file(file_path)
        raise HTTPException(status_code=400, detail=msg)

    return VoiceUploadResponse(
        voice_id=voice_id,
        filename=file.filename,
        duration=duration,
        status=ProcessingStatus.COMPLETED,
        message=msg
    )


@router.post(
    "/clone",
    response_model=VoiceCloneResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
)
async def create_voice_clone(request: VoiceCloneRequest):
    """
    Create a voice clone from an uploaded sample.

    This process may take a few moments depending on the service used.
    """
    # Get the uploaded file
    file_path = await file_handler.get_file(request.voice_id, "voice")
    if not file_path:
        raise HTTPException(status_code=404, detail="Voice sample not found")

    # Create the clone
    clone_id, status, message = await voice_service.create_clone(
        request.voice_id,
        file_path,
        request.name,
        request.description
    )

    if status == ProcessingStatus.FAILED:
        raise HTTPException(status_code=400, detail=message)

    return VoiceCloneResponse(
        clone_id=clone_id,
        voice_id=request.voice_id,
        status=status,
        message=message
    )


@router.post(
    "/synthesize",
    response_model=VoiceSynthesizeResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
)
async def synthesize_speech(request: VoiceSynthesizeRequest):
    """
    Synthesize speech using a cloned voice.

    Converts text to speech using the specified voice clone.
    """
    # Check if clone exists
    clone_status = await voice_service.get_clone_status(request.clone_id)
    if not clone_status:
        raise HTTPException(status_code=404, detail="Voice clone not found")

    # Synthesize speech
    audio_id, audio_path, duration, status, message = await voice_service.synthesize_speech(
        request.clone_id,
        request.text,
        request.stability,
        request.similarity_boost
    )

    if status == ProcessingStatus.FAILED:
        raise HTTPException(status_code=400, detail=message)

    return VoiceSynthesizeResponse(
        audio_id=audio_id,
        clone_id=request.clone_id,
        text=request.text,
        audio_url=f"/api/v1/voice/audio/{audio_id}",
        duration=duration,
        status=status
    )


@router.get("/audio/{audio_id}")
async def get_audio_file(audio_id: str):
    """
    Download synthesized audio file.
    """
    audio_path = await file_handler.get_output_file(audio_id, "voice")
    if not audio_path:
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(
        audio_path,
        media_type="audio/mpeg",
        filename=f"{audio_id}.mp3"
    )


@router.get("/{voice_id}/status")
async def get_voice_status(voice_id: str):
    """
    Get status of a voice sample or clone.
    """
    # Check if it's a clone ID
    clone_status = await voice_service.get_clone_status(voice_id)
    if clone_status:
        return clone_status

    # Check if it's a voice sample
    file_path = await file_handler.get_file(voice_id, "voice")
    if file_path:
        return {
            "voice_id": voice_id,
            "status": ProcessingStatus.COMPLETED,
            "file_exists": True
        }

    raise HTTPException(status_code=404, detail="Voice not found")


@router.get("/clones")
async def list_voice_clones():
    """
    List all available voice clones.
    """
    clones = await voice_service.list_clones()
    return {"clones": clones}


@router.delete("/{clone_id}")
async def delete_voice_clone(clone_id: str):
    """
    Delete a voice clone.
    """
    success = await voice_service.delete_clone(clone_id)
    if not success:
        raise HTTPException(status_code=404, detail="Clone not found or could not be deleted")

    return {"status": "deleted", "clone_id": clone_id}
