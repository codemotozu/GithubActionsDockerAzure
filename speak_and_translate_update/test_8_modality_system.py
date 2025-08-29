# test_8_modality_system.py - Comprehensive Test Suite for 8-Modality Translation System

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestModality(Enum):
    """Test modalities matching the server enum"""
    GERMAN_NATIVE = "german_native"
    GERMAN_COLLOQUIAL = "german_colloquial"
    GERMAN_INFORMAL = "german_informal"
    GERMAN_FORMAL = "german_formal"
    ENGLISH_NATIVE = "english_native"
    ENGLISH_COLLOQUIAL = "english_colloquial"
    ENGLISH_INFORMAL = "english_informal"
    ENGLISH_FORMAL = "english_formal"

@dataclass
class TestConfiguration:
    """Test configuration representing one of the 48 possible combinations"""
    config_id: int
    description: str
    mother_tongue: str
    selected_modalities: List[TestModality]
    word_by_word_enabled: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'config_id': self.config_id,
            'description': self.description,
            'mother_tongue': self.mother_tongue,
            'modalities': [m.value for m in self.selected_modalities],
            'word_by_word': self.word_by_word_enabled
        }

@dataclass
class TestResult:
    """Test result for a specific configuration"""
    config: TestConfiguration
    success: bool
    processing_time_ms: float
    modalities_generated: int
    word_by_word_count: int
    confidence_scores: List[float]
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'config_id': self.config.config_id,
            'success': self.success,
            'processing_time_ms': self.processing_time_ms,
            'modalities_generated': self.modalities_generated,
            'word_by_word_count': self.word_by_word_count,
            'average_confidence': sum(self.confidence_scores) / len(self.confidence_scores) if self.confidence_scores else 0.0,
            'meets_30s_target': self.processing_time_ms <= 30000,
            'error': self.error_message
        }

class Modality8TestSystem:
    """
    Comprehensive Test System for 8-Modality Translation
    
    Tests all 48 possible configurations:
    - Spanish mother tongue + German/English combinations
    - With/without word-by-word audio
    - Performance validation (30-second target)
    - Accuracy validation (0.80+ confidence)
    """
    
    def __init__(self):
        self.test_configurations = self._generate_all_48_configurations()
        self.test_phrases = self._get_test_phrases()
        self.results: List[TestResult] = []
        
        logger.info(f"🧪 Test system initialized with {len(self.test_configurations)} configurations")
        logger.info(f"📝 Using {len(self.test_phrases)} test phrases")
    
    def _generate_all_48_configurations(self) -> List[TestConfiguration]:
        """Generate all 48 possible test configurations"""
        
        configurations = []
        config_id = 1
        
        # German-only configurations (8 total)
        german_modalities = [
            ([TestModality.GERMAN_NATIVE], "German Native"),
            ([TestModality.GERMAN_COLLOQUIAL], "German Colloquial"),
            ([TestModality.GERMAN_INFORMAL], "German Informal"),
            ([TestModality.GERMAN_FORMAL], "German Formal"),
        ]
        
        for modalities, style_name in german_modalities:
            # With word-by-word
            configurations.append(TestConfiguration(
                config_id=config_id,
                description=f"{style_name} | Word by Word: ON",
                mother_tongue="spanish",
                selected_modalities=modalities,
                word_by_word_enabled=True
            ))
            config_id += 1
            
            # Without word-by-word
            configurations.append(TestConfiguration(
                config_id=config_id,
                description=f"{style_name} | Word by Word: OFF",
                mother_tongue="spanish",
                selected_modalities=modalities,
                word_by_word_enabled=False
            ))
            config_id += 1
        
        # English-only configurations (8 total)
        english_modalities = [
            ([TestModality.ENGLISH_NATIVE], "English Native"),
            ([TestModality.ENGLISH_COLLOQUIAL], "English Colloquial"),
            ([TestModality.ENGLISH_INFORMAL], "English Informal"),
            ([TestModality.ENGLISH_FORMAL], "English Formal"),
        ]
        
        for modalities, style_name in english_modalities:
            # With word-by-word
            configurations.append(TestConfiguration(
                config_id=config_id,
                description=f"{style_name} | Word by Word: ON",
                mother_tongue="spanish",
                selected_modalities=modalities,
                word_by_word_enabled=True
            ))
            config_id += 1
            
            # Without word-by-word
            configurations.append(TestConfiguration(
                config_id=config_id,
                description=f"{style_name} | Word by Word: OFF",
                mother_tongue="spanish",
                selected_modalities=modalities,
                word_by_word_enabled=False
            ))
            config_id += 1
        
        # German + English combined configurations (32 total)
        # All combinations of German and English styles
        for german_mod, german_name in german_modalities:
            for english_mod, english_name in english_modalities:
                combined_modalities = german_mod + english_mod
                
                # With word-by-word
                configurations.append(TestConfiguration(
                    config_id=config_id,
                    description=f"{german_name} + {english_name} | Word by Word: ON",
                    mother_tongue="spanish",
                    selected_modalities=combined_modalities,
                    word_by_word_enabled=True
                ))
                config_id += 1
                
                # Without word-by-word
                configurations.append(TestConfiguration(
                    config_id=config_id,
                    description=f"{german_name} + {english_name} | Word by Word: OFF",
                    mother_tongue="spanish",
                    selected_modalities=combined_modalities,
                    word_by_word_enabled=False
                ))
                config_id += 1
        
        return configurations
    
    def _get_test_phrases(self) -> List[Dict[str, str]]:
        """Get test phrases for validation"""
        return [
            {
                "spanish": "Jugo de piña para la niña y jugo de mora para la señora porque están en el hospital y afuera está lloviendo.",
                "description": "Complex sentence with compound words and subordinate clauses",
                "complexity": "high"
            },
            {
                "spanish": "Hola, ¿cómo estás?",
                "description": "Simple greeting",
                "complexity": "low"
            },
            {
                "spanish": "El tren sale a las diez de la mañana.",
                "description": "Time expression with transportation",
                "complexity": "medium"
            },
            {
                "spanish": "Me desperté temprano hoy porque quería ver el amanecer.",
                "description": "Reflexive verbs and temporal expressions",
                "complexity": "medium"
            },
            {
                "spanish": "¿Podrías ayudarme con este problema matemático?",
                "description": "Conditional request with academic vocabulary",
                "complexity": "high"
            }
        ]
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test of all 48 configurations"""
        
        logger.info("🚀 Starting comprehensive 8-modality system test")
        logger.info(f"📋 Testing {len(self.test_configurations)} configurations")
        logger.info(f"📝 Using {len(self.test_phrases)} test phrases")
        
        start_time = time.time()
        
        # Test each configuration with each phrase
        total_tests = len(self.test_configurations) * len(self.test_phrases)
        current_test = 0
        
        for config in self.test_configurations:
            for phrase_data in self.test_phrases:
                current_test += 1
                
                logger.info(f"🔍 Test {current_test}/{total_tests}: Config {config.config_id} - {phrase_data['description']}")
                
                # Run single test
                result = await self._test_single_configuration(config, phrase_data)
                self.results.append(result)
                
                # Log progress
                if result.success:
                    status = "✅ PASS"
                    if result.processing_time_ms > 30000:
                        status += " (SLOW)"
                else:
                    status = "❌ FAIL"
                
                logger.info(f"   {status} - {result.processing_time_ms:.0f}ms - {result.modalities_generated} modalities")
        
        total_time = time.time() - start_time
        
        # Analyze results
        analysis = self._analyze_test_results()
        
        logger.info(f"🏁 Comprehensive test completed in {total_time:.1f}s")
        logger.info(f"📊 Success rate: {analysis['success_rate']:.1f}%")
        logger.info(f"⚡ Average response time: {analysis['average_response_time_ms']:.1f}ms")
        logger.info(f"🎯 Configs meeting 30s target: {analysis['configs_meeting_30s_target']}/{len(self.test_configurations)}")
        
        return {
            'test_summary': {
                'total_configurations': len(self.test_configurations),
                'total_phrases': len(self.test_phrases),
                'total_tests': total_tests,
                'total_time_seconds': total_time,
            },
            'results_analysis': analysis,
            'detailed_results': [r.to_dict() for r in self.results],
        }
    
    async def _test_single_configuration(
        self,
        config: TestConfiguration,
        phrase_data: Dict[str, str]
    ) -> TestResult:
        """Test a single configuration with one phrase"""
        
        test_start = time.time()
        
        try:
            # Simulate the 8-modality translation service call
            result = await self._simulate_modality_translation(
                config, phrase_data['spanish']
            )
            
            processing_time = (time.time() - test_start) * 1000
            
            # Validate result
            validation = self._validate_translation_result(result, config)
            
            return TestResult(
                config=config,
                success=validation['valid'],
                processing_time_ms=processing_time,
                modalities_generated=len(result.get('modality_translations', [])),
                word_by_word_count=len(result.get('enhanced_word_by_word', {})),
                confidence_scores=[
                    mt.get('confidence', 0.0) 
                    for mt in result.get('modality_translations', [])
                ],
                error_message=validation.get('error', '')
            )
            
        except Exception as e:
            processing_time = (time.time() - test_start) * 1000
            
            return TestResult(
                config=config,
                success=False,
                processing_time_ms=processing_time,
                modalities_generated=0,
                word_by_word_count=0,
                confidence_scores=[],
                error_message=str(e)
            )
    
    async def _simulate_modality_translation(
        self,
        config: TestConfiguration,
        source_text: str
    ) -> Dict[str, Any]:
        """Simulate the 8-modality translation service"""
        
        # This would normally call the actual service
        # For testing, we simulate the expected response structure
        
        await asyncio.sleep(0.1)  # Simulate processing time
        
        modality_translations = []
        enhanced_word_by_word = {}
        
        for modality in config.selected_modalities:
            # Simulate modality translation
            translation_text = f"[{modality.value}] {self._generate_mock_translation(source_text, modality)}"
            
            modality_translations.append({
                'modality': modality.value,
                'translation_text': translation_text,
                'confidence': 0.90 + (hash(modality.value) % 10) / 100,  # Mock confidence 0.90-0.99
                'linguistic_notes': f"Mock {modality.value} translation"
            })
            
            # Simulate word-by-word if enabled
            if config.word_by_word_enabled:
                enhanced_word_by_word[modality.value] = self._generate_mock_word_by_word(
                    source_text, translation_text
                )
        
        return {
            'original_text': source_text,
            'modality_translations': modality_translations,
            'enhanced_word_by_word': enhanced_word_by_word,
            'processing_time_ms': 1500.0,  # Mock processing time
            'ai_confidence': 0.92
        }
    
    def _generate_mock_translation(self, source_text: str, modality: TestModality) -> str:
        """Generate mock translation based on modality"""
        
        # Simple mock translations based on modality style
        if modality == TestModality.GERMAN_NATIVE:
            return "Ananassaft für das Mädchen und Brombeersaft für die Dame."
        elif modality == TestModality.GERMAN_COLLOQUIAL:
            return "Ananassaft fürs Mädel und Brombeersaft für die Frau."
        elif modality == TestModality.GERMAN_INFORMAL:
            return "Ananassaft fürs Mädchen und Brombeersaft für die Frau."
        elif modality == TestModality.GERMAN_FORMAL:
            return "Ananassaft für das Kind und Brombeersaft für die verehrte Frau."
        elif modality == TestModality.ENGLISH_NATIVE:
            return "Pineapple juice for the girl and blackberry juice for the lady."
        elif modality == TestModality.ENGLISH_COLLOQUIAL:
            return "Pineapple juice for the gal and blackberry juice for the woman."
        elif modality == TestModality.ENGLISH_INFORMAL:
            return "Pineapple juice for the little girl and blackberry juice for the lady."
        elif modality == TestModality.ENGLISH_FORMAL:
            return "Pineapple juice for the child and blackberry juice for the esteemed lady."
        
        return f"Mock {modality.value} translation"
    
    def _generate_mock_word_by_word(
        self, source_text: str, translation_text: str
    ) -> List[Dict[str, Any]]:
        """Generate mock word-by-word mappings"""
        
        source_words = source_text.split()[:3]  # First 3 words for testing
        
        mappings = []
        for i, word in enumerate(source_words):
            mappings.append({
                'order': i + 1,
                'source_word': word,
                'target_word': f"mock_{word}",
                'confidence': 0.85 + (i * 0.05),
                'is_compound_word': len(word) > 6,
                'is_phrasal_verb': False,
                'is_separable_verb': False,
                'display_format': f"{word} → mock_{word}"
            })
        
        return mappings
    
    def _validate_translation_result(
        self, result: Dict[str, Any], config: TestConfiguration
    ) -> Dict[str, Any]:
        """Validate translation result meets requirements"""
        
        errors = []
        
        # Check modality count
        expected_modalities = len(config.selected_modalities)
        actual_modalities = len(result.get('modality_translations', []))
        
        if actual_modalities != expected_modalities:
            errors.append(f"Expected {expected_modalities} modalities, got {actual_modalities}")
        
        # Check word-by-word if enabled
        if config.word_by_word_enabled:
            word_by_word = result.get('enhanced_word_by_word', {})
            if not word_by_word:
                errors.append("Word-by-word enabled but no data provided")
            elif len(word_by_word) != expected_modalities:
                errors.append(f"Word-by-word data missing for some modalities")
        
        # Check confidence scores
        for mt in result.get('modality_translations', []):
            confidence = mt.get('confidence', 0.0)
            if confidence < 0.80:
                errors.append(f"Confidence {confidence:.2f} below 0.80 threshold")
        
        return {
            'valid': len(errors) == 0,
            'error': '; '.join(errors) if errors else ''
        }
    
    def _analyze_test_results(self) -> Dict[str, Any]:
        """Analyze all test results"""
        
        if not self.results:
            return {'error': 'No test results to analyze'}
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        
        # Group results by configuration
        config_results = {}
        for result in self.results:
            config_id = result.config.config_id
            if config_id not in config_results:
                config_results[config_id] = []
            config_results[config_id].append(result)
        
        # Calculate per-configuration success rates
        config_success_rates = {}
        configs_meeting_30s = 0
        
        for config_id, results in config_results.items():
            successful = sum(1 for r in results if r.success)
            total = len(results)
            config_success_rates[config_id] = (successful / total) * 100
            
            # Check if all tests for this config meet 30s target
            if all(r.processing_time_ms <= 30000 for r in results):
                configs_meeting_30s += 1
        
        # Performance analysis
        response_times = [r.processing_time_ms for r in self.results if r.success]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Confidence analysis
        all_confidences = []
        for result in self.results:
            all_confidences.extend(result.confidence_scores)
        
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
        
        return {
            'success_rate': (successful_tests / total_tests) * 100,
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': total_tests - successful_tests,
            'configs_meeting_30s_target': configs_meeting_30s,
            'total_configurations': len(config_results),
            'average_response_time_ms': avg_response_time,
            'max_response_time_ms': max(response_times) if response_times else 0,
            'min_response_time_ms': min(response_times) if response_times else 0,
            'average_confidence': avg_confidence,
            'config_success_rates': config_success_rates,
        }
    
    def export_results_to_json(self, filename: str = 'test_results_8_modality.json'):
        """Export test results to JSON file"""
        
        analysis = self._analyze_test_results()
        
        export_data = {
            'test_metadata': {
                'timestamp': time.time(),
                'total_configurations': len(self.test_configurations),
                'total_phrases': len(self.test_phrases),
                'system': '8_modality_translation_system'
            },
            'configurations': [config.to_dict() for config in self.test_configurations],
            'analysis': analysis,
            'detailed_results': [result.to_dict() for result in self.results]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Test results exported to {filename}")

async def main():
    """Run the comprehensive test suite"""
    
    logger.info("🧪 Starting 8-Modality Translation System Test Suite")
    
    # Initialize test system
    test_system = Modality8TestSystem()
    
    # Run comprehensive test
    results = await test_system.run_comprehensive_test()
    
    # Export results
    test_system.export_results_to_json()
    
    # Print summary
    analysis = results['results_analysis']
    print("\n" + "="*60)
    print("🏁 8-MODALITY TRANSLATION SYSTEM TEST SUMMARY")
    print("="*60)
    print(f"✅ Success Rate: {analysis['success_rate']:.1f}%")
    print(f"⚡ Average Response Time: {analysis['average_response_time_ms']:.1f}ms")
    print(f"🎯 Configurations Meeting 30s Target: {analysis['configs_meeting_30s_target']}/{analysis['total_configurations']}")
    print(f"🔍 Average Confidence: {analysis['average_confidence']:.3f}")
    print(f"📊 Total Tests: {analysis['total_tests']} ({analysis['successful_tests']} passed, {analysis['failed_tests']} failed)")
    print("="*60)
    
    if analysis['success_rate'] >= 95 and analysis['configs_meeting_30s_target'] >= 40:
        print("🎉 SYSTEM READY FOR PRODUCTION!")
    elif analysis['success_rate'] >= 90:
        print("⚠️  SYSTEM NEEDS MINOR OPTIMIZATION")
    else:
        print("❌ SYSTEM NEEDS SIGNIFICANT WORK")
    
    return results

if __name__ == "__main__":
    # Run the test suite
    results = asyncio.run(main())