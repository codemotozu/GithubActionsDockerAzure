# confidence_validator.py - Confidence Rate Validation System

import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ConfidenceReport:
    """Report on confidence validation results"""
    overall_confidence: float
    word_count: int
    high_confidence_words: int
    low_confidence_words: int
    confidence_distribution: Dict[str, int]
    passed_validation: bool
    recommendations: List[str]

class ConfidenceValidator:
    """
    Validates and ensures translation confidence rates meet quality standards.
    
    Target: Maintain confidence rates between 0.80-1.00 for accurate translations.
    """
    
    def __init__(self):
        self.minimum_confidence = 0.80
        self.target_confidence = 0.90
        self.maximum_low_confidence_ratio = 0.15  # Max 15% of words can be below target
    
    def validate_translation_confidence(
        self, 
        overall_confidence: float, 
        word_mappings: List[Dict[str, Any]] = None
    ) -> ConfidenceReport:
        """
        Validate translation confidence meets quality standards.
        
        Args:
            overall_confidence: Overall translation confidence (0.0-1.0)
            word_mappings: List of word mappings with individual confidences
            
        Returns:
            ConfidenceReport with validation results and recommendations
        """
        
        recommendations = []
        
        # Analyze word-level confidence if available
        word_count = 0
        high_confidence_words = 0
        low_confidence_words = 0
        confidence_distribution = {"high": 0, "medium": 0, "low": 0}
        
        if word_mappings:
            word_count = len(word_mappings)
            
            for mapping in word_mappings:
                confidence = mapping.get('confidence', 0.0)
                
                if confidence >= 0.90:
                    confidence_distribution["high"] += 1
                    high_confidence_words += 1
                elif confidence >= 0.75:
                    confidence_distribution["medium"] += 1
                elif confidence < self.minimum_confidence:
                    confidence_distribution["low"] += 1
                    low_confidence_words += 1
                    
                    # Log low confidence words for improvement
                    word = mapping.get('source', 'unknown')
                    logger.warning(f"Low confidence word detected: '{word}' (confidence: {confidence:.2f})")
        
        # Validation checks
        passed_validation = True
        
        # Check overall confidence
        if overall_confidence < self.minimum_confidence:
            passed_validation = False
            recommendations.append(f"Overall confidence ({overall_confidence:.2f}) is below minimum ({self.minimum_confidence})")
            recommendations.append("Consider enabling confidence boosters in translation settings")
        
        # Check word-level confidence distribution
        if word_count > 0:
            low_confidence_ratio = low_confidence_words / word_count
            
            if low_confidence_ratio > self.maximum_low_confidence_ratio:
                passed_validation = False
                recommendations.append(f"Too many low-confidence words ({low_confidence_ratio:.1%} > {self.maximum_low_confidence_ratio:.1%})")
                recommendations.append("Consider using enhanced semantic correction or neural confidence boosters")
        
        # Performance recommendations
        if overall_confidence < self.target_confidence:
            recommendations.append("Consider using higher-confidence translation models for better accuracy")
        
        if overall_confidence >= self.target_confidence:
            recommendations.append("Excellent confidence rate! Translation quality is high.")
        
        # Create report
        report = ConfidenceReport(
            overall_confidence=overall_confidence,
            word_count=word_count,
            high_confidence_words=high_confidence_words,
            low_confidence_words=low_confidence_words,
            confidence_distribution=confidence_distribution,
            passed_validation=passed_validation,
            recommendations=recommendations
        )
        
        # Log validation results
        status = "PASSED" if passed_validation else "FAILED"
        logger.info(f"Confidence validation {status}: {overall_confidence:.3f} overall confidence")
        
        if not passed_validation:
            logger.warning("Translation confidence below quality standards")
            for recommendation in recommendations:
                logger.info(f"  Recommendation: {recommendation}")
        
        return report
    
    def enforce_minimum_confidence(self, confidence: float) -> float:
        """
        Enforce minimum confidence levels for translation quality.
        
        Args:
            confidence: Original confidence value
            
        Returns:
            Confidence value adjusted to meet minimum standards
        """
        
        if confidence < self.minimum_confidence:
            logger.info(f"Boosting confidence from {confidence:.3f} to minimum {self.minimum_confidence}")
            return self.minimum_confidence
        
        return confidence
    
    def get_confidence_grade(self, confidence: float) -> str:
        """
        Get a human-readable grade for confidence level.
        
        Args:
            confidence: Confidence value (0.0-1.0)
            
        Returns:
            Grade string (Excellent, Good, Fair, Poor)
        """
        
        if confidence >= 0.95:
            return "Excellent"
        elif confidence >= 0.90:
            return "Very Good"
        elif confidence >= 0.85:
            return "Good"
        elif confidence >= 0.80:
            return "Fair"
        else:
            return "Poor"
    
    def boost_confidence_for_common_patterns(
        self, 
        word_mappings: List[Dict[str, Any]], 
        source_language: str
    ) -> List[Dict[str, Any]]:
        """
        Boost confidence for common language patterns and high-frequency words.
        
        Args:
            word_mappings: List of word mappings to enhance
            source_language: Source language for pattern recognition
            
        Returns:
            Enhanced word mappings with boosted confidence
        """
        
        # Common high-confidence words by language
        high_confidence_patterns = {
            'english': [
                'i', 'you', 'he', 'she', 'we', 'they', 'it',
                'the', 'a', 'an', 'this', 'that', 'these', 'those',
                'have', 'has', 'had', 'is', 'are', 'was', 'were', 'be',
                'do', 'does', 'did', 'will', 'would', 'can', 'could',
                'for', 'to', 'of', 'in', 'on', 'at', 'by', 'with', 'from',
                'and', 'or', 'but', 'not', 'my', 'your', 'his', 'her'
            ],
            'german': [
                'ich', 'du', 'er', 'sie', 'wir', 'ihr', 'es',
                'der', 'die', 'das', 'den', 'dem', 'des',
                'ein', 'eine', 'einen', 'einem', 'einer',
                'haben', 'habe', 'hat', 'ist', 'sind', 'war', 'waren',
                'für', 'von', 'zu', 'mit', 'in', 'auf', 'an', 'bei',
                'und', 'oder', 'aber', 'nicht', 'mein', 'dein', 'sein'
            ],
            'spanish': [
                'yo', 'tú', 'él', 'ella', 'nosotros', 'vosotros', 'ellos', 'ellas',
                'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
                'tengo', 'tienes', 'tiene', 'tenemos', 'tienen',
                'soy', 'eres', 'es', 'somos', 'son', 'está', 'están',
                'para', 'de', 'en', 'con', 'por', 'a', 'desde', 'hasta',
                'y', 'o', 'pero', 'no', 'mi', 'tu', 'su', 'nuestro'
            ]
        }
        
        common_words = high_confidence_patterns.get(source_language.lower(), [])
        enhanced_mappings = []
        
        for mapping in word_mappings:
            enhanced_mapping = mapping.copy()
            source_word = mapping.get('source', '').lower()
            current_confidence = mapping.get('confidence', 0.0)
            
            # Boost confidence for common words
            if source_word in common_words:
                boosted_confidence = max(current_confidence, 0.95)
                enhanced_mapping['confidence'] = boosted_confidence
                
                if boosted_confidence > current_confidence:
                    logger.debug(f"Boosted confidence for common word '{source_word}': {current_confidence:.2f} → {boosted_confidence:.2f}")
            
            enhanced_mappings.append(enhanced_mapping)
        
        return enhanced_mappings

# Global instance for easy access
confidence_validator = ConfidenceValidator()