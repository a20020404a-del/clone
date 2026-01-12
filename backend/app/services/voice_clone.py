"""Voice Cloning Service using ElevenLabs API"""
import os
import uuid
import asyncio
from pathlib import Path
from typing import Optional, Tuple
import httpx
from pydub import AudioSegment

from ..config import get_settings
from ..models.schemas import ProcessingStatus


class VoiceCloneService:
    """Service for voice cloning and synthesis using ElevenLabs"""

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.elevenlabs_api_key
        self.base_url = "https://api.elevenlabs.io/v1"
        self._clones: dict = {}  # In-memory storage for demo

    @property
    def headers(self) -> dict:
        """Get API headers"""
        return {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    async def validate_audio(self, file_path: Path) -> Tuple[bool, float, str]:
        """
        Validate audio file for voice cloning requirements.

        Returns:
            Tuple of (is_valid, duration, message)
        """
        try:
            audio = AudioSegment.from_file(str(file_path))
            duration = len(audio) / 1000.0  # Convert to seconds

            # Check duration (need ~20 seconds)
            if duration < 10:
                return False, duration, "Audio too short. Need at least 10 seconds."
            if duration > 300:
                return False, duration, "Audio too long. Maximum 5 minutes."

            # Check if audio has content (not silent)
            if audio.dBFS < -50:
                return False, duration, "Audio appears to be silent or too quiet."

            return True, duration, "Audio validation successful"

        except Exception as e:
            return False, 0, f"Failed to process audio: {str(e)}"

    async def save_upload(self, file_content: bytes, filename: str) -> Tuple[str, Path]:
        """
        Save uploaded voice file.

        Returns:
            Tuple of (voice_id, file_path)
        """
        voice_id = str(uuid.uuid4())
        upload_dir = self.settings.upload_dir / "voice"
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Determine file extension
        ext = Path(filename).suffix.lower()
        if not ext:
            ext = ".mp3"

        file_path = upload_dir / f"{voice_id}{ext}"
        file_path.write_bytes(file_content)

        return voice_id, file_path

    async def create_clone(
        self,
        voice_id: str,
        file_path: Path,
        name: str = "My Clone",
        description: Optional[str] = None
    ) -> Tuple[str, ProcessingStatus, str]:
        """
        Create a voice clone using ElevenLabs API.

        Returns:
            Tuple of (clone_id, status, message)
        """
        if not self.api_key:
            # Demo mode - simulate cloning
            clone_id = str(uuid.uuid4())
            self._clones[clone_id] = {
                "voice_id": voice_id,
                "name": name,
                "file_path": str(file_path),
                "status": ProcessingStatus.COMPLETED
            }
            return clone_id, ProcessingStatus.COMPLETED, "Clone created (demo mode)"

        try:
            async with httpx.AsyncClient() as client:
                # Read the audio file
                with open(file_path, "rb") as f:
                    files = {
                        "files": (file_path.name, f, "audio/mpeg")
                    }
                    data = {
                        "name": name,
                        "description": description or f"Voice clone from {voice_id}"
                    }

                    response = await client.post(
                        f"{self.base_url}/voices/add",
                        headers={"xi-api-key": self.api_key},
                        files=files,
                        data=data,
                        timeout=60.0
                    )

                    if response.status_code == 200:
                        result = response.json()
                        clone_id = result.get("voice_id", str(uuid.uuid4()))
                        self._clones[clone_id] = {
                            "voice_id": voice_id,
                            "name": name,
                            "elevenlabs_id": clone_id,
                            "status": ProcessingStatus.COMPLETED
                        }
                        return clone_id, ProcessingStatus.COMPLETED, "Voice clone created successfully"
                    else:
                        error = response.json().get("detail", "Unknown error")
                        return "", ProcessingStatus.FAILED, f"Failed to create clone: {error}"

        except Exception as e:
            return "", ProcessingStatus.FAILED, f"Clone creation error: {str(e)}"

    async def synthesize_speech(
        self,
        clone_id: str,
        text: str,
        stability: float = 0.5,
        similarity_boost: float = 0.75
    ) -> Tuple[str, Path, float, ProcessingStatus, str]:
        """
        Synthesize speech using cloned voice.

        Returns:
            Tuple of (audio_id, audio_path, duration, status, message)
        """
        audio_id = str(uuid.uuid4())
        output_dir = self.settings.output_dir / "voice"
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_path = output_dir / f"{audio_id}.mp3"

        if not self.api_key:
            # Demo mode - create a placeholder
            # In production, this would use ElevenLabs API
            self._create_demo_audio(audio_path, text)
            duration = len(text) * 0.1  # Rough estimate
            return audio_id, audio_path, duration, ProcessingStatus.COMPLETED, "Audio synthesized (demo mode)"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/text-to-speech/{clone_id}",
                    headers=self.headers,
                    json={
                        "text": text,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {
                            "stability": stability,
                            "similarity_boost": similarity_boost
                        }
                    },
                    timeout=120.0
                )

                if response.status_code == 200:
                    audio_path.write_bytes(response.content)
                    # Get duration
                    audio = AudioSegment.from_file(str(audio_path))
                    duration = len(audio) / 1000.0
                    return audio_id, audio_path, duration, ProcessingStatus.COMPLETED, "Speech synthesized successfully"
                else:
                    error = response.json().get("detail", "Unknown error")
                    return audio_id, audio_path, 0, ProcessingStatus.FAILED, f"Synthesis failed: {error}"

        except Exception as e:
            return audio_id, audio_path, 0, ProcessingStatus.FAILED, f"Synthesis error: {str(e)}"

    def _create_demo_audio(self, path: Path, text: str):
        """Create a silent demo audio file"""
        # Create a short silent audio for demo purposes
        duration_ms = max(1000, len(text) * 80)  # ~80ms per character
        silent = AudioSegment.silent(duration=duration_ms)
        silent.export(str(path), format="mp3")

    async def get_clone_status(self, clone_id: str) -> Optional[dict]:
        """Get status of a voice clone"""
        return self._clones.get(clone_id)

    async def list_clones(self) -> list:
        """List all voice clones"""
        if not self.api_key:
            return list(self._clones.values())

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/voices",
                    headers=self.headers
                )
                if response.status_code == 200:
                    return response.json().get("voices", [])
        except Exception:
            pass
        return []

    async def delete_clone(self, clone_id: str) -> bool:
        """Delete a voice clone"""
        if clone_id in self._clones:
            del self._clones[clone_id]

        if not self.api_key:
            return True

        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/voices/{clone_id}",
                    headers=self.headers
                )
                return response.status_code == 200
        except Exception:
            return False
