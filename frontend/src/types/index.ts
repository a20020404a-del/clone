// Processing status enum
export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed';

// Chat mode enum
export type ChatMode = 'auto' | 'manual';

// Voice types
export interface VoiceUploadResponse {
  voice_id: string;
  filename: string;
  duration: number;
  status: ProcessingStatus;
  message: string;
}

export interface VoiceCloneRequest {
  voice_id: string;
  name?: string;
  description?: string;
}

export interface VoiceCloneResponse {
  clone_id: string;
  voice_id: string;
  status: ProcessingStatus;
  message: string;
}

export interface VoiceSynthesizeRequest {
  clone_id: string;
  text: string;
  stability?: number;
  similarity_boost?: number;
}

export interface VoiceSynthesizeResponse {
  audio_id: string;
  clone_id: string;
  text: string;
  audio_url: string;
  duration: number;
  status: ProcessingStatus;
}

// Avatar types
export interface ImageUploadResponse {
  image_id: string;
  filename: string;
  width: number;
  height: number;
  face_detected: boolean;
  status: ProcessingStatus;
  message: string;
}

export interface AvatarGenerateRequest {
  image_id: string;
  audio_id: string;
  expression_scale?: number;
}

export interface AvatarGenerateResponse {
  video_id: string;
  image_id: string;
  audio_id: string;
  status: ProcessingStatus;
  progress: number;
  message: string;
}

export interface AvatarStatusResponse {
  video_id: string;
  status: ProcessingStatus;
  progress: number;
  video_url?: string;
  error?: string;
}

// Chat types
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  audio_url?: string;
  video_url?: string;
}

export interface ChatRequest {
  message: string;
  clone_id: string;
  image_id: string;
  conversation_id?: string;
  generate_video?: boolean;
}

export interface ChatResponse {
  conversation_id: string;
  message: ChatMessage;
  response: ChatMessage;
  video_id?: string;
  status: ProcessingStatus;
}

// Manual input types
export interface ManualSpeakRequest {
  text: string;
  clone_id: string;
  image_id: string;
  preview_only?: boolean;
}

export interface ManualSpeakResponse {
  task_id: string;
  text: string;
  clone_id: string;
  image_id: string;
  status: ProcessingStatus;
  audio_url?: string;
  video_url?: string;
}

// Session types
export interface AvatarSession {
  session_id: string;
  name: string;
  voice_id?: string;
  clone_id?: string;
  image_id?: string;
  is_ready: boolean;
}

// WebSocket message types
export interface WSMessage {
  type: 'ack' | 'chunk' | 'status' | 'audio' | 'video' | 'complete' | 'error';
  content?: string;
  status?: string;
  audio_url?: string;
  video_url?: string;
  video_id?: string;
  response?: string;
  error?: string;
  duration?: number;
}

// App state
export interface AppState {
  // Session
  voiceId: string | null;
  cloneId: string | null;
  imageId: string | null;
  isReady: boolean;

  // Chat
  mode: ChatMode;
  conversationId: string | null;
  messages: ChatMessage[];
  isLoading: boolean;

  // Current video
  currentVideoUrl: string | null;
  currentAudioUrl: string | null;

  // Actions
  setVoiceId: (id: string | null) => void;
  setCloneId: (id: string | null) => void;
  setImageId: (id: string | null) => void;
  setMode: (mode: ChatMode) => void;
  addMessage: (message: ChatMessage) => void;
  setMessages: (messages: ChatMessage[]) => void;
  setIsLoading: (loading: boolean) => void;
  setCurrentVideo: (url: string | null) => void;
  setCurrentAudio: (url: string | null) => void;
  reset: () => void;
}
