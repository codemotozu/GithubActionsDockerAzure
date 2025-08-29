#!/usr/bin/env python3
"""Test to verify the difference between sentence audio and word-by-word audio"""
import requests
import json
import time

def test_audio_difference():
    """Test the difference between word-by-word audio ON vs OFF"""
    url = "http://localhost:8000/api/conversation"
    base_text = "me levante temprano porque quiero tener una vida diferente"
    
    # Test 1: Word-by-word audio OFF
    payload1 = {
        "text": base_text,
        "stylePreferences": {
            "motherTongue": "spanish",
            "germanNative": True,
            "germanFormal": True,
            "englishNative": True,
            "englishFormal": True,
            "germanWordByWord": False,  # OFF
            "englishWordByWord": False   # OFF
        }
    }
    
    print("=== TEST 1: Word-by-word audio DISABLED ===")
    print("Expected: Simple sentence audio")
    print("Check server logs for: 'Simple translation reading'")
    
    try:
        response1 = requests.post(url, json=payload1, timeout=60)
        response1.raise_for_status()
        data1 = response1.json()
        
        print(f"Audio generated: {data1.get('audio_path') is not None}")
        print(f"Audio file: {data1.get('audio_path', 'None')}")
        print("Check server console for audio type message...")
        
    except Exception as e:
        print(f"Test 1 failed: {e}")
    
    print("\nWaiting 3 seconds...\n")
    time.sleep(3)
    
    # Test 2: Word-by-word audio ON
    payload2 = {
        "text": base_text,
        "stylePreferences": {
            "motherTongue": "spanish",
            "germanNative": True,
            "germanFormal": True,
            "englishNative": True,
            "englishFormal": True,
            "germanWordByWord": True,   # ON
            "englishWordByWord": True    # ON
        }
    }
    
    print("=== TEST 2: Word-by-word audio ENABLED ===")
    print("Expected: Word-by-word breakdown audio")
    print("Check server logs for: 'Word-by-word breakdown'")
    
    try:
        response2 = requests.post(url, json=payload2, timeout=60)
        response2.raise_for_status()
        data2 = response2.json()
        
        print(f"Audio generated: {data2.get('audio_path') is not None}")
        print(f"Audio file: {data2.get('audio_path', 'None')}")
        print("Check server console for audio type message...")
        
    except Exception as e:
        print(f"Test 2 failed: {e}")
    
    print("\n" + "="*60)
    print("INSTRUCTIONS:")
    print("1. Check the server console logs for these messages:")
    print("   - Test 1 should show: 'Audio type: Simple translation reading'")
    print("   - Test 2 should show: 'Audio type: Word-by-word breakdown'")
    print("2. Listen to both audio files to hear the difference:")
    print("   - Test 1: Should be smooth sentence pronunciation")
    print("   - Test 2: Should break down word-by-word with Spanish equivalents")
    print("3. Both tests should provide visual word-by-word translations")

if __name__ == "__main__":
    test_audio_difference()