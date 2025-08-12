# server/app/domain/entities/translation.py - Enhanced for UI visualization

from typing import Dict, Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime

class WordByWordEntry(BaseModel):
    """
    Individual word-by-word entry for UI visualization.
    This ensures what's shown matches exactly what's heard.
    """
    source: str = Field(description="Source word/phrase (e.g., 'wake up', 'stehe auf')")
    spanish: str = Field(description="Spanish equivalent (e.g., 'despertar', 'me levanto')")
    language: str = Field(description="Source language ('german', 'english')")
    style: str = Field(description="Translation style (e.g., 'german_colloquial')")
    order: int = Field(description="Order in the sequence for audio playback")
    is_phrasal_verb: bool = Field(description="Whether this is a phrasal/separable verb")
    display_format: str = Field(description="Exact format as heard in audio: [word] ([spanish])")

class Translation(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    audio_path: Optional[str] = None
    translations: Optional[Dict[str, str]] = None
    
    # Enhanced word-by-word data for UI visualization
    # Key is unique identifier, value contains all UI display info
    word_by_word: Optional[Dict[str, Dict[str, Any]]] = Field(
        default=None,
        description="Enhanced word-by-word data structure for UI visualization. "
                   "Ensures frontend displays exactly what's heard in audio."
    )
    
    grammar_explanations: Optional[Dict[str, str]] = None
    created_at: datetime = Field(default_factory=datetime.now)

    def add_word_by_word_entry(
        self, 
        key: str, 
        source: str, 
        spanish: str, 
        language: str, 
        style: str, 
        order: int, 
        is_phrasal_verb: bool = False
    ):
        """
        Add a word-by-word entry with proper formatting for UI visualization.
        EXACT format: [target word] ([Spanish equivalent])
        """
        if self.word_by_word is None:
            self.word_by_word = {}
        
        display_format = f"[{source}] ([{spanish}])"
        
        self.word_by_word[key] = {
            "source": source,
            "spanish": spanish,
            "language": language,
            "style": style,
            "order": str(order),  # Convert to string for JSON compatibility
            "is_phrasal_verb": str(is_phrasal_verb).lower(),  # Convert to string
            "display_format": display_format
        }
    
    def get_word_pairs_by_language(self, language: str) -> List[Dict[str, Any]]:
        """Get all word pairs for a specific language, sorted by order."""
        if not self.word_by_word:
            return []
        
        pairs = []
        for key, data in self.word_by_word.items():
            if data.get('language') == language:
                pairs.append({
                    'key': key,
                    **data,
                    'order': int(data.get('order', 0))  # Convert back to int for sorting
                })
        
        # Sort by order
        pairs.sort(key=lambda x: x['order'])
        return pairs
    
    def get_available_languages(self) -> List[str]:
        """Get list of languages that have word-by-word data."""
        if not self.word_by_word:
            return []
        
        languages = set()
        for data in self.word_by_word.values():
            language = data.get('language')
            if language:
                languages.add(language)
        
        return sorted(list(languages))
    
    def has_word_by_word_for_language(self, language: str) -> bool:
        """Check if word-by-word data exists for a specific language."""
        return len(self.get_word_pairs_by_language(language)) > 0
    
    def count_word_pairs_by_language(self) -> Dict[str, int]:
        """Count word pairs by language."""
        if not self.word_by_word:
            return {}
        
        counts = {}
        for data in self.word_by_word.values():
            language = data.get('language', 'unknown')
            counts[language] = counts.get(language, 0) + 1
        
        return counts
    
    def get_phrasal_verbs_by_language(self, language: str) -> List[Dict[str, Any]]:
        """Get only phrasal/separable verbs for a specific language."""
        pairs = self.get_word_pairs_by_language(language)
        return [pair for pair in pairs if pair.get('is_phrasal_verb') == 'true']
    
    def debug_word_by_word_structure(self) -> str:
        """Generate debug information about the word-by-word structure."""
        if not self.word_by_word:
            return "📝 No word-by-word data available"
        
        debug_info = []
        debug_info.append("📝 WORD-BY-WORD DATA STRUCTURE:")
        debug_info.append("="*50)
        
        languages = self.get_available_languages()
        debug_info.append(f"Available languages: {', '.join(languages)}")
        
        counts = self.count_word_pairs_by_language()
        debug_info.append(f"Word pair counts: {counts}")
        
        debug_info.append("\nDetailed breakdown:")
        for key, data in self.word_by_word.items():
            debug_info.append(f"Key: {key}")
            debug_info.append(f"  Source: {data.get('source')}")
            debug_info.append(f"  Spanish: {data.get('spanish')}")
            debug_info.append(f"  Language: {data.get('language')}")
            debug_info.append(f"  Style: {data.get('style')}")
            debug_info.append(f"  Order: {data.get('order')}")
            debug_info.append(f"  Is Phrasal Verb: {data.get('is_phrasal_verb')}")
            debug_info.append(f"  Display Format: {data.get('display_format')}")
            debug_info.append("")
        
        debug_info.append("="*50)
        return "\n".join(debug_info)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }