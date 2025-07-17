
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
from typing import Optional


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
            model_name="gemini-2.0-flash-exp", generation_config=self.generation_config
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
        """Create a dynamic prompt based on user's style preferences"""
        prompt_parts = ["Text\n(Could be any phrase or word)\n<example to follow>\n"]
        
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
"Ich (Yo) muss (debo) diese Informationen (esta información) nachschlagen (buscar/consultar)." """)
            if "colloquial" in german_styles:
                prompt_parts.append("""* Conversational-colloquial:
"Ich muss das mal nachschauen" (colloquial with modal particle)
* word by word Conversational-colloquial German-Spanish:
"Ich (Yo) muss (debo) das (eso) mal (una vez) nachschauen (revisar)." """)
            if "informal" in german_styles:
                prompt_parts.append("""* Conversational-informal:
"Ich schau das mal nach" (informal, relaxed)
* word by word Conversational-informal German-Spanish:
"Ich (Yo) schau nach (busco/reviso) das (eso) mal (una vez)." """)
            if "formal" in german_styles:
                prompt_parts.append("""* Conversational-formal:
"Ich möchte diese Angaben überprüfen" (formal, polite)
* word by word Conversational-formal German-Spanish:
"Ich (Yo) möchte (me gustaría) diese Angaben (estos datos) überprüfen (verificar)." """)

        # Generate English section with enhanced examples
        if english_styles:
            prompt_parts.append("\nEnglish Translation:")
            if "native" in english_styles:
                prompt_parts.append("""* Conversational-native:
"I need to look up this information" (proper phrasal verb usage)
* word by word Conversational-native English-Spanish:
"I (Yo) need to (necesito) look up (buscar/consultar) this information (esta información)." """)
            if "colloquial" in english_styles:
                prompt_parts.append("""* Conversational-colloquial:
"I gotta check this out" (colloquial with reduced forms)
* word by word Conversational-colloquial English-Spanish:
"I (Yo) gotta (tengo que) check out (revisar) this (esto)." """)
            if "informal" in english_styles:
                prompt_parts.append("""* Conversational-informal:
"I need to check this info" (informal, abbreviated)
* word by word Conversational-informal English-Spanish:
"I (Yo) need to (necesito) check (revisar) this info (esta información)." """)
            if "formal" in english_styles:
                prompt_parts.append("""* Conversational-formal:
"I would like to verify this information" (formal, complete)
* word by word Conversational-formal English-Spanish:
"I (Yo) would like to (me gustaría) verify (verificar) this information (esta información)." """)

        prompt_parts.append("\n</example to follow>")
        return "\n".join(prompt_parts)

    def _normalize_text(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text)
        ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
        return ascii_text

    def _restore_accents(self, text: str) -> str:
        accent_map = {
            "a": "á",
            "e": "é",
            "i": "í",
            "o": "ó",
            "u": "ú",
            "n": "ñ",
            "A": "Á",
            "E": "É",
            "I": "Í",
            "O": "Ó",
            "U": "Ú",
            "N": "Ñ",
        }

        patterns = {
            r"([aeiou])´": lambda m: accent_map[m.group(1)],
            r"([AEIOU])´": lambda m: accent_map[m.group(1)],
            r"n~": "ñ",
            r"N~": "Ñ",
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

            translations, word_pairs = self._extract_text_and_pairs(generated_text, style_preferences)

            audio_filename = None

            # Always generate audio if we have translations, regardless of word_pairs
            if translations:
                # Use the enhanced TTS service which handles word-by-word preferences
                audio_filename = await self.tts_service.text_to_speech_word_pairs(
                    word_pairs=word_pairs,  # Can be empty if word-by-word is disabled
                    source_lang=source_lang,
                    target_lang=target_lang,
                    complete_text="\n".join(translations),
                    style_preferences=style_preferences,  # Pass style preferences to TTS
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
                    "main": translations[0] if translations else generated_text
                },
                word_by_word=self._generate_word_by_word(text, generated_text),
                grammar_explanations=self._generate_grammar_explanations(
                    generated_text
                ),
            )

        except Exception as e:
            print(f"Error in process_prompt: {str(e)}")
            raise Exception(f"Translation processing failed: {str(e)}")

    def _extract_text_and_pairs(
        self, generated_text: str, style_preferences
    ) -> tuple[list[str], list[tuple[str, str, bool]]]:
        """
        Extract texts and word pairs based on user's style preferences.
        Returns: tuple of ([texts], [(source_word, target_word, is_german)])
        """
        translations = []
        word_pairs = []

        # Define all possible patterns
        all_patterns = [
            # German patterns
            {
                "text_pattern": r'German Translation:.*?\* Conversational-native:\s*"([^"]+)"',
                "pairs_pattern": r'\* word by word Conversational-native German-Spanish:\s*"([^"]+)"',
                "is_german": True,
                "style": "native",
                "enabled": style_preferences.german_native if style_preferences else False,
            },
            {
                "text_pattern": r'\* Conversational-colloquial:\s*"([^"]+)"',
                "pairs_pattern": r'\* word by word Conversational-colloquial German-Spanish:\s*"([^"]+)"',
                "is_german": True,
                "style": "colloquial",
                "enabled": style_preferences.german_colloquial if style_preferences else False,
            },
            {
                "text_pattern": r'\* Conversational-informal:\s*"([^"]+)"',
                "pairs_pattern": r'\* word by word Conversational-informal German-Spanish:\s*"([^"]+)"',
                "is_german": True,
                "style": "informal",
                "enabled": style_preferences.german_informal if style_preferences else False,
            },
            {
                "text_pattern": r'\* [Cc]onversational-formal:\s*"([^"]+)"',
                "pairs_pattern": r'\* word by word [Cc]onversational-formal German-Spanish:\s*"([^"]+)"',
                "is_german": True,
                "style": "formal",
                "enabled": style_preferences.german_formal if style_preferences else False,
            },
            # English patterns
            {
                "text_pattern": r'English Translation:.*?\* Conversational-native:\s*"([^"]+)"',
                "pairs_pattern": r'\* word by word Conversational-native English-Spanish:\s*"([^"]+)"',
                "is_german": False,
                "style": "native",
                "enabled": style_preferences.english_native if style_preferences else False,
            },
            {
                "text_pattern": r'English Translation:.*?\* Conversational-colloquial:\s*"([^"]+)"',
                "pairs_pattern": r'\* word by word Conversational-colloquial English-Spanish:\s*"([^"]+)"',
                "is_german": False,
                "style": "colloquial",
                "enabled": style_preferences.english_colloquial if style_preferences else False,
            },
            {
                "text_pattern": r'English Translation:.*?\* Conversational-informal:\s*"([^"]+)"',
                "pairs_pattern": r'\* word by word Conversational-informal English-Spanish:\s*"([^"]+)"',
                "is_german": False,
                "style": "informal",
                "enabled": style_preferences.english_informal if style_preferences else False,
            },
            {
                "text_pattern": r'English Translation:.*?\* [Cc]onversational-formal:\s*"([^"]+)"',
                "pairs_pattern": r'\* word by word [Cc]onversational-formal English-Spanish:\s*"([^"]+)"',
                "is_german": False,
                "style": "formal",
                "enabled": style_preferences.english_formal if style_preferences else False,
            },
        ]

        # Process patterns in two passes:
        # Pass 1: Extract all translation texts for enabled styles
        # Pass 2: Extract word pairs only if word-by-word is enabled
        
        for pattern_set in all_patterns:
            if not pattern_set["enabled"]:
                continue

            # ALWAYS extract translation text if the style is enabled
            text_match = re.search(
                pattern_set["text_pattern"], generated_text, re.DOTALL | re.IGNORECASE
            )
            if text_match:
                translations.append(text_match.group(1).strip())

        # Second pass: Extract word pairs only if word-by-word is enabled for the language
        for pattern_set in all_patterns:
            if not pattern_set["enabled"]:
                continue

            # Only extract word pairs if word-by-word is enabled for this language
            should_extract_pairs = False
            if pattern_set["is_german"] and getattr(style_preferences, 'german_word_by_word', True):
                should_extract_pairs = True
            elif not pattern_set["is_german"] and getattr(style_preferences, 'english_word_by_word', False):
                should_extract_pairs = True

            if should_extract_pairs:
                pairs_match = re.search(
                    pattern_set["pairs_pattern"], generated_text, re.IGNORECASE
                )
                if pairs_match:
                    pairs_text = pairs_match.group(1)
                    pair_matches = re.findall(r"(\S+)\s*\(([^)]+)\)", pairs_text)
                    for source, target in pair_matches:
                        source = source.strip()
                        target = target.strip()
                        if source and target:
                            word_pairs.append((source, target, pattern_set["is_german"]))

        # Remove duplicates while preserving order
        seen_pairs = set()
        unique_pairs = []
        for pair in word_pairs:
            pair_tuple = (pair[0], pair[1], pair[2])
            if pair_tuple not in seen_pairs:
                seen_pairs.add(pair_tuple)
                unique_pairs.append(pair)

        print(f"🎵 Audio generation summary:")
        print(f"   Translations found: {len(translations)}")
        print(f"   Word pairs found: {len(unique_pairs)}")
        print(f"   German word-by-word enabled: {getattr(style_preferences, 'german_word_by_word', 'Not set')}")
        print(f"   English word-by-word enabled: {getattr(style_preferences, 'english_word_by_word', 'Not set')}")

        return translations, unique_pairs

    def _extract_native_translation(self, text: str) -> Optional[str]:
        """Extract the native translation from the generated text."""
        native_pattern = r'\* Conversational-native:\s*"([^"]+)"'
        match = re.search(native_pattern, text)
        if match:
            return match.group(1)
        return None

    def _extract_colloquial_translation(self, text: str) -> Optional[str]:
        """Extract the colloquial translation from the generated text."""
        colloquial_pattern = r'\* Conversational-colloquial:\s*"([^"]+)"'
        match = re.search(colloquial_pattern, text)
        if match:
            return match.group(1)
        return None

    def _extract_informal_translation(self, text: str) -> Optional[str]:
        """Extract the informal translation from the generated text."""
        informal_pattern = r'\* Conversational-informal:\s*"([^"]+)"'
        match = re.search(informal_pattern, text)
        if match:
            return match.group(1)
        return None

    def _extract_formal_translation(self, text: str) -> Optional[str]:
        """Extract the formal translation from the generated text."""
        formal_pattern = r'\* [Cc]onversational-formal:\s*"([^"]+)"'
        match = re.search(formal_pattern, text)
        if match:
            return match.group(1)
        return None

    def _get_temp_directory(self) -> str:
        """Get the appropriate temporary directory based on the operating system."""
        if os.name == "nt":
            temp_dir = os.environ.get("TEMP") or os.environ.get("TMP")
        else:
            temp_dir = "/tmp"

        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

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





