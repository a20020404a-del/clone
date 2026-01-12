"""Avatar Generation Service using SadTalker/Wav2Lip"""
import os
import uuid
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import cv2
import numpy as np

from ..config import get_settings
from ..models.schemas import ProcessingStatus


class AvatarGeneratorService:
    """Service for generating talking avatar videos"""

    def __init__(self):
        self.settings = get_settings()
        self._images: dict = {}  # In-memory storage for image metadata
        self._tasks: dict = {}  # Track generation tasks

    async def validate_image(self, file_path: Path) -> Tuple[bool, dict, str]:
        """
        Validate image for avatar generation.

        Returns:
            Tuple of (is_valid, metadata, message)
        """
        try:
            img = Image.open(file_path)
            width, height = img.size

            # Check minimum size
            if width < 256 or height < 256:
                return False, {}, "Image too small. Minimum 256x256 pixels required."

            # Check maximum size
            if width > 4096 or height > 4096:
                return False, {}, "Image too large. Maximum 4096x4096 pixels."

            # Try to detect face using OpenCV
            face_detected = await self._detect_face(file_path)

            if not face_detected:
                return False, {}, "No face detected in image. Please use a clear front-facing photo."

            metadata = {
                "width": width,
                "height": height,
                "format": img.format,
                "mode": img.mode,
                "face_detected": face_detected
            }

            return True, metadata, "Image validation successful"

        except Exception as e:
            return False, {}, f"Failed to process image: {str(e)}"

    async def _detect_face(self, image_path: Path) -> bool:
        """Detect face in image using OpenCV"""
        try:
            # Load the cascade classifier
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            face_cascade = cv2.CascadeClassifier(cascade_path)

            # Read image
            img = cv2.imread(str(image_path))
            if img is None:
                return False

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Detect faces
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(50, 50)
            )

            return len(faces) > 0

        except Exception:
            # If face detection fails, assume face is present
            return True

    async def save_upload(self, file_content: bytes, filename: str) -> Tuple[str, Path]:
        """
        Save uploaded image file.

        Returns:
            Tuple of (image_id, file_path)
        """
        image_id = str(uuid.uuid4())
        upload_dir = self.settings.upload_dir / "image"
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Determine file extension
        ext = Path(filename).suffix.lower()
        if not ext or ext not in [".jpg", ".jpeg", ".png"]:
            ext = ".png"

        file_path = upload_dir / f"{image_id}{ext}"
        file_path.write_bytes(file_content)

        return image_id, file_path

    async def preprocess_image(self, file_path: Path, image_id: str) -> Tuple[Path, dict]:
        """
        Preprocess image for avatar generation.
        - Crop to face region with padding
        - Resize to optimal dimensions
        - Normalize colors
        """
        try:
            img = cv2.imread(str(file_path))
            if img is None:
                return file_path, {}

            # Detect face for cropping
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            face_cascade = cv2.CascadeClassifier(cascade_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(50, 50))

            if len(faces) > 0:
                # Get the largest face
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])

                # Add padding around face
                padding = int(max(w, h) * 0.5)
                x1 = max(0, x - padding)
                y1 = max(0, y - padding)
                x2 = min(img.shape[1], x + w + padding)
                y2 = min(img.shape[0], y + h + padding)

                # Crop
                cropped = img[y1:y2, x1:x2]

                # Resize to standard size
                target_size = 512
                cropped = cv2.resize(cropped, (target_size, target_size))

                # Save processed image
                processed_dir = self.settings.upload_dir / "image" / "processed"
                processed_dir.mkdir(parents=True, exist_ok=True)
                processed_path = processed_dir / f"{image_id}_processed.png"
                cv2.imwrite(str(processed_path), cropped)

                metadata = {
                    "original_size": img.shape[:2],
                    "face_bbox": [int(x), int(y), int(w), int(h)],
                    "processed_size": (target_size, target_size)
                }

                return processed_path, metadata

            return file_path, {}

        except Exception as e:
            print(f"Image preprocessing error: {e}")
            return file_path, {}

    async def generate_avatar(
        self,
        image_id: str,
        image_path: Path,
        audio_path: Path,
        expression_scale: float = 1.0
    ) -> Tuple[str, ProcessingStatus, str]:
        """
        Generate talking avatar video.

        Returns:
            Tuple of (video_id, status, message)
        """
        video_id = str(uuid.uuid4())
        output_dir = self.settings.output_dir / "video"
        output_dir.mkdir(parents=True, exist_ok=True)
        video_path = output_dir / f"{video_id}.mp4"

        # Initialize task tracking
        self._tasks[video_id] = {
            "image_id": image_id,
            "status": ProcessingStatus.PROCESSING,
            "progress": 0,
            "video_path": str(video_path)
        }

        try:
            # For demo/development, create a simple video
            # In production, this would call SadTalker or Wav2Lip
            success = await self._generate_demo_video(
                image_path,
                audio_path,
                video_path,
                video_id,
                expression_scale
            )

            if success:
                self._tasks[video_id]["status"] = ProcessingStatus.COMPLETED
                self._tasks[video_id]["progress"] = 100
                return video_id, ProcessingStatus.COMPLETED, "Avatar video generated successfully"
            else:
                self._tasks[video_id]["status"] = ProcessingStatus.FAILED
                return video_id, ProcessingStatus.FAILED, "Failed to generate avatar video"

        except Exception as e:
            self._tasks[video_id]["status"] = ProcessingStatus.FAILED
            return video_id, ProcessingStatus.FAILED, f"Generation error: {str(e)}"

    async def _generate_demo_video(
        self,
        image_path: Path,
        audio_path: Path,
        video_path: Path,
        video_id: str,
        expression_scale: float
    ) -> bool:
        """
        Generate a demo video by combining image with audio.
        In production, this would use SadTalker/Wav2Lip for lip-sync.
        """
        try:
            from pydub import AudioSegment

            # Get audio duration
            audio = AudioSegment.from_file(str(audio_path))
            duration = len(audio) / 1000.0  # seconds
            fps = 25

            # Read image
            img = cv2.imread(str(image_path))
            if img is None:
                return False

            # Resize for video
            height, width = img.shape[:2]
            if width > 720:
                scale = 720 / width
                width = 720
                height = int(height * scale)
                img = cv2.resize(img, (width, height))

            # Create video writer
            temp_video = video_path.with_suffix(".temp.mp4")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(temp_video), fourcc, fps, (width, height))

            # Generate frames with subtle animation
            total_frames = int(duration * fps)
            for i in range(total_frames):
                # Update progress
                progress = int((i / total_frames) * 80)
                self._tasks[video_id]["progress"] = progress

                # Create frame with subtle movement (simulating talking)
                frame = img.copy()

                # Add subtle scaling animation for "breathing" effect
                t = i / fps
                scale = 1.0 + 0.005 * np.sin(t * 2 * np.pi * 0.5) * expression_scale

                if scale != 1.0:
                    center = (width // 2, height // 2)
                    M = cv2.getRotationMatrix2D(center, 0, scale)
                    frame = cv2.warpAffine(frame, M, (width, height))

                out.write(frame)

            out.release()

            # Combine video with audio using ffmpeg
            self._tasks[video_id]["progress"] = 90

            # Use ffmpeg to combine video and audio
            cmd = [
                "ffmpeg", "-y",
                "-i", str(temp_video),
                "-i", str(audio_path),
                "-c:v", "libx264",
                "-c:a", "aac",
                "-shortest",
                str(video_path)
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=300)

            # Clean up temp file
            if temp_video.exists():
                temp_video.unlink()

            if result.returncode == 0 and video_path.exists():
                self._tasks[video_id]["progress"] = 100
                return True
            else:
                # If ffmpeg fails, keep the video without audio
                if temp_video.exists():
                    temp_video.rename(video_path)
                return video_path.exists()

        except Exception as e:
            print(f"Video generation error: {e}")
            return False

    async def get_task_status(self, video_id: str) -> Optional[dict]:
        """Get status of a video generation task"""
        return self._tasks.get(video_id)

    async def get_video_path(self, video_id: str) -> Optional[Path]:
        """Get path to generated video"""
        task = self._tasks.get(video_id)
        if task and task["status"] == ProcessingStatus.COMPLETED:
            path = Path(task["video_path"])
            if path.exists():
                return path
        return None

    def register_image(self, image_id: str, file_path: Path, metadata: dict):
        """Register image metadata"""
        self._images[image_id] = {
            "file_path": str(file_path),
            **metadata
        }

    def get_image_info(self, image_id: str) -> Optional[dict]:
        """Get image information"""
        return self._images.get(image_id)

    def get_image_path(self, image_id: str) -> Optional[Path]:
        """Get path to uploaded image"""
        info = self._images.get(image_id)
        if info:
            return Path(info["file_path"])
        return None
