
# server/app/domain/entities/translation.py
from typing import Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class Translation(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    audio_path: Optional[str] = None
    translations: Optional[Dict[str, str]] = None
    word_by_word: Optional[Dict[str, Dict[str, str]]] = None
    grammar_explanations: Optional[Dict[str, str]] = None
    created_at: datetime = Field(default_factory=datetime.now)

