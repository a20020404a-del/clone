"""Chat API endpoints for auto-response mode"""
from fastapi import APIRouter, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import json
import asyncio

from ..models.schemas import (
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    ProcessingStatus,
    ErrorResponse
)
from ..services.llm import LLMService
from ..services.voice_clone import VoiceCloneService
from ..services.avatar_gen import AvatarGeneratorService
from ..services.stt import STTService
from ..utils.file_handler import FileHandler

router = APIRouter()

# Service instances
llm_service = LLMService()
voice_service = VoiceCloneService()
avatar_service = AvatarGeneratorService()
stt_service = STTService()
file_handler = FileHandler()


@router.post(
    "/message",
    response_model=ChatResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
)
async def send_message(request: ChatRequest):
    """
    Send a text message and get an AI response with avatar video.

    The response includes:
    - AI-generated text response
    - Synthesized audio using the cloned voice
    - Avatar video with lip-sync (if generate_video is True)
    """
    # Validate clone exists
    clone_status = await voice_service.get_clone_status(request.clone_id)
    if not clone_status:
        raise HTTPException(status_code=404, detail="Voice clone not found")

    # Validate image exists
    image_path = avatar_service.get_image_path(request.image_id)
    if not image_path:
        raise HTTPException(status_code=404, detail="Reference image not found")

    # Content filtering
    is_safe, filter_result = llm_service.filter_content(request.message)
    if not is_safe:
        raise HTTPException(status_code=400, detail=filter_result)

    # Generate AI response
    conversation_id, response_text, response_message = await llm_service.chat(
        request.message,
        request.conversation_id
    )

    video_id = None

    if request.generate_video:
        # Synthesize speech
        audio_id, audio_path, duration, audio_status, _ = await voice_service.synthesize_speech(
            request.clone_id,
            response_text
        )

        if audio_status == ProcessingStatus.COMPLETED:
            # Generate avatar video
            video_id, video_status, _ = await avatar_service.generate_avatar(
                request.image_id,
                image_path,
                audio_path
            )

            # Update response message with URLs
            response_message.audio_url = f"/api/v1/voice/audio/{audio_id}"
            if video_status == ProcessingStatus.COMPLETED:
                response_message.video_url = f"/api/v1/avatar/{video_id}/video"

    # Create user message for response
    from ..models.schemas import ChatMessage
    from datetime import datetime

    user_message = ChatMessage(
        role="user",
        content=request.message,
        timestamp=datetime.utcnow()
    )

    return ChatResponse(
        conversation_id=conversation_id,
        message=user_message,
        response=response_message,
        video_id=video_id,
        status=ProcessingStatus.COMPLETED
    )


@router.post("/voice")
async def send_voice_message(
    file: UploadFile = File(...),
    clone_id: str = None,
    image_id: str = None,
    conversation_id: str = None,
    generate_video: bool = True
):
    """
    Send a voice message and get an AI response.

    The voice is transcribed to text, processed by AI,
    and the response is synthesized back to speech.
    """
    # Save uploaded audio
    content = await file.read()
    voice_id, audio_path = await file_handler.save_upload_file(content, file.filename, "voice")

    # Transcribe voice to text
    transcription, confidence, msg = await stt_service.transcribe(audio_path)

    if not transcription:
        raise HTTPException(status_code=400, detail=f"Could not transcribe audio: {msg}")

    # Process as regular message
    request = ChatRequest(
        message=transcription,
        clone_id=clone_id,
        image_id=image_id,
        conversation_id=conversation_id,
        generate_video=generate_video
    )

    response = await send_message(request)

    # Add transcription info
    return {
        **response.dict(),
        "transcription": transcription,
        "transcription_confidence": confidence
    }


@router.websocket("/stream")
async def chat_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat streaming.

    Messages should be JSON with format:
    {
        "message": "user message",
        "clone_id": "voice clone id",
        "image_id": "reference image id",
        "conversation_id": "optional conversation id"
    }
    """
    await websocket.accept()

    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            request_data = json.loads(data)

            message = request_data.get("message", "")
            clone_id = request_data.get("clone_id")
            image_id = request_data.get("image_id")
            conversation_id = request_data.get("conversation_id")

            # Content filtering
            is_safe, filter_result = llm_service.filter_content(message)
            if not is_safe:
                await websocket.send_json({
                    "type": "error",
                    "error": filter_result
                })
                continue

            # Send acknowledgment
            await websocket.send_json({
                "type": "ack",
                "message": message
            })

            # Stream AI response
            full_response = ""
            async for chunk in llm_service.stream_chat(message, conversation_id):
                full_response += chunk
                await websocket.send_json({
                    "type": "chunk",
                    "content": chunk
                })

            # Generate audio and video
            if clone_id and image_id:
                await websocket.send_json({
                    "type": "status",
                    "status": "generating_audio"
                })

                # Synthesize speech
                audio_id, audio_path, duration, audio_status, _ = await voice_service.synthesize_speech(
                    clone_id,
                    full_response
                )

                if audio_status == ProcessingStatus.COMPLETED:
                    await websocket.send_json({
                        "type": "audio",
                        "audio_url": f"/api/v1/voice/audio/{audio_id}",
                        "duration": duration
                    })

                    # Generate avatar video
                    image_path = avatar_service.get_image_path(image_id)
                    if image_path:
                        await websocket.send_json({
                            "type": "status",
                            "status": "generating_video"
                        })

                        video_id, video_status, _ = await avatar_service.generate_avatar(
                            image_id,
                            image_path,
                            audio_path
                        )

                        if video_status == ProcessingStatus.COMPLETED:
                            await websocket.send_json({
                                "type": "video",
                                "video_url": f"/api/v1/avatar/{video_id}/video",
                                "video_id": video_id
                            })

            # Send completion
            await websocket.send_json({
                "type": "complete",
                "response": full_response
            })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })


@router.get(
    "/history/{conversation_id}",
    response_model=ChatHistoryResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_chat_history(conversation_id: str):
    """
    Get conversation history.
    """
    history = await llm_service.get_conversation_history(conversation_id)
    if not history:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ChatHistoryResponse(**history)


@router.delete("/history/{conversation_id}")
async def clear_chat_history(conversation_id: str):
    """
    Clear conversation history.
    """
    success = await llm_service.clear_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"status": "cleared", "conversation_id": conversation_id}


@router.post("/conversation")
async def create_conversation(persona: str = None):
    """
    Create a new conversation session.
    """
    conversation_id = await llm_service.create_conversation(persona)
    return {
        "conversation_id": conversation_id,
        "persona": persona,
        "status": "created"
    }
