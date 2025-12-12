"""
ElevenLabs Service - Text-to-Speech, Sound Effects, Music
"""
import base64
import json
import logging
import os
from typing import Optional, List, Dict, Any, Tuple
import os
PROXY_URL = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")

import httpx

from app.config import (
    get_settings, ELEVENLABS_BASE_URL, ELEVENLABS_ENDPOINTS, 
    AUDIO_SETTINGS, ELEVENLABS_MODEL_ID
)
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
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for ElevenLabs API requests"""
        return {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def text_to_dialogue(
        self,
        lines: List[Dict[str, Any]],
        model_id: str = ELEVENLABS_MODEL_ID
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Generate dialogue audio from script lines.
        
        Args:
            lines: List of script lines with speaker, voice_id, text
            model_id: ElevenLabs model to use (default: eleven_v3)
        
        Returns:
            Tuple of (audio_bytes, timestamps_data)
        """
        url = f"{ELEVENLABS_BASE_URL}{ELEVENLABS_ENDPOINTS['text_to_dialogue']}"
        
        # Prepare inputs for ElevenLabs API
        # Format: [{"text": "...", "voice_id": "..."}, ...]
        inputs = []
        for line in lines:
            input_item = {
                "text": line["text"],
                "voice_id": line["voice_id"]
            }
            inputs.append(input_item)
        
        # Request body - ВАЖНО: model_id обязателен!
        body = {
            "inputs": inputs,
            "model_id": model_id  # eleven_v3
        }
        
        logger.info(f"ElevenLabs text_to_dialogue: {len(inputs)} lines, model={model_id}")
        logger.debug(f"Request body: {json.dumps(body, ensure_ascii=False)[:500]}...")
        
        try:
            async with httpx.AsyncClient(timeout=300.0, proxy=PROXY_URL) as client:
                response = await client.post(
                    url, 
                    json=body, 
                    headers=self._get_headers()
                )
                
                # Log response status
                logger.info(f"ElevenLabs response status: {response.status_code}")
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"ElevenLabs API error: {response.status_code} - {error_text}")
                    raise ElevenLabsError(
                        f"API returned {response.status_code}",
                        details=self._parse_error(error_text)
                    )
                
                data = response.json()
                
                # Extract audio and timestamps
                audio_base64 = data.get("audio_base64", "")
                audio_bytes = base64.b64decode(audio_base64) if audio_base64 else b""
                
                if not audio_bytes:
                    logger.warning("ElevenLabs returned empty audio")
                
                timestamps = {
                    "voice_segments": data.get("voice_segments", []),
                    "alignment": data.get("alignment", {})
                }
                
                logger.info(f"ElevenLabs audio generated: {len(audio_bytes)} bytes")
                
                return audio_bytes, timestamps
                
        except httpx.HTTPStatusError as e:
            error_details = self._parse_error(e.response.text)
            logger.error(f"ElevenLabs API error: {e.response.status_code} - {error_details}")
            raise ElevenLabsError(
                f"API returned {e.response.status_code}",
                details=error_details
            )
        except httpx.RequestError as e:
            logger.error(f"ElevenLabs request error: {e}")
            raise ElevenLabsError(f"Request failed: {str(e)}")
        except Exception as e:
            logger.error(f"ElevenLabs unexpected error: {e}")
            raise ElevenLabsError(f"Unexpected error: {str(e)}")
    
    def _parse_error(self, error_text: str) -> str:
        """Parse error response and return user-friendly message"""
        try:
            error_data = json.loads(error_text)
            if "detail" in error_data:
                detail = error_data["detail"]
                if isinstance(detail, dict):
                    return detail.get("message", str(detail))
                return str(detail)
            if "error" in error_data:
                return error_data["error"]
            if "message" in error_data:
                return error_data["message"]
            return error_text
        except json.JSONDecodeError:
            return error_text
    
    async def generate_dialogue_in_parts(
        self,
        lines: List[Dict[str, Any]],
        model_id: str = ELEVENLABS_MODEL_ID
    ) -> Tuple[List[bytes], List[Dict[str, Any]]]:
        """
        Generate dialogue in parts if script is too long.
        
        Returns:
            Tuple of (list of audio_bytes, list of timestamps)
        """
        parts = self._split_into_parts(lines)
        
        logger.info(f"Generating dialogue in {len(parts)} part(s)")
        
        audio_parts = []
        timestamps_parts = []
        
        for i, part in enumerate(parts):
            logger.info(f"Processing part {i+1}/{len(parts)} ({len(part)} lines)")
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
        
        logger.info(f"Generating sound effect: {prompt[:50]}...")
        
        try:
            async with httpx.AsyncClient(timeout=120.0, proxy=PROXY_URL) as client:
                response = await client.post(
                    url, 
                    json=body, 
                    headers=self._get_headers()
                )
                
                if response.status_code != 200:
                    error_details = self._parse_error(response.text)
                    logger.error(f"Sound generation error: {response.status_code} - {error_details}")
                    raise ElevenLabsError(
                        f"Sound generation failed: {response.status_code}",
                        details=error_details
                    )
                
                logger.info(f"Sound effect generated: {len(response.content)} bytes")
                return response.content
                
        except httpx.RequestError as e:
            logger.error(f"ElevenLabs request error: {e}")
            raise ElevenLabsError(f"Request failed: {str(e)}")
    
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
        
        logger.info(f"Creating music plan: {prompt[:50]}..., duration={duration_ms}ms")
        
        try:
            async with httpx.AsyncClient(timeout=60.0, proxy=PROXY_URL) as client:
                response = await client.post(
                    url, 
                    json=body, 
                    headers=self._get_headers()
                )
                
                if response.status_code != 200:
                    error_details = self._parse_error(response.text)
                    logger.error(f"Music plan error: {response.status_code} - {error_details}")
                    raise ElevenLabsError(
                        f"Music plan creation failed: {response.status_code}",
                        details=error_details
                    )
                
                plan = response.json()
                logger.info(f"Music plan created successfully")
                return plan
                
        except httpx.RequestError as e:
            logger.error(f"ElevenLabs request error: {e}")
            raise ElevenLabsError(f"Request failed: {str(e)}")
    
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
            
        }
        
        logger.info(f"Generating music, instrumental={force_instrumental}")
        
        try:
            async with httpx.AsyncClient(timeout=300.0, proxy=PROXY_URL) as client:
                response = await client.post(
                    url, 
                    json=body, 
                    headers=self._get_headers()
                )
                
                if response.status_code != 200:
                    error_details = self._parse_error(response.text)
                    logger.error(f"Music generation error: {response.status_code} - {error_details}")
                    raise ElevenLabsError(
                        f"Music generation failed: {response.status_code}",
                        details=error_details
                    )
                
                logger.info(f"Music generated: {len(response.content)} bytes")
                return response.content
                
        except httpx.RequestError as e:
            logger.error(f"ElevenLabs request error: {e}")
            raise ElevenLabsError(f"Request failed: {str(e)}")
    
    async def get_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available voices.
        
        Returns:
            List of voice dictionaries
        """
        url = f"{ELEVENLABS_BASE_URL}{ELEVENLABS_ENDPOINTS['voices']}"
        
        logger.info("Fetching available voices from ElevenLabs")
        
        try:
            async with httpx.AsyncClient(timeout=30.0, proxy=PROXY_URL) as client:
                response = await client.get(
                    url, 
                    headers=self._get_headers()
                )
                
                if response.status_code != 200:
                    error_details = self._parse_error(response.text)
                    logger.error(f"Voices fetch error: {response.status_code} - {error_details}")
                    raise ElevenLabsError(
                        f"Failed to get voices: {response.status_code}",
                        details=error_details
                    )
                
                data = response.json()
                voices = data.get("voices", [])
                logger.info(f"Found {len(voices)} voices")
                return voices
                
        except httpx.RequestError as e:
            logger.error(f"ElevenLabs request error: {e}")
            raise ElevenLabsError(f"Request failed: {str(e)}")
    
    async def test_voice(
        self,
        voice_id: str,
        text: str = "Привет! Это тест голоса. Hello! This is a voice test."
    ) -> bytes:
        """
        Test a voice with a short text.
        
        Args:
            voice_id: ElevenLabs voice ID
            text: Text to speak
        
        Returns:
            Audio bytes
        """
        logger.info(f"Testing voice: {voice_id}")
        
        # Use text-to-dialogue with a single line
        lines = [{"text": text, "voice_id": voice_id}]
        audio_bytes, _ = await self.text_to_dialogue(lines, model_id=ELEVENLABS_MODEL_ID)
        return audio_bytes
    
    async def validate_api_key(self) -> bool:
        """
        Validate that the API key is working.
        
        Returns:
            True if valid, raises exception otherwise
        """
        try:
            # Try to get user info or voices list
            await self.get_voices()
            return True
        except ElevenLabsError as e:
            if "401" in str(e) or "Unauthorized" in str(e):
                raise ElevenLabsError("Invalid API key", details="Please check your ElevenLabs API key")
            raise
