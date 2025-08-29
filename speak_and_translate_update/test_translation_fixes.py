#!/usr/bin/env python3
import requests
import json

# Test the fixes for malformed Spanish translations and rate limiting
def test_translation_fixes():
    url = "http://localhost:8000/api/conversation"
    
    # Test sentence that was causing issues
    payload = {
        "text": "Hoy me levanté temprano porque quería tener un día productivo",
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
            "germanWordByWord": False,  # Should see visual but no audio
            "englishWordByWord": True   # Should see visual AND audio
        }
    }
    
    print("Testing translation fixes...")
    print(f"Request: {payload['text']}")
    print(f"Expected: Clean Spanish translations without 'implied' text")
    
    try:
        response = requests.post(url, json=payload, timeout=120)  # Longer timeout for rate limiting
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\nResponse received (status: {response.status_code})")
        
        # Check if we have word-by-word data
        word_by_word_data = data.get('word_by_word', {})
        print(f"Word-by-word entries: {len(word_by_word_data)}")
        
        # Look for malformed translations
        malformed_count = 0
        clean_count = 0
        
        for key, value in word_by_word_data.items():
            display_format = value.get('display_format', '')
            spanish_equivalent = value.get('spanish', '')
            
            # Check for malformed patterns
            is_malformed = (
                ' - implied' in spanish_equivalent or
                ' - implied in' in spanish_equivalent or
                'implied' in spanish_equivalent.lower()
            )
            
            if is_malformed:
                malformed_count += 1
                print(f"MALFORMED: {display_format}")
            else:
                clean_count += 1
                print(f"CLEAN: {display_format}")
        
        print(f"\nResults:")
        print(f"  Clean translations: {clean_count}")
        print(f"  Malformed translations: {malformed_count}")
        print(f"  Audio generated: {'Yes' if data.get('audio_path') else 'No'}")
        
        # Check success
        success = malformed_count == 0 and clean_count > 0
        
        if success:
            print(f"\nSUCCESS! All translations are clean and well-formatted")
            if data.get('audio_path'):
                print(f"BONUS: Audio was successfully generated (rate limiting fixes worked)")
        else:
            print(f"\nPARTIAL SUCCESS: Found {malformed_count} malformed translations that need fixing")
            
        return success
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_translation_fixes()
    exit(0 if success else 1)