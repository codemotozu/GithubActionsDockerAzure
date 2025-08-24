#!/usr/bin/env python3
# debug_word_by_word.py - Debug the word-by-word synchronization issue

import asyncio
import sys
import os

# Add the server directory to the Python path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

async def debug_word_by_word():
    """Debug the word-by-word synchronization data flow"""
    
    try:
        print("DEBUG: Starting word-by-word synchronization debug...")
        print("="*50)
        
        # Import required modules
        from server.app.application.services.translation_service import TranslationService
        
        # Check if the domain entities exist
        try:
            from server.app.domain.entities.translation_style_preferences import TranslationStylePreferences
            print("SUCCESS: TranslationStylePreferences imported successfully")
        except ImportError as e:
            print(f"ERROR: Could not import TranslationStylePreferences: {e}")
            # Let's check what's in the domain directory
            domain_path = os.path.join(os.path.dirname(__file__), 'server', 'app', 'domain')
            if os.path.exists(domain_path):
                print(f"Domain directory exists at: {domain_path}")
                entities_path = os.path.join(domain_path, 'entities')
                if os.path.exists(entities_path):
                    print(f"Entities directory exists at: {entities_path}")
                    files = os.listdir(entities_path)
                    print(f"Files in entities: {files}")
                else:
                    print("Entities directory does not exist")
            else:
                print("Domain directory does not exist")
            return False
        
        # Create test style preferences
        style_prefs = TranslationStylePreferences(
            mother_tongue="spanish",
            german_native=True,
            german_word_by_word=True,  # ENABLED
            english_native=True,
            english_word_by_word=False  # DISABLED
        )
        
        print(f"Style preferences created:")
        print(f"  German word-by-word: {style_prefs.german_word_by_word}")
        print(f"  English word-by-word: {style_prefs.english_word_by_word}")
        
        # Create translation service
        service = TranslationService()
        print("TranslationService created successfully")
        
        # Test translation
        print("\nTesting translation process...")
        result = await service.process_prompt(
            text="Jugo de pina para la nina",  # Removed accents to avoid encoding issues
            source_lang="spanish", 
            target_lang="multi",
            style_preferences=style_prefs,
            mother_tongue="spanish"
        )
        
        print(f"Translation result received")
        print(f"  Original: {result.original_text}")
        print(f"  Translated: {result.translated_text[:100]}...")
        
        # Check word_by_word data
        word_by_word = result.word_by_word
        print(f"\nWord-by-word data analysis:")
        print(f"  Type: {type(word_by_word)}")
        print(f"  Is None: {word_by_word is None}")
        
        if word_by_word:
            print(f"  Length: {len(word_by_word)}")
            print(f"  Keys (first 5): {list(word_by_word.keys())[:5]}")
            
            # Check for German entries
            german_entries = [k for k, v in word_by_word.items() if isinstance(v, dict) and v.get('language') == 'german']
            print(f"  German entries: {len(german_entries)}")
            
            if german_entries:
                print("  Sample German entry:")
                sample_key = german_entries[0]
                sample_data = word_by_word[sample_key]
                for key, value in sample_data.items():
                    print(f"    {key}: {value}")
        else:
            print("  No word-by-word data found!")
            
        return word_by_word is not None and len(word_by_word) > 0
        
    except Exception as e:
        print(f"ERROR in debug: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(debug_word_by_word())
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")