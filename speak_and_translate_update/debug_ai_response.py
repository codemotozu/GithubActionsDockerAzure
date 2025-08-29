#!/usr/bin/env python3
import requests
import json

def debug_ai_response():
    """Debug what the AI is actually returning for word-by-word mappings"""
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
            "germanWordByWord": True,
            "englishWordByWord": True
        }
    }
    
    print("Debugging AI response for style-specific word-by-word mappings...")
    print(f"Input: {payload['text']}")
    print("Enabled styles: German Native/Formal, English Native/Formal")
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        
        data = response.json()
        
        # Check if the server logs show the raw AI response
        print("\n=== ANALYZING RESPONSE ===")
        print("Check the server console for:")
        print("1. Raw AI response text (should show different word-by-word for each style)")
        print("2. Extraction debug messages")
        print("3. Style-specific word-by-word parsing")
        
        # Show what we received
        word_by_word = data.get('word_by_word', {})
        if word_by_word:
            print(f"\n=== RECEIVED WORD-BY-WORD DATA ===")
            for key, value in word_by_word.items():
                style = value.get('style', 'unknown')
                source = value.get('source', '')
                spanish = value.get('spanish', '')
                print(f"{key}: {style} - [{source}] -> [{spanish}]")
        else:
            print("❌ No word-by-word data received!")
        
        return True
            
    except Exception as e:
        print(f"Request failed: {e}")
        return False

if __name__ == "__main__":
    debug_ai_response()