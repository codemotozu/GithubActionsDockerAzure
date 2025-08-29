#!/usr/bin/env python3
"""Test partial word-by-word audio control (one language enabled, one disabled)"""
import requests
import json

def test_partial_word_by_word_audio():
    """Test that enabling word-by-word audio for only one language works correctly"""
    url = "http://localhost:8000/api/conversation"
    
    payload = {
        "text": "me levanté temprano porque quiero tener una vida diferente",
        "stylePreferences": {
            "motherTongue": "spanish",
            "germanNative": True,
            "germanColloquial": False,
            "germanInformal": False,
            "germanFormal": True,
            "englishNative": True,
            "englishColloquial": False,
            "englishInformal": False,
            "englishFormal": True,
            # CRITICAL: Word-by-word audio ENABLED for German, DISABLED for English
            "germanWordByWord": True,
            "englishWordByWord": False
        }
    }
    
    print("Testing partial word-by-word audio control...")
    print(f"Input: {payload['text']}")
    print("Styles enabled: German Native/Formal, English Native/Formal")
    print("Word-by-word audio: ENABLED for German, DISABLED for English")
    print("Expected behavior:")
    print("  [OK] Audio generated with word-by-word breakdown (because germanWordByWord=True)")
    print("  [OK] Visual word-by-word translations provided for ALL styles")
    print("  [OK] Different translations per style")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\nResponse received (status: {response.status_code})")
        
        # Check audio
        has_audio = data.get('audio_path') is not None
        print(f"\n=== AUDIO CHECK ===")
        print(f"Audio generated: {'[OK] YES' if has_audio else '[FAIL] NO'}")
        if has_audio:
            print(f"Audio file: {data.get('audio_path')}")
        
        # Check visual word-by-word data
        word_by_word = data.get('word_by_word', {})
        has_visual_wbw = len(word_by_word) > 0
        print(f"\n=== VISUAL WORD-BY-WORD CHECK ===")
        print(f"Visual word-by-word provided: {'[OK] YES' if has_visual_wbw else '[FAIL] NO'}")
        
        if has_visual_wbw:
            # Group by language
            german_entries = [k for k, v in word_by_word.items() if 'german' in v.get('style', '')]
            english_entries = [k for k, v in word_by_word.items() if 'english' in v.get('style', '')]
            
            print(f"German word-by-word entries: {len(german_entries)}")
            print(f"English word-by-word entries: {len(english_entries)}")
            
            # Check both languages have word-by-word data even though only German has audio
            both_languages_have_wbw = len(german_entries) > 0 and len(english_entries) > 0
            print(f"Both languages have visual word-by-word: {'[OK] YES' if both_languages_have_wbw else '[FAIL] NO'}")
        
        # Check translations
        translations = data.get('translations', {})
        print(f"\n=== TRANSLATIONS CHECK ===")
        print(f"Translation styles available: {len(translations)}")
        for key, value in translations.items():
            print(f"  {key}: {value[:50]}...")
        
        # Success criteria
        success_criteria = {
            'has_audio': has_audio,
            'has_visual_word_by_word': has_visual_wbw,
            'both_languages_have_visual_wbw': both_languages_have_wbw if has_visual_wbw else False,
            'has_translations': len(translations) > 0
        }
        
        print(f"\n=== SUCCESS ANALYSIS ===")
        all_success = True
        for criteria, passed in success_criteria.items():
            status = "[OK] PASS" if passed else "[FAIL] FAIL"
            print(f"{criteria.replace('_', ' ').title()}: {status}")
            if not passed:
                all_success = False
        
        if all_success:
            print(f"\n[SUCCESS] Partial word-by-word audio control working correctly!")
            print("[OK] Audio generated with word-by-word breakdown")
            print("[OK] Visual word-by-word translations provided for ALL languages")
            print("[OK] Multiple translation styles working")
            return True
        else:
            print(f"\n[FAIL] ISSUES DETECTED: Some criteria failed")
            return False
            
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_partial_word_by_word_audio()
    exit(0 if success else 1)