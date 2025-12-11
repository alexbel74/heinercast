"""
LLM Service - OpenRouter, Polza, OpenAI integration
"""
import json
import logging
from typing import Optional, List, Dict, Any

import httpx

from app.config import get_settings, LLM_PROVIDERS
from app.core.exceptions import LLMProviderError, MissingAPIKeyError
from app.core.security import decrypt_api_key
from app.models.user import User
from app.models.project import Project
from app.models.episode import Episode
from app.models.project_character import ProjectCharacter

settings = get_settings()
logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM API interactions"""
    
    def __init__(self, user: User):
        self.user = user
        self.provider = user.llm_provider or "openrouter"
        self.model = user.llm_model
        self._api_key = None
    
    @property
    def api_key(self) -> str:
        """Get the API key (decrypted if user has one, or use default)"""
        if self._api_key:
            return self._api_key
        
        if self.user.llm_api_key:
            self._api_key = decrypt_api_key(self.user.llm_api_key)
        elif self.provider == "openrouter" and settings.default_openrouter_api_key:
            self._api_key = settings.default_openrouter_api_key
        else:
            raise MissingAPIKeyError(f"LLM ({self.provider})")
        
        return self._api_key
    
    @property
    def base_url(self) -> str:
        """Get the base URL for the provider"""
        return LLM_PROVIDERS.get(self.provider, {}).get("base_url", "")
    
    def get_available_models(self) -> List[str]:
        """Get available models for the current provider"""
        return LLM_PROVIDERS.get(self.provider, {}).get("models", [])
    
    async def generate_script(
        self,
        project: Project,
        episode: Episode,
        characters: List[ProjectCharacter],
        previous_episodes: Optional[List[Episode]] = None,
        custom_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate a script for an episode.
        
        Args:
            project: The project containing the episode
            episode: The episode to generate script for
            characters: List of characters in the project
            previous_episodes: Previous episodes for context (if continuation)
            custom_prompt: Optional custom system prompt
            temperature: LLM temperature setting
        
        Returns:
            Script JSON with story_title, genre_tone, lines, etc.
        """
        # Build the context
        context = self._build_generation_context(
            project, episode, characters, previous_episodes
        )
        
        # Build messages
        system_prompt = custom_prompt or self.user.ai_writer_prompt
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context}
        ]
        
        # Make API call
        response = await self._chat_completion(messages, temperature)
        
        # Parse response
        script = self._parse_script_response(response)
        
        return script
    
    async def generate_summary(self, script_text: str) -> str:
        """
        Generate a summary of an episode for continuation context.
        
        Args:
            script_text: The full script text
        
        Returns:
            Summary string (3-5 sentences)
        """
        system_prompt = """You are a skilled summarizer. Create a concise summary (3-5 sentences) 
of the following audiobook episode script. Focus on:
- Key events and plot developments
- Character interactions and development
- The main conflict or tension
Do NOT spoil any final twists, but mention the core conflict."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Summarize this episode:\n\n{script_text}"}
        ]
        
        response = await self._chat_completion(messages, temperature=0.5)
        
        return response.strip()
    
    def _build_generation_context(
        self,
        project: Project,
        episode: Episode,
        characters: List[ProjectCharacter],
        previous_episodes: Optional[List[Episode]] = None
    ) -> str:
        """Build the context string for script generation"""
        
        # Build characters list
        characters_info = []
        for char in characters:
            char_info = {
                "role": char.role,
                "character_name": char.character_name,
                "voice_id": str(char.voice_id),
                "voice_name": char.voice.elevenlabs_name if char.voice else "Unknown"
            }
            characters_info.append(char_info)
        
        # Base context
        context_parts = [
            f"PROJECT TITLE: {project.title}",
            f"PROJECT DESCRIPTION: {project.description}",
            f"GENRE/TONE: {project.genre_tone}",
            "",
            f"EPISODE NUMBER: {episode.episode_number}",
            f"EPISODE DESCRIPTION: {episode.description}",
            f"TARGET DURATION: {episode.target_duration_minutes} minutes",
            "",
            "CHARACTERS:",
            json.dumps(characters_info, indent=2, ensure_ascii=False),
        ]
        
        # Add sound effects instruction if enabled
        if episode.include_sound_effects:
            context_parts.append("")
            context_parts.append("SOUND EFFECTS: Include sound_effect descriptions where appropriate (e.g., 'distant machinery humming', 'footsteps on gravel'). Set to null if no sound effect for that line.")
        else:
            context_parts.append("")
            context_parts.append("SOUND EFFECTS: Do NOT include sound effects (set all sound_effect to null)")
        
        # Add previous episodes context if this is a continuation
        if previous_episodes and len(previous_episodes) > 0:
            context_parts.append("")
            context_parts.append("=== PREVIOUS EPISODES CONTEXT ===")
            
            # Add summaries of all but the last episode
            if len(previous_episodes) > 1:
                context_parts.append("\nSUMMARIES OF EARLIER EPISODES:")
                for prev_ep in previous_episodes[:-1]:
                    if prev_ep.summary:
                        context_parts.append(f"\nEpisode {prev_ep.episode_number} ({prev_ep.title}):")
                        context_parts.append(prev_ep.summary)
            
            # Add full script of the immediately previous episode
            last_episode = previous_episodes[-1]
            if last_episode.script_text:
                context_parts.append(f"\nFULL SCRIPT OF PREVIOUS EPISODE ({last_episode.title}):")
                context_parts.append(last_episode.script_text[:10000])  # Limit length
        
        context_parts.append("")
        context_parts.append("=== GENERATE THE SCRIPT ===")
        context_parts.append("Create an engaging script that continues the story naturally. Return ONLY valid JSON.")
        
        return "\n".join(context_parts)
    
    async def _chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ) -> str:
        """Make a chat completion API call"""
        
        url = f"{self.base_url}/chat/completions"
        
        # Determine the model to use
        model = self.model
        if not model:
            models = self.get_available_models()
            model = models[0] if models else "gpt-4o-mini"
        
        # Build request body
        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 8000
        }
        
        # Add response format for JSON
        if "gpt" in model.lower() or "claude" in model.lower():
            body["response_format"] = {"type": "json_object"}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Add OpenRouter-specific headers
        if self.provider == "openrouter":
            headers["HTTP-Referer"] = settings.app_url
            headers["X-Title"] = settings.app_name
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=body, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                return content
                
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API error: {e.response.status_code} - {e.response.text}")
            raise LLMProviderError(
                self.provider,
                f"API returned {e.response.status_code}",
                details=e.response.text
            )
        except httpx.RequestError as e:
            logger.error(f"LLM request error: {e}")
            raise LLMProviderError(self.provider, str(e))
    
    def _parse_script_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into a script dictionary"""
        
        try:
            # Try to extract JSON from the response
            # Sometimes LLMs wrap JSON in markdown code blocks
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()
            
            script = json.loads(response)
            
            # Validate required fields
            required_fields = ["story_title", "genre_tone", "lines"]
            for field in required_fields:
                if field not in script:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate lines structure
            if not isinstance(script["lines"], list) or len(script["lines"]) == 0:
                raise ValueError("Script must have at least one line")
            
            for line in script["lines"]:
                if "speaker" not in line or "text" not in line:
                    raise ValueError("Each line must have 'speaker' and 'text' fields")
                
                # Ensure voice_id exists (even if empty)
                if "voice_id" not in line:
                    line["voice_id"] = ""
                
                # Ensure sound_effect exists
                if "sound_effect" not in line:
                    line["sound_effect"] = None
            
            # Add duration estimate if not present
            if "approx_duration_minutes" not in script:
                total_chars = sum(len(line["text"]) for line in script["lines"])
                script["approx_duration_minutes"] = max(1, total_chars // 850)
            
            return script
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse script JSON: {e}")
            logger.error(f"Response was: {response[:500]}...")
            raise LLMProviderError(
                self.provider,
                "Failed to parse script response as JSON",
                details=str(e)
            )
        except ValueError as e:
            logger.error(f"Script validation failed: {e}")
            raise LLMProviderError(
                self.provider,
                f"Invalid script structure: {e}"
            )
