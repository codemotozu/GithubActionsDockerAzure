#!/usr/bin/env python3
# trace_debug.py - Trace the extraction process

import asyncio
import sys
import os

# Add the server directory to the Python path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

# Set UTF-8 encoding for console output
import codecs
if sys.platform == "win32":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

async def trace_extraction():
    """Trace the extraction process to see where word pairs get lost"""
    
    try:
        print("TRACE: Starting extraction trace")
        
        from server.app.application.services.translation_service import TranslationService
        from server.app.domain.entities.translation_style_preferences import TranslationStylePreferences
        
        service = TranslationService()
        
        # Create test style preferences
        style_prefs = TranslationStylePreferences(
            mother_tongue="spanish",
            german_native=True,
            german_word_by_word=True,  # ENABLED
            english_native=True,
            english_word_by_word=False  # DISABLED
        )
        
        print(f"Style preferences attributes:")
        for attr in ['german_word_by_word', 'english_word_by_word', 'german_native', 'english_native']:
            value = getattr(style_prefs, attr, 'NOT_FOUND')
            print(f"  {attr}: {value}")
        
        # Mock AI response with proper format that matches parser expectations
        mock_ai_response = """
MULTI-STYLE TRANSLATION RESULTS:

GERMAN TRANSLATIONS:
German Native: Ananassaft für das Kind

ENGLISH TRANSLATIONS:
English Native: Pineapple juice for the child

GERMAN WORD-BY-WORD:
German Native word-by-word: [Ananassaft] ([jugo de piña]) [für] ([para]) [das] ([la]) [Kind] ([niña])

ENGLISH WORD-BY-WORD:
English Native word-by-word: [Pineapple] ([jugo]) [juice] ([de piña]) [for] ([para]) [the] ([la]) [child] ([niña])
"""
        
        print(f"\nTesting extraction with mock AI response...")
        
        # Test the extraction process
        translations_data = await service._extract_translations_fixed(mock_ai_response, style_prefs)
        
        print(f"\nExtraction results:")
        print(f"- Translations count: {len(translations_data.get('translations', []))}")
        print(f"- Style data count: {len(translations_data.get('style_data', []))}")
        
        for i, style_info in enumerate(translations_data.get('style_data', [])):
            style_name = style_info.get('style_name', 'unknown')
            is_german = style_info.get('is_german', False)
            word_pairs = style_info.get('word_pairs', [])
            
            print(f"\nStyle {i+1}: {style_name}")
            print(f"  is_german: {is_german}")
            print(f"  word_pairs count: {len(word_pairs)}")
            
            if word_pairs:
                print(f"  Sample pairs: {word_pairs[:2]}")
            else:
                print(f"  NO WORD PAIRS FOUND!")
        
        # Now test UI sync data creation
        print(f"\nTesting UI sync data creation...")
        ui_data = service._create_perfect_ui_sync_data(translations_data, style_prefs)
        
        print(f"UI data result: {len(ui_data) if ui_data else 0} entries")
        
        return len(ui_data) > 0 if ui_data else False
        
    except Exception as e:
        print(f"ERROR in trace: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(trace_extraction())
    print(f"\nTrace result: {'SUCCESS' if success else 'FAILED'}")