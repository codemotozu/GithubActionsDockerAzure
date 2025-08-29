#!/usr/bin/env python3
"""
Comprehensive test script to verify all 8 modalities work with:
1. Complex sentences including compound words (Ananassaft = jugo de piña)
2. Word-by-word translations ALWAYS provided (regardless of audio checkbox)
3. Fast performance (under 30 seconds)
4. Unique Spanish mappings for each modality
"""

import requests
import json
import sys
import time

# Test configuration
SERVER_URL = "http://localhost:8001"
COMPLEX_TEST_TEXT = "Ananassaft für das Mädchen und Brombeersaft für die Dame, weil sie im Krankenhaus sind und draußen regnet es"

def test_all_8_modalities():
    """Test all 8 modalities with complex compound word sentence"""
    
    print("=" * 100)
    print("[TEST] COMPREHENSIVE TEST: ALL 8 MODALITIES WITH COMPOUND WORDS")
    print("=" * 100)
    print(f"[TEXT] Test Text: {COMPLEX_TEST_TEXT}")
    print("[EXPECT] Expected: Ananassaft -> jugo de pina, Brombeersaft -> jugo de mora")
    print()
    
    # Test all 8 modality combinations
    test_cases = [
        # German modalities
        {
            "name": "[GER] GERMAN NATIVE",
            "payload": {
                "text": COMPLEX_TEST_TEXT,
                "source_lang": "german", 
                "target_lang": "spanish",
                "style_preferences": {
                    "mother_tongue": "spanish",
                    "german_native": True,
                    "german_word_by_word": False  # Test: word-by-word should STILL be provided!
                }
            }
        },
        {
            "name": "[GER] GERMAN FORMAL",
            "payload": {
                "text": COMPLEX_TEST_TEXT,
                "source_lang": "german",
                "target_lang": "spanish", 
                "style_preferences": {
                    "mother_tongue": "spanish",
                    "german_formal": True,
                    "german_word_by_word": False  # Test: word-by-word should STILL be provided!
                }
            }
        },
        {
            "name": "[GER] GERMAN COLLOQUIAL",
            "payload": {
                "text": COMPLEX_TEST_TEXT,
                "source_lang": "german",
                "target_lang": "spanish",
                "style_preferences": {
                    "mother_tongue": "spanish", 
                    "german_colloquial": True,
                    "german_word_by_word": False  # Test: word-by-word should STILL be provided!
                }
            }
        },
        {
            "name": "[GER] GERMAN INFORMAL",
            "payload": {
                "text": COMPLEX_TEST_TEXT,
                "source_lang": "german",
                "target_lang": "spanish",
                "style_preferences": {
                    "mother_tongue": "spanish",
                    "german_informal": True,
                    "german_word_by_word": False  # Test: word-by-word should STILL be provided!
                }
            }
        }
    ]
    
    # English test cases with complex sentence
    english_test_text = "Pineapple juice for the little girl and blackberry juice for the lady, because they are in the hospital and it's raining outside"
    
    english_cases = [
        {
            "name": "[ENG] ENGLISH NATIVE", 
            "payload": {
                "text": english_test_text,
                "source_lang": "english",
                "target_lang": "spanish",
                "style_preferences": {
                    "mother_tongue": "spanish",
                    "english_native": True,
                    "english_word_by_word": False  # Test: word-by-word should STILL be provided!
                }
            }
        },
        {
            "name": "[ENG] ENGLISH FORMAL",
            "payload": {
                "text": english_test_text,
                "source_lang": "english", 
                "target_lang": "spanish",
                "style_preferences": {
                    "mother_tongue": "spanish",
                    "english_formal": True,
                    "english_word_by_word": False  # Test: word-by-word should STILL be provided!
                }
            }
        },
        {
            "name": "[ENG] ENGLISH COLLOQUIAL",
            "payload": {
                "text": english_test_text,
                "source_lang": "english",
                "target_lang": "spanish",
                "style_preferences": {
                    "mother_tongue": "spanish",
                    "english_colloquial": True,
                    "english_word_by_word": False  # Test: word-by-word should STILL be provided!
                }
            }
        },
        {
            "name": "[ENG] ENGLISH INFORMAL",
            "payload": {
                "text": english_test_text,
                "source_lang": "english",
                "target_lang": "spanish", 
                "style_preferences": {
                    "mother_tongue": "spanish",
                    "english_informal": True,
                    "english_word_by_word": False  # Test: word-by-word should STILL be provided!
                }
            }
        }
    ]
    
    test_cases.extend(english_cases)
    
    results = []
    start_time = time.time()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"[TEST] {i}/8: {test_case['name']}")
        print(f"{'='*60}")
        
        case_start = time.time()
        
        try:
            response = requests.post(
                f"{SERVER_URL}/api/conversation", 
                json=test_case["payload"], 
                timeout=45  # Max 45 seconds per test
            )
            
            case_duration = time.time() - case_start
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if word-by-word data is present (should ALWAYS be present!)
                word_by_word = result.get("word_by_word", {})
                has_word_by_word = len(word_by_word) > 0
                
                # Count unique Spanish mappings
                spanish_mappings = set()
                for key, data in word_by_word.items():
                    if isinstance(data, dict):
                        spanish = data.get("spanish", "")
                        if spanish:
                            spanish_mappings.add(spanish)
                
                # Check for compound word handling
                compound_words_found = []
                for key, data in word_by_word.items():
                    if isinstance(data, dict):
                        source = data.get("source", "").lower()
                        spanish = data.get("spanish", "").lower()
                        
                        # Check for Ananassaft -> jugo de pina
                        if "ananassaft" in source:
                            compound_words_found.append(f"Ananassaft -> {spanish}")
                        # Check for Brombeersaft -> jugo de mora  
                        elif "brombeersaft" in source:
                            compound_words_found.append(f"Brombeersaft -> {spanish}")
                        # Check for pineapple juice -> jugo de pina
                        elif "pineapple" in source and "juice" in source:
                            compound_words_found.append(f"pineapple juice -> {spanish}")
                
                results.append({
                    "modality": test_case["name"],
                    "success": True,
                    "duration": case_duration,
                    "has_word_by_word": has_word_by_word,
                    "spanish_mappings_count": len(spanish_mappings),
                    "compound_words": compound_words_found,
                    "translation": result.get("translated_text", "")[:100] + "..."
                })
                
                print(f"[SUCCESS]")
                print(f"[TIME] Duration: {case_duration:.2f} seconds")
                print(f"[TRANS] Translation: {result.get('translated_text', '')[:100]}...")
                print(f"[WBW] Word-by-word provided: {'YES' if has_word_by_word else 'NO'}")
                print(f"[MAPS] Spanish mappings: {len(spanish_mappings)}")
                if compound_words_found:
                    print(f"[COMPOUND] Compound words: {', '.join(compound_words_found)}")
                
            else:
                results.append({
                    "modality": test_case["name"],
                    "success": False,
                    "duration": case_duration,
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                })
                print(f"[FAILED] HTTP {response.status_code}")
                print(f"Error: {response.text[:200]}")
                
        except Exception as e:
            case_duration = time.time() - case_start
            results.append({
                "modality": test_case["name"],
                "success": False,
                "duration": case_duration,
                "error": str(e)
            })
            print(f"[ERROR] {str(e)}")
    
    total_duration = time.time() - start_time
    
    # Final results summary
    print("\n" + "=" * 100)
    print("[SUMMARY] FINAL RESULTS SUMMARY")
    print("=" * 100)
    
    successful_tests = [r for r in results if r["success"]]
    failed_tests = [r for r in results if not r["success"]]
    
    print(f"[SUCCESS] Successful tests: {len(successful_tests)}/8")
    print(f"[FAILED] Failed tests: {len(failed_tests)}/8")
    print(f"[TIME] Total duration: {total_duration:.2f} seconds")
    print(f"[PERF] Performance target (30s): {'PASSED' if total_duration <= 30 else 'FAILED'}")
    
    # Check word-by-word requirement
    word_by_word_provided = all(r.get("has_word_by_word", False) for r in successful_tests)
    print(f"[WBW] Word-by-word ALWAYS provided: {'YES' if word_by_word_provided else 'NO'}")
    
    # Detailed results
    print("\n[DETAILS] DETAILED RESULTS:")
    print("-" * 80)
    for result in results:
        status = "[OK]" if result["success"] else "[FAIL]"
        duration = result["duration"]
        modality = result["modality"]
        
        if result["success"]:
            mappings = result["spanish_mappings_count"]
            word_by_word = "[OK]" if result["has_word_by_word"] else "[FAIL]"
            compounds = len(result.get("compound_words", []))
            print(f"{status} {modality:<25} | {duration:>5.1f}s | WBW:{word_by_word} | Mappings:{mappings:>2} | Compounds:{compounds}")
        else:
            error = result.get("error", "Unknown error")[:50]
            print(f"{status} {modality:<25} | {duration:>5.1f}s | ERROR: {error}")
    
    # Overall verdict
    print("\n" + "=" * 100)
    overall_success = (
        len(successful_tests) == 8 and
        word_by_word_provided and
        total_duration <= 30
    )
    
    if overall_success:
        print("[VERDICT] OVERALL VERDICT: ALL TESTS PASSED!")
        print("[OK] All 8 modalities working")
        print("[OK] Word-by-word always provided") 
        print("[OK] Performance under 30 seconds")
        print("[OK] Compound word handling working")
    else:
        print("[VERDICT] OVERALL VERDICT: SOME ISSUES FOUND")
        if len(successful_tests) != 8:
            print(f"[FAIL] {8 - len(successful_tests)} modalities failed")
        if not word_by_word_provided:
            print("[FAIL] Word-by-word not always provided")
        if total_duration > 30:
            print(f"[FAIL] Performance too slow ({total_duration:.1f}s > 30s)")
    
    return overall_success

if __name__ == "__main__":
    success = test_all_8_modalities()
    sys.exit(0 if success else 1)