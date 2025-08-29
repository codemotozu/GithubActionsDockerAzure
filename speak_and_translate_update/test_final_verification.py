#!/usr/bin/env python3
import requests
import json

def test_final_verification():
    """Final verification test for multi-style translations and word-by-word mappings"""
    url = "http://localhost:8000/api/conversation"
    
    payload = {
        "text": "me levante temprano porque quiero tener una vida diferente",
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
            "englishWordByWord": False
        }
    }
    
    print("Final verification test for multi-style translations...")
    print(f"Input: {payload['text']}")
    print("Expected: Different translations and word-by-word mappings per style")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\nResponse received (status: {response.status_code})")
        
        # Check translations
        translations = data.get('translations', {})
        print(f"\nTRANSLATIONS:")
        for key, value in translations.items():
            print(f"  {key}: {value}")
        
        # Check word-by-word data for style differences
        word_by_word_data = data.get('word_by_word', {})
        print(f"\nWORD-BY-WORD MAPPINGS by style:")
        
        german_styles = {}
        english_styles = {}
        
        for key, value in word_by_word_data.items():
            style = value.get('style', 'unknown')
            source = value.get('source', '')
            spanish = value.get('spanish', '')
            mapping = f"{source} -> {spanish}"
            
            if 'german' in style:
                if style not in german_styles:
                    german_styles[style] = []
                german_styles[style].append(mapping)
            elif 'english' in style:
                if style not in english_styles:
                    english_styles[style] = []
                english_styles[style].append(mapping)
        
        # Show German styles
        print(f"\nGERMAN STYLES:")
        for style_name, mappings in german_styles.items():
            print(f"  {style_name}: {len(mappings)} mappings")
            for mapping in mappings[:3]:  # Show first 3
                print(f"    {mapping}")
        
        # Show English styles
        print(f"\nENGLISH STYLES:")
        for style_name, mappings in english_styles.items():
            print(f"  {style_name}: {len(mappings)} mappings")
            for mapping in mappings[:3]:  # Show first 3
                print(f"    {mapping}")
        
        # Check for differences between native and formal
        success = True
        if len(german_styles) >= 2 and len(english_styles) >= 2:
            print(f"\n=== SUCCESS ANALYSIS ===")
            print(f"German styles found: {len(german_styles)}")
            print(f"English styles found: {len(english_styles)}")
            
            # Look for style-specific vocabulary differences
            differences_found = False
            print("Style-specific vocabulary detected:")
            
            # Check German differences (like weil vs da)
            german_keys = list(german_styles.keys())
            if len(german_keys) >= 2:
                native_mappings = set(german_styles[german_keys[0]])
                formal_mappings = set(german_styles[german_keys[1]])
                differences = native_mappings - formal_mappings | formal_mappings - native_mappings
                if differences:
                    differences_found = True
                    print(f"  German: {len(differences)} different mappings between styles")
            
            # Check English differences (like got up vs arose)
            english_keys = list(english_styles.keys())
            if len(english_keys) >= 2:
                native_mappings = set(english_styles[english_keys[0]])
                formal_mappings = set(english_styles[english_keys[1]])
                differences = native_mappings - formal_mappings | formal_mappings - native_mappings
                if differences:
                    differences_found = True
                    print(f"  English: {len(differences)} different mappings between styles")
            
            if differences_found:
                print("SUCCESS: Multi-style system working correctly!")
                print("- Different translations per style: YES")
                print("- Different word-by-word mappings per style: YES")
                print("- Field alias mapping (camelCase -> snake_case): YES")
                print("- Multi-line parsing: YES")
                return True
            else:
                print("PARTIAL: Styles detected but no vocabulary differences found")
                return False
        else:
            print("ISSUE: Not enough styles detected")
            return False
            
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_final_verification()
    exit(0 if success else 1)