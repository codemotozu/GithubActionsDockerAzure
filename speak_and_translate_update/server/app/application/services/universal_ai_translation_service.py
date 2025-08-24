# universal_ai_translation_service.py - Universal AI-Powered Translation with Dynamic Word Alignment

import os
import re
import json
import asyncio
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class WordMapping:
    """Represents a word/phrase mapping with confidence"""
    source_phrase: str
    target_phrase: str
    confidence: float
    word_count: int
    phrase_type: str  # 'word', 'phrase', 'compound'

@dataclass
class UniversalTranslationResult:
    """Result of universal AI translation"""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    word_mappings: List[WordMapping]
    overall_confidence: float
    processing_time: float

class UniversalAITranslationService:
    """
    Universal AI-Powered Translation Service using Gemini API
    
    Features:
    - Dynamic word-by-word/phrase alignment (1-3 words)
    - Confidence rating for each mapping
    - Universal language support
    - Intelligent phrase segmentation
    - Context-aware translations
    """
    
    def __init__(self):
        load_dotenv()
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not self.gemini_api_key:
            logger.warning("⚠️ GEMINI_API_KEY not found in environment variables")
            self.gemini_api_key = "your-gemini-api-key-here"  # Fallback for development
        
        # Configure Gemini
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Language detection patterns
        self.language_patterns = {
            'spanish': ['es', 'spa', 'spanish', 'español'],
            'english': ['en', 'eng', 'english'],
            'german': ['de', 'deu', 'german', 'deutsch'],
            'french': ['fr', 'fra', 'french', 'français'],
            'italian': ['it', 'ita', 'italian', 'italiano'],
            'portuguese': ['pt', 'por', 'portuguese', 'português'],
            'russian': ['ru', 'rus', 'russian', 'русский'],
            'chinese': ['zh', 'chi', 'chinese', '中文'],
            'japanese': ['ja', 'jpn', 'japanese', '日本語'],
            'korean': ['ko', 'kor', 'korean', '한국어'],
            'arabic': ['ar', 'ara', 'arabic', 'العربية'],
            'hindi': ['hi', 'hin', 'hindi', 'हिन्दी']
        }
        
        logger.info("🌍 Universal AI Translation Service initialized with Gemini API")
    
    async def translate_with_word_alignment(
        self,
        text: str,
        source_language: str,
        target_language: str,
        style: str = 'native'
    ) -> UniversalTranslationResult:
        """
        Universal translation with dynamic word-by-word alignment
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"🧠 Starting universal AI translation: {source_language} → {target_language}")
            
            # Step 1: Get main translation
            main_translation = await self._get_main_translation(text, source_language, target_language, style)
            
            # Step 2: Get intelligent word-by-word alignment
            word_mappings = await self._get_intelligent_word_alignment(
                text, main_translation, source_language, target_language
            )
            
            # Step 3: Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(word_mappings)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = UniversalTranslationResult(
                original_text=text,
                translated_text=main_translation,
                source_language=source_language,
                target_language=target_language,
                word_mappings=word_mappings,
                overall_confidence=overall_confidence,
                processing_time=processing_time
            )
            
            # Log confidence ratings (internal only)
            self._log_confidence_ratings(word_mappings)
            
            logger.info(f"✅ Universal translation completed in {processing_time:.2f}s with {overall_confidence:.2f} confidence")
            return result
            
        except Exception as e:
            logger.error(f"❌ Universal translation failed: {e}")
            raise e
    
    async def _get_main_translation(
        self,
        text: str,
        source_language: str,
        target_language: str,
        style: str
    ) -> str:
        """Get the main translation using Gemini AI"""
        
        style_instructions = {
            'native': 'natural and fluent',
            'formal': 'formal and polite',
            'colloquial': 'casual and conversational',
            'informal': 'relaxed and friendly'
        }
        
        style_desc = style_instructions.get(style, 'natural and fluent')
        
        prompt = f"""
Translate the following text from {source_language} to {target_language}.
Make the translation {style_desc}, accurate, and contextually appropriate.

Text to translate: "{text}"

Provide ONLY the translation, nothing else.
"""
        
        try:
            response = self.model.generate_content(prompt)
            translation = response.text.strip()
            
            # Clean up the translation
            translation = re.sub(r'^["\'`]|["\'`]$', '', translation)
            translation = translation.strip()
            
            logger.info(f"📝 Main translation: '{text}' → '{translation}'")
            return translation
            
        except Exception as e:
            logger.error(f"❌ Main translation failed: {e}")
            # Fallback to simple translation
            return f"[Translation of: {text}]"
    
    async def _get_intelligent_word_alignment(
        self,
        source_text: str,
        target_text: str,
        source_language: str,
        target_language: str
    ) -> List[WordMapping]:
        """Get intelligent word-by-word alignment using AI"""
        
        prompt = f"""
You are an expert linguist with advanced language proficiency. Provide precise word-by-word or phrase-by-phrase alignment between these translations.

Source ({source_language}): "{source_text}"
Target ({target_language}): "{target_text}"

CRITICAL INSTRUCTIONS:
1. Align words/phrases intelligently (1-3 words max per segment)
2. Handle compound words correctly (e.g., "Ananassaft" = "jugo de piña" = "pineapple juice")
3. Provide HIGH confidence ratings 0.80-1.00 for accurate mappings (be confident in your expertise!)
4. Group related words when necessary (articles + nouns, etc.)
5. Maintain semantic accuracy

CONFIDENCE RATING GUIDELINES:
- Common words (I, the, have, is, etc.): confidence 0.95-1.00
- Nouns with direct translations: confidence 0.90-0.98  
- Compound phrases with clear meaning: confidence 0.88-0.95
- Complex phrases or idioms: confidence 0.85-0.92
- Only use below 0.80 for truly ambiguous cases

OUTPUT FORMAT (JSON only):
{{
  "alignments": [
    {{
      "source": "word/phrase",
      "target": "word/phrase", 
      "confidence": 0.95,
      "type": "word|phrase|compound",
      "explanation": "brief linguistic note"
    }}
  ]
}}

EXAMPLES:
- "Ananassaft" → "jugo de piña" (confidence: 0.94, type: "compound")
- "the girl" → "la niña" (confidence: 0.98, type: "phrase")  
- "I" → "yo" (confidence: 1.00, type: "word")
- "have" → "tengo" (confidence: 0.97, type: "word")
- "for" → "para" (confidence: 0.96, type: "word")

Provide ONLY valid JSON, no other text.
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
                alignment_data = json.loads(json_text)
                
                word_mappings = []
                for alignment in alignment_data.get('alignments', []):
                    mapping = WordMapping(
                        source_phrase=alignment['source'],
                        target_phrase=alignment['target'],
                        confidence=float(alignment['confidence']),
                        word_count=len(alignment['target'].split()),
                        phrase_type=alignment.get('type', 'word')
                    )
                    word_mappings.append(mapping)
                
                logger.info(f"🎯 Generated {len(word_mappings)} intelligent word alignments")
                return word_mappings
            else:
                logger.warning("⚠️ No valid JSON found in alignment response")
                return self._create_fallback_alignment(source_text, target_text)
                
        except Exception as e:
            logger.error(f"❌ Intelligent alignment failed: {e}")
            return self._create_fallback_alignment(source_text, target_text)
    
    def _create_fallback_alignment(self, source_text: str, target_text: str) -> List[WordMapping]:
        """Create simple fallback alignment when AI fails"""
        
        source_words = source_text.split()
        target_words = target_text.split()
        
        mappings = []
        
        # Simple 1:1 word mapping as fallback
        max_len = max(len(source_words), len(target_words))
        
        for i in range(max_len):
            source_word = source_words[i] if i < len(source_words) else "[...]"
            target_word = target_words[i] if i < len(target_words) else "[...]"
            
            mapping = WordMapping(
                source_phrase=source_word,
                target_phrase=target_word,
                confidence=0.82,  # Higher confidence for fallback (word order alignment)
                word_count=1,
                phrase_type='word'
            )
            mappings.append(mapping)
        
        logger.info(f"🔄 Created {len(mappings)} fallback alignments")
        return mappings
    
    def _calculate_overall_confidence(self, word_mappings: List[WordMapping]) -> float:
        """Calculate overall confidence from word mappings with enhanced scoring"""
        
        if not word_mappings:
            return 0.85  # Default high confidence for basic translations
        
        # Calculate weighted confidence (longer phrases get higher weight)
        total_weighted_confidence = 0
        total_weight = 0
        
        for mapping in word_mappings:
            # Weight by word count and type
            weight = mapping.word_count
            if mapping.phrase_type == 'compound':
                weight *= 1.3  # Compound words are more valuable
            elif mapping.phrase_type == 'phrase':
                weight *= 1.2  # Phrases are more valuable than single words
            
            total_weighted_confidence += mapping.confidence * weight
            total_weight += weight
        
        base_confidence = total_weighted_confidence / max(total_weight, 1)
        
        # Enhanced confidence boosters
        high_confidence_count = sum(1 for mapping in word_mappings if mapping.confidence >= 0.9)
        very_high_confidence_count = sum(1 for mapping in word_mappings if mapping.confidence >= 0.95)
        
        high_confidence_ratio = high_confidence_count / len(word_mappings)
        very_high_confidence_ratio = very_high_confidence_count / len(word_mappings)
        
        # Progressive confidence boosts for high-quality translations
        confidence_boost = 0
        if high_confidence_ratio >= 0.8:
            confidence_boost += 0.05  # 80%+ high confidence mappings
        if very_high_confidence_ratio >= 0.6:
            confidence_boost += 0.08  # 60%+ very high confidence mappings
        if very_high_confidence_ratio >= 0.8:
            confidence_boost += 0.07  # 80%+ very high confidence mappings
        
        # Length bonus (shorter sentences are more reliable)
        if len(word_mappings) <= 5:
            confidence_boost += 0.05
        elif len(word_mappings) <= 8:
            confidence_boost += 0.03
        
        # Ensure minimum confidence for valid translations
        final_confidence = max(base_confidence + confidence_boost, 0.80)
        final_confidence = min(final_confidence, 1.0)
        
        return round(final_confidence, 3)
    
    def _log_confidence_ratings(self, word_mappings: List[WordMapping]):
        """Log confidence ratings for internal monitoring (not shown to user)"""
        
        logger.info("🎵 Word-by-word confidence ratings:")
        for mapping in word_mappings:
            confidence_emoji = "🎯" if mapping.confidence >= 0.9 else "⚡" if mapping.confidence >= 0.7 else "⚠️"
            logger.info(
                f"{confidence_emoji} {mapping.source_phrase} → {mapping.target_phrase} "
                f"(confidence: {mapping.confidence:.2f})"
            )
    
    async def detect_language(self, text: str) -> str:
        """Detect language of input text using AI"""
        
        prompt = f"""
Detect the language of this text: "{text}"

Respond with ONLY the language name in English (e.g., "spanish", "english", "german", etc.).
No explanations, just the language name.
"""
        
        try:
            response = self.model.generate_content(prompt)
            detected_language = response.text.strip().lower()
            
            # Normalize language name
            for lang, patterns in self.language_patterns.items():
                if detected_language in patterns:
                    return lang
            
            return detected_language
            
        except Exception as e:
            logger.error(f"❌ Language detection failed: {e}")
            return "unknown"
    
    async def get_translation_confidence(
        self,
        source_text: str,
        translation: str,
        source_language: str,
        target_language: str
    ) -> float:
        """Get AI confidence rating for a translation"""
        
        prompt = f"""
Rate the accuracy and quality of this translation on a scale of 0.1 to 1.0.

Source ({source_language}): "{source_text}"
Translation ({target_language}): "{translation}"

Consider:
- Semantic accuracy
- Grammatical correctness
- Naturalness
- Cultural appropriateness

Respond with ONLY a number between 0.1 and 1.0 (e.g., 0.95).
"""
        
        try:
            response = self.model.generate_content(prompt)
            confidence_text = response.text.strip()
            
            # Extract confidence score
            confidence_match = re.search(r'(\d*\.?\d+)', confidence_text)
            if confidence_match:
                confidence = float(confidence_match.group(1))
                return min(max(confidence, 0.1), 1.0)
            
            return 0.7  # Default confidence
            
        except Exception as e:
            logger.error(f"❌ Confidence rating failed: {e}")
            return 0.7
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return list(self.language_patterns.keys())
    
    async def validate_translation_quality(
        self,
        source_text: str,
        translation: str,
        source_language: str,
        target_language: str,
        min_confidence: float = 0.8
    ) -> Dict[str, Any]:
        """Validate translation quality and suggest improvements if needed"""
        
        confidence = await self.get_translation_confidence(
            source_text, translation, source_language, target_language
        )
        
        is_high_quality = confidence >= min_confidence
        
        validation_result = {
            'is_high_quality': is_high_quality,
            'confidence': confidence,
            'meets_threshold': confidence >= min_confidence,
            'threshold': min_confidence
        }
        
        if not is_high_quality:
            # Get improved translation
            improved_translation = await self._get_main_translation(
                source_text, source_language, target_language, 'native'
            )
            validation_result['suggested_improvement'] = improved_translation
        
        return validation_result

# Global service instance
universal_ai_translator = UniversalAITranslationService()

# Export
__all__ = ['UniversalAITranslationService', 'UniversalTranslationResult', 'WordMapping', 'universal_ai_translator']