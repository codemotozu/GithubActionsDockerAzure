# translation_service.py - Updated with dynamic mother tongue support

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
            model_name="gemini-2.0-flash", generation_config=self.generation_config
        )

        self.tts_service = EnhancedTTSService()

        # Language detection patterns for dynamic mother tongue detection
        self.language_patterns = {
            'spanish': {
                'keywords': ['yo', 'tú', 'él', 'ella', 'nosotros', 'vosotros', 'ellos', 'ellas', 'es', 'son', 'está', 'están', 'tiene', 'tienes', 'para', 'con', 'de', 'en', 'la', 'el', 'los', 'las', 'un', 'una', 'unos', 'unas'],
                'patterns': [r'\b(soy|eres|somos|sois|son)\b', r'\b(tengo|tienes|tiene|tenemos|tenéis|tienen)\b', r'\b(estoy|estás|está|estamos|estáis|están)\b']
            },
            'english': {
                'keywords': ['i', 'you', 'he', 'she', 'we', 'they', 'am', 'is', 'are', 'was', 'were', 'have', 'has', 'had', 'the', 'a', 'an', 'and', 'or', 'but', 'with', 'for', 'to'],
                'patterns': [r'\b(am|is|are|was|were)\b', r'\b(have|has|had)\b', r'\b(do|does|did)\b']
            },
            'german': {
                'keywords': ['ich', 'du', 'er', 'sie', 'wir', 'ihr', 'sie', 'bin', 'bist', 'ist', 'sind', 'war', 'waren', 'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einen', 'einem', 'einer', 'und', 'oder', 'aber', 'mit', 'für', 'zu'],
                'patterns': [r'\b(bin|bist|ist|sind|war|waren)\b', r'\b(habe|hast|hat|haben|hatte|hatten)\b', r'\b(mache|machst|macht|machen)\b']
            }
        }

    def _detect_input_language(self, text: str, mother_tongue: str = None) -> str:
        """
        Detect the language of input text. If mother_tongue is provided, use it as primary hint.
        """
        text_lower = text.lower()
        
        # If mother tongue is explicitly provided, prioritize it
        if mother_tongue:
            return mother_tongue
            
        # Score each language based on keyword matches
        scores = {'spanish': 0, 'english': 0, 'german': 0}
        
        for lang, data in self.language_patterns.items():
            # Count keyword matches
            for keyword in data['keywords']:
                if f' {keyword} ' in f' {text_lower} ' or text_lower.startswith(f'{keyword} ') or text_lower.endswith(f' {keyword}'):
                    scores[lang] += 1
            
            # Count pattern matches
            for pattern in data['patterns']:
                matches = re.findall(pattern, text_lower)
                scores[lang] += len(matches) * 2  # Patterns are weighted higher
        
        # Return the language with highest score, default to spanish if tied
        detected = max(scores, key=scores.get)
        print(f"🔍 Language detection scores: {scores} -> Detected: {detected}")
        return detected

    def _create_dynamic_mother_tongue_prompt(self, input_text: str, mother_tongue: str, style_preferences) -> str:
        """
        Create a dynamic prompt based on detected mother tongue and user preferences.
        Implements the exact logic from the requirements.
        """
        
        # Define the target languages based on mother tongue
        target_languages = []
        if mother_tongue == 'spanish':
            # Spanish input -> German and/or English
            if any([style_preferences.german_native, style_preferences.german_colloquial, 
                   style_preferences.german_informal, style_preferences.german_formal]):
                target_languages.append('german')
            if any([style_preferences.english_native, style_preferences.english_colloquial,
                   style_preferences.english_informal, style_preferences.english_formal]):
                target_languages.append('english')
        elif mother_tongue == 'english':
            # English input -> German and/or Spanish
            if any([style_preferences.german_native, style_preferences.german_colloquial,
                   style_preferences.german_informal, style_preferences.german_formal]):
                target_languages.append('german')
            # For English mother tongue, we translate to Spanish (not back to English)
            target_languages.append('spanish')
        elif mother_tongue == 'german':
            # German input -> English and/or Spanish
            if any([style_preferences.english_native, style_preferences.english_colloquial,
                   style_preferences.english_informal, style_preferences.english_formal]):
                target_languages.append('english')
            target_languages.append('spanish')

        print(f"🎯 Mother tongue: {mother_tongue} -> Target languages: {target_languages}")

        # Build the dynamic prompt
        prompt_parts = [
            f"""You are an expert multilingual translator. The user's mother tongue is {mother_tongue.upper()}.

CRITICAL TRANSLATION RULES:
- Input text is in {mother_tongue.upper()}
- Translate to the requested target languages
- For word-by-word breakdowns, EVERY word must have a Spanish equivalent
- Group phrasal verbs, separable verbs, and compound expressions as single units
- Maintain grammatical accuracy and natural flow

Text to translate: "{input_text}"

Required translations:"""
        ]

        # Add German translations if requested
        if 'german' in target_languages:
            prompt_parts.append("\nGerman Translation:")
            
            if style_preferences.german_native:
                prompt_parts.append('* Conversational-native:\n"[Natural German translation]"')
                if style_preferences.german_word_by_word:
                    prompt_parts.append('* word by word Conversational-native German-Spanish:\n"[German word/phrase] ([Spanish translation]) [next word/phrase] ([Spanish translation]) ..."')
                    
            if style_preferences.german_colloquial:
                prompt_parts.append('* Conversational-colloquial:\n"[Colloquial German translation]"')
                if style_preferences.german_word_by_word:
                    prompt_parts.append('* word by word Conversational-colloquial German-Spanish:\n"[German word/phrase] ([Spanish translation]) [next word/phrase] ([Spanish translation]) ..."')
                    
            if style_preferences.german_informal:
                prompt_parts.append('* Conversational-informal:\n"[Informal German translation]"')
                if style_preferences.german_word_by_word:
                    prompt_parts.append('* word by word Conversational-informal German-Spanish:\n"[German word/phrase] ([Spanish translation]) [next word/phrase] ([Spanish translation]) ..."')
                    
            if style_preferences.german_formal:
                prompt_parts.append('* Conversational-formal:\n"[Formal German translation]"')
                if style_preferences.german_word_by_word:
                    prompt_parts.append('* word by word Conversational-formal German-Spanish:\n"[German word/phrase] ([Spanish translation]) [next word/phrase] ([Spanish translation]) ..."')

        # Add English translations if requested
        if 'english' in target_languages:
            prompt_parts.append("\nEnglish Translation:")
            
            if style_preferences.english_native:
                prompt_parts.append('* Conversational-native:\n"[Natural English translation]"')
                if style_preferences.english_word_by_word:
                    prompt_parts.append('* word by word Conversational-native English-Spanish:\n"[English word/phrase] ([Spanish translation]) [next word/phrase] ([Spanish translation]) ..."')
                    
            if style_preferences.english_colloquial:
                prompt_parts.append('* Conversational-colloquial:\n"[Colloquial English translation]"')
                if style_preferences.english_word_by_word:
                    prompt_parts.append('* word by word Conversational-colloquial English-Spanish:\n"[English word/phrase] ([Spanish translation]) [next word/phrase] ([Spanish translation]) ..."')
                    
            if style_preferences.english_informal:
                prompt_parts.append('* Conversational-informal:\n"[Informal English translation]"')
                if style_preferences.english_word_by_word:
                    prompt_parts.append('* word by word Conversational-informal English-Spanish:\n"[English word/phrase] ([Spanish translation]) [next word/phrase] ([Spanish translation]) ..."')
                    
            if style_preferences.english_formal:
                prompt_parts.append('* Conversational-formal:\n"[Formal English translation]"')
                if style_preferences.english_word_by_word:
                    prompt_parts.append('* word by word Conversational-formal English-Spanish:\n"[English word/phrase] ([Spanish translation]) [next word/phrase] ([Spanish translation]) ..."')

        # Add Spanish translations if requested (for English/German mother tongue)
        if 'spanish' in target_languages:
            prompt_parts.append("\nSpanish Translation:")
            prompt_parts.append('* Conversational-colloquial:\n"[Natural Spanish translation]"')
            # Note: Spanish is always the reference language, so no word-by-word needed

        return "\n".join(prompt_parts)

    async def process_prompt(
        self, text: str, source_lang: str, target_lang: str, style_preferences=None, mother_tongue: str = None
    ) -> Translation:
        try:
            # Use default preferences if none provided
            if style_preferences is None:
                from ...infrastructure.api.routes import TranslationStylePreferences
                style_preferences = TranslationStylePreferences(
                    german_colloquial=True,
                    english_colloquial=True,
                    german_word_by_word=True,
                    english_word_by_word=False
                )

            # Detect the actual input language (can override source_lang)
            detected_mother_tongue = self._detect_input_language(text, mother_tongue)
            
            print(f"🎯 Processing translation:")
            print(f"   Input text: '{text}'")
            print(f"   Detected mother tongue: {detected_mother_tongue}")
            print(f"   German word-by-word: {getattr(style_preferences, 'german_word_by_word', False)}")
            print(f"   English word-by-word: {getattr(style_preferences, 'english_word_by_word', False)}")

            # Create dynamic prompt based on mother tongue
            dynamic_prompt = self._create_dynamic_mother_tongue_prompt(
                text, detected_mother_tongue, style_preferences
            )
            
            print(f"📝 Generated prompt preview: {dynamic_prompt[:200]}...")

            # Create a new chat session with the dynamic prompt
            chat_session = self.model.start_chat(
                history=[{
                    "role": "user",
                    "parts": [dynamic_prompt],
                }]
            )

            response = chat_session.send_message(text)
            generated_text = response.text

            print(f"🤖 Gemini response preview: {generated_text[:200]}...")

            # Extract translations and word pairs
            translations_data = self._extract_text_and_pairs_v2(generated_text, style_preferences)

            audio_filename = None

            # Check if word-by-word audio is requested (check preferences directly)
            word_by_word_requested = False
            if style_preferences:
                word_by_word_requested = (
                    style_preferences.german_word_by_word or 
                    style_preferences.english_word_by_word
                )
            
            print(f"🎵 Audio generation check:")
            print(f"   Translations available: {len(translations_data['translations']) > 0}")
            print(f"   German word-by-word requested: {getattr(style_preferences, 'german_word_by_word', False)}")
            print(f"   English word-by-word requested: {getattr(style_preferences, 'english_word_by_word', False)}")
            print(f"   Overall word-by-word requested: {word_by_word_requested}")
            
            # Generate audio if word-by-word is requested and we have translations
            if translations_data['translations'] and word_by_word_requested:
                print("🎵 Generating audio with word-by-word breakdown...")
                audio_filename = await self.tts_service.text_to_speech_word_pairs_v2(
                    translations_data=translations_data,
                    source_lang=detected_mother_tongue,
                    target_lang="es",  # Spanish is always the reference
                    style_preferences=style_preferences,
                )
            else:
                if not word_by_word_requested:
                    print("🔇 No audio generated - word-by-word not requested")
                else:
                    print("🔇 No audio generated - no translations available")

            if audio_filename:
                print(f"✅ Successfully generated audio: {audio_filename}")
            else:
                print("ℹ️ No audio generated")

            return Translation(
                original_text=text,
                translated_text=generated_text,
                source_language=detected_mother_tongue,
                target_language="multi",  # Multiple target languages
                audio_path=audio_filename if audio_filename else None,
                translations={
                    "main": translations_data['translations'][0] if translations_data['translations'] else generated_text
                },
                word_by_word=self._generate_word_by_word(text, generated_text),
                grammar_explanations=self._generate_grammar_explanations(generated_text),
            )

        except Exception as e:
            print(f"❌ Error in process_prompt: {str(e)}")
            raise Exception(f"Translation processing failed: {str(e)}")

    def _extract_text_and_pairs_v2(
        self, generated_text: str, style_preferences
    ) -> Dict:
        """
        Extract texts and word pairs with proper multi-language support.
        """
        result = {
            'translations': [],
            'style_data': []
        }

        # Detect what language sections we have
        has_german = "German Translation:" in generated_text
        has_english = "English Translation:" in generated_text
        has_spanish = "Spanish Translation:" in generated_text
        
        print(f"🔍 Detected sections: German={has_german}, English={has_english}, Spanish={has_spanish}")

        # Split into sections
        sections = {}
        if has_german:
            if has_english:
                parts = generated_text.split("English Translation:")
                sections['german'] = parts[0]
                sections['english'] = "English Translation:" + parts[1] if len(parts) > 1 else ""
            elif has_spanish:
                parts = generated_text.split("Spanish Translation:")
                sections['german'] = parts[0]
                sections['spanish'] = "Spanish Translation:" + parts[1] if len(parts) > 1 else ""
            else:
                sections['german'] = generated_text
                
        if has_english and 'english' not in sections:
            if has_spanish:
                parts = generated_text.split("Spanish Translation:")
                if "English Translation:" in generated_text:
                    english_start = generated_text.find("English Translation:")
                    spanish_start = generated_text.find("Spanish Translation:")
                    if english_start < spanish_start:
                        sections['english'] = generated_text[english_start:spanish_start]
                        sections['spanish'] = generated_text[spanish_start:]
                    else:
                        sections['spanish'] = generated_text[spanish_start:english_start]
                        sections['english'] = generated_text[english_start:]
            else:
                sections['english'] = generated_text

        if has_spanish and 'spanish' not in sections:
            sections['spanish'] = generated_text

        # Process German styles if present
        if 'german' in sections and any([
            style_preferences.german_native, style_preferences.german_colloquial,
            style_preferences.german_informal, style_preferences.german_formal
        ]):
            self._process_language_section(
                sections['german'], 'german', style_preferences, result
            )

        # Process English styles if present
        if 'english' in sections and any([
            style_preferences.english_native, style_preferences.english_colloquial,
            style_preferences.english_informal, style_preferences.english_formal
        ]):
            self._process_language_section(
                sections['english'], 'english', style_preferences, result
            )

        # Process Spanish section (always colloquial, no word-by-word)
        if 'spanish' in sections:
            spanish_match = re.search(r'\*\s*[Cc]onversational-colloquial:\s*"([^"]+)"', sections['spanish'])
            if spanish_match:
                result['translations'].append(spanish_match.group(1))
                result['style_data'].append({
                    'translation': spanish_match.group(1),
                    'word_pairs': [],  # Spanish doesn't need word-by-word
                    'is_german': False,
                    'style_name': 'spanish_colloquial'
                })

        print(f"🎵 Final extraction: {len(result['translations'])} translations, {len(result['style_data'])} style entries")
        
        return result

    def _process_language_section(self, section: str, language: str, style_preferences, result: Dict):
        """Process a specific language section (German or English)"""
        is_german = (language == 'german')
        
        styles_to_check = ['native', 'colloquial', 'informal', 'formal']
        
        for style in styles_to_check:
            # Check if this style is enabled
            enabled = getattr(style_preferences, f'{language}_{style}', False)
            word_by_word_enabled = getattr(style_preferences, f'{language}_word_by_word', False)
            
            if enabled:
                style_data = self._extract_single_style(
                    section,
                    rf'\*\s*[Cc]onversational-{style}:\s*"([^"]+)"',
                    rf'\*\s*word by word [Cc]onversational-{style} (?:{language.title()}-Spanish|{language.title()}):\s*"([^"]+)"',
                    is_german,
                    f'{language}_{style}',
                    word_by_word_enabled
                )
                
                if style_data:
                    result['translations'].append(style_data['translation'])
                    result['style_data'].append(style_data)

    def _extract_single_style(
        self, 
        text_section: str, 
        text_pattern: str, 
        pairs_pattern: str,
        is_german: bool,
        style_name: str,
        word_by_word_enabled: bool
    ) -> Optional[Dict]:
        """Extract translation and word pairs for a single style with improved parsing"""
        
        # Extract main translation
        text_match = re.search(text_pattern, text_section, re.IGNORECASE | re.DOTALL)
        if not text_match:
            print(f"   ⚠️ No translation found for {style_name}")
            return None
            
        translation_text = text_match.group(1).strip()
        print(f"   ✅ Found translation for {style_name}: '{translation_text[:50]}...'")
        
        # Extract word pairs if enabled
        word_pairs = []
        if word_by_word_enabled:
            print(f"   🔍 Looking for word pairs for {style_name}...")
            
            # Try multiple pattern variations for word pairs
            pairs_patterns = [
                pairs_pattern,
                pairs_pattern.replace('"([^"]+)"', r'"?([^"\n]+)"?'),  # Optional quotes
                pairs_pattern.replace('German-Spanish', '(?:German-Spanish|German|Alemán-Español)'),
                pairs_pattern.replace('English-Spanish', '(?:English-Spanish|English|Inglés-Español)'),
                # More flexible pattern
                rf'\*\s*word by word.*?{style_name.split("_")[1]}.*?:\s*"?([^"\n]+)"?',
            ]
            
            pairs_text = None
            for pattern in pairs_patterns:
                try:
                    pairs_match = re.search(pattern, text_section, re.IGNORECASE | re.DOTALL)
                    if pairs_match:
                        pairs_text = pairs_match.group(1)
                        print(f"   📝 Found pairs text: '{pairs_text[:100]}...'")
                        break
                except Exception as e:
                    print(f"   ⚠️ Pattern failed: {e}")
                    continue
            
            if pairs_text:
                # Enhanced regex patterns to capture word-translation pairs
                pair_patterns = [
                    r'([^()]+?)\s*\(([^)]+?)\)',  # Standard: word (translation)
                    r'(\S+(?:\s+\S+)?)\s*\(([^)]+?)\)',  # One or two words (translation)
                    r'"([^"]+)"\s*\(([^)]+?)\)',  # "word" (translation)
                    r'([^,()]+?)\s*\(([^)]+?)\)',  # Anything except comma/parens (translation)
                ]
                
                for pair_pattern in pair_patterns:
                    try:
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
                                print(f"      ✅ Extracted pair: '{source}' -> '{target}'")
                            
                            if word_pairs:
                                break  # We found pairs, stop trying other patterns
                    except Exception as e:
                        print(f"   ⚠️ Pair extraction failed: {e}")
                        continue
                
                # If still no pairs found, try a simpler approach
                if not word_pairs:
                    print(f"   🔄 Trying simple extraction for {style_name}...")
                    # Split by common separators and look for parentheses
                    segments = re.split(r'[,;]\s*', pairs_text)
                    for segment in segments:
                        match = re.search(r'(.+?)\s*\(([^)]+)\)', segment)
                        if match:
                            source = match.group(1).strip().strip('"\'')
                            target = match.group(2).strip().strip('"\'')
                            if source and target:
                                word_pairs.append((source, target))
                                print(f"      ✅ Simple extraction: '{source}' -> '{target}'")
                                
        print(f"   📊 {style_name}: Found translation + {len(word_pairs)} word pairs")
        
        return {
            'translation': translation_text,
            'word_pairs': word_pairs,
            'is_german': is_german,
            'style_name': style_name
        }

    # Keep existing methods unchanged
    def _generate_word_by_word(self, original: str, translated: str) -> dict[str, dict[str, str]]:
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
            "structure": "Dynamic grammar explanation based on detected patterns",
            "tense": "Tense usage adapted to mother tongue",
        }

    # Keep all other existing helper methods unchanged...
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