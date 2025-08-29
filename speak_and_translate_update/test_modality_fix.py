#!/usr/bin/env python3
"""
Test script to verify that modality-specific word-by-word translations are working correctly.
This test will check if German native vs German formal produce different word-by-word mappings.
"""

import requests
import json
import sys

# Test configuration
SERVER_URL = "http://localhost:8001"
TEST_TEXT = "el armario es de color café y la cama es de color también café y me levanté hoy temprano"

def test_modality_specific_word_by_word():
    """Test that different modalities produce different word-by-word translations"""
    
    print("[TEST] Testing Modality-Specific Word-by-Word Translations")
    print("=" * 80)
    print(f"[TEXT] Test Text: {TEST_TEXT}")
    print()
    
    # Prepare the request payload
    payload = {
        "text": TEST_TEXT,
        "source_lang": "spanish",
        "target_lang": "multi",
        "style_preferences": {
            "mother_tongue": "spanish",
            "german_native": True,
            "german_colloquial": False,
            "german_informal": False, 
            "german_formal": True,
            "english_native": True,
            "english_colloquial": False,
            "english_informal": False,
            "english_formal": True,
            "german_word_by_word": True,
            "english_word_by_word": True
        }
    }
    
    try:
        print("[REQ] Sending translation request...")
        response = requests.post(f"{SERVER_URL}/api/conversation", json=payload, timeout=120)
        
        if response.status_code != 200:
            print(f"[ERROR] Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        result = response.json()
        
        # Extract word-by-word data
        word_by_word = result.get("word_by_word", {})
        translations = result.get("translations", {})
        
        print("[OK] Translation request successful!")
        print()
        print("[RESULTS] TRANSLATIONS RECEIVED:")
        print("-" * 40)
        
        # Display translations
        for style, translation in translations.items():
            if style != "main":  # Skip the main translation
                print(f"[STYLE] {style}: {translation}")
        
        print()
        print("[ANALYSIS] WORD-BY-WORD ANALYSIS:")
        print("-" * 40)
        
        # Analyze German word-by-word
        german_styles = ["german_native", "german_formal"]
        german_word_pairs = {}
        
        for style in german_styles:
            pairs = []
            # Look for word pairs in the word_by_word data
            for key, data in word_by_word.items():
                if isinstance(data, dict) and data.get("style") == style:
                    source = data.get("source", "")
                    spanish = data.get("spanish", "")
                    if source and spanish:
                        pairs.append(f"{source} → {spanish}")
            german_word_pairs[style] = pairs
        
        # Analyze English word-by-word  
        english_styles = ["english_native", "english_formal"]
        english_word_pairs = {}
        
        for style in english_styles:
            pairs = []
            # Look for word pairs in the word_by_word data
            for key, data in word_by_word.items():
                if isinstance(data, dict) and data.get("style") == style:
                    source = data.get("source", "")
                    spanish = data.get("spanish", "")
                    if source and spanish:
                        pairs.append(f"{source} → {spanish}")
            english_word_pairs[style] = pairs
        
        # Display word-by-word mappings
        print("[GERMAN] GERMAN WORD-BY-WORD MAPPINGS:")
        for style in german_styles:
            pairs = german_word_pairs[style]
            print(f"   {style}: {len(pairs)} pairs")
            for pair in pairs[:5]:  # Show first 5 pairs
                print(f"      {pair}")
            if len(pairs) > 5:
                print(f"      ... and {len(pairs) - 5} more")
        
        print()
        print("[ENGLISH] ENGLISH WORD-BY-WORD MAPPINGS:")
        for style in english_styles:
            pairs = english_word_pairs[style]
            print(f"   {style}: {len(pairs)} pairs")
            for pair in pairs[:5]:  # Show first 5 pairs
                print(f"      {pair}")
            if len(pairs) > 5:
                print(f"      ... and {len(pairs) - 5} more")
        
        print()
        print("[TEST] UNIQUENESS TEST:")
        print("-" * 40)
        
        # Test if German native and formal have different mappings
        german_native_pairs = set(german_word_pairs["german_native"])
        german_formal_pairs = set(german_word_pairs["german_formal"])
        german_identical = german_native_pairs == german_formal_pairs
        
        # Test if English native and formal have different mappings
        english_native_pairs = set(english_word_pairs["english_native"])
        english_formal_pairs = set(english_word_pairs["english_formal"])
        english_identical = english_native_pairs == english_formal_pairs
        
        print(f"[GERMAN] German Native vs Formal: {'[FAIL] IDENTICAL' if german_identical else '[PASS] DIFFERENT'}")
        print(f"[ENGLISH] English Native vs Formal: {'[FAIL] IDENTICAL' if english_identical else '[PASS] DIFFERENT'}")
        
        # Overall test result
        test_passed = not german_identical and not english_identical
        
        print()
        print("=" * 80)
        if test_passed:
            print("[SUCCESS] TEST PASSED: Modalities produce different word-by-word translations!")
            return True
        else:
            print("[FAILED] TEST FAILED: Some modalities still produce identical word-by-word translations.")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Network error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_modality_specific_word_by_word()
    sys.exit(0 if success else 1)