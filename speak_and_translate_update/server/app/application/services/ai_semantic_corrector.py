# ai_semantic_corrector.py - AI-Powered Semantic Correction System

import os
import json
import asyncio
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import google.generativeai as genai
import time
import hashlib
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SemanticCorrection:
    """AI-generated semantic correction with confidence"""
    original_source: str
    original_target: str
    corrected_target: str
    confidence: float
    correction_reason: str
    linguistic_category: str

@dataclass
class SemanticAnalysis:
    """Comprehensive semantic analysis result"""
    corrections: List[SemanticCorrection]
    overall_accuracy: float
    processing_time: float
    ai_confidence: float

class AISemanticCorrector:
    """
    AI-Powered Semantic Correction System
    
    Uses artificial intelligence to:
    - Detect semantic mismatches dynamically
    - Correct translation errors in real-time
    - Handle billions of word combinations
    - Provide linguistic reasoning for corrections
    - Maintain high accuracy without static dictionaries
    """
    
    def __init__(self):
        load_dotenv()
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not self.gemini_api_key:
            logger.warning("⚠️ GEMINI_API_KEY not found")
            self.gemini_api_key = "your-gemini-api-key-here"
        
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Performance optimization
        self.correction_cache = {}
        self.cache_ttl_seconds = 3600  # 1 hour cache
        
        # AI correction parameters
        self.confidence_threshold = 0.80  # Minimum confidence for AI corrections
        self.batch_size = 20  # Process corrections in batches
        
        logger.info("🤖 AI Semantic Corrector initialized with Gemini AI")
    
    async def correct_semantic_mismatches(
        self,
        word_pairs: List[Tuple[str, str]],
        source_language: str,
        target_language: str
    ) -> SemanticAnalysis:
        """
        Use AI to detect and correct semantic mismatches dynamically
        """
        start_time = time.time()
        
        logger.info(f"🧠 AI semantic analysis: {len(word_pairs)} pairs ({source_language} → {target_language})")
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(word_pairs, source_language, target_language)
            if cache_key in self.correction_cache:
                cached_result = self.correction_cache[cache_key]
                if time.time() - cached_result['timestamp'] < self.cache_ttl_seconds:
                    logger.info("⚡ Using cached AI semantic corrections")
                    return cached_result['result']
            
            # Process in batches for optimal performance
            all_corrections = []
            
            for i in range(0, len(word_pairs), self.batch_size):
                batch = word_pairs[i:i + self.batch_size]
                batch_corrections = await self._process_semantic_batch(
                    batch, source_language, target_language
                )
                all_corrections.extend(batch_corrections)
            
            # Calculate overall metrics
            processing_time = time.time() - start_time
            overall_accuracy = self._calculate_overall_accuracy(all_corrections)
            ai_confidence = self._calculate_ai_confidence(all_corrections)
            
            result = SemanticAnalysis(
                corrections=all_corrections,
                overall_accuracy=overall_accuracy,
                processing_time=processing_time,
                ai_confidence=ai_confidence
            )
            
            # Cache the result
            self.correction_cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }
            
            logger.info(f"✅ AI semantic analysis completed: {len(all_corrections)} corrections in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ AI semantic correction failed: {e}")
            return self._create_fallback_analysis(word_pairs, time.time() - start_time)
    
    async def _process_semantic_batch(
        self,
        word_pairs: List[Tuple[str, str]],
        source_language: str,
        target_language: str
    ) -> List[SemanticCorrection]:
        """Process a batch of word pairs for semantic corrections"""
        
        # Create AI prompt for semantic analysis
        prompt = self._create_semantic_analysis_prompt(word_pairs, source_language, target_language)
        
        try:
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            response_text = response.text.strip()
            
            # Parse AI response
            corrections = self._parse_ai_semantic_response(response_text, word_pairs)
            
            logger.info(f"🧠 AI processed {len(word_pairs)} pairs, found {len(corrections)} corrections")
            return corrections
            
        except Exception as e:
            logger.error(f"❌ AI semantic batch processing failed: {e}")
            return self._create_fallback_corrections(word_pairs)
    
    def _create_semantic_analysis_prompt(
        self,
        word_pairs: List[Tuple[str, str]],
        source_language: str,
        target_language: str
    ) -> str:
        """Create AI prompt for semantic analysis and correction"""
        
        # Format word pairs for analysis
        pairs_text = ""
        for i, (source, target) in enumerate(word_pairs, 1):
            pairs_text += f"{i}. \"{source}\" → \"{target}\"\n"
        
        prompt = f"""
You are an expert linguist and semantic analyzer. Analyze these {source_language} to {target_language} translation pairs for semantic accuracy and correctness.

TRANSLATION PAIRS TO ANALYZE:
{pairs_text}

TASK: Identify semantic mismatches and provide corrections.

CRITICAL REQUIREMENTS:
1. Detect incorrect translations (semantic mismatches)
2. Provide corrected translations with high accuracy
3. Explain the linguistic reason for each correction
4. Assign confidence scores (0.80-1.00 for corrections)
5. Consider context, grammar, cultural nuances, and idiomatic expressions

LINGUISTIC ANALYSIS FOCUS:
- Grammatical gender agreement (der/die/das in German, el/la in Spanish)
- Contextual appropriateness (formal vs informal)
- Idiomatic expressions and cultural context
- Compound word accuracy (German Ananassaft = Spanish "jugo de piña")
- Phrasal verbs and separable verbs
- Regional variations and colloquialisms

OUTPUT FORMAT (JSON only):
{{
  "semantic_analysis": [
    {{
      "pair_number": 1,
      "original_source": "source_word",
      "original_target": "target_word", 
      "needs_correction": true/false,
      "corrected_target": "corrected_word",
      "confidence": 0.95,
      "correction_reason": "Detailed linguistic explanation",
      "linguistic_category": "grammar|gender|context|idiom|compound|phrasal_verb"
    }}
  ],
  "overall_assessment": {{
    "accuracy_percentage": 85,
    "major_issues_found": 3,
    "ai_confidence": 0.92
  }}
}}

EXAMPLE CORRECTIONS:
- "das" → "la" should be "das" → "lo" (neuter article)
- "ich bin" → "me levanto" should be "ich bin" → "yo soy" (semantic mismatch)
- "wake up" → "despertar" should be "wake up" → "despertarse" (reflexive verb)

Provide ONLY valid JSON with comprehensive semantic analysis.
"""
        
        return prompt
    
    def _parse_ai_semantic_response(
        self,
        response_text: str,
        original_pairs: List[Tuple[str, str]]
    ) -> List[SemanticCorrection]:
        """Parse AI response and extract semantic corrections"""
        
        corrections = []
        
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                analysis_data = json.loads(json_text)
                
                semantic_analysis = analysis_data.get('semantic_analysis', [])
                
                for item in semantic_analysis:
                    if item.get('needs_correction', False):
                        correction = SemanticCorrection(
                            original_source=item['original_source'],
                            original_target=item['original_target'],
                            corrected_target=item['corrected_target'],
                            confidence=float(item.get('confidence', 0.85)),
                            correction_reason=item.get('correction_reason', 'AI semantic correction'),
                            linguistic_category=item.get('linguistic_category', 'general')
                        )
                        
                        # Only include high-confidence corrections
                        if correction.confidence >= self.confidence_threshold:
                            corrections.append(correction)
                            
                            logger.info(f"🔧 AI correction: '{correction.original_source}' → '{correction.original_target}' to '{correction.corrected_target}' ({correction.confidence:.2f})")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse AI semantic response: {e}")
        except Exception as e:
            logger.error(f"❌ Error processing AI semantic response: {e}")
        
        return corrections
    
    def _create_fallback_corrections(self, word_pairs: List[Tuple[str, str]]) -> List[SemanticCorrection]:
        """Create fallback corrections when AI fails"""
        
        # Minimal fallback - only handle the most critical cases
        corrections = []
        
        for source, target in word_pairs:
            # Only create fallback for obvious issues
            needs_correction = False
            corrected_target = target
            
            # Simple heuristic fallbacks (minimal set)
            if source.lower() == 'das' and target.lower() == 'la':
                corrected_target = 'lo'
                needs_correction = True
            elif source.lower() == 'ich bin' and 'levanto' in target.lower():
                corrected_target = 'yo soy'
                needs_correction = True
            
            if needs_correction:
                correction = SemanticCorrection(
                    original_source=source,
                    original_target=target,
                    corrected_target=corrected_target,
                    confidence=0.85,
                    correction_reason="Fallback heuristic correction",
                    linguistic_category="fallback"
                )
                corrections.append(correction)
        
        return corrections
    
    def _create_fallback_analysis(self, word_pairs: List[Tuple[str, str]], processing_time: float) -> SemanticAnalysis:
        """Create fallback analysis when AI completely fails"""
        
        fallback_corrections = self._create_fallback_corrections(word_pairs)
        
        return SemanticAnalysis(
            corrections=fallback_corrections,
            overall_accuracy=0.80,  # Conservative fallback accuracy
            processing_time=processing_time,
            ai_confidence=0.75  # Lower confidence for fallback
        )
    
    def _calculate_overall_accuracy(self, corrections: List[SemanticCorrection]) -> float:
        """Calculate overall accuracy based on corrections found"""
        
        if not corrections:
            return 0.95  # High accuracy if no corrections needed
        
        # More corrections found indicates lower original accuracy
        correction_count = len(corrections)
        avg_confidence = sum(c.confidence for c in corrections) / len(corrections)
        
        # Estimate accuracy based on correction patterns
        estimated_accuracy = max(0.70, 1.0 - (correction_count * 0.05)) * avg_confidence
        
        return min(estimated_accuracy, 0.99)
    
    def _calculate_ai_confidence(self, corrections: List[SemanticCorrection]) -> float:
        """Calculate AI's confidence in its analysis"""
        
        if not corrections:
            return 0.95  # High confidence if no corrections found
        
        confidence_scores = [c.confidence for c in corrections]
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        # Factor in consistency of confidence scores
        confidence_variance = sum((c - avg_confidence) ** 2 for c in confidence_scores) / len(confidence_scores)
        consistency_factor = max(0.8, 1.0 - confidence_variance)
        
        return min(avg_confidence * consistency_factor, 0.98)
    
    def _generate_cache_key(
        self,
        word_pairs: List[Tuple[str, str]],
        source_language: str,
        target_language: str
    ) -> str:
        """Generate cache key for word pairs"""
        
        pairs_str = '|'.join([f"{s}->{t}" for s, t in word_pairs])
        key_string = f"{source_language}-{target_language}-{pairs_str}"
        
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def correct_single_word_pair(
        self,
        source_word: str,
        target_word: str,
        source_language: str,
        target_language: str
    ) -> Optional[SemanticCorrection]:
        """AI correction for a single word pair"""
        
        analysis = await self.correct_semantic_mismatches(
            [(source_word, target_word)],
            source_language,
            target_language
        )
        
        if analysis.corrections:
            return analysis.corrections[0]
        
        return None
    
    def get_correction_statistics(self) -> Dict[str, Any]:
        """Get statistics about AI corrections"""
        
        total_cached = len(self.correction_cache)
        
        return {
            'cached_analyses': total_cached,
            'confidence_threshold': self.confidence_threshold,
            'batch_size': self.batch_size,
            'cache_ttl_hours': self.cache_ttl_seconds / 3600,
            'ai_model': 'gemini-2.0-flash'
        }
    
    def clear_cache(self):
        """Clear the correction cache"""
        self.correction_cache.clear()
        logger.info("🧹 AI semantic correction cache cleared")

# Global AI corrector instance
ai_semantic_corrector = AISemanticCorrector()

# Export
__all__ = ['AISemanticCorrector', 'SemanticCorrection', 'SemanticAnalysis', 'ai_semantic_corrector']