"""
Summary Service - Generate episode summaries for continuation context
"""
import logging
from typing import Optional

from app.services.llm_service import LLMService
from app.models.user import User
from app.models.episode import Episode

logger = logging.getLogger(__name__)


class SummaryService:
    """Service for generating episode summaries"""
    
    def __init__(self, user: User):
        self.user = user
        self.llm_service = LLMService(user)
    
    async def generate_summary(self, episode: Episode) -> str:
        """
        Generate a summary for an episode.
        
        Args:
            episode: The episode to summarize
        
        Returns:
            Summary string (3-5 sentences)
        """
        if not episode.script_text:
            return ""
        
        return await self.llm_service.generate_summary(episode.script_text)
    
    async def update_episode_summary(self, episode: Episode) -> str:
        """
        Generate and return a summary for the episode.
        Note: The caller is responsible for saving to database.
        
        Args:
            episode: The episode to summarize
        
        Returns:
            Generated summary
        """
        summary = await self.generate_summary(episode)
        return summary
    
    def build_script_text_from_json(self, script_json: dict) -> str:
        """
        Build a readable text version of the script from JSON.
        
        Args:
            script_json: Script JSON with lines
        
        Returns:
            Formatted script text
        """
        if not script_json or "lines" not in script_json:
            return ""
        
        lines = []
        
        # Add title if present
        if script_json.get("story_title"):
            lines.append(f"# {script_json['story_title']}")
            lines.append("")
        
        # Add genre/tone if present
        if script_json.get("genre_tone"):
            lines.append(f"*{script_json['genre_tone']}*")
            lines.append("")
        
        # Add dialogue lines
        for line in script_json["lines"]:
            speaker = line.get("speaker", "Unknown")
            text = line.get("text", "")
            sound_effect = line.get("sound_effect")
            
            lines.append(f"**{speaker}**: {text}")
            
            if sound_effect:
                lines.append(f"  🔊 [{sound_effect}]")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def extract_key_events(self, script_json: dict, max_events: int = 5) -> list:
        """
        Extract key events from a script for quick reference.
        
        Args:
            script_json: Script JSON
            max_events: Maximum number of events to extract
        
        Returns:
            List of key event descriptions
        """
        if not script_json or "lines" not in script_json:
            return []
        
        events = []
        lines = script_json["lines"]
        
        # Simple heuristic: lines with sound effects often indicate key moments
        for line in lines:
            if line.get("sound_effect") and len(events) < max_events:
                events.append({
                    "speaker": line.get("speaker", "Unknown"),
                    "context": line.get("text", "")[:100],
                    "sound": line.get("sound_effect")
                })
        
        # If not enough events, add some from the beginning and end
        if len(events) < max_events and len(lines) > 0:
            # Add first line
            first_line = lines[0]
            events.insert(0, {
                "speaker": first_line.get("speaker", "Unknown"),
                "context": first_line.get("text", "")[:100],
                "position": "opening"
            })
        
        if len(events) < max_events and len(lines) > 1:
            # Add last line
            last_line = lines[-1]
            events.append({
                "speaker": last_line.get("speaker", "Unknown"),
                "context": last_line.get("text", "")[:100],
                "position": "closing"
            })
        
        return events[:max_events]
