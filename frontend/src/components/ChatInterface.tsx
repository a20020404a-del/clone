'use client';

import { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useAppStore } from '@/stores/useAppStore';
import { chatApi, avatarApi } from '@/services/api';
import { Send, Mic, MicOff, Loader2, Trash2 } from 'lucide-react';
import type { ChatMessage } from '@/types';

interface ChatInterfaceProps {
  cloneId: string;
  imageId: string;
}

export default function ChatInterface({ cloneId, imageId }: ChatInterfaceProps) {
  const {
    messages,
    addMessage,
    setMessages,
    isLoading,
    setIsLoading,
    setCurrentVideo,
    setCurrentAudio,
  } = useAppStore();

  const [input, setInput] = useState('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: chatApi.sendMessage,
    onMutate: () => {
      setIsLoading(true);
    },
    onSuccess: (data) => {
      setConversationId(data.conversation_id);

      // Add assistant message
      addMessage(data.response);

      // Set video/audio URLs
      if (data.response.video_url) {
        setCurrentVideo(data.response.video_url);
      } else if (data.response.audio_url) {
        setCurrentAudio(data.response.audio_url);
      }
    },
    onError: (error: any) => {
      console.error('Chat error:', error);
      addMessage({
        role: 'assistant',
        content: 'エラーが発生しました。もう一度お試しください。',
        timestamp: new Date().toISOString(),
      });
    },
    onSettled: () => {
      setIsLoading(false);
    },
  });

  // Handle send message
  const handleSend = () => {
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    addMessage(userMessage);
    setInput('');

    sendMessageMutation.mutate({
      message: userMessage.content,
      clone_id: cloneId,
      image_id: imageId,
      conversation_id: conversationId || undefined,
      generate_video: true,
    });
  };

  // Handle voice input
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const audioFile = new File([audioBlob], 'voice-input.webm', {
          type: 'audio/webm',
        });

        // Send voice message
        setIsLoading(true);
        try {
          const response = await chatApi.sendVoice(
            audioFile,
            cloneId,
            imageId,
            conversationId || undefined
          );

          setConversationId(response.conversation_id);

          // Add user message with transcription
          addMessage({
            role: 'user',
            content: response.transcription || '(音声入力)',
            timestamp: new Date().toISOString(),
          });

          // Add assistant response
          addMessage(response.response);

          if (response.response.video_url) {
            setCurrentVideo(response.response.video_url);
          }
        } catch (error) {
          console.error('Voice chat error:', error);
          addMessage({
            role: 'assistant',
            content: 'エラーが発生しました。もう一度お試しください。',
            timestamp: new Date().toISOString(),
          });
        } finally {
          setIsLoading(false);
        }

        // Stop all tracks
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Recording error:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Clear chat
  const clearChat = () => {
    setMessages([]);
    setConversationId(null);
    setCurrentVideo(null);
    setCurrentAudio(null);
  };

  // Handle Enter key
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <span className="text-sm text-gray-500">
          {messages.length > 0
            ? `${messages.length} メッセージ`
            : 'AIアバターと会話を始めましょう'}
        </span>
        {messages.length > 0 && (
          <button
            onClick={clearChat}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            title="チャットをクリア"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 py-12">
            <p className="text-lg mb-2">👋 こんにちは！</p>
            <p className="text-sm">メッセージを入力するか、マイクボタンで話しかけてください</p>
          </div>
        )}

        {messages.map((msg, index) => (
          <div
            key={index}
            className={`chat-message ${msg.role}`}
          >
            <p className="whitespace-pre-wrap">{msg.content}</p>
            <span className="text-xs opacity-60 mt-1 block">
              {new Date(msg.timestamp).toLocaleTimeString('ja-JP', {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          </div>
        ))}

        {isLoading && (
          <div className="chat-message assistant">
            <div className="flex items-center gap-2">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full loading-dot" />
                <span className="w-2 h-2 bg-gray-400 rounded-full loading-dot" />
                <span className="w-2 h-2 bg-gray-400 rounded-full loading-dot" />
              </div>
              <span className="text-sm text-gray-500">考え中...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-100 p-4">
        <div className="flex items-center gap-2">
          {/* Voice Input */}
          <button
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isLoading}
            className={`p-3 rounded-full transition-all ${
              isRecording
                ? 'bg-red-500 text-white animate-pulse'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            } disabled:opacity-50`}
          >
            {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
          </button>

          {/* Text Input */}
          <div className="flex-1 relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="メッセージを入力..."
              disabled={isLoading || isRecording}
              className="w-full px-4 py-3 bg-gray-100 rounded-full focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
            />
          </div>

          {/* Send Button */}
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="p-3 bg-primary-500 text-white rounded-full hover:bg-primary-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>

        {isRecording && (
          <p className="text-center text-sm text-red-500 mt-2 animate-pulse">
            🎙️ 録音中... タップして停止
          </p>
        )}
      </div>
    </div>
  );
}
