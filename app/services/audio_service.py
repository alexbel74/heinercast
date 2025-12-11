"""
Audio Service - FFmpeg processing for audio merging
"""
import asyncio
import logging
import os
import subprocess
import tempfile
import uuid
from typing import Optional, List, Dict, Any

from app.config import get_settings, AUDIO_SETTINGS
from app.core.exceptions import AudioProcessingError

settings = get_settings()
logger = logging.getLogger(__name__)


class AudioService:
    """Service for audio processing with FFmpeg"""
    
    def __init__(self):
        self.storage_path = settings.storage_path
        self.temp_path = os.path.join(self.storage_path, "temp")
        os.makedirs(self.temp_path, exist_ok=True)
    
    async def save_audio(
        self,
        audio_bytes: bytes,
        filename: Optional[str] = None,
        subfolder: str = "audio"
    ) -> str:
        """
        Save audio bytes to storage.
        
        Args:
            audio_bytes: Audio data
            filename: Optional filename (will generate UUID if not provided)
            subfolder: Subfolder within storage
        
        Returns:
            Relative path to saved file
        """
        if not filename:
            filename = f"{uuid.uuid4()}.mp3"
        
        folder_path = os.path.join(self.storage_path, subfolder)
        os.makedirs(folder_path, exist_ok=True)
        
        file_path = os.path.join(folder_path, filename)
        
        # Write file asynchronously
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._write_file, file_path, audio_bytes)
        
        return f"/storage/{subfolder}/{filename}"
    
    def _write_file(self, path: str, data: bytes):
        """Synchronous file write"""
        with open(path, "wb") as f:
            f.write(data)
    
    async def get_audio_duration(self, file_path: str) -> float:
        """
        Get duration of an audio file in seconds.
        
        Args:
            file_path: Path to audio file
        
        Returns:
            Duration in seconds
        """
        # Convert relative path to absolute if needed
        if file_path.startswith("/storage/"):
            file_path = os.path.join(self.storage_path, file_path[9:])
        
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        
        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                raise AudioProcessingError(f"ffprobe failed: {stderr.decode()}")
            
            return float(stdout.decode().strip())
            
        except ValueError as e:
            raise AudioProcessingError(f"Failed to parse duration: {e}")
        except FileNotFoundError:
            raise AudioProcessingError("ffprobe not found. Please install FFmpeg.")
    
    async def merge_audio_parts(
        self,
        audio_parts: List[bytes],
        output_filename: Optional[str] = None
    ) -> str:
        """
        Merge multiple audio parts into one file.
        
        Args:
            audio_parts: List of audio bytes
            output_filename: Optional output filename
        
        Returns:
            Path to merged audio file
        """
        if len(audio_parts) == 1:
            # Only one part, just save it
            return await self.save_audio(audio_parts[0], output_filename)
        
        # Save parts to temp files
        temp_files = []
        list_file_path = os.path.join(self.temp_path, f"{uuid.uuid4()}_list.txt")
        
        try:
            for i, audio in enumerate(audio_parts):
                temp_path = os.path.join(self.temp_path, f"{uuid.uuid4()}_part{i}.mp3")
                with open(temp_path, "wb") as f:
                    f.write(audio)
                temp_files.append(temp_path)
            
            # Create concat list file
            with open(list_file_path, "w") as f:
                for temp_file in temp_files:
                    f.write(f"file '{temp_file}'\n")
            
            # Output path
            if not output_filename:
                output_filename = f"{uuid.uuid4()}.mp3"
            output_path = os.path.join(self.storage_path, "audio", output_filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # FFmpeg concat command
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", list_file_path,
                "-c", "copy",
                output_path
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                raise AudioProcessingError(f"FFmpeg concat failed: {stderr.decode()}")
            
            return f"/storage/audio/{output_filename}"
            
        finally:
            # Cleanup temp files
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except:
                    pass
            try:
                os.remove(list_file_path)
            except:
                pass
    
    async def merge_voice_with_sounds(
        self,
        voice_audio_path: str,
        sounds: List[Dict[str, Any]],
        output_filename: Optional[str] = None
    ) -> str:
        """
        Merge voice audio with sound effects at specific times.
        
        Args:
            voice_audio_path: Path to voice audio
            sounds: List of sound dicts with url, start_time, duration
            output_filename: Optional output filename
        
        Returns:
            Path to merged audio
        """
        if not sounds:
            return voice_audio_path
        
        # Convert paths
        if voice_audio_path.startswith("/storage/"):
            voice_audio_path = os.path.join(self.storage_path, voice_audio_path[9:])
        
        # Download/prepare sound files
        sound_files = []
        for sound in sounds:
            sound_path = sound.get("local_path") or sound.get("url", "")
            if sound_path.startswith("/storage/"):
                sound_path = os.path.join(self.storage_path, sound_path[9:])
            sound_files.append({
                "path": sound_path,
                "start_time": sound.get("start_time", 0),
                "duration": sound.get("duration", 3)
            })
        
        # Build FFmpeg filter complex
        inputs = ["-i", voice_audio_path]
        filter_parts = []
        
        for i, sound in enumerate(sound_files):
            inputs.extend(["-i", sound["path"]])
            delay_ms = int(sound["start_time"] * 1000)
            filter_parts.append(f"[{i+1}]adelay={delay_ms}|{delay_ms}[s{i}]")
        
        # Mix all sounds with voice
        if len(sound_files) == 1:
            filter_complex = f"{filter_parts[0]};[0][s0]amix=inputs=2:duration=first"
        else:
            filter_complex = ";".join(filter_parts)
            mix_inputs = "[0]" + "".join(f"[s{i}]" for i in range(len(sound_files)))
            filter_complex += f";{mix_inputs}amix=inputs={len(sound_files)+1}:duration=first"
        
        # Output path
        if not output_filename:
            output_filename = f"{uuid.uuid4()}.mp3"
        output_path = os.path.join(self.storage_path, "audio", output_filename)
        
        cmd = ["ffmpeg", "-y"] + inputs + [
            "-filter_complex", filter_complex,
            "-c:a", "libmp3lame",
            "-q:a", str(AUDIO_SETTINGS["output_quality"]),
            output_path
        ]
        
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {stderr.decode()}")
            raise AudioProcessingError(f"Sound merge failed: {stderr.decode()[:500]}")
        
        return f"/storage/audio/{output_filename}"
    
    async def merge_with_background_music(
        self,
        voice_audio_path: str,
        music_path: str,
        music_volume: float = 0.3,
        output_filename: Optional[str] = None
    ) -> str:
        """
        Merge voice audio with background music.
        
        Args:
            voice_audio_path: Path to voice audio
            music_path: Path to background music
            music_volume: Volume of background music (0.0-1.0)
            output_filename: Optional output filename
        
        Returns:
            Path to merged audio
        """
        # Convert paths
        if voice_audio_path.startswith("/storage/"):
            voice_audio_path = os.path.join(self.storage_path, voice_audio_path[9:])
        if music_path.startswith("/storage/"):
            music_path = os.path.join(self.storage_path, music_path[9:])
        
        # Output path
        if not output_filename:
            output_filename = f"{uuid.uuid4()}.mp3"
        output_path = os.path.join(self.storage_path, "audio", output_filename)
        
        # FFmpeg command with music volume adjustment and duration match
        filter_complex = f"[1]volume={music_volume}[music];[0][music]amix=inputs=2:duration=first"
        
        cmd = [
            "ffmpeg", "-y",
            "-i", voice_audio_path,
            "-i", music_path,
            "-filter_complex", filter_complex,
            "-c:a", "libmp3lame",
            "-q:a", str(AUDIO_SETTINGS["output_quality"]),
            output_path
        ]
        
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {stderr.decode()}")
            raise AudioProcessingError(f"Music merge failed: {stderr.decode()[:500]}")
        
        return f"/storage/audio/{output_filename}"
    
    async def full_merge(
        self,
        voice_audio_path: str,
        sounds: Optional[List[Dict[str, Any]]] = None,
        music_path: Optional[str] = None,
        voice_volume: float = 1.0,
        sounds_volume: float = 0.8,
        music_volume: float = 0.3,
        output_filename: Optional[str] = None
    ) -> str:
        """
        Full audio merge: voice + sounds + music.
        
        Args:
            voice_audio_path: Path to voice audio
            sounds: List of sound effects
            music_path: Path to background music
            voice_volume: Voice volume
            sounds_volume: Sounds volume
            music_volume: Music volume
            output_filename: Optional output filename
        
        Returns:
            Path to final merged audio
        """
        # Convert main voice path
        if voice_audio_path.startswith("/storage/"):
            abs_voice_path = os.path.join(self.storage_path, voice_audio_path[9:])
        else:
            abs_voice_path = voice_audio_path
        
        # Build inputs and filter
        inputs = ["-i", abs_voice_path]
        filter_parts = []
        current_output = "[0]"
        
        if voice_volume != 1.0:
            filter_parts.append(f"[0]volume={voice_volume}[v]")
            current_output = "[v]"
        
        # Add sounds
        if sounds:
            for i, sound in enumerate(sounds):
                sound_path = sound.get("local_path") or sound.get("url", "")
                if sound_path.startswith("/storage/"):
                    sound_path = os.path.join(self.storage_path, sound_path[9:])
                inputs.extend(["-i", sound_path])
                
                input_idx = len(inputs) // 2
                delay_ms = int(sound.get("start_time", 0) * 1000)
                filter_parts.append(
                    f"[{input_idx}]volume={sounds_volume},adelay={delay_ms}|{delay_ms}[s{i}]"
                )
            
            # Mix sounds with voice
            sound_inputs = "".join(f"[s{i}]" for i in range(len(sounds)))
            filter_parts.append(
                f"{current_output}{sound_inputs}amix=inputs={len(sounds)+1}:duration=first[vs]"
            )
            current_output = "[vs]"
        
        # Add music
        if music_path:
            if music_path.startswith("/storage/"):
                music_path = os.path.join(self.storage_path, music_path[9:])
            inputs.extend(["-i", music_path])
            
            music_idx = len(inputs) // 2
            filter_parts.append(f"[{music_idx}]volume={music_volume}[m]")
            filter_parts.append(f"{current_output}[m]amix=inputs=2:duration=first[out]")
            current_output = "[out]"
        
        # Build final filter complex
        if filter_parts:
            filter_complex = ";".join(filter_parts)
            # Remove brackets from final output if it's the only output
            if current_output.startswith("[") and current_output.endswith("]"):
                map_output = current_output
            else:
                map_output = None
        else:
            filter_complex = None
            map_output = None
        
        # Output path
        if not output_filename:
            output_filename = f"{uuid.uuid4()}.mp3"
        output_path = os.path.join(self.storage_path, "audio", output_filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Build command
        cmd = ["ffmpeg", "-y"] + inputs
        
        if filter_complex:
            cmd.extend(["-filter_complex", filter_complex])
            if map_output:
                cmd.extend(["-map", map_output])
        
        cmd.extend([
            "-c:a", "libmp3lame",
            "-q:a", str(AUDIO_SETTINGS["output_quality"]),
            output_path
        ])
        
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {stderr.decode()}")
            raise AudioProcessingError(f"Full merge failed: {stderr.decode()[:500]}")
        
        return f"/storage/audio/{output_filename}"
    
    async def cleanup_temp_files(self, max_age_hours: int = 24):
        """Clean up old temporary files"""
        import time
        
        now = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for filename in os.listdir(self.temp_path):
            file_path = os.path.join(self.temp_path, filename)
            try:
                if os.path.isfile(file_path):
                    file_age = now - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup {file_path}: {e}")
