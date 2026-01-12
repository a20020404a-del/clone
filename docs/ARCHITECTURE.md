# AI Avatar System - Architecture Design

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │  Upload  │  │  Avatar  │  │   Chat   │  │  Manual Input    │ │
│  │  Panel   │  │  Display │  │Interface │  │     Panel        │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘ │
└───────┼─────────────┼─────────────┼──────────────────┼──────────┘
        │             │             │                  │
        ▼             ▼             ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (FastAPI)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ /upload  │  │ /avatar  │  │  /chat   │  │    /manual       │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘ │
└───────┼─────────────┼─────────────┼──────────────────┼──────────┘
        │             │             │                  │
        ▼             ▼             ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Services Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Voice Clone  │  │   Avatar     │  │    LLM Service       │   │
│  │   Service    │  │  Generator   │  │  (Claude/GPT-4)      │   │
│  │ (ElevenLabs) │  │  (SadTalker) │  │                      │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Voice Cloning**: ElevenLabs API (primary), OpenVoice (fallback)
- **Avatar Generation**: SadTalker / Wav2Lip
- **LLM**: Claude API (Anthropic)
- **Speech-to-Text**: OpenAI Whisper
- **Task Queue**: Celery + Redis (for async processing)

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Video Player**: react-player
- **API Client**: Axios + React Query

### Infrastructure
- **Storage**: Local filesystem / S3-compatible
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Cache**: Redis

## API Endpoints

### Voice Service
```
POST /api/v1/voice/upload          # Upload voice sample (20s audio)
POST /api/v1/voice/clone           # Create voice clone
POST /api/v1/voice/synthesize      # Text-to-Speech with cloned voice
GET  /api/v1/voice/{id}/status     # Check cloning status
```

### Avatar Service
```
POST /api/v1/avatar/upload-image   # Upload reference image
POST /api/v1/avatar/generate       # Generate talking avatar video
GET  /api/v1/avatar/{id}/status    # Check generation status
GET  /api/v1/avatar/{id}/video     # Download generated video
```

### Chat Service (Auto-response mode)
```
POST /api/v1/chat/message          # Send text message
POST /api/v1/chat/voice            # Send voice message
WS   /api/v1/chat/stream           # Real-time streaming
GET  /api/v1/chat/history          # Get conversation history
```

### Manual Input Service
```
POST /api/v1/manual/speak          # Make avatar speak custom text
GET  /api/v1/manual/{id}/status    # Check processing status
GET  /api/v1/manual/{id}/video     # Get generated video
```

## Data Flow

### 1. Initial Setup Flow
```
User → Upload Voice (20s) → Voice Cloning Service → Store Voice Model
User → Upload Photo → Face Detection → Store Reference Image
```

### 2. Auto-response Mode Flow
```
User Input (Text/Voice)
    → STT (if voice)
    → LLM (Claude)
    → TTS (Cloned Voice)
    → Avatar Generation
    → Video Output
```

### 3. Manual Input Mode Flow
```
User Text Input
    → TTS (Cloned Voice)
    → Avatar Generation
    → Video Output
```

## File Structure

```
clone/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Configuration
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── voice.py         # Voice endpoints
│   │   │   ├── avatar.py        # Avatar endpoints
│   │   │   ├── chat.py          # Chat endpoints
│   │   │   └── manual.py        # Manual input endpoints
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── voice_clone.py   # Voice cloning logic
│   │   │   ├── avatar_gen.py    # Avatar generation logic
│   │   │   ├── llm.py           # LLM integration
│   │   │   └── stt.py           # Speech-to-Text
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py       # Pydantic models
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── file_handler.py  # File utilities
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── UploadPanel.tsx
│   │   │   ├── AvatarDisplay.tsx
│   │   │   ├── ChatInterface.tsx
│   │   │   └── ManualInput.tsx
│   │   ├── hooks/
│   │   │   └── useAvatar.ts
│   │   ├── services/
│   │   │   └── api.ts
│   │   └── types/
│   │       └── index.ts
│   ├── package.json
│   └── Dockerfile
├── docs/
│   └── ARCHITECTURE.md
└── docker-compose.yml
```

## Security Considerations

1. **Input Validation**: Strict file type/size validation
2. **Rate Limiting**: Prevent abuse of API endpoints
3. **Content Filtering**: Filter inappropriate content via LLM
4. **Authentication**: JWT-based authentication (future)
5. **CORS**: Proper CORS configuration

## Performance Optimization

1. **Async Processing**: Use background tasks for video generation
2. **Caching**: Cache generated videos for repeated requests
3. **Streaming**: Stream video generation progress
4. **CDN**: Use CDN for video delivery (production)
