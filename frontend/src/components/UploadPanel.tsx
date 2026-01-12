'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useMutation } from '@tanstack/react-query';
import { useAppStore } from '@/stores/useAppStore';
import { voiceApi, avatarApi } from '@/services/api';
import { Mic, Image, Check, Loader2, AlertCircle } from 'lucide-react';

interface UploadPanelProps {
  onComplete?: () => void;
}

type Step = 'voice' | 'clone' | 'image' | 'complete';

export default function UploadPanel({ onComplete }: UploadPanelProps) {
  const { voiceId, cloneId, imageId, setVoiceId, setCloneId, setImageId } = useAppStore();
  const [currentStep, setCurrentStep] = useState<Step>(
    imageId ? 'complete' : cloneId ? 'image' : voiceId ? 'clone' : 'voice'
  );
  const [error, setError] = useState<string | null>(null);

  // Voice upload mutation
  const voiceUploadMutation = useMutation({
    mutationFn: voiceApi.upload,
    onSuccess: (data) => {
      setVoiceId(data.voice_id);
      setCurrentStep('clone');
      setError(null);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Voice upload failed');
    },
  });

  // Voice clone mutation
  const voiceCloneMutation = useMutation({
    mutationFn: voiceApi.clone,
    onSuccess: (data) => {
      setCloneId(data.clone_id);
      setCurrentStep('image');
      setError(null);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Voice cloning failed');
    },
  });

  // Image upload mutation
  const imageUploadMutation = useMutation({
    mutationFn: avatarApi.uploadImage,
    onSuccess: (data) => {
      setImageId(data.image_id);
      setCurrentStep('complete');
      setError(null);
      onComplete?.();
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Image upload failed');
    },
  });

  // Voice dropzone
  const onVoiceDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      voiceUploadMutation.mutate(acceptedFiles[0]);
    }
  }, []);

  const voiceDropzone = useDropzone({
    onDrop: onVoiceDrop,
    accept: {
      'audio/*': ['.mp3', '.wav', '.m4a', '.ogg'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  // Image dropzone
  const onImageDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      imageUploadMutation.mutate(acceptedFiles[0]);
    }
  }, []);

  const imageDropzone = useDropzone({
    onDrop: onImageDrop,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png'],
    },
    maxFiles: 1,
    maxSize: 5 * 1024 * 1024, // 5MB
  });

  // Handle clone creation
  const handleCreateClone = () => {
    if (voiceId) {
      voiceCloneMutation.mutate({
        voice_id: voiceId,
        name: 'My Avatar Voice',
      });
    }
  };

  const isLoading =
    voiceUploadMutation.isPending ||
    voiceCloneMutation.isPending ||
    imageUploadMutation.isPending;

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-800 mb-2">アバターセットアップ</h2>
      <p className="text-gray-500 mb-6">音声ファイルと写真をアップロードしてアバターを作成</p>

      {/* Progress Steps */}
      <div className="flex items-center justify-between mb-8">
        {[
          { step: 'voice', label: '音声', icon: Mic },
          { step: 'clone', label: 'クローン', icon: Check },
          { step: 'image', label: '写真', icon: Image },
        ].map(({ step, label, icon: Icon }, index) => {
          const stepOrder = ['voice', 'clone', 'image', 'complete'];
          const currentIndex = stepOrder.indexOf(currentStep);
          const stepIndex = stepOrder.indexOf(step);
          const isActive = currentStep === step;
          const isComplete = stepIndex < currentIndex;

          return (
            <div key={step} className="flex items-center">
              <div
                className={`flex items-center justify-center w-10 h-10 rounded-full ${
                  isComplete
                    ? 'bg-green-500 text-white'
                    : isActive
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-200 text-gray-400'
                }`}
              >
                {isComplete ? <Check className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
              </div>
              <span
                className={`ml-2 font-medium ${
                  isActive ? 'text-primary-500' : isComplete ? 'text-green-500' : 'text-gray-400'
                }`}
              >
                {label}
              </span>
              {index < 2 && (
                <div
                  className={`w-16 h-1 mx-4 rounded ${
                    isComplete ? 'bg-green-500' : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      )}

      {/* Step Content */}
      {currentStep === 'voice' && (
        <div>
          <div
            {...voiceDropzone.getRootProps()}
            className={`upload-zone ${voiceDropzone.isDragActive ? 'active' : ''}`}
          >
            <input {...voiceDropzone.getInputProps()} />
            {voiceUploadMutation.isPending ? (
              <div className="flex flex-col items-center">
                <Loader2 className="w-12 h-12 text-primary-500 animate-spin mb-4" />
                <p className="text-gray-600">アップロード中...</p>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <Mic className="w-12 h-12 text-gray-400 mb-4" />
                <p className="text-lg font-medium text-gray-700 mb-2">音声ファイルをドロップ</p>
                <p className="text-sm text-gray-500 mb-4">または クリックして選択</p>
                <p className="text-xs text-gray-400">
                  MP3, WAV, M4A, OGG • 10秒以上 • 最大10MB
                </p>
              </div>
            )}
          </div>
          <p className="mt-4 text-sm text-gray-500 text-center">
            💡 20秒程度のクリアな音声が理想的です
          </p>
        </div>
      )}

      {currentStep === 'clone' && (
        <div className="text-center">
          <div className="mb-6">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Check className="w-10 h-10 text-green-500" />
            </div>
            <p className="text-lg font-medium text-gray-700">音声アップロード完了</p>
            <p className="text-sm text-gray-500">次は音声クローンを作成します</p>
          </div>
          <button
            onClick={handleCreateClone}
            disabled={voiceCloneMutation.isPending}
            className="btn-primary inline-flex items-center gap-2"
          >
            {voiceCloneMutation.isPending ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                クローン作成中...
              </>
            ) : (
              <>
                <Mic className="w-5 h-5" />
                音声クローンを作成
              </>
            )}
          </button>
        </div>
      )}

      {currentStep === 'image' && (
        <div>
          <div
            {...imageDropzone.getRootProps()}
            className={`upload-zone ${imageDropzone.isDragActive ? 'active' : ''}`}
          >
            <input {...imageDropzone.getInputProps()} />
            {imageUploadMutation.isPending ? (
              <div className="flex flex-col items-center">
                <Loader2 className="w-12 h-12 text-primary-500 animate-spin mb-4" />
                <p className="text-gray-600">アップロード中...</p>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <Image className="w-12 h-12 text-gray-400 mb-4" />
                <p className="text-lg font-medium text-gray-700 mb-2">写真をドロップ</p>
                <p className="text-sm text-gray-500 mb-4">または クリックして選択</p>
                <p className="text-xs text-gray-400">JPG, PNG • 正面顔 • 最大5MB</p>
              </div>
            )}
          </div>
          <p className="mt-4 text-sm text-gray-500 text-center">
            💡 正面を向いた鮮明な顔写真を使用してください
          </p>
        </div>
      )}

      {currentStep === 'complete' && (
        <div className="text-center">
          <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Check className="w-12 h-12 text-green-500" />
          </div>
          <p className="text-xl font-bold text-gray-800 mb-2">セットアップ完了！</p>
          <p className="text-gray-500 mb-6">アバターの準備ができました</p>
          <button onClick={onComplete} className="btn-primary">
            始める
          </button>
        </div>
      )}
    </div>
  );
}
