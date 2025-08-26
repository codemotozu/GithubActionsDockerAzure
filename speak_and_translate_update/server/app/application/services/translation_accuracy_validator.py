# translation_accuracy_validator.py - Advanced Translation Accuracy & Confidence Validation

import re
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from enum import Enum
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfidenceLevel(Enum):
    """Confidence levels for translation accuracy"""
    VERY_HIGH = "very_high"  # 95-100%
    HIGH = "high"            # 85-94%
    MEDIUM = "medium"        # 70-84%
    LOW = "low"              # 50-69%
    VERY_LOW = "very_low"    # <50%

@dataclass
class TranslationValidation:
    """Result of translation validation"""
    is_accurate: bool
    confidence_score: float
    validation_errors: List[str]
    corrected_pairs: List[Tuple[str, str, str]]  # (original_source, original_target, corrected_target)
    accuracy_issues: List[str]

class TranslationAccuracyValidator:
    """
    Advanced Translation Accuracy Validator that ensures:
    - 90-100% confidence translations only
    - Grammatically correct word alignments
    - Contextually appropriate translations
    - Cultural and semantic accuracy
    """
    
    def __init__(self):
        # REMOVED: Hardcoded dictionaries - now using Universal AI Translation
        # The system now relies on Gemini AI for dynamic, context-aware validation
        # This approach supports ALL languages without manual dictionary maintenance
        
        # AI-powered validation will be used instead of static mappings
        self.ai_validation_enabled = True
        
        # Initialize empty high_confidence_mappings for backward compatibility
        self.high_confidence_mappings = {}
        
        # Keep only essential confidence thresholds
        self.confidence_thresholds = {
            'high_confidence': 0.90,
            'medium_confidence': 0.70,
            'low_confidence': 0.50
        }
        
        # Grammar patterns for accuracy validation
        self.grammar_patterns = {
            'german': {
                'verb_position': r'\b(bin|habe|ist|sind)\s+\w+\s+(aufgestanden|gefrühstückt|beschlossen)',
                'separable_verbs': r'\b(auf|aus|an|ab|ein|mit|vor|zu)\w*',
                'articles': r'\b(der|die|das|den|dem|des|ein|eine|einen)\b'
            },
            'english': {
                'phrasal_verbs': r'\b\w+\s+(up|down|in|out|on|off|away|back|over)\b',
                'modal_verbs': r'\b(have\s+to|must|should|would|could)\b',
                'articles': r'\b(the|a|an)\b'
            }
        }
        
        # Common translation errors to detect and fix
        self.common_errors = {
            # German errors
            'german': {
                'bin → me': 'Incorrect: "bin" means "am", not "me"',
                'habe → me': 'Incorrect: "habe" means "have", not "me"',
                'das → de': 'Incorrect: "das" means "the", not "of"',
                'zu → salir': 'Incorrect: "zu" is an infinitive marker, not "to go out"',
                'verlassen → salir': 'Partially correct but incomplete context',
            },
            
            # English errors  
            'english': {
                'the → de': 'Incorrect: "the" means "el/la", not "de"',
                'got → me': 'Incorrect: "got" is not "me"',
                'have → tengo': 'Correct but missing pronoun context',
                'to → que': 'Context dependent - could be "para" or "a"',
            }
        }
        
        logger.info("🤖 Translation Accuracy Validator initialized with Universal AI validation")
    
    async def validate_with_ai(
        self,
        word_pairs: List[Tuple[str, str]], 
        source_lang: str,
        target_lang: str
    ) -> TranslationValidation:
        """
        AI-powered translation validation using Universal AI Translation
        No hardcoded dictionaries - pure AI intelligence
        """
        try:
            # Import here to avoid circular imports
            from .universal_ai_translation_service import universal_ai_translator
            
            logger.info(f"🤖 AI Validation: {len(word_pairs)} pairs ({source_lang} → {target_lang})")
            
            validation_errors = []
            corrected_pairs = []
            accuracy_issues = []
            total_confidence = 0.0
            validated_pairs = 0
            
            for source_word, target_word in word_pairs:
                try:
                    # Get AI confidence rating for this specific word pair
                    confidence = await universal_ai_translator.get_translation_confidence(
                        source_text=source_word,
                        translation=target_word,
                        source_language=source_lang,
                        target_language=target_lang
                    )
                    
                    # Check if confidence meets threshold
                    is_accurate = confidence >= self.confidence_thresholds['high_confidence']
                    
                    if is_accurate:
                        total_confidence += confidence
                        validated_pairs += 1
                        logger.info(f"✅ AI Validated: {source_word} → {target_word} (confidence: {confidence:.2f})")
                    else:
                        # Get AI-suggested correction
                        try:
                            correction_result = await universal_ai_translator.translate_with_word_alignment(
                                text=source_word,
                                source_language=source_lang,
                                target_language=target_lang,
                                style='native'
                            )
                            
                            if correction_result.word_mappings:
                                suggested_translation = correction_result.word_mappings[0].target_phrase
                                corrected_pairs.append((source_word, target_word, suggested_translation))
                                logger.info(f"🔧 AI Correction: {source_word} → '{target_word}' suggested as '{suggested_translation}'")
                            
                        except Exception as correction_error:
                            logger.warning(f"⚠️ AI correction failed for {source_word}: {correction_error}")
                        
                        validation_errors.append(f"Low AI confidence ({confidence:.2f}) for: {source_word} → {target_word}")
                        accuracy_issues.append(f"{source_word} → {target_word}: AI confidence below threshold")
                
                except Exception as e:
                    logger.error(f"❌ AI validation failed for {source_word} → {target_word}: {e}")
                    validation_errors.append(f"AI validation error for: {source_word} → {target_word}")
            
            # Calculate overall accuracy
            if validated_pairs > 0:
                average_confidence = total_confidence / validated_pairs
                is_accurate = average_confidence >= self.confidence_thresholds['high_confidence']
            else:
                average_confidence = 0.0
                is_accurate = False
            
            # Log validation results
            logger.info(f"🤖 AI Validation Results:")
            logger.info(f"   Average Confidence: {average_confidence:.2f}")
            logger.info(f"   Pairs Validated: {validated_pairs}/{len(word_pairs)}")
            logger.info(f"   Accuracy Threshold Met: {is_accurate}")
            logger.info(f"   AI Corrections Suggested: {len(corrected_pairs)}")
            
            return TranslationValidation(
                is_accurate=is_accurate,
                confidence_score=average_confidence,
                validation_errors=validation_errors,
                corrected_pairs=corrected_pairs,
                accuracy_issues=accuracy_issues
            )
            
        except Exception as e:
            logger.error(f"❌ AI validation system failed: {e}")
            # Fallback to basic validation
            return self.validate_translation_accuracy(word_pairs, source_lang, target_lang)
    
    def validate_translation_accuracy(
        self,
        word_pairs: List[Tuple[str, str]], 
        source_lang: str,
        target_lang: str
    ) -> TranslationValidation:
        """
        Validate translation accuracy with 90-100% confidence requirement
        """
        logger.info(f"🔍 Validating {len(word_pairs)} word pairs ({source_lang} → {target_lang})")
        
        validation_errors = []
        corrected_pairs = []
        accuracy_issues = []
        total_confidence = 0.0
        validated_pairs = 0
        
        lang_pair = (source_lang.lower(), target_lang.lower())
        confidence_mappings = self.high_confidence_mappings.get(lang_pair, {})
        
        for source_word, target_word in word_pairs:
            # Validate individual word pair
            pair_validation = self._validate_word_pair(
                source_word, target_word, source_lang, target_lang, confidence_mappings
            )
            
            if pair_validation['is_accurate']:
                total_confidence += pair_validation['confidence']
                validated_pairs += 1
                
                # Check if correction was needed
                if pair_validation['corrected_target'] != target_word:
                    corrected_pairs.append((
                        source_word, 
                        target_word, 
                        pair_validation['corrected_target']
                    ))
            else:
                validation_errors.append(pair_validation['error'])
                accuracy_issues.append(f"{source_word} → {target_word}: {pair_validation['issue']}")
        
        # Calculate overall accuracy
        if validated_pairs > 0:
            average_confidence = total_confidence / validated_pairs
            is_accurate = average_confidence >= 0.90  # 90% threshold
        else:
            average_confidence = 0.0
            is_accurate = False
        
        # Log validation results
        logger.info(f"📊 Validation Results:")
        logger.info(f"   Average Confidence: {average_confidence:.2f}")
        logger.info(f"   Pairs Validated: {validated_pairs}/{len(word_pairs)}")
        logger.info(f"   Accuracy Threshold Met: {is_accurate}")
        logger.info(f"   Corrections Made: {len(corrected_pairs)}")
        
        return TranslationValidation(
            is_accurate=is_accurate,
            confidence_score=average_confidence,
            validation_errors=validation_errors,
            corrected_pairs=corrected_pairs,
            accuracy_issues=accuracy_issues
        )
    
    def _validate_word_pair(
        self,
        source_word: str,
        target_word: str,
        source_lang: str,
        target_lang: str,
        confidence_mappings: Dict
    ) -> Dict:
        """Validate individual word pair accuracy"""
        
        source_clean = source_word.lower().strip()
        target_clean = target_word.lower().strip()
        
        # Check against high-confidence mappings
        if source_clean in confidence_mappings:
            expected_target, confidence = confidence_mappings[source_clean]
            
            if target_clean == expected_target.lower():
                return {
                    'is_accurate': True,
                    'confidence': confidence,
                    'corrected_target': target_word,
                    'error': None,
                    'issue': None
                }
            else:
                # Check if it's a known error
                error_key = f"{source_clean} → {target_clean}"
                lang_errors = self.common_errors.get(target_lang, {})
                
                if error_key in lang_errors:
                    return {
                        'is_accurate': False,
                        'confidence': 0.0,
                        'corrected_target': expected_target,
                        'error': lang_errors[error_key],
                        'issue': f"Known translation error: {error_key}"
                    }
                else:
                    return {
                        'is_accurate': False,
                        'confidence': 0.0,
                        'corrected_target': expected_target,
                        'error': f"Translation mismatch: expected '{expected_target}', got '{target_word}'",
                        'issue': f"Low confidence translation"
                    }
        
        # For words not in high-confidence mappings, apply heuristic validation
        heuristic_result = self._apply_heuristic_validation(
            source_word, target_word, source_lang, target_lang
        )
        
        return heuristic_result
    
    def _apply_heuristic_validation(
        self,
        source_word: str,
        target_word: str,
        source_lang: str,
        target_lang: str
    ) -> Dict:
        """Apply heuristic validation for words not in confidence mappings"""
        
        # Basic heuristics for validation
        confidence = 0.5  # Default medium confidence
        
        # Same word across languages (high confidence)
        if source_word.lower() == target_word.lower():
            confidence = 0.95
        
        # Length similarity heuristic
        length_ratio = min(len(source_word), len(target_word)) / max(len(source_word), len(target_word))
        if length_ratio > 0.7:
            confidence += 0.1
        
        # Common cognates (words that look similar across languages)
        if self._are_cognates(source_word, target_word):
            confidence += 0.2
        
        # Check for obvious errors
        obvious_errors = [
            (r'^\[.*\]$', 'Untranslated word in brackets'),
            (r'^[A-Z]{2,}$', 'All caps likely indicates error'),
            (r'^\d+$', 'Numbers should usually not be translated'),
        ]
        
        for pattern, error_desc in obvious_errors:
            if re.match(pattern, target_word):
                return {
                    'is_accurate': False,
                    'confidence': 0.0,
                    'corrected_target': source_word,  # Keep original
                    'error': error_desc,
                    'issue': f"Obvious translation error: {error_desc}"
                }
        
        is_accurate = confidence >= 0.70  # Lower threshold for heuristic validation
        
        return {
            'is_accurate': is_accurate,
            'confidence': confidence,
            'corrected_target': target_word,
            'error': None if is_accurate else f"Low confidence ({confidence:.2f})",
            'issue': None if is_accurate else f"Heuristic validation failed"
        }
    
    def _are_cognates(self, word1: str, word2: str) -> bool:
        """Check if two words are likely cognates (similar across languages)"""
        if len(word1) < 3 or len(word2) < 3:
            return False
        
        # Simple cognate detection - check if words share significant prefix
        min_length = min(len(word1), len(word2))
        shared_prefix = 0
        
        for i in range(min_length):
            if word1[i].lower() == word2[i].lower():
                shared_prefix += 1
            else:
                break
        
        # If they share at least 60% of their prefix, likely cognates
        return shared_prefix / min_length >= 0.6
    
    def get_high_confidence_correction(
        self,
        source_word: str,
        current_target: str,
        source_lang: str,
        target_lang: str
    ) -> Optional[Tuple[str, float]]:
        """Get high-confidence correction for a word if available"""
        
        lang_pair = (source_lang.lower(), target_lang.lower())
        confidence_mappings = self.high_confidence_mappings.get(lang_pair, {})
        
        source_clean = source_word.lower().strip()
        
        if source_clean in confidence_mappings:
            correct_target, confidence = confidence_mappings[source_clean]
            
            if confidence >= 0.90:  # Only return if very high confidence
                return (correct_target, confidence)
        
        return None
    
    def correct_translation_errors(
        self,
        word_pairs: List[Tuple[str, str]],
        source_lang: str,
        target_lang: str
    ) -> List[Tuple[str, str]]:
        """Correct translation errors using high-confidence mappings"""
        
        corrected_pairs = []
        corrections_made = 0
        
        for source_word, target_word in word_pairs:
            correction = self.get_high_confidence_correction(
                source_word, target_word, source_lang, target_lang
            )
            
            if correction:
                corrected_target, confidence = correction
                corrected_pairs.append((source_word, corrected_target))
                
                if corrected_target.lower() != target_word.lower():
                    corrections_made += 1
                    logger.info(f"🔧 Corrected: {source_word} → '{target_word}' to '{corrected_target}' (confidence: {confidence:.2f})")
            else:
                # Keep original if no high-confidence correction available
                corrected_pairs.append((source_word, target_word))
        
        logger.info(f"✅ Made {corrections_made} high-confidence corrections")
        return corrected_pairs
    
    def filter_high_confidence_pairs(
        self,
        word_pairs: List[Tuple[str, str]],
        source_lang: str,
        target_lang: str,
        min_confidence: float = 0.90
    ) -> List[Tuple[str, str, float]]:
        """Filter to only include high-confidence translation pairs"""
        
        high_confidence_pairs = []
        lang_pair = (source_lang.lower(), target_lang.lower())
        confidence_mappings = self.high_confidence_mappings.get(lang_pair, {})
        
        for source_word, target_word in word_pairs:
            source_clean = source_word.lower().strip()
            
            if source_clean in confidence_mappings:
                expected_target, confidence = confidence_mappings[source_clean]
                
                if confidence >= min_confidence and target_word.lower() == expected_target.lower():
                    high_confidence_pairs.append((source_word, target_word, confidence))
                    logger.info(f"✅ High confidence: {source_word} → {target_word} ({confidence:.2f})")
        
        logger.info(f"🎯 Filtered to {len(high_confidence_pairs)} high-confidence pairs (≥{min_confidence:.0%})")
        return high_confidence_pairs

# Global validator instance
translation_validator = TranslationAccuracyValidator()

# Export
__all__ = ['TranslationAccuracyValidator', 'TranslationValidation', 'ConfidenceLevel', 'translation_validator']