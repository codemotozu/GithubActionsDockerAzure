#!/usr/bin/env python3
"""Debug the exact issue the user is experiencing"""
import requests
import json
import time

def debug_user_issue():
    """Debug what the user is actually experiencing"""
    url = "http://localhost:8000/api/conversation"
    
    print("=== DEBUGGING USER'S WORD-BY-WORD AUDIO ISSUE ===")
    print("Testing the exact scenario the user described...")
    
    # Test case 1: Word-by-word audio DISABLED for both languages
    payload1 = {
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
            "germanWordByWord": False,  # UNCHECKED
            "englishWordByWord": False  # UNCHECKED
        }
    }
    
    print("\n" + "="*80)
    print("TEST 1: Word-by-word audio UNCHECKED for both languages")
    print("Expected: Sentence audio + Visual word-by-word translations")
    print("="*80)
    
    try:
        print("\n📤 Sending request...")
        print("📤 Request payload:")
        print(json.dumps(payload1, indent=2))
        
        response1 = requests.post(url, json=payload1, timeout=90)
        response1.raise_for_status()
        
        data1 = response1.json()
        
        print(f"\n📥 Response received (status: {response1.status_code})")
        
        # Detailed analysis
        print("\n🔍 DETAILED ANALYSIS:")
        print("-" * 50)
        
        # Audio check
        has_audio = data1.get('audio_path') is not None
        audio_path = data1.get('audio_path', 'None')
        print(f"🎵 Audio generated: {has_audio}")
        print(f"🎵 Audio file: {audio_path}")
        
        # Word-by-word visual check
        word_by_word = data1.get('word_by_word', {})
        has_wbw = len(word_by_word) > 0
        print(f"👁️ Visual word-by-word provided: {has_wbw}")
        print(f"👁️ Word-by-word entries count: {len(word_by_word)}")
        
        if has_wbw:
            print("\n👁️ Visual word-by-word sample (first 5):")
            count = 0
            for key, value in word_by_word.items():
                if count >= 5:
                    break
                style = value.get('style', 'unknown')
                source = value.get('source', '')
                spanish = value.get('spanish', '')
                print(f"   {style}: {source} -> {spanish}")
                count += 1
        
        # Translation styles check
        translations = data1.get('translations', {})
        print(f"\n🗣️ Translation styles count: {len(translations)}")
        for key, value in translations.items():
            print(f"   {key}: {value[:60]}...")
        
        # Check if this matches expected behavior
        print(f"\n✅ SUCCESS CRITERIA CHECK:")
        criteria = {
            'Audio generated': has_audio,
            'Visual word-by-word provided': has_wbw,
            'Multiple translation styles': len(translations) > 2,
            'Word-by-word entries > 0': len(word_by_word) > 0
        }
        
        all_good = True
        for name, passed in criteria.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {name}: {status}")
            if not passed:
                all_good = False
        
        if not all_good:
            print(f"\n❌ FOUND THE ISSUE! Some criteria failed.")
            print("Let me check the server logs for more details...")
            
            # Print raw response for debugging
            print(f"\n🔍 RAW RESPONSE DATA:")
            print("-" * 30)
            print(json.dumps(data1, indent=2)[:1000] + "...")
            
        else:
            print(f"\n🤔 System appears to be working correctly...")
            print("The user might be experiencing a different issue.")
            print("Let me test with audio enabled to compare...")
        
        return all_good
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_with_audio_enabled():
    """Test with word-by-word audio enabled for comparison"""
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
            "germanWordByWord": True,   # CHECKED
            "englishWordByWord": True   # CHECKED
        }
    }
    
    print("\n" + "="*80)
    print("TEST 2: Word-by-word audio CHECKED for both languages")
    print("Expected: Word-by-word audio + Visual word-by-word translations")
    print("="*80)
    
    try:
        response = requests.post(url, json=payload, timeout=90)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\n📥 Response received (status: {response.status_code})")
        
        has_audio = data.get('audio_path') is not None
        word_by_word = data.get('word_by_word', {})
        translations = data.get('translations', {})
        
        print(f"🎵 Audio generated: {has_audio}")
        print(f"👁️ Visual word-by-word provided: {len(word_by_word) > 0}")
        print(f"🗣️ Translation styles: {len(translations)}")
        
        return has_audio and len(word_by_word) > 0
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting comprehensive debug of user's issue...")
    
    # Test 1: Audio disabled
    success1 = debug_user_issue()
    
    time.sleep(2)
    
    # Test 2: Audio enabled 
    success2 = test_with_audio_enabled()
    
    print(f"\n" + "="*80)
    print("FINAL DIAGNOSIS:")
    print(f"   Audio disabled test: {'✅ WORKING' if success1 else '❌ FAILING'}")
    print(f"   Audio enabled test: {'✅ WORKING' if success2 else '❌ FAILING'}")
    
    if not success1:
        print("\n🚨 ISSUE CONFIRMED: Audio disabled scenario is not working correctly")
        print("The user's problem is real - investigating further...")
    else:
        print("\n🤔 Tests show system working correctly")
        print("The user may be experiencing a different issue or frontend problem")