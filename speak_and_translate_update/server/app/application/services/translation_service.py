# translation_service.py - Fixed for PERFECT UI-Audio synchronization

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
import asyncio
import json


class TranslationService:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)

        self.spell = SpellChecker()

        self.generation_config = {
            "temperature": 0.3,  # Lower for more consistent translations
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 8192,
        }

        self.model = GenerativeModel(
            model_name="gemini-2.0-flash", generation_config=self.generation_config
        )

        self.tts_service = EnhancedTTSService()

        # Audio generation settings
        self.audio_retry_attempts = 2
        self.audio_timeout_seconds = 30

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
        """Detect the language of input text. If mother_tongue is provided, use it as primary hint."""
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

    def _create_enhanced_context_prompt(self, input_text: str, mother_tongue: str, style_preferences) -> str:
        """Create a SIMPLIFIED prompt that ensures consistent AI response format."""
        
        print(f"🎯 Creating SIMPLIFIED context prompt for: {mother_tongue.upper()}")
        
        target_languages = []
        
        # Determine target languages based on mother tongue and selections
        if mother_tongue.lower() == 'spanish':
            if any([style_preferences.german_native, style_preferences.german_colloquial, 
                   style_preferences.german_informal, style_preferences.german_formal]):
                target_languages.append('german')
            if any([style_preferences.english_native, style_preferences.english_colloquial,
                   style_preferences.english_informal, style_preferences.english_formal]):
                target_languages.append('english')
                
        elif mother_tongue.lower() == 'english':
            target_languages.append('spanish')
            if any([style_preferences.german_native, style_preferences.german_colloquial,
                   style_preferences.german_informal, style_preferences.german_formal]):
                target_languages.append('german')
                
        elif mother_tongue.lower() == 'german':
            target_languages.append('spanish')
            if any([style_preferences.english_native, style_preferences.english_colloquial,
                   style_preferences.english_informal, style_preferences.english_formal]):
                target_languages.append('english')

        print(f"🎯 Target languages: {target_languages}")

        # SIMPLIFIED prompt with consistent format
        prompt = f"""Translate the {mother_tongue} text: "{input_text}"

Please provide translations in this EXACT format:

"""

        # Add language sections with SIMPLE format
        if 'german' in target_languages:
            prompt += """GERMAN TRANSLATIONS:
German Native: [German translation here]
German Colloquial: [Colloquial German translation here]

GERMAN WORD-BY-WORD:
Format each word as: [German word] ([Spanish equivalent])
Example: [Ich] ([Yo]) [gehe] ([voy]) [nach] ([a]) [Hause] ([casa])

"""

        if 'english' in target_languages:
            prompt += """ENGLISH TRANSLATIONS:
English Native: [English translation here]
English Colloquial: [Colloquial English translation here]

ENGLISH WORD-BY-WORD:
Format each word as: [English word] ([Spanish equivalent])
Example: [I] ([Yo]) [go] ([voy]) [home] ([casa])

"""

        if 'spanish' in target_languages:
            prompt += """SPANISH TRANSLATIONS:
Spanish Colloquial: [Spanish translation here]

"""

        prompt += """IMPORTANT RULES:
1. Use EXACT format shown above
2. For phrasal verbs (like "wake up"), treat as ONE unit: [wake up] ([despertar])
3. For German separable verbs (like "stehe auf"), treat as ONE unit: [stehe auf] ([me levanto])
4. Keep word-by-word on ONE line per language
5. Use contextually correct Spanish translations"""

        print(f"📝 Generated SIMPLIFIED prompt ({len(prompt)} characters)")
        return prompt

    def _should_generate_audio(self, translations_data: Dict, style_preferences) -> bool:
        """Only generate audio if user has selected translation styles"""
        has_translations = len(translations_data.get('translations', [])) > 0
        
        has_enabled_styles = False
        if style_preferences:
            style_checks = [
                style_preferences.german_native, style_preferences.german_colloquial,
                style_preferences.german_informal, style_preferences.german_formal,
                style_preferences.english_native, style_preferences.english_colloquial,
                style_preferences.english_informal, style_preferences.english_formal
            ]
            has_enabled_styles = any(style_checks)
        
        word_by_word_requested = False
        if style_preferences:
            word_by_word_requested = (
                style_preferences.german_word_by_word or 
                style_preferences.english_word_by_word
            )
        
        should_generate = has_translations and has_enabled_styles
        
        print(f"🎵 Audio Generation Decision:")
        print(f"   Translations available: {has_translations}")
        print(f"   Translation styles enabled: {has_enabled_styles}")
        print(f"   Word-by-word audio requested: {word_by_word_requested}")
        print(f"   🎯 Will generate audio: {should_generate}")
        print(f"   🎯 Audio type: {'Word-by-word breakdown' if word_by_word_requested else 'Simple translation reading'}")
        
        return should_generate

    async def _generate_audio_with_resilience(self, translations_data: Dict, detected_mother_tongue: str, style_preferences) -> Optional[str]:
        """Generate audio with enhanced error handling"""
        try:
            print("🎵 Attempting SYNCHRONIZED audio generation...")
            
            audio_task = asyncio.create_task(
                self.tts_service.text_to_speech_word_pairs_v2(
                    translations_data=translations_data,
                    source_lang=detected_mother_tongue,
                    target_lang="es",
                    style_preferences=style_preferences,
                )
            )
            
            try:
                audio_filename = await asyncio.wait_for(audio_task, timeout=self.audio_timeout_seconds)
                
                if audio_filename:
                    print(f"✅ SYNCHRONIZED audio generation successful: {audio_filename}")
                    return audio_filename
                else:
                    print("⚠️ Audio generation returned None")
                    return None
                    
            except asyncio.TimeoutError:
                print(f"⏰ Audio generation timed out after {self.audio_timeout_seconds} seconds")
                audio_task.cancel()
                return None
                
        except Exception as e:
            print(f"❌ Audio generation failed: {str(e)}")
            return None

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
                    mother_tongue="spanish"
                )

            # Detect the actual input language
            detected_mother_tongue = self._detect_input_language(text, mother_tongue)
            
            print(f"\n{'='*80}")
            print(f"🌐 PROCESSING ENHANCED CONTEXTUAL TRANSLATION")
            print(f"{'='*80}")
            print(f"📝 Input text: '{text}'")
            print(f"🌍 Detected mother tongue: {detected_mother_tongue}")

            # Create SIMPLIFIED context prompt 
            enhanced_prompt = self._create_enhanced_context_prompt(
                text, detected_mother_tongue, style_preferences
            )
            
            print(f"📤 Sending SIMPLIFIED prompt to Gemini AI...")

            try:
                # Use direct model call instead of chat session for more reliable parsing
                response = self.model.generate_content(enhanced_prompt)
                generated_text = response.text

                print(f"📥 Gemini response received ({len(generated_text)} characters)")
                print(f"📄 Response preview: {generated_text[:200]}...")

            except Exception as e:
                print(f"❌ Gemini API error: {str(e)}")
                # Fallback response
                generated_text = f"Translation error for '{text}'. Please try again."
                translations_data = {'translations': [generated_text], 'style_data': []}
                
                return Translation(
                    original_text=text,
                    translated_text=generated_text,
                    source_language=detected_mother_tongue,
                    target_language="multi",
                    audio_path=None,
                    translations={"main": generated_text},
                    word_by_word=None,
                    grammar_explanations=None,
                )

            # Extract translations with FIXED parsing
            translations_data = self._extract_translations_fixed(generated_text, style_preferences)

            audio_filename = None

            # Check if audio should be generated
            should_generate_audio = self._should_generate_audio(translations_data, style_preferences)
            
            # Generate synchronized audio
            if should_generate_audio:
                print("🎵 Starting SYNCHRONIZED audio generation...")
                audio_filename = await self._generate_audio_with_resilience(
                    translations_data, detected_mother_tongue, style_preferences
                )
                
                if audio_filename:
                    print(f"✅ SYNCHRONIZED audio completed: {audio_filename}")
                else:
                    print("ℹ️ Audio generation failed/skipped - continuing without audio")
            else:
                print("🔇 No audio generated - no translation styles enabled")

            # Create perfect UI-Audio synchronized data
            ui_word_by_word = self._create_perfect_ui_sync_data(translations_data, style_preferences)

            # Create final translation text
            final_translation_text = self._create_formatted_translation_text(translations_data)

            return Translation(
                original_text=text,
                translated_text=final_translation_text,
                source_language=detected_mother_tongue,
                target_language="multi",
                audio_path=audio_filename if audio_filename else None,
                translations={
                    "main": translations_data['translations'][0] if translations_data['translations'] else final_translation_text
                },
                word_by_word=ui_word_by_word,
                grammar_explanations=self._generate_grammar_explanations(final_translation_text),
            )

        except Exception as e:
            print(f"❌ Error in process_prompt: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Translation processing failed: {str(e)}")

    def _extract_translations_fixed(self, generated_text: str, style_preferences) -> Dict:
        """FIXED extraction with robust parsing"""
        result = {
            'translations': [],
            'style_data': []
        }

        print("🔍 EXTRACTING TRANSLATIONS (FIXED)")
        print("="*50)
        print(f"📄 Generated text length: {len(generated_text)}")

        try:
            # Split into lines for easier parsing
            lines = generated_text.split('\n')
            
            current_language = None
            word_by_word_text = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detect language sections
                if 'GERMAN TRANSLATIONS:' in line.upper():
                    current_language = 'german'
                    print(f"📍 Found German section")
                elif 'ENGLISH TRANSLATIONS:' in line.upper():
                    current_language = 'english'
                    print(f"📍 Found English section")
                elif 'SPANISH TRANSLATIONS:' in line.upper():
                    current_language = 'spanish'
                    print(f"📍 Found Spanish section")
                
                # Extract translations
                elif current_language == 'german':
                    if 'German Native:' in line:
                        translation = self._extract_translation_from_line(line, 'German Native:')
                        if translation and style_preferences.german_native:
                            result['translations'].append(translation)
                            result['style_data'].append({
                                'translation': translation,
                                'word_pairs': [],
                                'is_german': True,
                                'is_spanish': False,
                                'style_name': 'german_native'
                            })
                            print(f"✅ German Native: {translation[:50]}...")
                    
                    elif 'German Colloquial:' in line:
                        translation = self._extract_translation_from_line(line, 'German Colloquial:')
                        if translation and style_preferences.german_colloquial:
                            result['translations'].append(translation)
                            result['style_data'].append({
                                'translation': translation,
                                'word_pairs': [],
                                'is_german': True,
                                'is_spanish': False,
                                'style_name': 'german_colloquial'
                            })
                            print(f"✅ German Colloquial: {translation[:50]}...")
                    
                    elif 'GERMAN WORD-BY-WORD:' in line.upper():
                        # Start collecting word-by-word for German
                        print(f"📍 Found German word-by-word section")
                    
                    elif '[' in line and ']' in line and '(' in line and ')' in line and current_language == 'german':
                        # This looks like word-by-word data
                        word_by_word_text['german'] = line
                        print(f"📝 German word-by-word: {line[:100]}...")
                
                elif current_language == 'english':
                    if 'English Native:' in line:
                        translation = self._extract_translation_from_line(line, 'English Native:')
                        if translation and style_preferences.english_native:
                            result['translations'].append(translation)
                            result['style_data'].append({
                                'translation': translation,
                                'word_pairs': [],
                                'is_german': False,
                                'is_spanish': False,
                                'style_name': 'english_native'
                            })
                            print(f"✅ English Native: {translation[:50]}...")
                    
                    elif 'English Colloquial:' in line:
                        translation = self._extract_translation_from_line(line, 'English Colloquial:')
                        if translation and style_preferences.english_colloquial:
                            result['translations'].append(translation)
                            result['style_data'].append({
                                'translation': translation,
                                'word_pairs': [],
                                'is_german': False,
                                'is_spanish': False,
                                'style_name': 'english_colloquial'
                            })
                            print(f"✅ English Colloquial: {translation[:50]}...")
                    
                    elif 'ENGLISH WORD-BY-WORD:' in line.upper():
                        print(f"📍 Found English word-by-word section")
                    
                    elif '[' in line and ']' in line and '(' in line and ')' in line and current_language == 'english':
                        word_by_word_text['english'] = line
                        print(f"📝 English word-by-word: {line[:100]}...")
                
                elif current_language == 'spanish':
                    if 'Spanish Colloquial:' in line:
                        translation = self._extract_translation_from_line(line, 'Spanish Colloquial:')
                        if translation:
                            result['translations'].append(translation)
                            result['style_data'].append({
                                'translation': translation,
                                'word_pairs': [],
                                'is_german': False,
                                'is_spanish': True,
                                'style_name': 'spanish_colloquial'
                            })
                            print(f"✅ Spanish Colloquial: {translation[:50]}...")

            # Now process word-by-word data if we found any
            self._process_word_by_word_data(result, word_by_word_text, style_preferences)

            print(f"✅ Extracted {len(result['translations'])} translations")
            print(f"✅ Extracted {len(result['style_data'])} style entries")
            
        except Exception as e:
            print(f"❌ Error in extraction: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Fallback: create minimal result
            if not result['translations']:
                result['translations'] = [generated_text[:500]]  # Use first part of response
                result['style_data'] = [{
                    'translation': generated_text[:500],
                    'word_pairs': [],
                    'is_german': False,
                    'is_spanish': False,
                    'style_name': 'fallback'
                }]

        return result

    def _extract_translation_from_line(self, line: str, prefix: str) -> Optional[str]:
        """Extract translation text from a line"""
        try:
            # Remove the prefix and clean up
            translation = line.replace(prefix, '').strip()
            
            # Remove common brackets and quotes
            translation = translation.strip('[]"\'')
            
            # Must have some content
            if len(translation) > 3:
                return translation
            
        except Exception as e:
            print(f"❌ Error extracting from line '{line}': {str(e)}")
        
        return None

    def _process_word_by_word_data(self, result: Dict, word_by_word_text: Dict, style_preferences):
        """Process word-by-word data and add to style entries"""
        
        # Process German word-by-word
        if 'german' in word_by_word_text and style_preferences.german_word_by_word:
            german_pairs = self._parse_word_by_word_line(word_by_word_text['german'])
            if german_pairs:
                print(f"✅ Parsed {len(german_pairs)} German word pairs")
                
                # Add to existing German style entries
                for style_entry in result['style_data']:
                    if style_entry['is_german']:
                        style_entry['word_pairs'] = german_pairs
                        break
                else:
                    # Create new entry if no German styles exist
                    result['style_data'].append({
                        'translation': 'German translation (word-by-word only)',
                        'word_pairs': german_pairs,
                        'is_german': True,
                        'is_spanish': False,
                        'style_name': 'german_word_by_word'
                    })

        # Process English word-by-word
        if 'english' in word_by_word_text and style_preferences.english_word_by_word:
            english_pairs = self._parse_word_by_word_line(word_by_word_text['english'])
            if english_pairs:
                print(f"✅ Parsed {len(english_pairs)} English word pairs")
                
                # Add to existing English style entries
                for style_entry in result['style_data']:
                    if not style_entry['is_german'] and not style_entry['is_spanish']:
                        style_entry['word_pairs'] = english_pairs
                        break
                else:
                    # Create new entry if no English styles exist
                    result['style_data'].append({
                        'translation': 'English translation (word-by-word only)',
                        'word_pairs': english_pairs,
                        'is_german': False,
                        'is_spanish': False,
                        'style_name': 'english_word_by_word'
                    })

    def _parse_word_by_word_line(self, line: str) -> List[Tuple[str, str]]:
        """Parse a word-by-word line into pairs"""
        pairs = []
        
        try:
            # Find all [word] ([translation]) patterns
            pattern = r'\[([^\]]+)\]\s*\(\s*\[([^\]]+)\]\s*\)'
            matches = re.findall(pattern, line)
            
            if not matches:
                # Try simpler pattern without inner brackets
                pattern = r'\[([^\]]+)\]\s*\(\s*([^)]+)\s*\)'
                matches = re.findall(pattern, line)
            
            for source, target in matches:
                source = source.strip()
                target = target.strip()
                if source and target:
                    pairs.append((source, target))
                    print(f"   📝 Pair: '{source}' → '{target}'")
            
        except Exception as e:
            print(f"❌ Error parsing word-by-word line: {str(e)}")
        
        return pairs

    def _create_perfect_ui_sync_data(self, translations_data: Dict, style_preferences) -> Dict[str, Dict[str, str]]:
        """Create UI data that PERFECTLY matches what will be spoken in audio"""
        ui_data = {}
        
        print("📱 Creating PERFECT UI-Audio synchronization data...")
        print("="*60)
        
        for style_info in translations_data.get('style_data', []):
            style_name = style_info['style_name']
            word_pairs = style_info.get('word_pairs', [])
            is_german = style_info.get('is_german', False)
            is_spanish = style_info.get('is_spanish', False)
            
            # Check if word-by-word is enabled for this language
            should_include = False
            if is_german and getattr(style_preferences, 'german_word_by_word', False):
                should_include = True
            elif not is_german and not is_spanish and getattr(style_preferences, 'english_word_by_word', False):
                should_include = True
            
            if should_include and word_pairs:
                print(f"🔄 PERFECT SYNC: {style_name} with {len(word_pairs)} pairs")
                
                for i, (source_word, spanish_equiv) in enumerate(word_pairs):
                    # Clean for consistency
                    source_clean = source_word.strip().strip('"\'[]')
                    spanish_clean = spanish_equiv.strip().strip('"\'[]')
                    
                    # CRITICAL: Create EXACT same format for UI and audio
                    display_format = f"[{source_clean}] ([{spanish_clean}])"
                    
                    key = f"{style_name}_{i}_{source_clean.replace(' ', '_')}"
                    
                    ui_data[key] = {
                        "source": source_clean,
                        "spanish": spanish_clean,
                        "language": "german" if is_german else "english",
                        "style": style_name,
                        "order": str(i),
                        "is_phrasal_verb": str(" " in source_clean),
                        "display_format": display_format  # EXACT audio format
                    }
                    
                    print(f"   {i+1:2d}. UI: {display_format}")
                    if " " in source_clean:
                        verb_type = "German Separable Verb" if is_german else "English Phrasal Verb"
                        print(f"       🔗 {verb_type}: Single unit")
        
        print(f"✅ Created PERFECT UI sync data for {len(ui_data)} word pairs")
        print("="*60)
        return ui_data

    def _create_formatted_translation_text(self, translations_data: Dict) -> str:
        """Create nicely formatted translation text for display"""
        formatted_parts = []
        
        formatted_parts.append("=" * 50)
        formatted_parts.append("TRANSLATION RESULTS:")
        formatted_parts.append("=" * 50)
        
        # Group by language
        german_translations = []
        english_translations = []
        spanish_translations = []
        
        for style_info in translations_data.get('style_data', []):
            translation = style_info['translation']
            style_name = style_info['style_name']
            is_german = style_info.get('is_german', False)
            is_spanish = style_info.get('is_spanish', False)
            
            if is_german:
                german_translations.append(f"* {style_name.replace('_', ' ').title()}: {translation}")
            elif is_spanish:
                spanish_translations.append(f"* {style_name.replace('_', ' ').title()}: {translation}")
            else:
                english_translations.append(f"* {style_name.replace('_', ' ').title()}: {translation}")
        
        # Add German section
        if german_translations:
            formatted_parts.append("\nGERMAN TRANSLATIONS:")
            formatted_parts.append("-" * 25)
            formatted_parts.extend(german_translations)
        
        # Add English section
        if english_translations:
            formatted_parts.append("\nENGLISH TRANSLATIONS:")
            formatted_parts.append("-" * 25)
            formatted_parts.extend(english_translations)
        
        # Add Spanish section
        if spanish_translations:
            formatted_parts.append("\nSPANISH TRANSLATIONS:")
            formatted_parts.append("-" * 25)
            formatted_parts.extend(spanish_translations)
        
        formatted_parts.append("\n" + "=" * 50)
        
        return "\n".join(formatted_parts)

    # Keep all other existing methods unchanged...
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
            "structure": "Enhanced grammar explanation with context",
            "tense": "Tense usage adapted to mother tongue with context",
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