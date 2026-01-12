"""API routes package"""
from fastapi import APIRouter
from .voice import router as voice_router
from .avatar import router as avatar_router
from .chat import router as chat_router
from .manual import router as manual_router

api_router = APIRouter()

api_router.include_router(voice_router, prefix="/voice", tags=["Voice"])
api_router.include_router(avatar_router, prefix="/avatar", tags=["Avatar"])
api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
api_router.include_router(manual_router, prefix="/manual", tags=["Manual"])
