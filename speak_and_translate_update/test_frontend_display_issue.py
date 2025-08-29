#!/usr/bin/env python3
"""Test to verify what the frontend is actually receiving for display"""
import requests
import json

def test_frontend_display():
    """Test what frontend receives when word-by-word audio is disabled"""
    url = "http://localhost:8000/api/conversation"
    
    payload = {
        "text": "me doy besos porque me amo mucho",
        "stylePreferences": {
            "motherTongue": "spanish",
            "germanNative": True,
            "germanColloquial": True,
            "germanInformal": True,
            "germanFormal": True,
            "englishNative": True,
            "englishColloquial": True,
            "englishInformal": True,
            "englishFormal": True,
            # CRITICAL: Word-by-word audio DISABLED
            "germanWordByWord": False,
            "englishWordByWord": False
        }
    }
    
    print("=== FRONTEND DISPLAY ISSUE DIAGNOSIS ===")
    print("Testing with ALL STYLES ENABLED, but word-by-word audio DISABLED")
    print("Expected: Should see ALL 8 style translations with word-by-word visuals")
    print("Problem: User only sees ONE sentence")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\nResponse status: {response.status_code}")
        
        # Check what the frontend will receive
        print("\n=== WHAT FRONTEND RECEIVES ===")
        
        # Check translations (this feeds the main display)
        translations = data.get('translations', {})
        print(f"\nTRANSLATIONS (for main display): {len(translations)} styles")
        for key, value in translations.items():
            print(f"  {key}: {value}")
        
        # Check styles (this feeds the enhanced widget)
        styles = data.get('styles', [])
        print(f"\nSTYLES DATA (for enhanced widget): {len(styles)} styles")
        for i, style in enumerate(styles):
            style_name = style.get('name', 'unknown')
            translation = style.get('translation', 'no translation')
            word_pairs_count = len(style.get('word_pairs', []))
            print(f"  Style {i+1}: {style_name}")
            print(f"    Translation: {translation}")
            print(f"    Word pairs: {word_pairs_count}")
        
        # Check word-by-word (this is the visual data)
        word_by_word = data.get('word_by_word', {})
        print(f"\nWORD-BY-WORD DATA (for visual display): {len(word_by_word)} entries")
        
        # Group by style
        style_groups = {}
        for key, value in word_by_word.items():
            style = value.get('style', 'unknown')
            if style not in style_groups:
                style_groups[style] = 0
            style_groups[style] += 1
        
        for style, count in style_groups.items():
            print(f"  {style}: {count} word pairs")
        
        # Audio check
        has_audio = data.get('audio_path') is not None
        print(f"\nAUDIO GENERATED: {has_audio}")
        print(f"Audio file: {data.get('audio_path', 'None')}")
        
        # DIAGNOSIS
        print(f"\n=== DIAGNOSIS ===")
        if len(translations) == 1:
            print("❌ ISSUE FOUND: Only 1 translation in 'translations' field")
            print("   This means frontend will only show the 'main' translation")
        elif len(translations) >= 8:
            print("✅ TRANSLATIONS OK: Multiple translations available")
        
        if len(styles) == 0:
            print("❌ ISSUE FOUND: No 'styles' data provided")
            print("   Enhanced widget will have nothing to display")
        elif len(styles) >= 8:
            print("✅ STYLES OK: Multiple styles available for enhanced widget")
            
        if len(word_by_word) == 0:
            print("❌ ISSUE FOUND: No word-by-word data")
            print("   No visual word-by-word will be displayed")
        elif len(word_by_word) >= 50:
            print("✅ WORD-BY-WORD OK: Rich visual data available")
        
        # The key issue: Check if frontend has the right data structure
        expected_behavior = {
            'multiple_translations': len(translations) > 1,
            'multiple_styles': len(styles) > 1, 
            'visual_word_by_word': len(word_by_word) > 10,
            'audio_present': has_audio
        }
        
        print(f"\n=== EXPECTED BEHAVIOR CHECK ===")
        all_good = True
        for check, passed in expected_behavior.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{check.replace('_', ' ').title()}: {status}")
            if not passed:
                all_good = False
        
        if all_good:
            print(f"\n✅ BACKEND DATA IS CORRECT")
            print("The issue is likely in the FRONTEND DISPLAY LOGIC")
            print("The frontend should show all styles but might be filtering them")
        else:
            print(f"\n❌ BACKEND DATA ISSUE FOUND")
            print("Backend is not providing the expected data structure")
        
        return all_good
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_frontend_display()
    exit(0 if success else 1)