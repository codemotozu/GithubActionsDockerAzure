#!/usr/bin/env python3
import requests
import json

def simple_debug():
    url = "http://localhost:8000/api/conversation"
    
    # Test: Word-by-word audio DISABLED
    payload = {
        "text": "me levante temprano porque quiero tener una vida diferente",
        "stylePreferences": {
            "motherTongue": "spanish",
            "germanNative": True,
            "germanFormal": True,
            "englishNative": True,
            "englishFormal": True,
            "germanWordByWord": False,  # DISABLED
            "englishWordByWord": False  # DISABLED
        }
    }
    
    print("TESTING: Word-by-word audio DISABLED for both languages")
    print("Request payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\nResponse status: {response.status_code}")
        
        # Check key aspects
        has_audio = data.get('audio_path') is not None
        word_by_word = data.get('word_by_word', {})
        translations = data.get('translations', {})
        
        print(f"Audio generated: {has_audio}")
        print(f"Audio path: {data.get('audio_path', 'None')}")
        print(f"Visual word-by-word count: {len(word_by_word)}")
        print(f"Translation styles count: {len(translations)}")
        
        if len(word_by_word) > 0:
            print("\nFirst few word-by-word entries:")
            count = 0
            for key, value in word_by_word.items():
                if count >= 3:
                    break
                style = value.get('style', '')
                source = value.get('source', '')
                spanish = value.get('spanish', '')
                print(f"  {style}: {source} -> {spanish}")
                count += 1
        
        print(f"\nTranslations:")
        for key, value in translations.items():
            print(f"  {key}: {value}")
        
        # Check if this is what user expects
        expected_behavior = {
            'has_audio': has_audio,
            'has_visual_wbw': len(word_by_word) > 0,
            'has_multiple_styles': len(translations) > 2
        }
        
        print(f"\nBehavior check:")
        for key, value in expected_behavior.items():
            print(f"  {key}: {'OK' if value else 'FAIL'}")
        
        return all(expected_behavior.values())
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = simple_debug()
    print(f"\nTest result: {'SUCCESS' if success else 'FAILED'}")