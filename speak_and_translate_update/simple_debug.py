#!/usr/bin/env python3
# simple_debug.py - Simple debug without emojis

import asyncio
import sys
import os

# Add the server directory to the Python path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

# Set UTF-8 encoding for console output
import io
import codecs

# Redirect stdout to handle encoding issues
if sys.platform == "win32":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

async def simple_debug():
    """Simple debug focusing on the data flow"""
    
    try:
        print("DEBUG: Starting simple word-by-word debug")
        
        # Create mock data to test the UI sync function directly
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
        
        # Create mock translations_data as it would come from extraction
        mock_translations_data = {
            'translations': ['Ananassaft für das Kind'],
            'original_text': 'Jugo de pina para la nina',
            'style_data': [
                {
                    'style_name': 'german_native',
                    'translation': 'Ananassaft für das Kind',
                    'is_german': True,
                    'is_spanish': False,
                    'word_pairs': [
                        ('Ananassaft', 'Jugo de pina'),
                        ('für', 'para'), 
                        ('das', 'la'),
                        ('Kind', 'nina')
                    ]
                },
                {
                    'style_name': 'english_native',
                    'translation': 'Pineapple juice for the girl',
                    'is_german': False,
                    'is_spanish': False,
                    'word_pairs': [
                        ('Pineapple', 'Jugo'),
                        ('juice', 'de pina'),
                        ('for', 'para'),
                        ('the', 'la'),
                        ('girl', 'nina')
                    ]
                }
            ]
        }
        
        print("Mock data created")
        print(f"- German word-by-word enabled: {style_prefs.german_word_by_word}")  
        print(f"- English word-by-word enabled: {style_prefs.english_word_by_word}")
        print(f"- Style data entries: {len(mock_translations_data['style_data'])}")
        
        # Test the _create_perfect_ui_sync_data function directly
        ui_data = service._create_perfect_ui_sync_data(mock_translations_data, style_prefs)
        
        print(f"\nUI Data Result:")
        print(f"- Type: {type(ui_data)}")
        print(f"- Is None: {ui_data is None}")
        
        if ui_data:
            print(f"- Length: {len(ui_data)}")
            print(f"- Keys: {list(ui_data.keys())[:5]}")
            
            # Check for German entries (should exist)
            german_entries = [k for k, v in ui_data.items() if isinstance(v, dict) and v.get('language') == 'german']
            english_entries = [k for k, v in ui_data.items() if isinstance(v, dict) and v.get('language') == 'english']
            
            print(f"- German entries: {len(german_entries)} (expected: >0)")
            print(f"- English entries: {len(english_entries)} (expected: 0)")
            
            if german_entries:
                print("Sample German entry:")
                sample = ui_data[german_entries[0]]
                print(f"  display_format: {sample.get('display_format', 'N/A')}")
                print(f"  confidence: {sample.get('_internal_confidence', 'N/A')}")
        else:
            print("- NO UI DATA GENERATED!")
            
        return len(ui_data) > 0 if ui_data else False
        
    except Exception as e:
        print(f"ERROR in simple debug: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(simple_debug())
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")