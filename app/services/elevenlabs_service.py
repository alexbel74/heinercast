"""
ElevenLabs Service - Text-to-Speech, Sound Effects, Music
"""
import base64
import json
import logging
import os
from typing import Optional, List, Dict, Any, Tuple

import httpx

from app.config import get_settings, ELEVENLABS_BASE_URL, ELEVENLABS_ENDPOINTS, AUDIO_SETTINGS
from app.core.exceptions import ElevenLabsError, MissingAPIKeyError
from app.core.security import decrypt_api_key
from app.models.user import User

settings = get_settings()
logger = logging.getLogger(__name__)


class ElevenLabsService:
    """Service for ElevenLabs API interactions"""
    
    def __init__(self, user: User):
        self.user = user
        self._api_key = None
    
    @property
    def api_key(self) -> str:
        """Get the API key (decrypted)"""
        if self._api_key:
            return self._api_key
        
        if self.user.elevenlabs_api_key:
            self._api_key = decrypt_api_key(self.user.elevenlabs_api_key)
        elif settings.default_elevenlabs_api_key:
            self._api_key = settings.default_elevenlabs_api_key
        else:
            raise MissingAPIKeyError("ElevenLabs")
        
        return self._api_key
    
    async def text_to_dialogue(
        self,
        lines: List[Dict[str, Any]],
        model_id: str = "eleven_multilingual_v2"
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Generate dialogue audio from script lines.
        
        Args:
            lines: List of script lines with speaker, voice_id, text
            model_id: ElevenLabs model to use
        
        Returns:
            Tuple of (audio_bytes, timestamps_data)
        """
        url = f"{ELEVENLABS_BASE_URL}{ELEVENLABS_ENDPOINTS['text_to_dialogue']}"
        
        # Prepare inputs for ElevenLabs
        inputs = []
        for line in lines:
            inputs.append({
                "text": line["text"],
                "voice_id": line["voice_id"]
            })
        
        body = {
            "inputs": inputs,
            "model_id": model_id,
            "output_format": "mp3_44100_128"
        }
        
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(url, json=body, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract audio and timestamps
                audio_base64 = data.get("audio_base64", "")
                audio_bytes = base64.b64decode(audio_base64) if audio_base64 else b""
                
                timestamps = {
                    "voice_segments": data.get("voice_segments", []),
                    "alignment": data.get("alignment", {})
                }
                
                return audio_bytes, timestamps
                
        except httpx.HTTPStatusError as e:
            logger.error(f"ElevenLabs API error: {e.response.status_code} - {e.response.text}")
            raise ElevenLabsError(
                f"API returned {e.response.status_code}",
                details=e.response.text
            )
        except httpx.RequestError as e:
            logger.error(f"ElevenLabs request error: {e}")
            raise ElevenLabsError(str(e))
    
    async def generate_dialogue_in_parts(
        self,
        lines: List[Dict[str, Any]],
        model_id: str = "eleven_multilingual_v2"
    ) -> Tuple[List[bytes], List[Dict[str, Any]]]:
        """
        Generate dialogue in parts if script is too long.
        
        Returns:
            Tuple of (list of audio_bytes, list of timestamps)
        """
        parts = self._split_into_parts(lines)
        
        audio_parts = []
        timestamps_parts = []
        
        for part in parts:
            audio_bytes, timestamps = await self.text_to_dialogue(part, model_id)
            audio_parts.append(audio_bytes)
            timestamps_parts.append(timestamps)
        
        return audio_parts, timestamps_parts
    
    def _split_into_parts(
        self,
        lines: List[Dict[str, Any]],
        max_parts: int = 3
    ) -> List[List[Dict[str, Any]]]:
        """
        Split script lines into parts for API requests.
        Does not split individual lines.
        """
        total_chars = sum(len(line["text"]) for line in lines)
        
        # If within limit, return as single part
        if total_chars <= AUDIO_SETTINGS["max_chars_per_request"]:
            return [lines]
        
        target_chars_per_part = total_chars / max_parts
        
        parts = []
        current_part = []
        current_length = 0
        
        for line in lines:
            # Start new part if we've reached target and have room for more parts
            if (current_length >= target_chars_per_part and 
                len(parts) < max_parts - 1 and
                current_part):
                parts.append(current_part)
                current_part = []
                current_length = 0
            
            current_part.append(line)
            current_length += len(line["text"])
        
        if current_part:
            parts.append(current_part)
        
        return parts
    
    async def generate_sound_effect(
        self,
        prompt: str,
        duration_seconds: float = 3.0,
        prompt_influence: float = 0.3
    ) -> bytes:
        """
        Generate a sound effect.
        
        Args:
            prompt: Description of the sound effect
            duration_seconds: Duration of the sound
            prompt_influence: How much the prompt influences generation
        
        Returns:
            Audio bytes
        """
        url = f"{ELEVENLABS_BASE_URL}{ELEVENLABS_ENDPOINTS['sound_generation']}"
        
        body = {
            "text": prompt,
            "duration_seconds": duration_seconds,
            "prompt_influence": prompt_influence
        }
        
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=body, headers=headers)
                response.raise_for_status()
                
                return response.content
                
        except httpx.HTTPStatusError as e:
            logger.error(f"ElevenLabs sound generation error: {e.response.status_code}")
            raise ElevenLabsError(
                f"Sound generation failed: {e.response.status_code}",
                details=e.response.text
            )
        except httpx.RequestError as e:
            logger.error(f"ElevenLabs request error: {e}")
            raise ElevenLabsError(str(e))
    
    async def create_music_plan(
        self,
        prompt: str,
        duration_ms: int
    ) -> Dict[str, Any]:
        """
        Create a music composition plan.
        
        Args:
            prompt: Description of the music
            duration_ms: Duration in milliseconds
        
        Returns:
            Composition plan dictionary
        """
        url = f"{ELEVENLABS_BASE_URL}{ELEVENLABS_ENDPOINTS['music_plan']}"
        
        body = {
            "prompt": prompt,
            "music_length_ms": duration_ms
        }
        
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=body, headers=headers)
                response.raise_for_status()
                
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"ElevenLabs music plan error: {e.response.status_code}")
            raise ElevenLabsError(
                f"Music plan creation failed: {e.response.status_code}",
                details=e.response.text
            )
        except httpx.RequestError as e:
            logger.error(f"ElevenLabs request error: {e}")
            raise ElevenLabsError(str(e))
    
    async def generate_music(
        self,
        composition_plan: Dict[str, Any],
        force_instrumental: bool = True
    ) -> bytes:
        """
        Generate music from a composition plan.
        
        Args:
            composition_plan: The composition plan from create_music_plan
            force_instrumental: Force instrumental (no vocals)
        
        Returns:
            Audio bytes
        """
        url = f"{ELEVENLABS_BASE_URL}{ELEVENLABS_ENDPOINTS['music']}"
        
        body = {
            "composition_plan": composition_plan,
            "force_instrumental": force_instrumental
        }
        
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(url, json=body, headers=headers)
                response.raise_for_status()
                
                return response.content
                
        except httpx.HTTPStatusError as e:
            logger.error(f"ElevenLabs music generation error: {e.response.status_code}")
            raise ElevenLabsError(
                f"Music generation failed: {e.response.status_code}",
                details=e.response.text
            )
        except httpx.RequestError as e:
            logger.error(f"ElevenLabs request error: {e}")
            raise ElevenLabsError(str(e))
    
    async def get_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available voices.
        
        Returns:
            List of voice dictionaries
        """
        url = f"{ELEVENLABS_BASE_URL}{ELEVENLABS_ENDPOINTS['voices']}"
        
        headers = {
            "xi-api-key": self.api_key
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                return data.get("voices", [])
                
        except httpx.HTTPStatusError as e:
            logger.error(f"ElevenLabs voices error: {e.response.status_code}")
            raise ElevenLabsError(
                f"Failed to get voices: {e.response.status_code}",
                details=e.response.text
            )
        except httpx.RequestError as e:
            logger.error(f"ElevenLabs request error: {e}")
            raise ElevenLabsError(str(e))
    
    async def test_voice(
        self,
        voice_id: str,
        text: str = "Hello, this is a voice test."
    ) -> bytes:
        """
        Test a voice with a short text.
        
        Args:
            voice_id: ElevenLabs voice ID
            text: Text to speak
        
        Returns:
            Audio bytes
        """
        # Use text-to-dialogue with a single line
        lines = [{"text": text, "voice_id": voice_id}]
        audio_bytes, _ = await self.text_to_dialogue(lines)
        return audio_bytes
