# test_8_modality_complete_system.py - Comprehensive Test for 8-Modality System

import asyncio
import logging
import time
from typing import Dict, List, Any
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the enhanced translation service
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from server.app.application.services.enhanced_translation_service import enhanced_translation_service

@dataclass
class StylePreferences:
    """Style preferences for testing all 8 modalities"""
    german_native: bool = False
    german_colloquial: bool = False
    german_informal: bool = False
    german_formal: bool = False
    english_native: bool = False
    english_colloquial: bool = False
    english_informal: bool = False
    english_formal: bool = False
    german_word_by_word: bool = False
    english_word_by_word: bool = False
    mother_tongue: str = "spanish"

class EightModalityTestSuite:
    """
    Comprehensive test suite for all 8 modalities
    
    Tests:
    1. German Native, Colloquial, Informal, Formal (4 modalities)
    2. English Native, Colloquial, Informal, Formal (4 modalities)
    3. Word-by-word generation for ALL modalities (regardless of audio settings)
    4. Confidence enforcement (0.80-1.00)
    5. German compound word handling (Ananassaft → jugo de piña)
    6. Response time under 5 seconds
    """
    
    def __init__(self):
        self.test_sentence = "Ananassaft für das Mädchen und Brombeersaft für die Dame weil sie im Krankenhaus sind."
        self.results = []
        
    async def run_all_8_modality_tests(self) -> Dict[str, Any]:
        """Run comprehensive tests for all 8 modalities"""
        
        print("\n" + "="*100)
        print("🚀 TESTING ALL 8 MODALITIES SYSTEM")
        print("="*100)
        print(f"Test sentence: {self.test_sentence}")
        print(f"Expected: German compound word 'Ananassaft' → 'jugo de piña'")
        print(f"Expected: Word-by-word ALWAYS generated regardless of audio settings")
        print("="*100)
        
        # Test all possible combinations
        test_scenarios = [
            # German only tests
            {"name": "German Native Only", "german_native": True},
            {"name": "German Colloquial Only", "german_colloquial": True},
            {"name": "German Informal Only", "german_informal": True},
            {"name": "German Formal Only", "german_formal": True},
            
            # English only tests
            {"name": "English Native Only", "english_native": True},
            {"name": "English Colloquial Only", "english_colloquial": True},
            {"name": "English Informal Only", "english_informal": True},
            {"name": "English Formal Only", "english_formal": True},
            
            # Combined tests (key requirement)
            {"name": "All German Modalities", "german_native": True, "german_colloquial": True, "german_informal": True, "german_formal": True},
            {"name": "All English Modalities", "english_native": True, "english_colloquial": True, "english_informal": True, "english_formal": True},
            {"name": "All 8 Modalities", "german_native": True, "german_colloquial": True, "german_informal": True, "german_formal": True, "english_native": True, "english_colloquial": True, "english_informal": True, "english_formal": True},
            
            # Audio settings test (word-by-word should ALWAYS be generated)
            {"name": "All 8 Modalities + Audio", "german_native": True, "german_colloquial": True, "german_informal": True, "german_formal": True, "english_native": True, "english_colloquial": True, "english_informal": True, "english_formal": True, "german_word_by_word": True, "english_word_by_word": True}
        ]
        
        total_start = time.time()
        
        for i, scenario in enumerate(test_scenarios):
            await self._test_single_scenario(i + 1, scenario)
            
            # Brief pause between tests
            await asyncio.sleep(0.5)
        
        total_time = time.time() - total_start
        
        # Generate comprehensive report
        return self._generate_test_report(total_time)
    
    async def _test_single_scenario(self, test_num: int, scenario_config: Dict[str, Any]):
        """Test a single modality scenario"""
        
        scenario_name = scenario_config.pop("name")
        
        print(f"\n🧪 TEST {test_num}: {scenario_name}")
        print("-" * 60)
        
        # Create style preferences
        prefs = StylePreferences(**scenario_config)
        
        # Count expected modalities
        expected_modalities = sum([
            prefs.german_native, prefs.german_colloquial, prefs.german_informal, prefs.german_formal,
            prefs.english_native, prefs.english_colloquial, prefs.english_informal, prefs.english_formal
        ])
        
        print(f"   Expected modalities: {expected_modalities}")
        print(f"   Audio settings: German={prefs.german_word_by_word}, English={prefs.english_word_by_word}")
        
        start_time = time.time()
        
        try:
            # Process translation
            result = await enhanced_translation_service.process_prompt(
                text=self.test_sentence,
                source_lang="spanish",
                target_lang="multi", 
                style_preferences=prefs,
                mother_tongue="spanish"
            )
            
            processing_time = time.time() - start_time
            
            # Analyze results
            analysis = self._analyze_test_result(result, expected_modalities, prefs, processing_time)
            
            # Display results
            self._display_test_results(analysis, scenario_name)
            
            self.results.append({
                "test_name": scenario_name,
                "analysis": analysis,
                "processing_time": processing_time
            })
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            print(f"   ❌ TEST FAILED: {e}")
            
            self.results.append({
                "test_name": scenario_name,
                "analysis": {"success": False, "error": str(e)},
                "processing_time": processing_time
            })
    
    def _analyze_test_result(self, result, expected_modalities: int, prefs: StylePreferences, processing_time: float) -> Dict[str, Any]:
        """Analyze test result for compliance"""
        
        analysis = {
            "success": True,
            "errors": [],
            "processing_time": processing_time,
            "fast_response": processing_time < 5.0,
            "modalities_generated": 0,
            "word_by_word_generated": False,
            "compound_word_handled": False,
            "confidence_compliant": False,
            "confidence_scores": [],
            "avg_confidence": 0.0
        }
        
        try:
            # Check translations
            translations = getattr(result, 'translations', {})
            analysis["modalities_generated"] = len([k for k in translations.keys() if k not in ['error', 'main', 'emergency']])
            
            if analysis["modalities_generated"] != expected_modalities:
                analysis["errors"].append(f"Expected {expected_modalities} modalities, got {analysis['modalities_generated']}")
            
            # Check word-by-word (CRITICAL: Should ALWAYS be generated)
            word_by_word = getattr(result, 'word_by_word', {})
            analysis["word_by_word_generated"] = len(word_by_word) > 0
            
            if not analysis["word_by_word_generated"]:
                analysis["errors"].append("CRITICAL: Word-by-word data not generated (should ALWAYS be generated)")
                analysis["success"] = False
            
            # Check compound word handling
            for key, data in word_by_word.items():
                if isinstance(data, dict):
                    source = data.get('source', '')
                    spanish = data.get('spanish', '')
                    
                    # Check for Ananassaft → jugo de piña compound handling
                    if 'ananassaft' in source.lower():
                        if spanish == 'jugo de piña':
                            analysis["compound_word_handled"] = True
                        else:
                            analysis["errors"].append(f"Compound word not handled correctly: Ananassaft → {spanish} (expected: jugo de piña)")
                    
                    # Collect confidence scores
                    confidence = data.get('_internal_confidence')
                    if confidence:
                        try:
                            conf_val = float(confidence)
                            analysis["confidence_scores"].append(conf_val)
                        except (ValueError, TypeError):
                            pass
            
            # Check confidence compliance (0.80-1.00)
            if analysis["confidence_scores"]:
                analysis["avg_confidence"] = sum(analysis["confidence_scores"]) / len(analysis["confidence_scores"])
                analysis["confidence_compliant"] = all(score >= 0.80 for score in analysis["confidence_scores"])
                
                if not analysis["confidence_compliant"]:
                    low_scores = [score for score in analysis["confidence_scores"] if score < 0.80]
                    analysis["errors"].append(f"Confidence scores below 0.80: {low_scores}")
                    analysis["success"] = False
            
            # Final success check
            if analysis["errors"]:
                analysis["success"] = False
            
        except Exception as e:
            analysis["success"] = False
            analysis["errors"].append(f"Analysis failed: {str(e)}")
        
        return analysis
    
    def _display_test_results(self, analysis: Dict[str, Any], test_name: str):
        """Display test results"""
        
        status = "✅ PASS" if analysis["success"] else "❌ FAIL"
        print(f"   {status}")
        
        print(f"   Processing time: {analysis['processing_time']:.2f}s ({'FAST' if analysis['fast_response'] else 'SLOW'})")
        print(f"   Modalities: {analysis['modalities_generated']}")
        print(f"   Word-by-word: {'✅ Generated' if analysis['word_by_word_generated'] else '❌ Missing'}")
        print(f"   Compound words: {'✅ Handled' if analysis['compound_word_handled'] else '❌ Not handled'}")
        
        if analysis["confidence_scores"]:
            print(f"   Confidence: {analysis['avg_confidence']:.2f} avg ({'✅ Compliant' if analysis['confidence_compliant'] else '❌ Non-compliant'})")
        
        if analysis["errors"]:
            print(f"   Errors:")
            for error in analysis["errors"]:
                print(f"     - {error}")
    
    def _generate_test_report(self, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r["analysis"]["success"]])
        failed_tests = total_tests - successful_tests
        
        print(f"\n" + "="*100)
        print("🏆 8-MODALITY SYSTEM TEST REPORT")
        print("="*100)
        
        print(f"Total tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success rate: {successful_tests/total_tests:.1%}")
        print(f"Total testing time: {total_time:.2f}s")
        
        # Key requirements check
        word_by_word_always = all(r["analysis"]["word_by_word_generated"] for r in self.results)
        confidence_compliant = all(r["analysis"]["confidence_compliant"] for r in self.results if r["analysis"]["confidence_scores"])
        fast_responses = sum(1 for r in self.results if r["analysis"]["fast_response"])
        compound_handling = any(r["analysis"]["compound_word_handled"] for r in self.results)
        
        print(f"\n🎯 KEY REQUIREMENTS:")
        print(f"   Word-by-word ALWAYS generated: {'✅ YES' if word_by_word_always else '❌ NO'}")
        print(f"   Confidence 0.80-1.00 compliant: {'✅ YES' if confidence_compliant else '❌ NO'}")
        print(f"   Fast responses (≤5s): {fast_responses}/{total_tests}")
        print(f"   German compound words: {'✅ Handled' if compound_handling else '❌ Not handled'}")
        
        # Overall system assessment
        overall_compliant = (
            successful_tests >= total_tests * 0.9 and  # 90%+ success rate
            word_by_word_always and
            confidence_compliant and
            fast_responses >= total_tests * 0.8  # 80%+ fast responses
        )
        
        print(f"\n🚀 OVERALL 8-MODALITY SYSTEM: {'✅ READY FOR PRODUCTION' if overall_compliant else '❌ NEEDS FIXES'}")
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests/total_tests,
            "total_time": total_time,
            "requirements": {
                "word_by_word_always": word_by_word_always,
                "confidence_compliant": confidence_compliant,
                "fast_responses": fast_responses/total_tests,
                "compound_handling": compound_handling
            },
            "overall_compliant": overall_compliant,
            "detailed_results": self.results
        }

async def main():
    """Run the comprehensive 8-modality test suite"""
    
    test_suite = EightModalityTestSuite()
    report = await test_suite.run_all_8_modality_tests()
    
    return report

if __name__ == "__main__":
    # Run the test suite
    report = asyncio.run(main())
    
    print(f"\n🎯 Test completed with {report['success_rate']:.1%} success rate")
    print(f"Overall system ready: {report['overall_compliant']}")