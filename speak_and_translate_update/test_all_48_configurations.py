# test_all_48_configurations.py - Complete Test Suite for All 48 Configuration Scenarios

import asyncio
import logging
import time
import json
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
import pytest
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ConfigurationScenario:
    """Individual configuration scenario for testing"""
    scenario_id: int
    name: str
    description: str
    mother_tongue: str
    german_modalities: List[str]
    english_modalities: List[str]
    german_word_by_word: bool
    english_word_by_word: bool
    expected_translations: List[str]
    expected_word_pairs: int
    expected_audio: bool

@dataclass
class TestResult:
    """Test result for a configuration scenario"""
    scenario_id: int
    scenario_name: str
    success: bool
    response_time_ms: float
    confidence_scores: List[float]
    avg_confidence: float
    modalities_tested: int
    word_pairs_count: int
    audio_generated: bool
    error_message: Optional[str]
    detailed_results: Dict[str, Any]

class All48ConfigurationsTest:
    """
    Complete test suite for all 48 possible configuration scenarios
    
    Based on user specifications:
    - 8 modalities total (4 German + 4 English)
    - 2 word-by-word audio options (German ON/OFF + English ON/OFF)
    - Spanish as mother tongue
    - All possible combinations = 48 scenarios
    
    Test Coverage:
    1. German Only (8 cases): 4 modalities × 2 audio settings
    2. English Only (8 cases): 4 modalities × 2 audio settings  
    3. German + English Combined (32 cases): 4×4 modality combinations × 2×2 audio settings
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_sentence = "Ananassaft für das Mädchen und Brombeersaft für die Dame, weil sie im Krankenhaus sind und draußen regnet es."
        self.scenarios = self._generate_all_48_scenarios()
        self.results = []
        
        logger.info("🧪 All 48 Configurations Test Suite initialized")
        logger.info(f"   Base URL: {base_url}")
        logger.info(f"   Test sentence: {self.test_sentence}")
        logger.info(f"   Total scenarios: {len(self.scenarios)}")
    
    def _generate_all_48_scenarios(self) -> List[ConfigurationScenario]:
        """Generate all 48 possible configuration scenarios"""
        
        scenarios = []
        scenario_id = 1
        
        # German modalities
        german_modalities = ['native', 'colloquial', 'informal', 'formal']
        
        # English modalities  
        english_modalities = ['native', 'colloquial', 'informal', 'formal']
        
        # 1. German Only (8 cases)
        for german_mod in german_modalities:
            for german_audio in [False, True]:
                scenario = ConfigurationScenario(
                    scenario_id=scenario_id,
                    name=f"German {german_mod.title()} | Audio: {'ON' if german_audio else 'OFF'}",
                    description=f"German {german_mod} style with word-by-word audio {'enabled' if german_audio else 'disabled'}",
                    mother_tongue="spanish",
                    german_modalities=[german_mod],
                    english_modalities=[],
                    german_word_by_word=german_audio,
                    english_word_by_word=False,
                    expected_translations=[f"german_{german_mod}"],
                    expected_word_pairs=15 if german_audio else 0,  # Estimated word count
                    expected_audio=german_audio
                )
                scenarios.append(scenario)
                scenario_id += 1
        
        # 2. English Only (8 cases)
        for english_mod in english_modalities:
            for english_audio in [False, True]:
                scenario = ConfigurationScenario(
                    scenario_id=scenario_id,
                    name=f"English {english_mod.title()} | Audio: {'ON' if english_audio else 'OFF'}",
                    description=f"English {english_mod} style with word-by-word audio {'enabled' if english_audio else 'disabled'}",
                    mother_tongue="spanish",
                    german_modalities=[],
                    english_modalities=[english_mod],
                    german_word_by_word=False,
                    english_word_by_word=english_audio,
                    expected_translations=[f"english_{english_mod}"],
                    expected_word_pairs=13 if english_audio else 0,  # Estimated word count
                    expected_audio=english_audio
                )
                scenarios.append(scenario)
                scenario_id += 1
        
        # 3. German + English Combined (32 cases)
        for german_mod in german_modalities:
            for english_mod in english_modalities:
                for german_audio in [False, True]:
                    for english_audio in [False, True]:
                        scenario = ConfigurationScenario(
                            scenario_id=scenario_id,
                            name=f"German {german_mod.title()} + English {english_mod.title()} | Audio: G={'ON' if german_audio else 'OFF'}, E={'ON' if english_audio else 'OFF'}",
                            description=f"German {german_mod} + English {english_mod} with audio G={german_audio}, E={english_audio}",
                            mother_tongue="spanish",
                            german_modalities=[german_mod],
                            english_modalities=[english_mod],
                            german_word_by_word=german_audio,
                            english_word_by_word=english_audio,
                            expected_translations=[f"german_{german_mod}", f"english_{english_mod}"],
                            expected_word_pairs=28 if (german_audio or english_audio) else 0,
                            expected_audio=(german_audio or english_audio)
                        )
                        scenarios.append(scenario)
                        scenario_id += 1
        
        logger.info(f"✅ Generated {len(scenarios)} configuration scenarios:")
        logger.info(f"   German Only: 8 scenarios")
        logger.info(f"   English Only: 8 scenarios") 
        logger.info(f"   German + English: 32 scenarios")
        logger.info(f"   Total: {len(scenarios)} scenarios")
        
        return scenarios
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all 48 configuration tests"""
        
        logger.info(f"🚀 STARTING ALL 48 CONFIGURATION TESTS")
        logger.info(f"{'='*80}")
        
        start_time = time.time()
        
        # Run tests in batches to avoid overwhelming the server
        batch_size = 4
        for i in range(0, len(self.scenarios), batch_size):
            batch = self.scenarios[i:i+batch_size]
            
            logger.info(f"📦 Testing batch {i//batch_size + 1}: Scenarios {batch[0].scenario_id}-{batch[-1].scenario_id}")
            
            # Run batch tests concurrently
            batch_tasks = [self._test_single_scenario(scenario) for scenario in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"❌ Batch test failed: {result}")
                else:
                    self.results.append(result)
            
            # Brief pause between batches
            await asyncio.sleep(1)
        
        total_time = time.time() - start_time
        
        # Generate comprehensive test report
        test_report = self._generate_test_report(total_time)
        
        logger.info(f"✅ ALL 48 CONFIGURATION TESTS COMPLETED")
        logger.info(f"   Total time: {total_time:.2f} seconds")
        logger.info(f"   Success rate: {test_report['summary']['success_rate']:.1%}")
        
        return test_report
    
    async def _test_single_scenario(self, scenario: ConfigurationScenario) -> TestResult:
        """Test a single configuration scenario"""
        
        start_time = time.time()
        
        try:
            logger.info(f"🧪 Testing Scenario {scenario.scenario_id}: {scenario.name}")
            
            # Create request payload
            request_payload = self._create_request_payload(scenario)
            
            # Send API request
            response = await self._send_api_request(request_payload)
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Analyze response
            analysis = self._analyze_response(response, scenario)
            
            # Create test result
            test_result = TestResult(
                scenario_id=scenario.scenario_id,
                scenario_name=scenario.name,
                success=analysis['success'],
                response_time_ms=response_time_ms,
                confidence_scores=analysis['confidence_scores'],
                avg_confidence=analysis['avg_confidence'],
                modalities_tested=analysis['modalities_count'],
                word_pairs_count=analysis['word_pairs_count'],
                audio_generated=analysis['audio_generated'],
                error_message=analysis['error_message'],
                detailed_results=analysis['detailed_analysis']
            )
            
            # Log result
            status = "✅ PASS" if test_result.success else "❌ FAIL"
            logger.info(f"   {status} | {response_time_ms:.0f}ms | {test_result.modalities_tested} modalities | Conf: {test_result.avg_confidence:.2f}")
            
            if not test_result.success and test_result.error_message:
                logger.warning(f"   Error: {test_result.error_message}")
            
            return test_result
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            logger.error(f"❌ Scenario {scenario.scenario_id} failed: {e}")
            
            return TestResult(
                scenario_id=scenario.scenario_id,
                scenario_name=scenario.name,
                success=False,
                response_time_ms=response_time_ms,
                confidence_scores=[],
                avg_confidence=0.0,
                modalities_tested=0,
                word_pairs_count=0,
                audio_generated=False,
                error_message=str(e),
                detailed_results={}
            )
    
    def _create_request_payload(self, scenario: ConfigurationScenario) -> Dict[str, Any]:
        """Create API request payload for scenario"""
        
        style_preferences = {
            "german_native": "native" in scenario.german_modalities,
            "german_colloquial": "colloquial" in scenario.german_modalities,
            "german_informal": "informal" in scenario.german_modalities,
            "german_formal": "formal" in scenario.german_modalities,
            "english_native": "native" in scenario.english_modalities,
            "english_colloquial": "colloquial" in scenario.english_modalities,
            "english_informal": "informal" in scenario.english_modalities,
            "english_formal": "formal" in scenario.english_modalities,
            "german_word_by_word": scenario.german_word_by_word,
            "english_word_by_word": scenario.english_word_by_word,
            "mother_tongue": scenario.mother_tongue
        }
        
        return {
            "text": self.test_sentence,
            "source_lang": "spanish",
            "target_lang": "multi",
            "style_preferences": style_preferences
        }
    
    async def _send_api_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send API request and return response"""
        
        url = f"{self.base_url}/api/conversation"
        
        # Use asyncio to make the request asynchronous
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API request failed with status {response.status}: {await response.text()}")
    
    def _analyze_response(self, response: Dict[str, Any], scenario: ConfigurationScenario) -> Dict[str, Any]:
        """Analyze API response for the scenario"""
        
        analysis = {
            'success': True,
            'confidence_scores': [],
            'avg_confidence': 0.0,
            'modalities_count': 0,
            'word_pairs_count': 0,
            'audio_generated': False,
            'error_message': None,
            'detailed_analysis': {}
        }
        
        try:
            # Check basic response structure
            if 'translated_text' not in response:
                analysis['success'] = False
                analysis['error_message'] = "Missing translated_text in response"
                return analysis
            
            # Check translations
            translations = response.get('translations', {})
            analysis['modalities_count'] = len([k for k in translations.keys() if k not in ['error', 'main']])
            
            # Check word-by-word data
            word_by_word = response.get('word_by_word', {})
            analysis['word_pairs_count'] = len(word_by_word)
            
            # Extract confidence scores
            for pair_data in word_by_word.values():
                if isinstance(pair_data, dict) and '_internal_confidence' in pair_data:
                    try:
                        confidence = float(pair_data['_internal_confidence'])
                        analysis['confidence_scores'].append(confidence)
                    except (ValueError, TypeError):
                        pass
            
            # Calculate average confidence
            if analysis['confidence_scores']:
                analysis['avg_confidence'] = sum(analysis['confidence_scores']) / len(analysis['confidence_scores'])
            
            # Check audio generation
            analysis['audio_generated'] = response.get('audio_path') is not None
            
            # Validate expectations
            validation_results = self._validate_scenario_expectations(response, scenario)
            if not validation_results['valid']:
                analysis['success'] = False
                analysis['error_message'] = validation_results['error']
            
            # Check confidence requirements (0.80-1.00)
            low_confidence_pairs = [c for c in analysis['confidence_scores'] if c < 0.80]
            if low_confidence_pairs:
                analysis['success'] = False
                analysis['error_message'] = f"Found {len(low_confidence_pairs)} confidence scores below 0.80"
            
            # Detailed analysis
            analysis['detailed_analysis'] = {
                'expected_modalities': len(scenario.german_modalities) + len(scenario.english_modalities),
                'actual_modalities': analysis['modalities_count'],
                'expected_audio': scenario.expected_audio,
                'actual_audio': analysis['audio_generated'],
                'expected_word_pairs': scenario.expected_word_pairs,
                'actual_word_pairs': analysis['word_pairs_count'],
                'confidence_compliance': len(low_confidence_pairs) == 0,
                'response_structure_valid': 'translated_text' in response and 'translations' in response
            }
            
        except Exception as e:
            analysis['success'] = False
            analysis['error_message'] = f"Analysis failed: {str(e)}"
        
        return analysis
    
    def _validate_scenario_expectations(self, response: Dict[str, Any], scenario: ConfigurationScenario) -> Dict[str, Any]:
        """Validate response against scenario expectations"""
        
        validation = {'valid': True, 'error': None}
        
        try:
            translations = response.get('translations', {})
            
            # Check if expected modalities are present
            for expected_translation in scenario.expected_translations:
                if expected_translation not in translations:
                    validation['valid'] = False
                    validation['error'] = f"Missing expected translation: {expected_translation}"
                    return validation
            
            # Check word-by-word data when audio is enabled
            word_by_word = response.get('word_by_word', {})
            
            if scenario.german_word_by_word or scenario.english_word_by_word:
                if not word_by_word:
                    validation['valid'] = False
                    validation['error'] = "Word-by-word data missing when audio enabled"
                    return validation
            
            # Check audio path when audio expected
            if scenario.expected_audio:
                if not response.get('audio_path'):
                    validation['valid'] = False
                    validation['error'] = "Audio path missing when audio expected"
                    return validation
            
        except Exception as e:
            validation['valid'] = False
            validation['error'] = f"Validation error: {str(e)}"
        
        return validation
    
    def _generate_test_report(self, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        
        # Calculate summary statistics
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r.success])
        failed_tests = total_tests - successful_tests
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        # Response time statistics
        response_times = [r.response_time_ms for r in self.results]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        
        # Confidence statistics
        all_confidence_scores = []
        for result in self.results:
            all_confidence_scores.extend(result.confidence_scores)
        
        avg_confidence = sum(all_confidence_scores) / len(all_confidence_scores) if all_confidence_scores else 0
        min_confidence = min(all_confidence_scores) if all_confidence_scores else 0
        max_confidence = max(all_confidence_scores) if all_confidence_scores else 0
        
        # Compliance checks
        fast_responses = len([r for r in self.results if r.response_time_ms <= 5000])  # Within 5 seconds
        high_confidence = len([r for r in self.results if r.avg_confidence >= 0.80])  # Above 0.80 confidence
        
        # Error analysis
        error_categories = {}
        for result in self.results:
            if not result.success and result.error_message:
                error_type = result.error_message.split(':')[0] if ':' in result.error_message else result.error_message
                error_categories[error_type] = error_categories.get(error_type, 0) + 1
        
        # Generate report
        report = {
            'test_info': {
                'total_scenarios': len(self.scenarios),
                'test_sentence': self.test_sentence,
                'execution_time_seconds': total_time,
                'timestamp': datetime.now().isoformat()
            },
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': failed_tests,
                'success_rate': success_rate,
                'avg_response_time_ms': avg_response_time,
                'max_response_time_ms': max_response_time,
                'min_response_time_ms': min_response_time
            },
            'confidence_analysis': {
                'avg_confidence': avg_confidence,
                'min_confidence': min_confidence,
                'max_confidence': max_confidence,
                'total_word_pairs': len(all_confidence_scores),
                'confidence_compliant_tests': high_confidence,
                'confidence_compliance_rate': high_confidence / total_tests if total_tests > 0 else 0
            },
            'performance_analysis': {
                'fast_responses_5s': fast_responses,
                'fast_response_rate': fast_responses / total_tests if total_tests > 0 else 0,
                'avg_modalities_per_test': sum(r.modalities_tested for r in self.results) / total_tests if total_tests > 0 else 0,
                'avg_word_pairs_per_test': sum(r.word_pairs_count for r in self.results) / total_tests if total_tests > 0 else 0
            },
            'error_analysis': {
                'error_categories': error_categories,
                'most_common_error': max(error_categories.items(), key=lambda x: x[1]) if error_categories else None
            },
            'detailed_results': [asdict(result) for result in self.results],
            'compliance_report': {
                'response_time_requirement': f"{fast_responses}/{total_tests} tests within 5 seconds",
                'confidence_requirement': f"{high_confidence}/{total_tests} tests with confidence ≥ 0.80",
                'modality_coverage': f"All 8 modalities tested across {total_tests} scenarios",
                'overall_compliance': success_rate >= 0.95 and fast_responses/total_tests >= 0.90 and high_confidence/total_tests >= 0.95
            }
        }
        
        return report
    
    def save_test_results(self, filename: str = "test_results_all_48_configurations.json"):
        """Save test results to file"""
        
        if not self.results:
            logger.warning("No test results to save")
            return
        
        report = self._generate_test_report(0)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Test results saved to {filename}")
    
    def print_summary_report(self):
        """Print summary test report"""
        
        if not self.results:
            logger.warning("No test results available")
            return
        
        report = self._generate_test_report(0)
        
        print("\n" + "="*80)
        print("🧪 ALL 48 CONFIGURATION SCENARIOS - TEST SUMMARY")
        print("="*80)
        
        print(f"📊 OVERALL RESULTS:")
        print(f"   Total Tests: {report['summary']['total_tests']}")
        print(f"   Successful: {report['summary']['successful_tests']}")
        print(f"   Failed: {report['summary']['failed_tests']}")
        print(f"   Success Rate: {report['summary']['success_rate']:.1%}")
        
        print(f"\n⏱️ PERFORMANCE:")
        print(f"   Avg Response Time: {report['summary']['avg_response_time_ms']:.0f}ms")
        print(f"   Max Response Time: {report['summary']['max_response_time_ms']:.0f}ms")
        print(f"   Fast Responses (≤5s): {report['performance_analysis']['fast_response_rate']:.1%}")
        
        print(f"\n🎯 CONFIDENCE ANALYSIS:")
        print(f"   Avg Confidence: {report['confidence_analysis']['avg_confidence']:.2f}")
        print(f"   Min Confidence: {report['confidence_analysis']['min_confidence']:.2f}")
        print(f"   Compliance Rate (≥0.80): {report['confidence_analysis']['confidence_compliance_rate']:.1%}")
        
        print(f"\n🏆 COMPLIANCE STATUS:")
        print(f"   Response Time: {report['compliance_report']['response_time_requirement']}")
        print(f"   Confidence: {report['compliance_report']['confidence_requirement']}")
        print(f"   Overall Compliant: {'✅ YES' if report['compliance_report']['overall_compliance'] else '❌ NO'}")
        
        if report['error_analysis']['error_categories']:
            print(f"\n❌ ERROR CATEGORIES:")
            for error, count in report['error_analysis']['error_categories'].items():
                print(f"   {error}: {count} occurrences")
        
        print("="*80)

# Test execution functions
async def run_all_48_tests():
    """Run all 48 configuration tests"""
    
    test_suite = All48ConfigurationsTest()
    
    # Run all tests
    report = await test_suite.run_all_tests()
    
    # Print summary
    test_suite.print_summary_report()
    
    # Save results
    test_suite.save_test_results()
    
    return report

def main():
    """Main test execution"""
    logger.info("🚀 Starting All 48 Configuration Scenarios Test")
    
    # Run tests
    report = asyncio.run(run_all_48_tests())
    
    logger.info("✅ All 48 Configuration Tests Complete")
    
    return report

if __name__ == "__main__":
    main()