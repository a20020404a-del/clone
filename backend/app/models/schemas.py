"""Pydantic schemas for API request/response models"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


# Enums
class ProcessingStatus(str, Enum):
    """Status of async processing tasks"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ChatMode(str, Enum):
    """Chat interaction modes"""
    AUTO = "auto"  # AI auto-response
    MANUAL = "manual"  # User-defined text


# Voice Models
class VoiceUploadResponse(BaseModel):
    """Response after uploading voice sample"""
    voice_id: str
    filename: str
    duration: float
    status: ProcessingStatus = ProcessingStatus.PENDING
    message: str = "Voice sample uploaded successfully"


class VoiceCloneRequest(BaseModel):
    """Request to create voice clone"""
    voice_id: str
    name: Optional[str] = "My Clone"
    description: Optional[str] = None


class VoiceCloneResponse(BaseModel):
    """Response after voice cloning"""
    clone_id: str
    voice_id: str
    status: ProcessingStatus
    message: str


class VoiceSynthesizeRequest(BaseModel):
    """Request to synthesize speech"""
    clone_id: str
    text: str = Field(..., min_length=1, max_length=5000)
    stability: float = Field(default=0.5, ge=0, le=1)
    similarity_boost: float = Field(default=0.75, ge=0, le=1)


class VoiceSynthesizeResponse(BaseModel):
    """Response after speech synthesis"""
    audio_id: str
    clone_id: str
    text: str
    audio_url: str
    duration: float
    status: ProcessingStatus


# Avatar Models
class ImageUploadResponse(BaseModel):
    """Response after uploading reference image"""
    image_id: str
    filename: str
    width: int
    height: int
    face_detected: bool
    status: ProcessingStatus = ProcessingStatus.COMPLETED
    message: str = "Image uploaded successfully"


class AvatarGenerateRequest(BaseModel):
    """Request to generate avatar video"""
    image_id: str
    audio_id: str
    expression_scale: float = Field(default=1.0, ge=0.5, le=2.0)


class AvatarGenerateResponse(BaseModel):
    """Response after avatar generation"""
    video_id: str
    image_id: str
    audio_id: str
    status: ProcessingStatus
    progress: int = 0
    message: str


class AvatarStatusResponse(BaseModel):
    """Status of avatar generation"""
    video_id: str
    status: ProcessingStatus
    progress: int
    video_url: Optional[str] = None
    error: Optional[str] = None


# Chat Models
class ChatMessage(BaseModel):
    """Single chat message"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    audio_url: Optional[str] = None
    video_url: Optional[str] = None


class ChatRequest(BaseModel):
    """Request for chat interaction"""
    message: str = Field(..., min_length=1, max_length=2000)
    clone_id: str
    image_id: str
    conversation_id: Optional[str] = None
    generate_video: bool = True


class ChatResponse(BaseModel):
    """Response from chat"""
    conversation_id: str
    message: ChatMessage
    response: ChatMessage
    video_id: Optional[str] = None
    status: ProcessingStatus


class ChatHistoryResponse(BaseModel):
    """Conversation history"""
    conversation_id: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime


# Manual Input Models
class ManualSpeakRequest(BaseModel):
    """Request for manual speech"""
    text: str = Field(..., min_length=1, max_length=5000)
    clone_id: str
    image_id: str
    preview_only: bool = False  # If true, only generate audio


class ManualSpeakResponse(BaseModel):
    """Response for manual speech"""
    task_id: str
    text: str
    clone_id: str
    image_id: str
    status: ProcessingStatus
    audio_url: Optional[str] = None
    video_url: Optional[str] = None


# Session Models
class SessionCreate(BaseModel):
    """Create a new avatar session"""
    name: Optional[str] = "My Avatar"


class SessionResponse(BaseModel):
    """Avatar session info"""
    session_id: str
    name: str
    voice_id: Optional[str] = None
    clone_id: Optional[str] = None
    image_id: Optional[str] = None
    is_ready: bool = False
    created_at: datetime
    updated_at: datetime


# Error Models
class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


# Health Check
class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str
    services: dict
