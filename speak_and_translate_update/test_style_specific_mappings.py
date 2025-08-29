#!/usr/bin/env python3
import requests
import json

def test_style_specific_mappings():
    url = "http://localhost:8000/api/conversation"
    
    # Test sentence that should produce different translations per style
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
            "germanWordByWord": False,
            "englishWordByWord": True
        }
    }
    
    print("Testing style-specific word-by-word mappings...")
    print(f"Input: {payload['text']}")
    print("Expected: Different German and English words per style in word-by-word mappings")
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\nResponse received (status: {response.status_code})")
        
        # Check translations to see if they're different
        translations = data.get('translations', {})
        print(f"\nTranslations:")
        for key, value in translations.items():
            if key != 'main':
                print(f"  {key}: {value}")
        
        # Check word-by-word data for style differences
        word_by_word_data = data.get('word_by_word', {})
        print(f"\nWord-by-word entries by style:")
        
        # Group by style
        style_mappings = {}
        for key, value in word_by_word_data.items():
            style = value.get('style', 'unknown')
            language = value.get('language', 'unknown')
            source = value.get('source', '')
            spanish = value.get('spanish', '')
            
            if style not in style_mappings:
                style_mappings[style] = []
            style_mappings[style].append(f"[{source}] ([{spanish}])")
        
        # Check for differences between styles
        style_differences = {}
        
        # Compare German Native vs Formal
        if 'german_native' in style_mappings and 'german_formal' in style_mappings:
            native_set = set(style_mappings['german_native'])
            formal_set = set(style_mappings['german_formal'])
            german_differences = native_set - formal_set | formal_set - native_set
            if german_differences:
                style_differences['German'] = german_differences
            
        # Compare English Native vs Formal
        if 'english_native' in style_mappings and 'english_formal' in style_mappings:
            native_set = set(style_mappings['english_native'])
            formal_set = set(style_mappings['english_formal'])
            english_differences = native_set - formal_set | formal_set - native_set
            if english_differences:
                style_differences['English'] = english_differences
        
        # Show results
        for style, mappings in style_mappings.items():
            print(f"\n{style.replace('_', ' ').title()}:")
            for mapping in mappings[:3]:  # Show first 3
                print(f"  {mapping}")
            if len(mappings) > 3:
                print(f"  ... and {len(mappings)-3} more")
        
        print(f"\n=== STYLE DIFFERENCES ANALYSIS ===")
        
        if style_differences:
            print("✅ SUCCESS: Found differences between styles!")
            for language, diffs in style_differences.items():
                print(f"\n{language} style differences:")
                for diff in diffs:
                    print(f"  {diff}")
        else:
            print("❌ ISSUE: No differences found between styles")
            print("   All styles have identical word-by-word mappings")
        
        # Overall assessment
        has_differences = len(style_differences) > 0
        total_entries = len(word_by_word_data)
        
        print(f"\nSummary:")
        print(f"  Total word-by-word entries: {total_entries}")
        print(f"  Styles with unique mappings: {len(style_differences)}")
        print(f"  Success: {'YES' if has_differences else 'NO'}")
        
        return has_differences
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_style_specific_mappings()
    exit(0 if success else 1)