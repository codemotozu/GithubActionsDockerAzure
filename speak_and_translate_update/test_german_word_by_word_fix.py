#!/usr/bin/env python3
import requests
import json

# Test the fix for German word-by-word visual translations
def test_german_word_by_word_fix():
    url = "http://localhost:8000/api/conversation"
    
    # Same request from the logs where German was missing
    payload = {
        "text": "Me acabo quitar las gafas",
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
            "germanWordByWord": False,  # CRITICAL: This is False but we should still see German visual translations
            "englishWordByWord": True
        }
    }
    
    print("Testing German word-by-word visual fix...")
    print(f"Request: {payload}")
    print(f"Expected: German word-by-word visual translations should appear even though germanWordByWord=False")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\nResponse received (status: {response.status_code})")
        
        # Debug: Show the full response structure
        print(f"Response keys: {list(data.keys())}")
        print(f"Response structure debug:")
        for key, value in data.items():
            if isinstance(value, dict) and len(str(value)) < 500:
                print(f"   {key}: {value}")
            else:
                print(f"   {key}: <{type(value).__name__}> (length: {len(str(value))})")
        
        # Check if German word-by-word data is in the response
        word_by_word_data = data.get('word_by_word', {})
        
        print(f"\nWord-by-word data analysis:")
        print(f"   Total keys in word_by_word: {len(word_by_word_data)}")
        print(f"   Word-by-word keys: {list(word_by_word_data.keys())}")
        
        # Count German and English entries
        german_count = 0
        english_count = 0
        
        for key, value in word_by_word_data.items():
            language = value.get('language', 'unknown')
            style = value.get('style', 'unknown')
            if language == 'german':
                german_count += 1
                print(f"   GERMAN: {key} -> {value.get('display_format', 'N/A')}")
            elif language == 'english':
                english_count += 1
                print(f"   ENGLISH: {key} -> {value.get('display_format', 'N/A')}")
        
        print(f"\nSummary:")
        print(f"   German word-by-word entries: {german_count}")
        print(f"   English word-by-word entries: {english_count}")
        
        # The test passes if we have German entries even though germanWordByWord=False
        if german_count > 0:
            print(f"\nSUCCESS! German word-by-word visual translations are now showing!")
            print(f"   Fix verified: Visual translations appear regardless of audio settings")
            return True
        else:
            print(f"\nFAIL: German word-by-word visual translations still missing")
            print(f"   This indicates the fix didn't work as expected")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_german_word_by_word_fix()
    exit(0 if success else 1)