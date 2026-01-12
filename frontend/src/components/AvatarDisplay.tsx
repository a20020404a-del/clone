'use client';

import { useState, useRef, useEffect } from 'react';
import { useAppStore } from '@/stores/useAppStore';
import { avatarApi } from '@/services/api';
import { Play, Pause, Volume2, VolumeX, Loader2 } from 'lucide-react';

export default function AvatarDisplay() {
  const { currentVideoUrl, currentAudioUrl, imageId, isLoading } = useAppStore();
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [progress, setProgress] = useState(0);

  const imagePreviewUrl = imageId ? avatarApi.getPreviewUrl(imageId) : null;

  // Handle video playback
  useEffect(() => {
    if (currentVideoUrl && videoRef.current) {
      videoRef.current.load();
      videoRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
    }
  }, [currentVideoUrl]);

  // Handle audio playback
  useEffect(() => {
    if (currentAudioUrl && audioRef.current && !currentVideoUrl) {
      audioRef.current.load();
      audioRef.current.play().catch(() => {});
    }
  }, [currentAudioUrl, currentVideoUrl]);

  const togglePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
    if (audioRef.current) {
      audioRef.current.muted = !isMuted;
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      const progress = (videoRef.current.currentTime / videoRef.current.duration) * 100;
      setProgress(progress || 0);
    }
  };

  const handleVideoEnd = () => {
    setIsPlaying(false);
    setProgress(0);
  };

  return (
    <div className="flex flex-col items-center">
      {/* Avatar Container */}
      <div className="relative video-container bg-gray-100 w-full max-w-md">
        {/* Loading State */}
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/50 z-20">
            <div className="text-center text-white">
              <Loader2 className="w-12 h-12 animate-spin mx-auto mb-3" />
              <p className="text-sm">生成中...</p>
            </div>
          </div>
        )}

        {/* Video Player */}
        {currentVideoUrl ? (
          <video
            ref={videoRef}
            className="w-full h-full object-cover"
            onTimeUpdate={handleTimeUpdate}
            onEnded={handleVideoEnd}
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            playsInline
          >
            <source src={currentVideoUrl} type="video/mp4" />
          </video>
        ) : imagePreviewUrl ? (
          /* Static Image */
          <img
            src={imagePreviewUrl}
            alt="Avatar"
            className="w-full h-full object-cover"
          />
        ) : (
          /* Placeholder */
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200">
            <div className="text-center text-gray-400">
              <div className="w-24 h-24 rounded-full bg-gray-300 mx-auto mb-4 flex items-center justify-center">
                <span className="text-4xl">🎭</span>
              </div>
              <p className="text-sm">アバター待機中</p>
            </div>
          </div>
        )}

        {/* Progress Bar */}
        {currentVideoUrl && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-black/20">
            <div
              className="h-full bg-primary-500 transition-all duration-100"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
      </div>

      {/* Controls */}
      {currentVideoUrl && (
        <div className="flex items-center gap-4 mt-4">
          <button
            onClick={togglePlayPause}
            className="p-3 bg-white rounded-full shadow-md hover:bg-gray-50 transition-colors"
          >
            {isPlaying ? (
              <Pause className="w-6 h-6 text-gray-700" />
            ) : (
              <Play className="w-6 h-6 text-gray-700" />
            )}
          </button>
          <button
            onClick={toggleMute}
            className="p-3 bg-white rounded-full shadow-md hover:bg-gray-50 transition-colors"
          >
            {isMuted ? (
              <VolumeX className="w-6 h-6 text-gray-700" />
            ) : (
              <Volume2 className="w-6 h-6 text-gray-700" />
            )}
          </button>
        </div>
      )}

      {/* Hidden Audio Element for audio-only playback */}
      {currentAudioUrl && !currentVideoUrl && (
        <audio ref={audioRef} src={currentAudioUrl} autoPlay />
      )}

      {/* Status Text */}
      <div className="mt-4 text-center">
        {isLoading ? (
          <p className="text-sm text-gray-500">アバター動画を生成しています...</p>
        ) : currentVideoUrl ? (
          <p className="text-sm text-gray-500">動画を再生中</p>
        ) : (
          <p className="text-sm text-gray-400">メッセージを送信するとアバターが話し始めます</p>
        )}
      </div>
    </div>
  );
}
