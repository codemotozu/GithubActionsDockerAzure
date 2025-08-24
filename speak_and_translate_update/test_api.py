#!/usr/bin/env python3
"""Test script to validate the parsing fixes"""

import requests
import json

def test_conversation_api():
    url = "http://localhost:8000/api/conversation"
    
    payload = {
        "text": "creo que eso sería todo",
        "style_preferences": {
            "german_native": True,
            "english_native": True, 
            "german_word_by_word": True,
            "english_word_by_word": True,
            "mother_tongue": "spanish"
        }
    }
    
    headers = {"Content-Type": "application/json"}
    
    print("Testing API with parsing fixes...")
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Success! Checking word-by-word data...")
            
            if "word_by_word" in result:
                word_count = len(result["word_by_word"])
                print(f"Found {word_count} word pairs")
                
                # Check for empty Spanish translations
                empty_spanish = []
                for key, data in result["word_by_word"].items():
                    spanish = data.get("spanish", "")
                    if not spanish.strip():
                        empty_spanish.append(key)
                
                if empty_spanish:
                    print(f"WARNING: Found {len(empty_spanish)} empty Spanish translations:")
                    for key in empty_spanish[:5]:  # Show first 5
                        print(f"   {key}: {result['word_by_word'][key]}")
                else:
                    print("SUCCESS: All Spanish translations populated!")
                    
        else:
            print(f"ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"REQUEST FAILED: {e}")

if __name__ == "__main__":
    test_conversation_api()