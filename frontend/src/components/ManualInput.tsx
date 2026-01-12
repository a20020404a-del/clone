'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useAppStore } from '@/stores/useAppStore';
import { manualApi } from '@/services/api';
import { Play, Volume2, Loader2, FileText, Clock } from 'lucide-react';

interface ManualInputProps {
  cloneId: string;
  imageId: string;
}

interface TaskHistory {
  task_id: string;
  text: string;
  status: string;
  video_url?: string;
  audio_url?: string;
  timestamp: Date;
}

export default function ManualInput({ cloneId, imageId }: ManualInputProps) {
  const { setIsLoading, setCurrentVideo, setCurrentAudio } = useAppStore();
  const [text, setText] = useState('');
  const [previewOnly, setPreviewOnly] = useState(false);
  const [history, setHistory] = useState<TaskHistory[]>([]);

  const MAX_CHARS = 5000;
  const charCount = text.length;

  // Speak mutation
  const speakMutation = useMutation({
    mutationFn: manualApi.speak,
    onMutate: () => {
      setIsLoading(true);
    },
    onSuccess: (data) => {
      // Add to history
      setHistory((prev) => [
        {
          task_id: data.task_id,
          text: data.text,
          status: data.status,
          video_url: data.video_url,
          audio_url: data.audio_url,
          timestamp: new Date(),
        },
        ...prev.slice(0, 9), // Keep last 10
      ]);

      // Set video/audio
      if (data.video_url) {
        setCurrentVideo(data.video_url);
      } else if (data.audio_url) {
        setCurrentAudio(data.audio_url);
      }

      setText('');
    },
    onError: (error: any) => {
      console.error('Speak error:', error);
    },
    onSettled: () => {
      setIsLoading(false);
    },
  });

  // Preview mutation
  const previewMutation = useMutation({
    mutationFn: ({ text, cloneId }: { text: string; cloneId: string }) =>
      manualApi.preview(text, cloneId),
    onSuccess: (data) => {
      setCurrentAudio(data.audio_url);
    },
  });

  const handleSpeak = () => {
    if (!text.trim()) return;

    speakMutation.mutate({
      text: text.trim(),
      clone_id: cloneId,
      image_id: imageId,
      preview_only: previewOnly,
    });
  };

  const handlePreview = () => {
    if (!text.trim()) return;

    previewMutation.mutate({
      text: text.trim(),
      cloneId,
    });
  };

  const playFromHistory = (item: TaskHistory) => {
    if (item.video_url) {
      setCurrentVideo(item.video_url);
    } else if (item.audio_url) {
      setCurrentAudio(item.audio_url);
    }
  };

  const isLoading = speakMutation.isPending || previewMutation.isPending;

  return (
    <div className="flex flex-col h-full">
      {/* Input Section */}
      <div className="p-4 border-b border-gray-100">
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            喋らせたいテキスト
          </label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value.slice(0, MAX_CHARS))}
            placeholder="アバターに喋らせたい内容を入力してください..."
            className="w-full h-40 px-4 py-3 bg-gray-50 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
            disabled={isLoading}
          />
          <div className="flex items-center justify-between mt-2">
            <span
              className={`text-sm ${
                charCount > MAX_CHARS * 0.9 ? 'text-orange-500' : 'text-gray-400'
              }`}
            >
              {charCount} / {MAX_CHARS}
            </span>
            <label className="flex items-center gap-2 text-sm text-gray-600">
              <input
                type="checkbox"
                checked={previewOnly}
                onChange={(e) => setPreviewOnly(e.target.checked)}
                className="rounded text-primary-500 focus:ring-primary-500"
              />
              音声のみ（プレビュー）
            </label>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={handlePreview}
            disabled={!text.trim() || isLoading}
            className="flex-1 btn-secondary flex items-center justify-center gap-2"
          >
            {previewMutation.isPending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Volume2 className="w-5 h-5" />
            )}
            音声プレビュー
          </button>
          <button
            onClick={handleSpeak}
            disabled={!text.trim() || isLoading}
            className="flex-1 btn-primary flex items-center justify-center gap-2"
          >
            {speakMutation.isPending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Play className="w-5 h-5" />
            )}
            {previewOnly ? '音声生成' : '動画生成'}
          </button>
        </div>
      </div>

      {/* History Section */}
      <div className="flex-1 overflow-y-auto p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
          <Clock className="w-4 h-4" />
          履歴
        </h3>

        {history.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p className="text-sm">まだ履歴がありません</p>
          </div>
        ) : (
          <div className="space-y-3">
            {history.map((item) => (
              <div
                key={item.task_id}
                className="bg-gray-50 rounded-xl p-4 hover:bg-gray-100 transition-colors cursor-pointer"
                onClick={() => playFromHistory(item)}
              >
                <p className="text-sm text-gray-700 line-clamp-2 mb-2">{item.text}</p>
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>
                    {item.timestamp.toLocaleTimeString('ja-JP', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                  <span className="flex items-center gap-1">
                    {item.video_url ? (
                      <>
                        <Play className="w-3 h-3" /> 動画
                      </>
                    ) : (
                      <>
                        <Volume2 className="w-3 h-3" /> 音声
                      </>
                    )}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Tips */}
      <div className="p-4 bg-gray-50 border-t border-gray-100">
        <p className="text-xs text-gray-500">
          💡 ヒント: 短い文章の方が自然に聞こえます。句読点で区切ると間が生まれます。
        </p>
      </div>
    </div>
  );
}
