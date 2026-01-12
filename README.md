# AI Avatar System

20秒の音声ファイルと人物写真から、リアルタイムで話すAIアバターを生成するシステム。

## 機能

- **音声クローン**: 20秒の音声サンプルから声をクローン
- **アバター生成**: 写真と音声からリップシンク動画を自動生成
- **自動応答モード**: AIが質問に自動で回答しアバターが話す
- **手動入力モード**: 任意のテキストをアバターに喋らせる

## アーキテクチャ

```
┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│    Backend      │
│   (Next.js)     │     │   (FastAPI)     │
└─────────────────┘     └─────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  Voice Clone    │   │  Avatar Gen     │   │  LLM Service    │
│  (ElevenLabs)   │   │  (SadTalker)    │   │  (Claude API)   │
└─────────────────┘   └─────────────────┘   └─────────────────┘
```

## クイックスタート

### 必要条件

- Python 3.11+
- Node.js 20+
- ffmpeg (動画処理用)

### 1. バックエンドのセットアップ

```bash
cd backend

# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt

# 環境変数を設定
cp .env.example .env
# .env ファイルを編集してAPIキーを設定

# サーバーを起動
uvicorn app.main:app --reload --port 8000
```

### 2. フロントエンドのセットアップ

```bash
cd frontend

# 依存関係をインストール
npm install

# 開発サーバーを起動
npm run dev
```

### 3. アクセス

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 環境変数

```env
# APIキー（必須ではないがあると機能が向上）
ELEVENLABS_API_KEY=xxx    # 音声クローン用
ANTHROPIC_API_KEY=xxx     # 自動応答用
OPENAI_API_KEY=xxx        # 音声認識用

# オプション
DEBUG=true
```

## API エンドポイント

### Voice API
- `POST /api/v1/voice/upload` - 音声サンプルをアップロード
- `POST /api/v1/voice/clone` - 音声クローンを作成
- `POST /api/v1/voice/synthesize` - テキストから音声を生成

### Avatar API
- `POST /api/v1/avatar/upload-image` - 参照画像をアップロード
- `POST /api/v1/avatar/generate` - アバター動画を生成
- `GET /api/v1/avatar/{id}/status` - 生成状況を確認

### Chat API
- `POST /api/v1/chat/message` - メッセージを送信
- `WS /api/v1/chat/stream` - リアルタイムチャット

### Manual API
- `POST /api/v1/manual/speak` - テキストをアバターに喋らせる

## 使い方

1. **音声アップロード**: 20秒程度のクリアな音声ファイルをアップロード
2. **音声クローン作成**: アップロードした音声からクローンを作成
3. **写真アップロード**: 正面を向いた顔写真をアップロード
4. **利用開始**:
   - **自動応答モード**: テキストまたは音声で話しかけると、AIが応答してアバターが話す
   - **手動入力モード**: 任意のテキストを入力してアバターに喋らせる

## 技術スタック

### Backend
- FastAPI
- ElevenLabs API (音声クローン)
- Claude API (LLM)
- OpenCV (画像処理)
- ffmpeg (動画処理)

### Frontend
- Next.js 14
- Tailwind CSS
- Zustand (状態管理)
- React Query

## Docker での実行

```bash
# 環境変数を設定
export ELEVENLABS_API_KEY=your_key
export ANTHROPIC_API_KEY=your_key

# Docker Compose で起動
docker-compose up -d
```

## ライセンス

MIT License

## 注意事項

- 他人の声や画像を無断でクローンしないでください
- 生成されたコンテンツの責任は利用者にあります
- APIキーは安全に管理してください
