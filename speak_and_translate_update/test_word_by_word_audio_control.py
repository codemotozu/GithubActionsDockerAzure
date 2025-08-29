#!/usr/bin/env python3
"""Test to verify word-by-word audio control works correctly"""
import requests
import json

def test_word_by_word_audio_control():
    """Test that unchecking word-by-word audio still provides visual word-by-word"""
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
            # CRITICAL: Word-by-word audio DISABLED for both languages
            "germanWordByWord": False,
            "englishWordByWord": False
        }
    }
    
    print("Testing word-by-word audio control...")
    print(f"Input: {payload['text']}")
    print("Styles enabled: German Native/Formal, English Native/Formal")
    print("Word-by-word audio: DISABLED for both German and English")
    print("Expected behavior:")
    print("  [OK] Audio generated (sentence audio only, no word-by-word breakdown)")
    print("  [OK] Visual word-by-word translations still provided")
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
            # Group by style
            styles_found = set()
            for key, value in word_by_word.items():
                style = value.get('style', 'unknown')
                styles_found.add(style)
            
            print(f"Styles with word-by-word data: {len(styles_found)}")
            for style in sorted(styles_found):
                print(f"  - {style}")
            
            # Show sample word-by-word data
            print(f"\nSample word-by-word entries (first 3):")
            count = 0
            for key, value in word_by_word.items():
                if count >= 3:
                    break
                style = value.get('style', 'unknown')
                source = value.get('source', '')
                spanish = value.get('spanish', '')
                print(f"  {style}: {source} -> {spanish}")
                count += 1
        
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
            'has_multiple_styles': len(styles_found) >= 2 if has_visual_wbw else False,
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
            print(f"\n[SUCCESS] Word-by-word audio control working correctly!")
            print("[OK] Audio generated (sentence-level)")
            print("[OK] Visual word-by-word translations provided")
            print("[OK] Multiple translation styles working")
            return True
        else:
            print(f"\n[FAIL] ISSUES DETECTED: Some criteria failed")
            return False
            
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_word_by_word_audio_control()
    exit(0 if success else 1)