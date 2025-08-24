#!/usr/bin/env python3

import requests
import json
import sys

# Test the fixed translation service
def test_corrected_translations():
    url = "http://localhost:8000/api/conversation"
    
    # Test data - same as the user's example
    test_data = {
        "text": "mis prioridades son aprender idiomas con la aplicación que estoy haciendo",
        "source_lang": "spanish",
        "target_lang": "multi",
        "style_preferences": {
            "german_native": True,
            "german_formal": True,
            "english_native": True,
            "english_formal": True,
            "german_word_by_word": True,
            "english_word_by_word": True
        }
    }
    
    print("Testing translation fix...")
    print(f"Input: {test_data['text']}")
    print()
    
    try:
        response = requests.post(url, json=test_data, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            print("Translation successful!")
            
            # Check word-by-word data
            if 'word_by_word' in result:
                word_by_word = result['word_by_word']
                
                print(f"\nWord-by-word pairs found: {len(word_by_word)}")
                
                # Look for the specific corrections that should be applied
                corrections_found = []
                issues_found = []
                
                for key, data in word_by_word.items():
                    source = data.get('source', '')
                    spanish = data.get('spanish', '')
                    style = data.get('style', '')
                    
                    # Check for the specific corrections that should be present
                    if source.lower() == 'ich' and spanish.lower() == 'yo':
                        corrections_found.append(f"GOOD {style}: [ich] -> [yo] (corrected)")
                    elif source.lower() == 'ich' and spanish.lower() == 'estoy':
                        issues_found.append(f"BAD {style}: [ich] -> [estoy] (should be 'yo')")
                    
                    if source.lower() == 'der' and spanish.lower() in ['el', 'la']:
                        corrections_found.append(f"GOOD {style}: [der] -> [{spanish}] (article)")
                    
                    if 'mache' in source.lower() or 'entwickle' in source.lower():
                        if 'hago' in spanish.lower() or 'desarrollo' in spanish.lower():
                            corrections_found.append(f"GOOD {style}: [{source}] -> [{spanish}] (corrected verb)")
                        elif 'haciendo' in spanish.lower() and 'estoy' not in spanish.lower():
                            issues_found.append(f"BAD {style}: [{source}] -> [{spanish}] (should include 'estoy' or be 'hago/desarrollo')")
                    
                    print(f"  {style}: [{source}] -> [{spanish}]")
                
                print(f"\nCorrections Applied: {len(corrections_found)}")
                for correction in corrections_found:
                    print(f"  {correction}")
                
                if issues_found:
                    print(f"\nIssues Still Present: {len(issues_found)}")
                    for issue in issues_found:
                        print(f"  {issue}")
                else:
                    print("\nNo translation issues detected!")
                    
            else:
                print("No word-by-word data in response")
                
        else:
            print(f"Request failed with status {response.status_code}")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_corrected_translations()