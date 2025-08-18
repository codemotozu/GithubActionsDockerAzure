import requests
import json

url = "http://localhost:8000/api/conversation"

# Test simple phrase without audio to speed up testing
test_data = {
    "text": "quiero ganar masa muscular",
    "source_lang": "auto", 
    "target_lang": "multi",
    "style_preferences": {
        "mother_tongue": "spanish",
        "german_native": True,
        "english_native": True,
        "german_word_by_word": True,  # Need this for word pairs
        "english_word_by_word": True
    }
}

print("Testing 'quiero ganar masa muscular'...")

try:
    response = requests.post(url, json=test_data, timeout=20)
    if response.status_code == 200:
        data = response.json()
        print("SUCCESS! Let me check the mappings...")
        
        # Check if we have word_by_word data
        if 'word_by_word' in data:
            styles = data['word_by_word']
            for style_name, pairs in styles.items():
                print(f"\n{style_name}:")
                if isinstance(pairs, list):
                    for pair in pairs[:3]:  # First 3 pairs only
                        if isinstance(pair, dict):
                            target = pair.get('target_word', '')
                            spanish = pair.get('spanish_equivalent', '')
                            print(f"  [{target}] -> ([{spanish}])")
                            
                            # Check the fix
                            if target.lower() in ['ich', 'i'] and spanish == 'yo':
                                print(f"  ✓ FIXED: {target} correctly maps to 'yo'")
                            elif target.lower() in ['ich', 'i'] and spanish != 'yo':
                                print(f"  ✗ STILL BROKEN: {target} maps to '{spanish}' instead of 'yo'")
        else:
            print("No word_by_word data found")
            
    else:
        print(f"Error {response.status_code}: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")