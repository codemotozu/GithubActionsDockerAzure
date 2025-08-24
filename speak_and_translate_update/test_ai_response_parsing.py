#!/usr/bin/env python3
"""
Test script to debug AI response parsing
"""

def test_ai_response_parsing():
    """Test parsing of the actual AI response from the logs"""
    
    ai_response = """GERMAN TRANSLATIONS:
German Colloquial: Ich bin heute Morgen früh aufgestanden.

GERMAN WORD-BY-WORD:
Colloquial style word-by-word:
[Ich] : [me]
[bin] : [None]
[heute Morgen] : [esta mañana]
[früh] : [temprano]
[aufgestanden] : [levanto]

ENGLISH TRANSLATIONS:
English Colloquial: I got up early this morning.

ENGLISH WORD-BY-WORD:
[I] : [me]
[got up] : [levanto]
[this morning] : [esta mañana]
[early] : [temprano]"""

    print("Testing AI response parsing...")
    print("="*60)
    print(f"AI Response:")
    print(ai_response)
    print("="*60)
    
    # Simulate the parsing logic
    lines = ai_response.split('\n')
    current_language = None
    translations = []
    word_by_word_data = {}
    style_data = []
    
    # Mock style preferences
    class MockPrefs:
        german_colloquial = True
        english_colloquial = True
        german_word_by_word = True
        english_word_by_word = False
        
    style_preferences = MockPrefs()
    
    print("\nParsing step by step:")
    print("-" * 40)
    
    for i, line in enumerate(lines):
        line = line.strip()
        print(f"Line {i+1}: '{line}' -> Language: {current_language}")
        
        if not line:
            continue
        
        # Detect language sections
        if 'GERMAN TRANSLATIONS:' in line.upper():
            current_language = 'german'
            print(f"  -> Found German section")
        elif 'ENGLISH TRANSLATIONS:' in line.upper():
            current_language = 'english' 
            print(f"  -> Found English section")
        elif 'GERMAN WORD-BY-WORD:' in line.upper():
            current_language = 'german_wbw'
            print(f"  -> Found German word-by-word section")
        elif 'ENGLISH WORD-BY-WORD:' in line.upper():
            current_language = 'english_wbw'
            print(f"  -> Found English word-by-word section")
        
        # Extract translations
        elif current_language == 'german':
            if 'German Colloquial:' in line and style_preferences.german_colloquial:
                translation = line.split('German Colloquial:')[1].strip()
                translations.append(translation)
                style_data.append({
                    'translation': translation,
                    'word_pairs': [],
                    'is_german': True,
                    'is_spanish': False,
                    'style_name': 'german_colloquial'
                })
                print(f"  -> Found German Colloquial: {translation}")
                
        elif current_language == 'english':
            if 'English Colloquial:' in line and style_preferences.english_colloquial:
                translation = line.split('English Colloquial:')[1].strip()
                translations.append(translation)
                style_data.append({
                    'translation': translation,
                    'word_pairs': [],
                    'is_german': False,
                    'is_spanish': False,
                    'style_name': 'english_colloquial'
                })
                print(f"  -> Found English Colloquial: {translation}")
        
        # Extract word-by-word data
        elif current_language == 'german_wbw':
            if '[' in line and ']' in line and ':' in line:
                # Extract word pairs
                import re
                pattern = r'\[([^\]]+)\]\s*:\s*\[([^\]]+)\]'
                matches = re.findall(pattern, line)
                if matches:
                    for source, target in matches:
                        if 'german_wbw' not in word_by_word_data:
                            word_by_word_data['german_wbw'] = []
                        if target.lower() != 'none':
                            word_by_word_data['german_wbw'].append((source.strip(), target.strip()))
                            print(f"  -> German word pair: {source} -> {target}")
                        
        elif current_language == 'english_wbw':
            if '[' in line and ']' in line and ':' in line:
                # Extract word pairs
                import re
                pattern = r'\[([^\]]+)\]\s*:\s*\[([^\]]+)\]'
                matches = re.findall(pattern, line)
                if matches:
                    for source, target in matches:
                        if 'english_wbw' not in word_by_word_data:
                            word_by_word_data['english_wbw'] = []
                        word_by_word_data['english_wbw'].append((source.strip(), target.strip()))
                        print(f"  -> English word pair: {source} -> {target}")
    
    print("\n" + "="*60)
    print("PARSING RESULTS:")
    print("="*60)
    print(f"Total translations found: {len(translations)}")
    print(f"Total style_data entries: {len(style_data)}")
    
    print("\nTranslations:")
    for i, translation in enumerate(translations):
        print(f"  {i+1}. {translation}")
        
    print("\nStyle data:")
    for i, style in enumerate(style_data):
        print(f"  {i+1}. {style['style_name']}: {style['translation']}")
        
    print("\nWord-by-word data:")
    for lang, pairs in word_by_word_data.items():
        print(f"  {lang}: {len(pairs)} pairs")
        for pair in pairs:
            print(f"    {pair[0]} -> {pair[1]}")
    
    print("\n" + "="*60)
    if len(style_data) >= 2:
        print("SUCCESS: Both German and English translations were parsed!")
        return True
    else:
        print("ISSUE: Only {} style(s) parsed, expected 2".format(len(style_data)))
        return False

if __name__ == "__main__":
    result = test_ai_response_parsing()
    exit(0 if result else 1)