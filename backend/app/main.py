"""AI Avatar System - FastAPI Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .config import get_settings, init_directories
from .api import api_router
from .models.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    init_directories()
    print("🚀 AI Avatar System starting...")
    yield
    # Shutdown
    print("👋 AI Avatar System shutting down...")


# Create FastAPI app
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    AI自動生成アバターシステム API

    ## 機能

    * **音声クローン**: 20秒の音声サンプルから声をクローン
    * **アバター生成**: 写真と音声からリップシンク動画を生成
    * **自動応答モード**: AIが質問に自動で応答
    * **手動入力モード**: 任意のテキストを喋らせる

    ## 使い方

    1. 音声サンプルをアップロード (`/api/v1/voice/upload`)
    2. 音声クローンを作成 (`/api/v1/voice/clone`)
    3. 参照画像をアップロード (`/api/v1/avatar/upload-image`)
    4. 自動応答 (`/api/v1/chat/message`) または手動入力 (`/api/v1/manual/speak`)
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check API health and service status"""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        services={
            "voice_clone": "available" if settings.elevenlabs_api_key else "demo_mode",
            "llm": "available" if settings.anthropic_api_key else "demo_mode",
            "stt": "available" if settings.openai_api_key else "demo_mode",
            "avatar_gen": "available"
        }
    )


@app.get("/", tags=["Root"])
async def root():
    """API root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


# Mount static files for uploads and outputs (development only)
if settings.debug:
    app.mount("/uploads", StaticFiles(directory=str(settings.upload_dir)), name="uploads")
    app.mount("/outputs", StaticFiles(directory=str(settings.output_dir)), name="outputs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
