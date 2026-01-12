'use client';

import { useState } from 'react';
import { useAppStore } from '@/stores/useAppStore';
import UploadPanel from '@/components/UploadPanel';
import AvatarDisplay from '@/components/AvatarDisplay';
import ChatInterface from '@/components/ChatInterface';
import ManualInput from '@/components/ManualInput';
import { Settings, MessageSquare, Keyboard, RotateCcw } from 'lucide-react';

export default function Home() {
  const { isReady, mode, setMode, reset, cloneId, imageId } = useAppStore();
  const [showSetup, setShowSetup] = useState(!isReady);

  const handleReset = () => {
    reset();
    setShowSetup(true);
  };

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-400 to-primary-600 rounded-xl flex items-center justify-center">
              <span className="text-white text-xl">🎭</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-800">AI Avatar</h1>
              <p className="text-xs text-gray-500">Voice Clone & Lip-sync</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {isReady && (
              <button
                onClick={() => setShowSetup(!showSetup)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title="設定"
              >
                <Settings className="w-5 h-5 text-gray-600" />
              </button>
            )}
            <button
              onClick={handleReset}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="リセット"
            >
              <RotateCcw className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Setup Panel */}
        {(showSetup || !isReady) && (
          <div className="mb-8 animate-fade-in">
            <UploadPanel onComplete={() => setShowSetup(false)} />
          </div>
        )}

        {/* Main Content */}
        {isReady && !showSetup && (
          <div className="grid lg:grid-cols-2 gap-8">
            {/* Left: Avatar Display */}
            <div className="flex flex-col items-center">
              <AvatarDisplay />
            </div>

            {/* Right: Chat/Manual Input */}
            <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
              {/* Mode Tabs */}
              <div className="flex border-b border-gray-200">
                <button
                  onClick={() => setMode('auto')}
                  className={`flex-1 flex items-center justify-center gap-2 py-4 tab-button ${
                    mode === 'auto' ? 'active' : ''
                  }`}
                >
                  <MessageSquare className="w-5 h-5" />
                  <span>自動応答</span>
                </button>
                <button
                  onClick={() => setMode('manual')}
                  className={`flex-1 flex items-center justify-center gap-2 py-4 tab-button ${
                    mode === 'manual' ? 'active' : ''
                  }`}
                >
                  <Keyboard className="w-5 h-5" />
                  <span>手動入力</span>
                </button>
              </div>

              {/* Content */}
              <div className="h-[600px]">
                {mode === 'auto' ? (
                  <ChatInterface cloneId={cloneId!} imageId={imageId!} />
                ) : (
                  <ManualInput cloneId={cloneId!} imageId={imageId!} />
                )}
              </div>
            </div>
          </div>
        )}

        {/* Status Bar */}
        {isReady && (
          <div className="mt-8 text-center text-sm text-gray-500">
            <span className="inline-flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              アバター準備完了
            </span>
          </div>
        )}
      </div>
    </main>
  );
}
