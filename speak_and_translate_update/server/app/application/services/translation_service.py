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

### CRITICAL REQUIREMENT: COMPLETE WORD-BY-WORD COVERAGE
In word-by-word sections, you MUST provide Spanish translations for EVERY SINGLE WORD OR PHRASE in the translation. 
NO word should be left without a Spanish translation. If a word doesn't have a direct translation, provide the closest Spanish equivalent or explanation.

### IMPORTANT: In word-by-word sections:
- Group phrasal verbs together: "turn off" (apagar)
- Group separable verbs: "aufstehen" (levantarse), but show separation: "ich stehe auf" (me levanto)
- Group compound words: "Krankenhaus" (hospital)
- Group idiomatic expressions: "es regnet Katzen und Hunde" (llueve a cántaros)
- Show grammatical particles: "zu" (para), "um...zu" (para)
- Provide translation for EVERY article: "der" (el), "die" (la), "das" (el/lo)
- Provide translation for EVERY pronoun: "ich" (yo), "du" (tú), "er" (él)
- Provide translation for EVERY preposition: "in" (en), "auf" (sobre), "mit" (con)
- Provide translation for EVERY conjunction: "und" (y), "aber" (pero), "oder" (o)
- Provide translation for EVERY auxiliary verb: "haben" (haber), "sein" (ser/estar), "werden" (llegar a ser)

## EXAMPLES WITH COMPLETE COVERAGE:

**English Phrasal Verbs Example:**
Input: "I need to look up this information"
- Native: "I need to look up this information"
- Word-by-word: "I (yo) need (necesito) to (que) look up (buscar) this (esta) information (información)"

**German Complete Coverage Example:**
Input: "I wake up early"
- Native: "Ich stehe früh auf"
- Word-by-word: "Ich (yo) stehe auf (me levanto) früh (temprano)" 

**German Case System Example:**
Input: "I give the book to my friend"
- Native: "Ich gebe meinem Freund das Buch"
- Word-by-word: "Ich (yo) gebe (doy) meinem (a mi) Freund (amigo) das (el) Buch (libro)"

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
"[German word/phrase] ([Spanish translation]) [German word/phrase] ([Spanish translation]) [continuing for EVERY word]"

* Conversational-colloquial:
"[Colloquial German with proper grammar]"
* word by word Conversational-colloquial German-Spanish:
"[German word/phrase] ([Spanish translation]) [German word/phrase] ([Spanish translation]) [continuing for EVERY word]"

* Conversational-informal:
"[Informal German with proper grammar]"
* word by word Conversational-informal German-Spanish:
"[German word/phrase] ([Spanish translation]) [German word/phrase] ([Spanish translation]) [continuing for EVERY word]"

* Conversational-formal:
"[Formal German with proper grammar]"
* word by word Conversational-formal German-Spanish:
"[German word/phrase] ([Spanish translation]) [German word/phrase] ([Spanish translation]) [continuing for EVERY word]"

English Translation:
* Conversational-native:
"[Natural English with proper phrasal verbs and grammar]"
* word by word Conversational-native English-Spanish:
"[English word/phrase] ([Spanish translation]) [English word/phrase] ([Spanish translation]) [continuing for EVERY word]"

* Conversational-colloquial:
"[Colloquial English with proper grammar]"
* word by word Conversational-colloquial English-Spanish:
"[English word/phrase] ([Spanish translation]) [English word/phrase] ([Spanish translation]) [continuing for EVERY word]"

* Conversational-informal:
"[Informal English with proper grammar]"
* word by word Conversational-informal English-Spanish:
"[English word/phrase] ([Spanish translation]) [English word/phrase] ([Spanish translation]) [continuing for EVERY word]"

* Conversational-formal:
"[Formal English with proper grammar]"
* word by word Conversational-formal English-Spanish:
"[English word/phrase] ([Spanish translation]) [English word/phrase] ([Spanish translation]) [continuing for EVERY word]"



</example to follow>  
"""
                    ],
                }
            ]
        )

    def _create_dynamic_prompt(self, style_preferences) -> str:
        """Create a dynamic prompt based on user's style preferences with complete coverage emphasis"""
        prompt_parts = ["Text\n(Could be any phrase or word)\n<example to follow>\n"]
        
        # Add emphasis on complete coverage
        prompt_parts.append("""
CRITICAL: You must provide Spanish translations for EVERY SINGLE WORD in the word-by-word breakdown. 
NO word should be left untranslated. Every article, preposition, pronoun, verb, noun, adjective, and adverb must have a Spanish equivalent.
""")
        
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

        # Generate German section with enhanced examples
        if german_styles:
            prompt_parts.append("German Translation:")
            if "native" in german_styles:
                prompt_parts.append("""* Conversational-native:
"Ich muss diese Informationen nachschlagen" (with proper separable verb)
* word by word Conversational-native German-Spanish:
"Ich (yo) muss (debo) diese (esta) Informationen (información) nachschlagen (buscar/consultar)" """)
            if "colloquial" in german_styles:
                prompt_parts.append("""* Conversational-colloquial:
"Ich muss das mal nachschauen" (colloquial with modal particle)
* word by word Conversational-colloquial German-Spanish:
"Ich (yo) muss (debo) das (eso) mal (una vez) nachschauen (revisar)" """)
            if "informal" in german_styles:
                prompt_parts.append("""* Conversational-informal:
"Ich schau das mal nach" (informal, relaxed)
* word by word Conversational-informal German-Spanish:
"Ich (yo) schau (busco) das (eso) mal (una vez) nach (después)" """)
            if "formal" in german_styles:
                prompt_parts.append("""* Conversational-formal:
"Ich möchte diese Angaben überprüfen" (formal, polite)
* word by word Conversational-formal German-Spanish:
"Ich (yo) möchte (me gustaría) diese (estos) Angaben (datos) überprüfen (verificar)" """)

        # Generate English section with enhanced examples
        if english_styles:
            prompt_parts.append("\nEnglish Translation:")
            if "native" in english_styles:
                prompt_parts.append("""* Conversational-native:
"I need to look up this information" (proper phrasal verb usage)
* word by word Conversational-native English-Spanish:
"I (yo) need (necesito) to (que) look up (buscar/consultar) this (esta) information (información)" """)
            if "colloquial" in english_styles:
                prompt_parts.append("""* Conversational-colloquial:
"I gotta check this out" (colloquial with reduced forms)
* word by word Conversational-colloquial English-Spanish:
"I (yo) gotta (tengo que) check (revisar) this (esto) out (fuera)" """)
            if "informal" in english_styles:
                prompt_parts.append("""* Conversational-informal:
"I need to check this info" (informal, abbreviated)
* word by word Conversational-informal English-Spanish:
"I (yo) need (necesito) to (que) check (revisar) this (esta) info (información)" """)
            if "formal" in english_styles:
                prompt_parts.append("""* Conversational-formal:
"I would like to verify this information" (formal, complete)
* word by word Conversational-formal English-Spanish:
"I (yo) would (me) like (gustaría) to (que) verify (verificar) this (esta) information (información)" """)

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
        FIXED: Each style gets its own unique word pairs extracted from its specific section.
        """
        result = {
            'translations': [],
            'style_data': []  # List of (translation, word_pairs, is_german, style_name)
        }

        # Split the text into German and English sections
        german_section = ""
        english_section = ""
        
        if "German Translation:" in generated_text and "English Translation:" in generated_text:
            parts = generated_text.split("English Translation:")
            german_section = parts[0]
            english_section = "English Translation:" + parts[1] if len(parts) > 1 else ""
        elif "German Translation:" in generated_text:
            german_section = generated_text
        elif "English Translation:" in generated_text:
            english_section = generated_text

        # Process German styles
        if style_preferences.german_native and german_section:
            native_data = self._extract_single_style(
                german_section,
                r'\* Conversational-native:\s*"([^"]+)"',
                r'\* word by word Conversational-native German-Spanish:\s*"([^"]+)"',
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
                r'\* Conversational-colloquial:\s*"([^"]+)"',
                r'\* word by word Conversational-colloquial German-Spanish:\s*"([^"]+)"',
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
                r'\* Conversational-informal:\s*"([^"]+)"',
                r'\* word by word Conversational-informal German-Spanish:\s*"([^"]+)"',
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
                r'\* [Cc]onversational-formal:\s*"([^"]+)"',
                r'\* word by word [Cc]onversational-formal German-Spanish:\s*"([^"]+)"',
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
                r'\* Conversational-native:\s*"([^"]+)"',
                r'\* word by word Conversational-native English-Spanish:\s*"([^"]+)"',
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
                r'\* Conversational-colloquial:\s*"([^"]+)"',
                r'\* word by word Conversational-colloquial English-Spanish:\s*"([^"]+)"',
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
                r'\* Conversational-informal:\s*"([^"]+)"',
                r'\* word by word Conversational-informal English-Spanish:\s*"([^"]+)"',
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
                r'\* [Cc]onversational-formal:\s*"([^"]+)"',
                r'\* word by word [Cc]onversational-formal English-Spanish:\s*"([^"]+)"',
                False,
                "english_formal",
                style_preferences.english_word_by_word
            )
            if formal_data:
                result['translations'].append(formal_data['translation'])
                result['style_data'].append(formal_data)

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
        FIXED: Better handling of word pair extraction to capture ALL words with their translations.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Extract translation text
        text_match = re.search(text_pattern, text_section, re.DOTALL | re.IGNORECASE)
        
        if not text_match:
            return None
            
        translation_text = text_match.group(1).strip()
        
        # Extract word pairs if word-by-word is enabled
        word_pairs = []
        if word_by_word_enabled:
            pairs_match = re.search(pairs_pattern, text_section, re.IGNORECASE)
            if pairs_match:
                pairs_text = pairs_match.group(1)
                
                # Enhanced regex pattern to capture ALL word-translation pairs
                # This pattern is more flexible and captures various formats
                pair_matches = re.findall(
                    r'([^()]+?)\s*\(([^)]+?)\)',
                    pairs_text
                )
                
                for source, target in pair_matches:
                    # Clean up the extracted pairs
                    source = source.strip().rstrip('.,!?;:')  # Remove trailing punctuation
                    target = target.strip()
                    
                    # Skip empty pairs
                    if not source or not target:
                        continue
                    
                    # Skip pairs that are too long (likely parsing errors)
                    if len(source.split()) > 8:  # Reasonable limit for phrases
                        continue
                        
                    word_pairs.append((source, target))
                    logger.debug(f"   Extracted pair: '{source}' -> '{target}'")
                
                # Fallback: If no pairs found with the main pattern, try alternative patterns
                if not word_pairs:
                    # Try pattern without quotes
                    alt_pairs_text = pairs_text.replace('"', '')
                    alt_matches = re.findall(
                        r'(\w+(?:\s+\w+)*)\s*\(([^)]+?)\)',
                        alt_pairs_text
                    )
                    for source, target in alt_matches:
                        source = source.strip()
                        target = target.strip()
                        if source and target:
                            word_pairs.append((source, target))
        
        logger.info(f"   {style_name}: Found {len(word_pairs)} word pairs")
        
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