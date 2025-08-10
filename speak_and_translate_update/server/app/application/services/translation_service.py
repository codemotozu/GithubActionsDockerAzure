






























# translation_service.py
from google.generativeai import GenerativeModel
import google.generativeai as genai
import os
from dotenv import load_dotenv
from ...domain.entities.translation import Translation
from spellchecker import SpellChecker
import unicodedata
import regex as re
from .tts_service import EnhancedTTSService
import tempfile
from typing import Optional, Dict, List, Tuple


class TranslationService:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)

        self.spell = SpellChecker()

        self.generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }

        self.model = GenerativeModel(
            # model_name="gemini-2.0-flash-exp", generation_config=self.generation_config
            model_name="gemini-2.0-flash", generation_config=self.generation_config
        )

        self.tts_service = EnhancedTTSService()

        self.chat_session = self.model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [
                        """Text  
(Could be any phrase or word)  
<example to follow>  


You are an expert German-English translator with deep knowledge of grammar rules. Follow these specific guidelines:

## CRITICAL GRAMMAR RULES TO FOLLOW:

### ENGLISH GRAMMAR RULES:
1. **Phrasal Verbs**: Group phrasal verbs as single units (e.g., "turn off", "look up", "come up with", "put up with")
2. **Prepositions**: Use correct prepositions with verbs, nouns, and adjectives
3. **Tense Consistency**: Match tense appropriately between languages
4. **Idiomatic Expressions**: Translate meaning, not word-for-word
5. **Modal Verbs**: Use appropriate modals (can, should, must, might)

### GERMAN GRAMMAR RULES:
1. **Separable Verbs**: Handle separable verbs correctly (e.g., "aufstehen" → "ich stehe auf")
2. **Verb Position**: Follow German word order rules (V2 in main clauses, verb-final in subordinate clauses)
3. **Case System**: Use correct cases (Nominativ, Akkusativ, Dativ, Genitiv)
4. **Adjective Declensions**: Properly decline adjectives based on case, gender, and number
5. **Modal Verbs**: Position modal verbs correctly with infinitives at the end

## TRANSLATION STYLES:

### For each requested style, provide:
1. **Translation sentence**: Grammatically correct and natural-sounding
2. **Word-by-word breakdown**: Show how phrases/grammar structures map between languages

### IMPORTANT: In word-by-word sections:
- Group phrasal verbs together: "turn off" (apagar)
- Group separable verbs: "aufstehen" (levantarse), but show separation: "ich stehe auf" (me levanto)
- Group compound words: "Krankenhaus" (hospital)
- Group idiomatic expressions: "es regnet Katzen und Hunde" (it's raining cats and dogs)
- Show grammatical particles: "zu" (to), "um...zu" (in order to)

## EXAMPLES WITH GRAMMAR FOCUS:

**English Phrasal Verbs Example:**
Input: "I need to look up this information"
- Native: "I need to look up this information"
- Word-by-word: "I (Yo) need (necesito) to look up (buscar) this (esta) information (información)"

**German Separable Verbs Example:**
Input: "I wake up early"
- Native: "Ich stehe früh auf"
- Word-by-word: "Ich (I) stehe auf (wake up) früh (early)" 

**German Case System Example:**
Input: "I give the book to my friend"
- Native: "Ich gebe meinem Freund das Buch"
- Word-by-word: "Ich (I) gebe (give) meinem Freund (to my friend-DATIVE) das Buch (the book-ACCUSATIVE)"

## STYLE DEFINITIONS:

**Native**: Most natural, fluent expression a native speaker would use
**Colloquial**: Conversational, informal, everyday language
**Informal**: Relaxed, casual, friendly tone
**Formal**: Professional, polite, structured language

---

Text to translate:
(Input text will be provided here)

<example to follow>

German Translation:
* Conversational-native:
"[Natural German with proper grammar rules applied]"
* word by word Conversational-native German-Spanish:
"[German words/phrases] ([Spanish equivalents]) [showing grammar structures]"

* Conversational-colloquial:
"[Colloquial German with proper grammar]"
* word by word Conversational-colloquial German-Spanish:
"[German words/phrases] ([Spanish equivalents]) [showing grammar structures]"

* Conversational-informal:
"[Informal German with proper grammar]"
* word by word Conversational-informal German-Spanish:
"[German words/phrases] ([Spanish equivalents]) [showing grammar structures]"

* Conversational-formal:
"[Formal German with proper grammar]"
* word by word Conversational-formal German-Spanish:
"[German words/phrases] ([Spanish equivalents]) [showing grammar structures]"

English Translation:
* Conversational-native:
"[Natural English with proper phrasal verbs and grammar]"
* word by word Conversational-native English-Spanish:
"[English words/phrases] ([Spanish equivalents]) [showing grammar structures]"

* Conversational-colloquial:
"[Colloquial English with proper grammar]"
* word by word Conversational-colloquial English-Spanish:
"[English words/phrases] ([Spanish equivalents]) [showing grammar structures]"

* Conversational-informal:
"[Informal English with proper grammar]"
* word by word Conversational-informal English-Spanish:
"[English words/phrases] ([Spanish equivalents]) [showing grammar structures]"

* Conversational-formal:
"[Formal English with proper grammar]"
* word by word Conversational-formal English-Spanish:
"[English words/phrases] ([Spanish equivalents]) [showing grammar structures]"



</example to follow>  
"""
                    ],
                }
            ]
        )

    def _create_dynamic_prompt(self, style_preferences) -> str:
        """Create a dynamic prompt based on user's style preferences with complete coverage emphasis"""
        prompt_parts = ["""You are an expert multilingual translator. Analyze the input text and determine its language, then translate accordingly.

    If the input is in Spanish, translate to German and English.
    If the input is in English, translate to German and Spanish.
    If the input is in German, translate to English and Spanish.

    CRITICAL: You must provide Spanish translations for EVERY SINGLE WORD in the word-by-word breakdown. 
    NO word should be left untranslated. Every article, preposition, pronoun, verb, noun, adjective, and adverb must have a Spanish equivalent.

    Text
    (Could be any phrase or word)
    <example to follow>
    """]
        
        # Check if any German styles are selected
        german_styles = []
        if style_preferences.german_native:
            german_styles.append("native")
        if style_preferences.german_colloquial:
            german_styles.append("colloquial")
        if style_preferences.german_informal:
            german_styles.append("informal")
        if style_preferences.german_formal:
            german_styles.append("formal")
            
        # Check if any English styles are selected
        english_styles = []
        if style_preferences.english_native:
            english_styles.append("native")
        if style_preferences.english_colloquial:
            english_styles.append("colloquial")
        if style_preferences.english_informal:
            english_styles.append("informal")
        if style_preferences.english_formal:
            english_styles.append("formal")

        # Generate German section
        if german_styles:
            prompt_parts.append("\nGerman Translation:")
            for style in german_styles:
                if style == "native":
                    prompt_parts.append('* Conversational-native:\n"[Natural German translation]"')
                    if style_preferences.german_word_by_word:
                        prompt_parts.append('* word by word Conversational-native German-Spanish:\n"[word] ([translation]) [word] ([translation]) ..."')
                elif style == "colloquial":
                    prompt_parts.append('* Conversational-colloquial:\n"[Colloquial German translation]"')
                    if style_preferences.german_word_by_word:
                        prompt_parts.append('* word by word Conversational-colloquial German-Spanish:\n"[word] ([translation]) [word] ([translation]) ..."')
                elif style == "informal":
                    prompt_parts.append('* Conversational-informal:\n"[Informal German translation]"')
                    if style_preferences.german_word_by_word:
                        prompt_parts.append('* word by word Conversational-informal German-Spanish:\n"[word] ([translation]) [word] ([translation]) ..."')
                elif style == "formal":
                    prompt_parts.append('* Conversational-formal:\n"[Formal German translation]"')
                    if style_preferences.german_word_by_word:
                        prompt_parts.append('* word by word Conversational-formal German-Spanish:\n"[word] ([translation]) [word] ([translation]) ..."')

        # Generate English section
        if english_styles:
            prompt_parts.append("\nEnglish Translation:")
            for style in english_styles:
                if style == "native":
                    prompt_parts.append('* Conversational-native:\n"[Natural English translation]"')
                    if style_preferences.english_word_by_word:
                        prompt_parts.append('* word by word Conversational-native English-Spanish:\n"[word] ([translation]) [word] ([translation]) ..."')
                elif style == "colloquial":
                    prompt_parts.append('* Conversational-colloquial:\n"[Colloquial English translation]"')
                    if style_preferences.english_word_by_word:
                        prompt_parts.append('* word by word Conversational-colloquial English-Spanish:\n"[word] ([translation]) [word] ([translation]) ..."')
                elif style == "informal":
                    prompt_parts.append('* Conversational-informal:\n"[Informal English translation]"')
                    if style_preferences.english_word_by_word:
                        prompt_parts.append('* word by word Conversational-informal English-Spanish:\n"[word] ([translation]) [word] ([translation]) ..."')
                elif style == "formal":
                    prompt_parts.append('* Conversational-formal:\n"[Formal English translation]"')
                    if style_preferences.english_word_by_word:
                        prompt_parts.append('* word by word Conversational-formal English-Spanish:\n"[word] ([translation]) [word] ([translation]) ..."')

        prompt_parts.append("\n</example to follow>")
        return "\n".join(prompt_parts)

    async def process_prompt(
        self, text: str, source_lang: str, target_lang: str, style_preferences=None
    ) -> Translation:
        try:
            # Use default preferences if none provided (backward compatibility)
            if style_preferences is None:
                # Default to colloquial only for backward compatibility
                from ...infrastructure.api.routes import TranslationStylePreferences
                style_preferences = TranslationStylePreferences(
                    german_colloquial=True,
                    english_colloquial=True,
                    german_word_by_word=True,  # Default word-by-word preferences
                    english_word_by_word=False
                )

            print(f"🎯 Processing with preferences:")
            print(f"   German word-by-word: {getattr(style_preferences, 'german_word_by_word', 'Not set')}")
            print(f"   English word-by-word: {getattr(style_preferences, 'english_word_by_word', 'Not set')}")

            # Update chat session with dynamic prompt based on style preferences
            dynamic_prompt = self._create_dynamic_prompt(style_preferences)
            
            # Create a new chat session with the dynamic prompt
            chat_session = self.model.start_chat(
                history=[{
                    "role": "user",
                    "parts": [dynamic_prompt],
                }]
            )

            response = chat_session.send_message(text)
            generated_text = response.text

            print(f"Generated text from Gemini: {generated_text[:100]}...")

            # Extract translations and word pairs with style-specific matching
            translations_data = self._extract_text_and_pairs_v2(generated_text, style_preferences)

            audio_filename = None

            # Always generate audio if we have translations
            if translations_data['translations']:
                # Use the enhanced TTS service with structured data
                audio_filename = await self.tts_service.text_to_speech_word_pairs_v2(
                    translations_data=translations_data,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    style_preferences=style_preferences,
                )

            if audio_filename:
                print(f"✅ Successfully generated audio: {audio_filename}")
            else:
                print("❌ Audio generation failed")

            return Translation(
                original_text=text,
                translated_text=generated_text,
                source_language=source_lang,
                target_language=target_lang,
                audio_path=audio_filename if audio_filename else None,
                translations={
                    "main": translations_data['translations'][0] if translations_data['translations'] else generated_text
                },
                word_by_word=self._generate_word_by_word(text, generated_text),
                grammar_explanations=self._generate_grammar_explanations(
                    generated_text
                ),
            )

        except Exception as e:
            print(f"Error in process_prompt: {str(e)}")
            raise Exception(f"Translation processing failed: {str(e)}")

    def _extract_text_and_pairs_v2(
        self, generated_text: str, style_preferences
    ) -> Dict:
        """
        Extract texts and word pairs with proper style-specific matching.
        FIXED: Now handles Spanish input and other language variations.
        """
        result = {
            'translations': [],
            'style_data': []  # List of (translation, word_pairs, is_german, style_name)
        }

        # First, detect what language sections we have
        has_german = "German Translation:" in generated_text
        has_english = "English Translation:" in generated_text
        has_spanish = "Spanish Translation:" in generated_text or "Spanish:" in generated_text
        
        # Log what we found
        print(f"🔍 Detected sections: German={has_german}, English={has_english}, Spanish={has_spanish}")
        print(f"📄 Generated text preview: {generated_text[:200]}...")

        # Split the text into language sections
        german_section = ""
        english_section = ""
        spanish_section = ""
        
        # Handle different possible structures
        if has_spanish and not has_german and not has_english:
            # Input was Spanish, output is Spanish translations to German/English
            # Gemini might have misunderstood - try to extract anyway
            spanish_section = generated_text
            
            # Try to find German and English translations within the Spanish section
            if "German:" in generated_text or "Alemán:" in generated_text:
                parts = re.split(r'(?:German:|Alemán:)', generated_text)
                if len(parts) > 1:
                    german_section = parts[1].split("English:")[0] if "English:" in parts[1] else parts[1]
                    
            if "English:" in generated_text or "Inglés:" in generated_text:
                parts = re.split(r'(?:English:|Inglés:)', generated_text)
                if len(parts) > 1:
                    english_section = parts[1]
        
        elif has_german and has_english:
            # Standard case - input was translated to German and English
            if "German Translation:" in generated_text and "English Translation:" in generated_text:
                parts = generated_text.split("English Translation:")
                german_section = parts[0]
                english_section = "English Translation:" + parts[1] if len(parts) > 1 else ""
            elif "German Translation:" in generated_text:
                german_section = generated_text
            elif "English Translation:" in generated_text:
                english_section = generated_text
        
        # If we still don't have proper sections, try alternative patterns
        if not german_section and not english_section:
            # Try to extract any conversational patterns directly
            lines = generated_text.split('\n')
            current_language = None
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Detect language based on various patterns
                if any(pattern in line.lower() for pattern in ['german', 'deutsch', 'alemán']):
                    current_language = 'german'
                    german_section = '\n'.join(lines[i:])
                elif any(pattern in line.lower() for pattern in ['english', 'inglés']):
                    current_language = 'english'
                    english_section = '\n'.join(lines[i:])
                
                # Also try to detect conversational styles directly
                if '* Conversational' in line or '* conversational' in line:
                    # We found a style line, determine which language it belongs to
                    if current_language == 'german':
                        if not german_section:
                            german_section = '\n'.join(lines[i:])
                    elif current_language == 'english':
                        if not english_section:
                            english_section = '\n'.join(lines[i:])
                    else:
                        # Try to guess based on content
                        if i > 0:
                            prev_lines = '\n'.join(lines[max(0, i-3):i])
                            if any(word in prev_lines.lower() for word in ['german', 'deutsch', 'alemán']):
                                german_section = '\n'.join(lines[i:])
                                current_language = 'german'
                            elif any(word in prev_lines.lower() for word in ['english', 'inglés']):
                                english_section = '\n'.join(lines[i:])
                                current_language = 'english'

        # Process German styles
        if style_preferences.german_native and german_section:
            native_data = self._extract_single_style(
                german_section,
                r'\*\s*[Cc]onversational-native:\s*"([^"]+)"',
                r'\*\s*word by word [Cc]onversational-native (?:German-Spanish|German):\s*"([^"]+)"',
                True,
                "german_native",
                style_preferences.german_word_by_word
            )
            if native_data:
                result['translations'].append(native_data['translation'])
                result['style_data'].append(native_data)

        if style_preferences.german_colloquial and german_section:
            colloquial_data = self._extract_single_style(
                german_section,
                r'\*\s*[Cc]onversational-colloquial:\s*"([^"]+)"',
                r'\*\s*word by word [Cc]onversational-colloquial (?:German-Spanish|German):\s*"([^"]+)"',
                True,
                "german_colloquial",
                style_preferences.german_word_by_word
            )
            if colloquial_data:
                result['translations'].append(colloquial_data['translation'])
                result['style_data'].append(colloquial_data)

        if style_preferences.german_informal and german_section:
            informal_data = self._extract_single_style(
                german_section,
                r'\*\s*[Cc]onversational-informal:\s*"([^"]+)"',
                r'\*\s*word by word [Cc]onversational-informal (?:German-Spanish|German):\s*"([^"]+)"',
                True,
                "german_informal",
                style_preferences.german_word_by_word
            )
            if informal_data:
                result['translations'].append(informal_data['translation'])
                result['style_data'].append(informal_data)

        if style_preferences.german_formal and german_section:
            formal_data = self._extract_single_style(
                german_section,
                r'\*\s*[Cc]onversational-formal:\s*"([^"]+)"',
                r'\*\s*word by word [Cc]onversational-formal (?:German-Spanish|German):\s*"([^"]+)"',
                True,
                "german_formal",
                style_preferences.german_word_by_word
            )
            if formal_data:
                result['translations'].append(formal_data['translation'])
                result['style_data'].append(formal_data)

        # Process English styles
        if style_preferences.english_native and english_section:
            native_data = self._extract_single_style(
                english_section,
                r'\*\s*[Cc]onversational-native:\s*"([^"]+)"',
                r'\*\s*word by word [Cc]onversational-native (?:English-Spanish|English):\s*"([^"]+)"',
                False,
                "english_native",
                style_preferences.english_word_by_word
            )
            if native_data:
                result['translations'].append(native_data['translation'])
                result['style_data'].append(native_data)

        if style_preferences.english_colloquial and english_section:
            colloquial_data = self._extract_single_style(
                english_section,
                r'\*\s*[Cc]onversational-colloquial:\s*"([^"]+)"',
                r'\*\s*word by word [Cc]onversational-colloquial (?:English-Spanish|English):\s*"([^"]+)"',
                False,
                "english_colloquial",
                style_preferences.english_word_by_word
            )
            if colloquial_data:
                result['translations'].append(colloquial_data['translation'])
                result['style_data'].append(colloquial_data)

        if style_preferences.english_informal and english_section:
            informal_data = self._extract_single_style(
                english_section,
                r'\*\s*[Cc]onversational-informal:\s*"([^"]+)"',
                r'\*\s*word by word [Cc]onversational-informal (?:English-Spanish|English):\s*"([^"]+)"',
                False,
                "english_informal",
                style_preferences.english_word_by_word
            )
            if informal_data:
                result['translations'].append(informal_data['translation'])
                result['style_data'].append(informal_data)

        if style_preferences.english_formal and english_section:
            formal_data = self._extract_single_style(
                english_section,
                r'\*\s*[Cc]onversational-formal:\s*"([^"]+)"',
                r'\*\s*word by word [Cc]onversational-formal (?:English-Spanish|English):\s*"([^"]+)"',
                False,
                "english_formal",
                style_preferences.english_word_by_word
            )
            if formal_data:
                result['translations'].append(formal_data['translation'])
                result['style_data'].append(formal_data)

        # If still no translations found, try a more aggressive extraction
        if len(result['translations']) == 0:
            print("⚠️ No translations found with standard patterns, trying fallback extraction...")
            
            # Look for any quoted text after "Conversational" patterns
            conversational_matches = re.findall(
                r'\*\s*[Cc]onversational-\w+:\s*"([^"]+)"',
                generated_text
            )
            
            for match in conversational_matches[:4]:  # Take up to 4 matches
                result['translations'].append(match)
                # Create a basic style data entry
                result['style_data'].append({
                    'translation': match,
                    'word_pairs': [],
                    'is_german': 'German' in generated_text[:generated_text.find(match)] if match in generated_text else False,
                    'style_name': 'extracted_style'
                })

        print(f"🎵 Extraction summary:")
        print(f"   Translations found: {len(result['translations'])}")
        print(f"   Style data entries: {len(result['style_data'])}")
        for style_info in result['style_data']:
            print(f"   - {style_info['style_name']}: {len(style_info['word_pairs'])} word pairs")

        return result

    def _extract_single_style(
        self, 
        text_section: str, 
        text_pattern: str, 
        pairs_pattern: str,
        is_german: bool,
        style_name: str,
        word_by_word_enabled: bool
    ) -> Optional[Dict]:
        """
        Extract translation and word pairs for a single style with improved parsing.
        FIXED: More flexible pattern matching and better error handling.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Try multiple pattern variations for better matching
        text_patterns = [
            text_pattern,
            text_pattern.replace('"([^"]+)"', r'"?([^"\n]+)"?'),  # Optional quotes
            text_pattern.replace('"([^"]+)"', r'["\']([^"\'\n]+)["\']'),  # Single or double quotes
        ]
        
        translation_text = None
        for pattern in text_patterns:
            try:
                text_match = re.search(pattern, text_section, re.DOTALL | re.IGNORECASE)
                if text_match:
                    translation_text = text_match.group(1).strip()
                    break
            except Exception as e:
                logger.debug(f"Pattern failed: {pattern}, Error: {e}")
                continue
        
        if not translation_text:
            logger.debug(f"No translation found for {style_name} with patterns")
            return None
            
        # Clean up the translation text
        translation_text = translation_text.strip('"\'').strip()
        
        # Extract word pairs if word-by-word is enabled
        word_pairs = []
        if word_by_word_enabled:
            # Try multiple pattern variations for word pairs
            pairs_patterns = [
                pairs_pattern,
                pairs_pattern.replace('"([^"]+)"', r'"?([^"\n]+)"?'),  # Optional quotes
                pairs_pattern.replace('German-Spanish', '(?:German-Spanish|German|Alemán-Español)'),
                pairs_pattern.replace('English-Spanish', '(?:English-Spanish|English|Inglés-Español)'),
            ]
            
            pairs_text = None
            for pattern in pairs_patterns:
                try:
                    pairs_match = re.search(pattern, text_section, re.IGNORECASE | re.DOTALL)
                    if pairs_match:
                        pairs_text = pairs_match.group(1)
                        break
                except Exception as e:
                    logger.debug(f"Pairs pattern failed: {pattern}, Error: {e}")
                    continue
            
            if pairs_text:
                # Enhanced regex patterns to capture word-translation pairs
                patterns_to_try = [
                    r'([^()]+?)\s*\(([^)]+?)\)',  # Standard: word (translation)
                    r'(\S+(?:\s+\S+)?)\s*\(([^)]+?)\)',  # One or two words (translation)
                    r'"([^"]+)"\s*\(([^)]+?)\)',  # "word" (translation)
                    r'([^,()]+?)\s*\(([^)]+?)\)',  # Anything except comma/parens (translation)
                ]
                
                for pair_pattern in patterns_to_try:
                    pair_matches = re.findall(pair_pattern, pairs_text)
                    if pair_matches:
                        for source, target in pair_matches:
                            # Clean up the extracted pairs
                            source = source.strip().strip('"\'').rstrip('.,!?;:')
                            target = target.strip().strip('"\'')
                            
                            # Skip empty pairs or overly long ones
                            if not source or not target or len(source.split()) > 8:
                                continue
                                
                            word_pairs.append((source, target))
                            logger.debug(f"   Extracted pair: '{source}' -> '{target}'")
                        
                        if word_pairs:
                            break  # We found pairs, stop trying other patterns
                
                # If still no pairs found, try a simpler approach
                if not word_pairs:
                    # Split by common separators and look for parentheses
                    segments = re.split(r'[,;]\s*', pairs_text)
                    for segment in segments:
                        match = re.search(r'(.+?)\s*\(([^)]+)\)', segment)
                        if match:
                            source = match.group(1).strip().strip('"\'')
                            target = match.group(2).strip().strip('"\'')
                            if source and target:
                                word_pairs.append((source, target))
        
        logger.info(f"   {style_name}: Found translation and {len(word_pairs)} word pairs")
        
        return {
            'translation': translation_text,
            'word_pairs': word_pairs,
            'is_german': is_german,
            'style_name': style_name
        }

    def _extract_text_and_pairs(
        self, generated_text: str, style_preferences
    ) -> tuple[list[str], list[tuple[str, str, bool]]]:
        """
        Legacy method for backward compatibility.
        Extract texts and word pairs based on user's style preferences.
        """
        result = self._extract_text_and_pairs_v2(generated_text, style_preferences)
        
        # Convert to legacy format
        translations = result['translations']
        
        # Flatten all word pairs with their language flag
        word_pairs = []
        for style_info in result['style_data']:
            for source, target in style_info['word_pairs']:
                word_pairs.append((source, target, style_info['is_german']))
        
        # Remove duplicates while preserving order
        seen_pairs = set()
        unique_pairs = []
        for pair in word_pairs:
            pair_tuple = (pair[0], pair[1], pair[2])
            if pair_tuple not in seen_pairs:
                seen_pairs.add(pair_tuple)
                unique_pairs.append(pair)
        
        return translations, unique_pairs

    def _generate_word_by_word(
        self, original: str, translated: str
    ) -> dict[str, dict[str, str]]:
        """Generate word-by-word translation mapping."""
        result = {}
        original_words = original.split()
        translated_words = translated.split()

        for i, word in enumerate(original_words):
            if i < len(translated_words):
                result[word] = {
                    "translation": translated_words[i],
                    "pos": "unknown",
                }
        return result

    def _generate_grammar_explanations(self, text: str) -> dict[str, str]:
        """Generate grammar explanations for the translation."""
        return {
            "structure": "Basic sentence structure explanation",
            "tense": "Tense usage explanation",
        }

    def _normalize_text(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text)
        ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
        return ascii_text

    def _restore_accents(self, text: str) -> str:
        accent_map = {
            "a": "á", "e": "é", "i": "í", "o": "ó", "u": "ú", "n": "ñ",
            "A": "Á", "E": "É", "I": "Í", "O": "Ó", "U": "Ú", "N": "Ñ",
        }

        patterns = {
            r"([aeiou])´": lambda m: accent_map[m.group(1)],
            r"([AEIOU])´": lambda m: accent_map[m.group(1)],
            r"n~": "ñ", r"N~": "Ñ",
        }

        for pattern, replacement in patterns.items():
            if callable(replacement):
                text = re.sub(pattern, replacement, text)
            else:
                text = re.sub(pattern, replacement, text)

        return text

    def _ensure_unicode(self, text: str) -> str:
        if isinstance(text, bytes):
            text = text.decode("utf-8")
        return unicodedata.normalize("NFKC", text)

    def _get_temp_directory(self) -> str:
        """Get the appropriate temporary directory based on the operating system."""
        if os.name == "nt":
            temp_dir = os.environ.get("TEMP") or os.environ.get("TMP")
        else:
            temp_dir = "/tmp"

        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    def _auto_fix_spelling(self, text: str) -> str:
        """Fix spelling in the given text."""
        words = re.findall(r"\b\w+\b|[^\w\s]", text)
        corrected_words = []

        for word in words:
            if not re.match(r"\w+", word):
                corrected_words.append(word)
                continue

            if self.spell.unknown([word]):
                correction = self.spell.correction(word)
                if correction:
                    if word.isupper():
                        correction = correction.upper()
                    elif word[0].isupper():
                        correction = correction.capitalize()
                    word = correction

            corrected_words.append(word)

        return " ".join(corrected_words)