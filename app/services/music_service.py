import httpx
import logging
import subprocess
import os
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)


class MusicService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.elevenlabs.io/v1"
    
    async def generate_music(
        self,
        prompt: str,
        duration_ms: int,
        force_instrumental: bool = True,
        output_format: str = "mp3_44100_128"
    ) -> bytes:
        """
        Generate background music using ElevenLabs API.
        
        Args:
            prompt: Text description of the music style
            duration_ms: Length of music in milliseconds (3000-300000)
            force_instrumental: If True, generates instrumental only
            output_format: Audio output format
            
        Returns:
            Audio bytes
        """
        if not self.api_key:
            raise ValueError("ElevenLabs API key not configured")
        
        # Clamp duration to API limits (3 sec to 5 min)
        duration_ms = max(3000, min(300000, duration_ms))
        
        url = f"{self.base_url}/music"
        
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        body = {
            "prompt": prompt,
            "music_length_ms": duration_ms,
            "model_id": "music_v1",
            "force_instrumental": force_instrumental
        }
        
        logger.info(f"Generating music: prompt='{prompt[:100]}...', duration={duration_ms}ms")
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    url,
                    json=body,
                    headers=headers,
                    params={"output_format": output_format}
                )
                response.raise_for_status()
                
                logger.info(f"Music generated successfully, size: {len(response.content)} bytes")
                return response.content
                
        except httpx.HTTPStatusError as e:
            logger.error(f"ElevenLabs music API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Music generation failed: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Music generation error: {str(e)}")
            raise
    
    @staticmethod
    def build_music_prompt(
        genre_tone: str,
        musical_atmosphere: Optional[str] = None,
        mood: str = "atmospheric"
    ) -> str:
        """Build a prompt for music generation based on project info."""
        if musical_atmosphere:
            return f"{musical_atmosphere}, background music for {genre_tone} audiobook, subtle, non-intrusive"
        return f"Cinematic {mood} background music for {genre_tone} audiobook, subtle, non-intrusive, suitable for narration"
    
    @staticmethod
    async def merge_audio_with_music(
        voice_path: str,
        music_path: str,
        output_path: str,
        music_volume_db: float = -12.0
    ) -> str:
        """
        Merge voice audio with background music using ffmpeg.
        
        Args:
            voice_path: Path to voice audio file
            music_path: Path to music audio file
            output_path: Path for output merged file
            music_volume_db: Volume adjustment for music in dB (negative = quieter)
            
        Returns:
            Path to merged audio file
        """
        # ffmpeg command to mix voice and music
        # Music is lowered by music_volume_db and mixed under voice
        cmd = [
            'ffmpeg', '-y',
            '-i', voice_path,
            '-i', music_path,
            '-filter_complex',
            f'[1:a]volume={music_volume_db}dB[music];[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[out]',
            '-map', '[out]',
            '-c:a', 'libmp3lame',
            '-b:a', '192k',
            output_path
        ]
        
        logger.info(f"Merging audio: voice={voice_path}, music={music_path}, volume={music_volume_db}dB")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Audio merged successfully: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg merge error: {e.stderr}")
            raise Exception(f"Audio merge failed: {e.stderr}")
