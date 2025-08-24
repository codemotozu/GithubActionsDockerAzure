#!/usr/bin/env python3
"""
Test the translation API with the fixed implementation
"""
import requests
import json
import sys

def test_translation():
    """Test the translation API"""
    url = "http://localhost:8000/api/conversation"
    
    # Test request with same configuration as the original issue
    payload = {
        "text": "me levanto esta mañana temprano",
        "style_preferences": {
            "german_colloquial": True,
            "english_colloquial": True,
            "german_word_by_word": True,
            "english_word_by_word": False,
            "mother_tongue": "spanish"
        }
    }
    
    print("Testing translation API...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("="*60)
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ SUCCESS! Response received:")
            print("-" * 40)
            
            # Check main translation
            if 'translated_text' in data:
                print(f"Translated Text: {data['translated_text'][:200]}...")
            
            # Check word-by-word data
            if 'word_by_word' in data and data['word_by_word']:
                wbw_data = data['word_by_word']
                print(f"Word-by-word entries: {len(wbw_data)}")
                
                # Group by style
                styles = {}
                for key, entry in wbw_data.items():
                    style = entry.get('style', 'unknown')
                    if style not in styles:
                        styles[style] = []
                    styles[style].append(entry)
                
                print(f"Styles found: {list(styles.keys())}")
                
                for style_name, entries in styles.items():
                    print(f"\n{style_name.upper()}:")
                    for entry in entries[:3]:  # Show first 3 entries
                        display = entry.get('display_format', 'N/A')
                        print(f"  - {display}")
                        
                if len(styles) >= 2:
                    print("\n✅ SUCCESS: Both German and English styles found!")
                    return True
                else:
                    print(f"\n❌ ISSUE: Only {len(styles)} style(s) found, expected 2")
                    return False
            else:
                print("❌ No word-by-word data found")
                return False
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    result = test_translation()
    sys.exit(0 if result else 1)