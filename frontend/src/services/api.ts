import axios from 'axios';
import type {
  VoiceUploadResponse,
  VoiceCloneRequest,
  VoiceCloneResponse,
  VoiceSynthesizeRequest,
  VoiceSynthesizeResponse,
  ImageUploadResponse,
  AvatarGenerateRequest,
  AvatarGenerateResponse,
  AvatarStatusResponse,
  ChatRequest,
  ChatResponse,
  ManualSpeakRequest,
  ManualSpeakResponse,
} from '@/types';

const API_BASE_URL = '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Voice API
export const voiceApi = {
  upload: async (file: File): Promise<VoiceUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<VoiceUploadResponse>('/voice/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  clone: async (request: VoiceCloneRequest): Promise<VoiceCloneResponse> => {
    const response = await api.post<VoiceCloneResponse>('/voice/clone', request);
    return response.data;
  },

  synthesize: async (request: VoiceSynthesizeRequest): Promise<VoiceSynthesizeResponse> => {
    const response = await api.post<VoiceSynthesizeResponse>('/voice/synthesize', request);
    return response.data;
  },

  getStatus: async (voiceId: string) => {
    const response = await api.get(`/voice/${voiceId}/status`);
    return response.data;
  },

  listClones: async () => {
    const response = await api.get('/voice/clones');
    return response.data.clones;
  },

  deleteClone: async (cloneId: string) => {
    const response = await api.delete(`/voice/${cloneId}`);
    return response.data;
  },
};

// Avatar API
export const avatarApi = {
  uploadImage: async (file: File): Promise<ImageUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<ImageUploadResponse>('/avatar/upload-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  generate: async (request: AvatarGenerateRequest): Promise<AvatarGenerateResponse> => {
    const response = await api.post<AvatarGenerateResponse>('/avatar/generate', request);
    return response.data;
  },

  getStatus: async (videoId: string): Promise<AvatarStatusResponse> => {
    const response = await api.get<AvatarStatusResponse>(`/avatar/${videoId}/status`);
    return response.data;
  },

  getVideoUrl: (videoId: string): string => {
    return `${API_BASE_URL}/avatar/${videoId}/video`;
  },

  getImageInfo: async (imageId: string) => {
    const response = await api.get(`/avatar/${imageId}/info`);
    return response.data;
  },

  getPreviewUrl: (imageId: string): string => {
    return `${API_BASE_URL}/avatar/${imageId}/preview`;
  },
};

// Chat API
export const chatApi = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/chat/message', request);
    return response.data;
  },

  sendVoice: async (
    file: File,
    cloneId: string,
    imageId: string,
    conversationId?: string
  ) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('clone_id', cloneId);
    formData.append('image_id', imageId);
    if (conversationId) {
      formData.append('conversation_id', conversationId);
    }
    formData.append('generate_video', 'true');
    const response = await api.post('/chat/voice', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  getHistory: async (conversationId: string) => {
    const response = await api.get(`/chat/history/${conversationId}`);
    return response.data;
  },

  clearHistory: async (conversationId: string) => {
    const response = await api.delete(`/chat/history/${conversationId}`);
    return response.data;
  },

  createConversation: async (persona?: string) => {
    const response = await api.post('/chat/conversation', { persona });
    return response.data;
  },

  // WebSocket connection
  createWebSocket: (
    onMessage: (data: any) => void,
    onError?: (error: Event) => void
  ): WebSocket => {
    const wsUrl = `ws://localhost:8000/api/v1/chat/stream`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    ws.onerror = (error) => {
      if (onError) onError(error);
    };

    return ws;
  },
};

// Manual API
export const manualApi = {
  speak: async (request: ManualSpeakRequest): Promise<ManualSpeakResponse> => {
    const response = await api.post<ManualSpeakResponse>('/manual/speak', request);
    return response.data;
  },

  getStatus: async (taskId: string) => {
    const response = await api.get(`/manual/${taskId}/status`);
    return response.data;
  },

  preview: async (text: string, cloneId: string) => {
    const response = await api.post('/manual/preview', null, {
      params: { text, clone_id: cloneId },
    });
    return response.data;
  },

  listTasks: async () => {
    const response = await api.get('/manual/tasks');
    return response.data.tasks;
  },

  cancelTask: async (taskId: string) => {
    const response = await api.delete(`/manual/${taskId}`);
    return response.data;
  },
};

// Health check
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
