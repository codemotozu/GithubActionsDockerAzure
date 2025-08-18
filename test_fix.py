import requests
import json

# Test the translation fix
url = "http://localhost:8000/api/conversation"

# Test case 1: The problematic "hoy me levante temprano"
test_data_1 = {
    "text": "hoy me levante temprano",
    "source_lang": "auto",
    "target_lang": "multi",
    "style_preferences": {
        "mother_tongue": "spanish",
        "german_native": True,
        "german_formal": True,
        "english_native": True,
        "english_formal": True,
        "german_word_by_word": True,
        "english_word_by_word": True
    }
}

print("Testing fix for: 'hoy me levante temprano'")
print("=" * 60)

try:
    response = requests.post(url, json=test_data_1, timeout=30)
    if response.status_code == 200:
        data = response.json()
        
        print("Response data structure:")
        print(json.dumps(data, indent=2)[:1000])  # Print first 1000 chars to see structure
        
        # Check word pairs - they might be in different structure
        if 'word_by_word' in data:
            styles = data.get('word_by_word', {})
            print(f"\nFound word_by_word data with keys: {list(styles.keys())}")
            
            for style_name, pairs in styles.items():
                print(f"\n{style_name.upper()}:")
                if isinstance(pairs, list):
                    for i, pair in enumerate(pairs[:5], 1):  # Show first 5 pairs
                        if isinstance(pair, dict):
                            target_word = pair.get('target_word', '')
                            spanish_word = pair.get('spanish_equivalent', '')
                            print(f"    {i}. [{target_word}] -> ([{spanish_word}])")
                            
                            # Check for the specific fixes
                            if target_word.lower() in ['ich', 'i']:
                                if spanish_word != 'yo':
                                    print(f"      ERROR: '{target_word}' should map to 'yo', not '{spanish_word}'")
                                else:
                                    print(f"      CORRECT: '{target_word}' correctly maps to 'yo'")
                        else:
                            print(f"    {i}. {pair}")
                else:
                    print(f"    Data type: {type(pairs)}")
        else:
            print("No word_by_word data found in response")
                        
    else:
        print(f"HTTP Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"Error: {e}")