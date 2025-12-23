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



# Cover style presets for AI audiobooks
COVER_STYLES = {
    "auto": {
        "name": "Auto (AI выберет)",
        "instructions": "",
        "mood": ""
    },
    "cyberpunk_neon": {
        "name": "Cyberpunk Neon",
        "instructions": "Neon lights, rain-soaked streets, holographic billboards, pink/cyan/purple color scheme, futuristic cityscape, glowing UI elements, reflective surfaces",
        "mood": "electric, dangerous, high-tech"
    },
    "tech_noir": {
        "name": "Tech Noir", 
        "instructions": "Dark corporate aesthetics, glass skyscrapers, cold blue lighting, deep shadows, silhouettes against screens, minimal color palette with blue/grey/black",
        "mood": "mysterious, corporate, cold, ominous"
    },
    "digital_glitch": {
        "name": "Digital Glitch",
        "instructions": "Pixelated elements, data corruption effects, matrix-style falling code, RGB color split, scan lines, digital artifacts, fragmented imagery",
        "mood": "unstable, corrupted, digital chaos"
    },
    "split_reality": {
        "name": "Split Reality",
        "instructions": "Mirror effects, duality theme, person shown twice (human and AI version), fragmented reality, half-human half-digital face, identity crisis visual",
        "mood": "questioning identity, duality, transformation"
    },
    "blade_runner": {
        "name": "Blade Runner Style",
        "instructions": "Rainy megacity at night, massive billboards, flying vehicles, dense urban environment, orange and teal color grading, atmospheric fog, retrofuturism",
        "mood": "melancholic, noir, dystopian beauty"
    },
    "clean_futurism": {
        "name": "Clean Futurism",
        "instructions": "Minimalist future aesthetics, white and light grey spaces, holographic interfaces, clean lines, soft lighting, Apple-style design, sterile environment",
        "mood": "pristine, controlled, utopian surface"
    },
    "corporate_dystopia": {
        "name": "Corporate Dystopia",
        "instructions": "Oppressive office environments, surveillance cameras, identical workers, grey cubicles, corporate logos, dehumanizing architecture, fluorescent lighting",
        "mood": "oppressive, conformist, soulless"
    },
    "neural_network": {
        "name": "Neural Network",
        "instructions": "Abstract neural connections, glowing synapses, brain-like structures, data flowing through networks, constellation-like patterns, deep blue and purple",
        "mood": "intellectual, vast, interconnected"
    },
    "holographic": {
        "name": "Holographic",
        "instructions": "Translucent holographic projections, light refracting effects, floating UI elements, person interacting with holograms, iridescent colors",
        "mood": "advanced, ethereal, technological wonder"
    },
    "retro_futurism": {
        "name": "Retro Futurism 80s",
        "instructions": "1980s vision of future, synthwave aesthetics, chrome and neon, grid lines, sunset gradients, VHS artifacts, geometric shapes",
        "mood": "nostalgic, stylized, synth-wave"
    },
    "photorealistic": {
        "name": "Photorealistic",
        "instructions": "Hyperrealistic photography style, real human faces, cinematic lighting, shallow depth of field, movie still quality, natural skin textures",
        "mood": "grounded, believable, cinematic"
    },
    "illustrated_artistic": {
        "name": "Illustrated Artistic",
        "instructions": "Digital painting style, visible brush strokes, artistic interpretation, concept art quality, rich colors, stylized proportions",
        "mood": "artistic, interpretive, expressive"
    },
    "minimalist_typography": {
        "name": "Minimalist",
        "instructions": "Simple geometric shapes, bold solid colors, negative space, abstract representation, single focal element, clean composition",
        "mood": "elegant, sophisticated, modern"
    },
    "cinematic_poster": {
        "name": "Cinematic Movie Poster",
        "instructions": "Hollywood movie poster composition, dramatic character poses, layered depth with background action, epic scale, lens flares, dramatic lighting",
        "mood": "epic, blockbuster, dramatic"
    },
    "dark_atmospheric": {
        "name": "Dark Atmospheric",
        "instructions": "Heavy shadows, fog and mist, single light source, mysterious silhouettes, moody color grading, noir influence, tension in composition",
        "mood": "tense, mysterious, foreboding"
    },
    "server_room": {
        "name": "Server Room / Data Center",
        "instructions": "Rows of servers with blinking lights, blue LED illumination, cables and hardware, person among machines, technological cathedral",
        "mood": "overwhelming technology, digital heart"
    },
    "surveillance": {
        "name": "Surveillance State",
        "instructions": "Multiple camera feeds, facial recognition overlays, tracking data, watched from above, privacy invasion theme, green night vision",
        "mood": "paranoid, watched, no privacy"
    },
    "android_human": {
        "name": "Android/Human Boundary",
        "instructions": "Humanoid robots, synthetic skin revealing machinery, uncanny valley aesthetics, human eyes in robot face, identity questioning",
        "mood": "uncanny, philosophical, boundary-blurring"
    }
}

# Diverse style sets for multiple variants
DIVERSE_STYLE_SETS = {
    2: [["cyberpunk_neon", "tech_noir"], ["blade_runner", "photorealistic"], ["digital_glitch", "split_reality"]],
    3: [["cyberpunk_neon", "tech_noir", "split_reality"], ["blade_runner", "dark_atmospheric", "photorealistic"]],
    4: [["cyberpunk_neon", "tech_noir", "split_reality", "blade_runner"], ["dark_atmospheric", "photorealistic", "digital_glitch", "cinematic_poster"]]
}


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
        reference_image_urls: Optional[List[str]] = None,
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
        
        if reference_image_urls:
            # Convert relative paths to full URLs for kie.ai
            full_urls = []
            for img_url in reference_image_urls:
                if img_url.startswith("/storage"):
                    img_url = f"http://37.233.81.221:8000{img_url}"
                full_urls.append(img_url)
            input_data["image_input"] = full_urls
        
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
                logger.info(f"Making POST request to URL: {url}")
                response = await client.post(url, json=body, headers=headers)
                logger.info(f"kie.ai request body: {body}")
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"kie.ai API response: {data}")
                
                return {
                    "task_id": data.get("taskId") or data.get("task_id") or (data.get("data", {}) or {}).get("taskId") or (data.get("data", {}) or {}).get("task_id"),
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
                logger.info(f"kie.ai API response: {data}")
                
                # Handle nested data structure
                inner_data = data.get("data", data)
                state = inner_data.get("state", "").lower()
                result = {
                    "task_id": task_id,
                    "status": state,
                    "url": None
                }
                
                if state == "success":
                    # Extract URL from resultJson
                    result_json = inner_data.get("resultJson", {})
                    if isinstance(result_json, str):
                        import json
                        result_json = json.loads(result_json)
                    
                    # Try resultUrls array first
                    result_urls = result_json.get("resultUrls", [])
                    if result_urls:
                        result["url"] = result_urls[0]
                    else:
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
        reference_image_urls: Optional[List[str]] = None,
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
            reference_image_urls=reference_image_urls,
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
        prompt: str = None,
        prompts: List[str] = None,
        count: int = 1,
        reference_image_urls: Optional[List[str]] = None,
        aspect_ratio: str = "1:1",
        resolution: str = "2K"
    ) -> List[str]:
        """
        Generate multiple cover variants with different prompts.

        Args:
            prompt: Single prompt (used for all if prompts not provided)
            prompts: List of different prompts for each variant
            count: Number of variants (1-4)
            reference_image_urls: Optional reference image URLs
            aspect_ratio: Image aspect ratio
            resolution: Image resolution

        Returns:
            List of image URLs
        """
        count = max(1, min(4, count))  # Clamp to 1-4
        
        # Build prompts list
        if prompts and len(prompts) >= count:
            prompt_list = prompts[:count]
        elif prompt:
            prompt_list = [prompt] * count
        else:
            raise ValueError("Either prompt or prompts must be provided")

        # Start all generations in parallel with different prompts
        tasks = []
        for i in range(count):
            task = self.generate_cover_and_wait(
                prompt=prompt_list[i],
                reference_image_urls=reference_image_urls,
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
    
    def get_styles_for_variants(self, num_variants: int, preferred_style: str = "auto") -> list:
        """Get list of styles for multiple variants."""
        if num_variants == 1:
            return [preferred_style if preferred_style != "auto" else "dark_atmospheric"]
        
        if preferred_style != "auto":
            all_styles = list(COVER_STYLES.keys())
            all_styles.remove("auto")
            if preferred_style in all_styles:
                all_styles.remove(preferred_style)
            import random
            random.shuffle(all_styles)
            return [preferred_style] + all_styles[:num_variants-1]
        
        import random
        style_sets = DIVERSE_STYLE_SETS.get(num_variants, DIVERSE_STYLE_SETS[4])
        chosen_set = random.choice(style_sets) if style_sets else list(COVER_STYLES.keys())[1:num_variants+1]
        return chosen_set[:num_variants]

    def build_cover_prompt(
        self,
        title: str,
        genre_tone: str,
        description: str,
        template: Optional[str] = None,
        style: str = "auto",
        episode_number: Optional[int] = None,
        project_title: Optional[str] = None,
        additional_instructions: Optional[str] = None,
        summary: Optional[str] = None
    ) -> str:
        """Build a cover generation prompt with style support."""
        # Get style settings (always needed)
        style_data = COVER_STYLES.get(style, COVER_STYLES.get("auto", {}))
        style_instructions = style_data.get("instructions", "")
        style_mood = style_data.get("mood", "dramatic, cinematic")
        
        # Build series info
        series_info = ""
        if project_title:
            series_info = f"Series: {project_title}\n"
        if episode_number:
            series_info += f"Episode: #{episode_number}\n"

        # Build style section
        if style != "auto" and style_instructions:
            style_section = f"""
VISUAL STYLE: {style_data.get('name', style)}
{style_instructions}
Mood: {style_mood}"""
        else:
            style_section = """
VISUAL STYLE: Cinematic, atmospheric, professional audiobook cover art
Dark and moody lighting, high production value
Mood: Dramatic, suspenseful, technological"""

        # Additional instructions
        extra = ""
        if additional_instructions:
            extra = f"\n\nADDITIONAL REQUIREMENTS:\n{additional_instructions}"

        # Extract episode title without "Эпизод X —" prefix
        episode_title_clean = title
        if " — " in title:
            episode_title_clean = title.split(" — ", 1)[-1]
        
        # Build synopsis
        synopsis_text = (summary if summary else description)[:500]
        
        # Default prompt template
        default_template = """Create a professional audiobook cover image.

STORY CONTENT:
{series_info}Title: {title}
Genre: {genre_tone}
Synopsis: {synopsis}
{style_section}

COMPOSITION & TEXT:
- Main visual in CENTER - striking and memorable
- High contrast for readability at small sizes
- Add text overlay:
  * TOP: "АУДИОКНИГА" (small elegant text)
  * BELOW TOP: "{series_name} {episode_num}" (series + number)
  * CENTER: "{episode_title}" (main title, large cinematic font)
- Professional typography with good contrast against background{extra}"""

        # Use custom template if provided, otherwise default
        prompt_template = template if template and template.strip() else default_template
        
        # Format the template
        try:
            return prompt_template.format(
                series_info=series_info,
                title=title,
                genre_tone=genre_tone,
                synopsis=synopsis_text,
                style_section=style_section,
                series_name=project_title or "",
                episode_num=episode_number or "",
                episode_title=episode_title_clean,
                extra=extra
            )
        except KeyError:
            return default_template.format(
                series_info=series_info,
                title=title,
                genre_tone=genre_tone,
                synopsis=synopsis_text,
                style_section=style_section,
                series_name=project_title or "",
                episode_num=episode_number or "",
                episode_title=episode_title_clean,
                extra=extra
            )
