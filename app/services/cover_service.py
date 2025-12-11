"""
Cover Service - kie.ai integration for cover generation
"""
import asyncio
import logging
from typing import Optional, List, Dict, Any

import httpx

from app.config import get_settings, KIEAI_BASE_URL, KIEAI_ENDPOINTS
from app.core.exceptions import KieAIError, MissingAPIKeyError
from app.core.security import decrypt_api_key
from app.models.user import User

settings = get_settings()
logger = logging.getLogger(__name__)


class CoverService:
    """Service for kie.ai cover generation"""
    
    def __init__(self, user: User):
        self.user = user
        self._api_key = None
    
    @property
    def api_key(self) -> str:
        """Get the API key (decrypted)"""
        if self._api_key:
            return self._api_key
        
        if self.user.kieai_api_key:
            self._api_key = decrypt_api_key(self.user.kieai_api_key)
        elif settings.default_kieai_api_key:
            self._api_key = settings.default_kieai_api_key
        else:
            raise MissingAPIKeyError("kie.ai")
        
        return self._api_key
    
    async def generate_cover(
        self,
        prompt: str,
        reference_image_url: Optional[str] = None,
        aspect_ratio: str = "1:1",
        resolution: str = "2K",
        callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a cover image.
        
        Args:
            prompt: Image generation prompt
            reference_image_url: Optional reference image URL
            aspect_ratio: Image aspect ratio
            resolution: Image resolution
            callback_url: Optional callback URL for async notification
        
        Returns:
            Dictionary with task_id and status
        """
        url = f"{KIEAI_BASE_URL}{KIEAI_ENDPOINTS['create_task']}"
        
        input_data = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "output_format": "png"
        }
        
        if reference_image_url:
            input_data["image_input"] = [reference_image_url]
        
        body = {
            "model": "nano-banana-pro",
            "input": input_data
        }
        
        if callback_url:
            body["callBackUrl"] = callback_url
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=body, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                return {
                    "task_id": data.get("taskId") or data.get("task_id"),
                    "status": "pending"
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"kie.ai task creation error: {e.response.status_code}")
            raise KieAIError(
                f"Task creation failed: {e.response.status_code}",
                details=e.response.text
            )
        except httpx.RequestError as e:
            logger.error(f"kie.ai request error: {e}")
            raise KieAIError(str(e))
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a cover generation task.
        
        Args:
            task_id: The task ID from generate_cover
        
        Returns:
            Dictionary with status and result if complete
        """
        url = f"{KIEAI_BASE_URL}{KIEAI_ENDPOINTS['record_info']}"
        params = {"taskId": task_id}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                state = data.get("state", "").lower()
                result = {
                    "task_id": task_id,
                    "status": state,
                    "url": None
                }
                
                if state == "success":
                    # Extract URL from resultJson
                    result_json = data.get("resultJson", {})
                    if isinstance(result_json, str):
                        import json
                        result_json = json.loads(result_json)
                    
                    # Try different possible URL locations
                    result["url"] = (
                        result_json.get("url") or
                        result_json.get("image_url") or
                        result_json.get("output", [{}])[0].get("url") if isinstance(result_json.get("output"), list) else None
                    )
                    
                    # If still no URL, try the data directly
                    if not result["url"]:
                        result["url"] = data.get("resultUrl") or data.get("url")
                
                elif state == "failed" or state == "error":
                    result["error"] = data.get("error") or data.get("message") or "Generation failed"
                
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"kie.ai status check error: {e.response.status_code}")
            raise KieAIError(
                f"Status check failed: {e.response.status_code}",
                details=e.response.text
            )
        except httpx.RequestError as e:
            logger.error(f"kie.ai request error: {e}")
            raise KieAIError(str(e))
    
    async def generate_cover_and_wait(
        self,
        prompt: str,
        reference_image_url: Optional[str] = None,
        aspect_ratio: str = "1:1",
        resolution: str = "2K",
        max_wait_seconds: int = 180,
        poll_interval: int = 5
    ) -> str:
        """
        Generate a cover and wait for completion.
        
        Args:
            prompt: Image generation prompt
            reference_image_url: Optional reference image URL
            aspect_ratio: Image aspect ratio
            resolution: Image resolution
            max_wait_seconds: Maximum time to wait
            poll_interval: Polling interval in seconds
        
        Returns:
            URL of the generated image
        """
        # Start generation
        result = await self.generate_cover(
            prompt=prompt,
            reference_image_url=reference_image_url,
            aspect_ratio=aspect_ratio,
            resolution=resolution
        )
        
        task_id = result["task_id"]
        if not task_id:
            raise KieAIError("No task ID returned")
        
        # Poll for completion
        elapsed = 0
        while elapsed < max_wait_seconds:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            
            status = await self.get_task_status(task_id)
            
            if status["status"] == "success":
                if status["url"]:
                    return status["url"]
                raise KieAIError("Generation succeeded but no URL returned")
            
            elif status["status"] in ["failed", "error"]:
                raise KieAIError(f"Generation failed: {status.get('error', 'Unknown error')}")
            
            # Still processing, continue polling
            logger.debug(f"Cover generation in progress: {status['status']}")
        
        raise KieAIError(f"Generation timed out after {max_wait_seconds} seconds")
    
    async def generate_multiple_covers(
        self,
        prompt: str,
        count: int = 1,
        reference_image_url: Optional[str] = None,
        aspect_ratio: str = "1:1",
        resolution: str = "2K"
    ) -> List[str]:
        """
        Generate multiple cover variants.
        
        Args:
            prompt: Image generation prompt
            count: Number of variants (1-4)
            reference_image_url: Optional reference image URL
            aspect_ratio: Image aspect ratio
            resolution: Image resolution
        
        Returns:
            List of image URLs
        """
        count = max(1, min(4, count))  # Clamp to 1-4
        
        # Start all generations in parallel
        tasks = []
        for _ in range(count):
            task = self.generate_cover_and_wait(
                prompt=prompt,
                reference_image_url=reference_image_url,
                aspect_ratio=aspect_ratio,
                resolution=resolution
            )
            tasks.append(task)
        
        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors and return successful URLs
        urls = []
        for result in results:
            if isinstance(result, str):
                urls.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Cover generation failed: {result}")
        
        if not urls:
            raise KieAIError("All cover generations failed")
        
        return urls
    
    def build_cover_prompt(
        self,
        title: str,
        genre_tone: str,
        description: str,
        template: Optional[str] = None
    ) -> str:
        """
        Build a cover generation prompt from episode/project data.
        
        Args:
            title: Story/episode title
            genre_tone: Genre and tone
            description: Story description
            template: Optional custom template
        
        Returns:
            Formatted prompt string
        """
        if template:
            return template.format(
                title=title,
                genre_tone=genre_tone,
                description=description
            )
        
        # Default prompt
        return f"""Create a cinematic audiobook cover for:
Title: {title}
Genre: {genre_tone}
Description: {description[:500]}

Style: Dark, atmospheric, professional audiobook cover art
Mood: Dramatic, cinematic
Format: Square, suitable for podcast/audiobook platforms
Do not include any text or letters in the image."""
