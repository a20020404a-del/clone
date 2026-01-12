"""Speech-to-Text Service using OpenAI Whisper"""
import uuid
from pathlib import Path
from typing import Optional, Tuple
import httpx

from ..config import get_settings


class STTService:
    """Service for Speech-to-Text conversion using Whisper API"""

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.openai_api_key
        self.base_url = "https://api.openai.com/v1"

    async def transcribe(
        self,
        audio_path: Path,
        language: str = "ja"
    ) -> Tuple[str, float, str]:
        """
        Transcribe audio to text.

        Args:
            audio_path: Path to audio file
            language: Language code (default: Japanese)

        Returns:
            Tuple of (transcription, confidence, message)
        """
        if not self.api_key:
            # Demo mode
            return self._demo_transcription(), 0.95, "Transcription (demo mode)"

        try:
            async with httpx.AsyncClient() as client:
                with open(audio_path, "rb") as f:
                    files = {
                        "file": (audio_path.name, f, "audio/mpeg"),
                    }
                    data = {
                        "model": "whisper-1",
                        "language": language,
                        "response_format": "json"
                    }

                    response = await client.post(
                        f"{self.base_url}/audio/transcriptions",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        files=files,
                        data=data,
                        timeout=60.0
                    )

                    if response.status_code == 200:
                        result = response.json()
                        text = result.get("text", "")
                        return text, 0.95, "Transcription successful"
                    else:
                        error = response.json().get("error", {}).get("message", "Unknown error")
                        return "", 0.0, f"Transcription failed: {error}"

        except Exception as e:
            return "", 0.0, f"Transcription error: {str(e)}"

    async def transcribe_with_timestamps(
        self,
        audio_path: Path,
        language: str = "ja"
    ) -> Tuple[list, str]:
        """
        Transcribe audio with word-level timestamps.

        Returns:
            Tuple of (segments_list, message)
        """
        if not self.api_key:
            return self._demo_segments(), "Transcription with timestamps (demo mode)"

        try:
            async with httpx.AsyncClient() as client:
                with open(audio_path, "rb") as f:
                    files = {
                        "file": (audio_path.name, f, "audio/mpeg"),
                    }
                    data = {
                        "model": "whisper-1",
                        "language": language,
                        "response_format": "verbose_json",
                        "timestamp_granularities[]": "word"
                    }

                    response = await client.post(
                        f"{self.base_url}/audio/transcriptions",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        files=files,
                        data=data,
                        timeout=60.0
                    )

                    if response.status_code == 200:
                        result = response.json()
                        segments = result.get("segments", [])
                        return segments, "Transcription successful"
                    else:
                        return [], "Transcription failed"

        except Exception as e:
            return [], f"Transcription error: {str(e)}"

    def _demo_transcription(self) -> str:
        """Return demo transcription text"""
        return "これはデモモードの音声認識結果です。APIキーを設定すると実際の音声認識が動作します。"

    def _demo_segments(self) -> list:
        """Return demo segments with timestamps"""
        return [
            {
                "start": 0.0,
                "end": 2.0,
                "text": "これはデモモードの",
                "words": [
                    {"word": "これは", "start": 0.0, "end": 0.5},
                    {"word": "デモモードの", "start": 0.5, "end": 2.0}
                ]
            },
            {
                "start": 2.0,
                "end": 4.0,
                "text": "音声認識結果です。",
                "words": [
                    {"word": "音声認識", "start": 2.0, "end": 3.0},
                    {"word": "結果です。", "start": 3.0, "end": 4.0}
                ]
            }
        ]

    async def detect_language(self, audio_path: Path) -> Tuple[str, float]:
        """
        Detect language from audio.

        Returns:
            Tuple of (language_code, confidence)
        """
        if not self.api_key:
            return "ja", 0.9

        # Use Whisper without specifying language for detection
        try:
            async with httpx.AsyncClient() as client:
                with open(audio_path, "rb") as f:
                    files = {
                        "file": (audio_path.name, f, "audio/mpeg"),
                    }
                    data = {
                        "model": "whisper-1",
                        "response_format": "verbose_json"
                    }

                    response = await client.post(
                        f"{self.base_url}/audio/transcriptions",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        files=files,
                        data=data,
                        timeout=60.0
                    )

                    if response.status_code == 200:
                        result = response.json()
                        language = result.get("language", "ja")
                        return language, 0.9

        except Exception:
            pass

        return "ja", 0.5
