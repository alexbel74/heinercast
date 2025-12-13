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

    @staticmethod
    async def merge_audio_with_sounds(
        voice_path: str,
        sounds: list,
        output_path: str,
        sounds_volume_db: float = -6.0
    ) -> str:
        """
        Merge voice audio with sound effects at specific timestamps using ffmpeg.

        Args:
            voice_path: Path to voice audio file
            sounds: List of sound dicts with 'local_path', 'start_time', 'duration'
            output_path: Path for output merged file
            sounds_volume_db: Volume adjustment for sounds in dB

        Returns:
            Path to merged audio file
        """
        import subprocess
        import logging
        logger = logging.getLogger(__name__)

        if not sounds:
            # No sounds, just copy voice
            import shutil
            shutil.copy(voice_path, output_path)
            return output_path

        # Build ffmpeg command with multiple sound inputs
        inputs = ['-i', voice_path]
        filter_parts = []
        
        valid_sounds = []
        for i, sound in enumerate(sounds):
            sound_path = f"/var/www/heinercast{sound.get('local_path', sound.get('url', ''))}"
            if sound_path.startswith('/var/www/heinercast/storage'):
                sound_path = sound_path.replace('/var/www/heinercast/storage', '/var/www/heinercast/storage')
            else:
                sound_path = f"/var/www/heinercast/storage{sound.get('url', '').replace('/storage', '')}"
            
            import os
            if os.path.exists(sound_path):
                inputs.extend(['-i', sound_path])
                valid_sounds.append((len(valid_sounds) + 1, sound))  # input index starts at 1 (0 is voice)

        if not valid_sounds:
            import shutil
            shutil.copy(voice_path, output_path)
            return output_path

        # Create filter for each sound with delay and volume adjustment
        sound_filters = []
        for input_idx, sound in valid_sounds:
            start_ms = int(sound.get('start_time', 0) * 1000)
            sound_filters.append(f"[{input_idx}:a]volume={sounds_volume_db}dB,adelay={start_ms}|{start_ms}[s{input_idx}]")

        # Mix all sounds together first, then mix with voice
        if len(valid_sounds) == 1:
            filter_complex = f"{sound_filters[0]};[0:a][s1]amix=inputs=2:duration=first:dropout_transition=0.5[out]"
        else:
            # Mix all sounds
            sound_labels = ''.join([f"[s{i}]" for i, _ in valid_sounds])
            filter_complex = ';'.join(sound_filters)
            filter_complex += f";{sound_labels}amix=inputs={len(valid_sounds)}:normalize=0[sounds];[0:a][sounds]amix=inputs=2:duration=first:dropout_transition=0.5[out]"

        cmd = [
            'ffmpeg', '-y',
            *inputs,
            '-filter_complex', filter_complex,
            '-map', '[out]',
            '-c:a', 'libmp3lame',
            '-b:a', '192k',
            output_path
        ]

        logger.info(f"Merging audio with {len(valid_sounds)} sounds")
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise Exception(f"FFmpeg failed: {result.stderr[:500]}")
            logger.info(f"Audio merged successfully: {output_path}")
            return output_path
        except subprocess.TimeoutExpired:
            raise Exception("FFmpeg timeout - audio merge took too long")

    @staticmethod
    async def merge_all(
        voice_path: str,
        sounds: list = None,
        music_path: str = None,
        output_path: str = None,
        sounds_volume_db: float = -6.0,
        music_volume_db: float = -12.0
    ) -> str:
        """
        Merge voice with sounds and/or music.
        
        Args:
            voice_path: Path to voice audio
            sounds: List of sound dicts with timestamps (optional)
            music_path: Path to background music (optional)
            output_path: Output file path
            sounds_volume_db: Volume for sounds
            music_volume_db: Volume for music
        """
        import subprocess
        import logging
        import os
        logger = logging.getLogger(__name__)

        if not sounds and not music_path:
            import shutil
            shutil.copy(voice_path, output_path)
            return output_path

        inputs = ['-i', voice_path]
        filter_parts = []
        input_idx = 1

        # Add sounds inputs
        valid_sounds = []
        if sounds:
            for sound in sounds:
                sound_file = f"/var/www/heinercast/storage{sound.get('url', '').replace('/storage', '')}"
                if os.path.exists(sound_file):
                    inputs.extend(['-i', sound_file])
                    valid_sounds.append((input_idx, sound))
                    input_idx += 1

        # Add music input
        music_input_idx = None
        if music_path and os.path.exists(music_path):
            inputs.extend(['-i', music_path])
            music_input_idx = input_idx
            input_idx += 1

        # Build filter complex
        filter_parts = []
        mix_inputs = ['[0:a]']  # Start with voice

        # Process sounds with delays
        if valid_sounds:
            for idx, sound in valid_sounds:
                start_ms = int(sound.get('start_time', 0) * 1000)
                filter_parts.append(f"[{idx}:a]volume={sounds_volume_db}dB,adelay={start_ms}|{start_ms}[s{idx}]")
                mix_inputs.append(f"[s{idx}]")

        # Process music
        if music_input_idx:
            filter_parts.append(f"[{music_input_idx}:a]volume={music_volume_db}dB[music]")
            mix_inputs.append("[music]")

        # Mix all together
        num_inputs = len(mix_inputs)
        filter_complex = ';'.join(filter_parts)
        if filter_complex:
            filter_complex += ';'
        filter_complex += f"{''.join(mix_inputs)}amix=inputs={num_inputs}:duration=first:dropout_transition=0.5[out]"

        cmd = [
            'ffmpeg', '-y',
            *inputs,
            '-filter_complex', filter_complex,
            '-map', '[out]',
            '-c:a', 'libmp3lame',
            '-b:a', '192k',
            output_path
        ]

        logger.info(f"Merging: voice + {len(valid_sounds)} sounds + {'music' if music_input_idx else 'no music'}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise Exception(f"FFmpeg failed: {result.stderr[:500]}")
            logger.info(f"Full merge completed: {output_path}")
            return output_path
        except subprocess.TimeoutExpired:
            raise Exception("FFmpeg timeout")
