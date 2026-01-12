import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { AppState, ChatMode, ChatMessage } from '@/types';

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      // Session state
      voiceId: null,
      cloneId: null,
      imageId: null,
      isReady: false,

      // Chat state
      mode: 'auto' as ChatMode,
      conversationId: null,
      messages: [],
      isLoading: false,

      // Media state
      currentVideoUrl: null,
      currentAudioUrl: null,

      // Actions
      setVoiceId: (id) =>
        set((state) => ({
          voiceId: id,
          isReady: id !== null && state.cloneId !== null && state.imageId !== null,
        })),

      setCloneId: (id) =>
        set((state) => ({
          cloneId: id,
          isReady: state.voiceId !== null && id !== null && state.imageId !== null,
        })),

      setImageId: (id) =>
        set((state) => ({
          imageId: id,
          isReady: state.voiceId !== null && state.cloneId !== null && id !== null,
        })),

      setMode: (mode) => set({ mode }),

      addMessage: (message) =>
        set((state) => ({
          messages: [...state.messages, message],
        })),

      setMessages: (messages) => set({ messages }),

      setIsLoading: (loading) => set({ isLoading: loading }),

      setCurrentVideo: (url) => set({ currentVideoUrl: url }),

      setCurrentAudio: (url) => set({ currentAudioUrl: url }),

      reset: () =>
        set({
          voiceId: null,
          cloneId: null,
          imageId: null,
          isReady: false,
          mode: 'auto',
          conversationId: null,
          messages: [],
          isLoading: false,
          currentVideoUrl: null,
          currentAudioUrl: null,
        }),
    }),
    {
      name: 'avatar-storage',
      partialize: (state) => ({
        voiceId: state.voiceId,
        cloneId: state.cloneId,
        imageId: state.imageId,
      }),
    }
  )
);
