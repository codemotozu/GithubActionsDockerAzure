#!/usr/bin/env python3
import requests
import json

def test_multi_line_fix():
    """Test the multi-line word-by-word parsing fix"""
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
            "germanWordByWord": False,
            "englishWordByWord": False
        }
    }
    
    print("Testing multi-line word-by-word parsing fix...")
    print(f"Input: {payload['text']}")
    print("Expected: Native and Formal styles should have DIFFERENT word-by-word mappings")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\nResponse received (status: {response.status_code})")
        
        # Check word-by-word data for differences
        word_by_word_data = data.get('word_by_word', {})
        print(f"\nWord-by-word entries by style:")
        
        # Group by style and look for differences
        styles = {}
        for key, value in word_by_word_data.items():
            style = value.get('style', 'unknown')
            source = value.get('source', '')
            spanish = value.get('spanish', '')
            
            if style not in styles:
                styles[style] = []
            styles[style].append(f"{source} → {spanish}")
        
        # Show styles and look for differences
        native_styles = []
        formal_styles = []
        
        for style_name, mappings in styles.items():
            print(f"\n{style_name.replace('_', ' ').title()}:")
            for mapping in mappings[:5]:  # Show first 5
                print(f"  {mapping}")
            if len(mappings) > 5:
                print(f"  ... and {len(mappings)-5} more")
            
            if 'native' in style_name:
                native_styles.extend(mappings)
            elif 'formal' in style_name:
                formal_styles.extend(mappings)
        
        # Check for differences
        native_set = set(native_styles)
        formal_set = set(formal_styles)
        differences = native_set - formal_set | formal_set - native_set
        
        print(f"\n=== ANALYSIS ===")
        if differences:
            print("✅ SUCCESS: Found differences between styles!")
            print(f"Different mappings: {len(differences)}")
            for diff in list(differences)[:3]:  # Show first 3 differences
                print(f"  {diff}")
            return True
        else:
            print("❌ ISSUE: No differences found between native and formal styles")
            print("All styles still have identical word-by-word mappings")
            return False
            
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_multi_line_fix()
    exit(0 if success else 1)