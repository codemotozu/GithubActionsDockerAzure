#!/usr/bin/env python3
import requests
import json

def test_snake_case_fields():
    url = "http://localhost:8000/api/conversation"
    
    # Test with SNAKE_CASE field names (matching Python model)
    payload = {
        "text": "vamos a probar esto",
        "stylePreferences": {
            "mother_tongue": "spanish",  # snake_case
            "german_native": True,       # snake_case 
            "german_colloquial": False,  # snake_case
            "german_informal": False,    # snake_case
            "german_formal": True,       # snake_case
            "english_native": True,      # snake_case
            "english_colloquial": False, # snake_case
            "english_informal": False,   # snake_case
            "english_formal": True,      # snake_case
            "german_word_by_word": False, # snake_case
            "english_word_by_word": True  # snake_case
        }
    }
    
    print("Testing with snake_case field names...")
    print(f"Input: {payload['text']}")
    print("Expected: Native and Formal styles should be selected")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\nResponse received (status: {response.status_code})")
        
        translations = data.get('translations', {})
        print(f"\nTranslations:")
        for key, value in translations.items():
            if key != 'main':
                print(f"  {key}: {value}")
        
        # Check if we see native/formal styles
        has_native = any('native' in key for key in translations.keys())
        has_formal = any('formal' in key for key in translations.keys())
        has_colloquial = any('colloquial' in key for key in translations.keys())
        
        print(f"\nStyle detection:")
        print(f"  Native styles found: {has_native}")
        print(f"  Formal styles found: {has_formal}")
        print(f"  Colloquial styles found: {has_colloquial}")
        
        if has_native and has_formal and not has_colloquial:
            print("\n✅ SUCCESS: Snake case field names work correctly!")
            return True
        else:
            print("\n❌ ISSUE: Wrong styles detected even with snake_case")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_snake_case_fields()
    exit(0 if success else 1)