# translation_service.py - Enhanced for MULTIPLE translation styles per language

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

    def _create_enhanced_multiple_styles_prompt(self, input_text: str, mother_tongue: str, style_preferences) -> str:
        """Create a comprehensive prompt that requests ALL selected translation styles."""
        
        print(f"🎯 Creating MULTIPLE STYLES prompt for: {mother_tongue.upper()}")
        
        # Collect selected German styles
        german_styles = []
        if getattr(style_preferences, 'german_native', False):
            german_styles.append('Native')
        if getattr(style_preferences, 'german_colloquial', False):
            german_styles.append('Colloquial')
        if getattr(style_preferences, 'german_informal', False):
            german_styles.append('Informal')
        if getattr(style_preferences, 'german_formal', False):
            german_styles.append('Formal')
        
        # Collect selected English styles
        english_styles = []
        if getattr(style_preferences, 'english_native', False):
            english_styles.append('Native')
        if getattr(style_preferences, 'english_colloquial', False):
            english_styles.append('Colloquial')
        if getattr(style_preferences, 'english_informal', False):
            english_styles.append('Informal')
        if getattr(style_preferences, 'english_formal', False):
            english_styles.append('Formal')

        print(f"🇩🇪 German styles selected: {german_styles}")
        print(f"🇺🇸 English styles selected: {english_styles}")

        # Start building the prompt
        prompt = f"""Translate the {mother_tongue} text: "{input_text}"

I need MULTIPLE translation styles. Please provide translations in this EXACT format:

"""

        # Add German section if any German styles are selected
        if german_styles:
            prompt += "GERMAN TRANSLATIONS:\n"
            for style in german_styles:
                prompt += f"German {style}: [Provide {style.lower()} German translation here]\n"
            
            # Add German word-by-word if requested
            if getattr(style_preferences, 'german_word_by_word', False):
                prompt += "\nGERMAN WORD-BY-WORD:\n"
                prompt += "Format each word as: [German word] ([Spanish equivalent])\n"
                prompt += "Example: [Ich] ([Yo]) [gehe] ([voy]) [nach] ([a]) [Hause] ([casa])\n"
            
            prompt += "\n"

        # Add English section if any English styles are selected
        if english_styles:
            prompt += "ENGLISH TRANSLATIONS:\n"
            for style in english_styles:
                prompt += f"English {style}: [Provide {style.lower()} English translation here]\n"
            
            # Add English word-by-word if requested
            if getattr(style_preferences, 'english_word_by_word', False):
                prompt += "\nENGLISH WORD-BY-WORD:\n"
                prompt += "Format each word as: [English word] ([Spanish equivalent])\n"
                prompt += "Example: [I] ([Yo]) [go] ([voy]) [home] ([casa])\n"
            
            prompt += "\n"

        # Add automatic Spanish translation for non-Spanish mother tongues
        if mother_tongue.lower() != 'spanish':
            prompt += "SPANISH TRANSLATIONS:\n"
            prompt += "Spanish Colloquial: [Spanish translation here]\n\n"

        prompt += """IMPORTANT RULES:
1. Provide ALL requested translation styles separately
2. Use EXACT format shown above with style names
3. For phrasal verbs (like "wake up"), treat as ONE unit: [wake up] ([despertar])
4. For German separable verbs (like "stehe auf"), treat as ONE unit: [stehe auf] ([me levanto])
5. Each style should be contextually appropriate (Native=natural, Colloquial=casual, Informal=friendly, Formal=respectful)
6. Keep word-by-word on ONE line per language
7. Use contextually correct Spanish translations for word-by-word"""

        print(f"📝 Generated MULTIPLE STYLES prompt ({len(prompt)} characters)")
        return prompt

    def _should_generate_audio(self, translations_data: Dict, style_preferences) -> bool:
        """Generate audio if user has selected any translation styles"""
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
        
        if word_by_word_requested:
            print(f"   🎯 Audio type: Complete sentences + Word-by-word breakdown")
        else:
            print(f"   🎯 Audio type: Complete sentences only")
        
        return should_generate

    async def _generate_audio_with_resilience(self, translations_data: Dict, detected_mother_tongue: str, style_preferences) -> Optional[str]:
        """Generate audio with enhanced error handling for multiple styles"""
        try:
            print("🎵 Attempting MULTIPLE STYLES audio generation...")
            
            audio_task = asyncio.create_task(
                self.tts_service.text_to_speech_multiple_styles_v3(
                    translations_data=translations_data,
                    source_lang=detected_mother_tongue,
                    target_lang="es",
                    style_preferences=style_preferences,
                )
            )
            
            try:
                audio_filename = await asyncio.wait_for(audio_task, timeout=self.audio_timeout_seconds)
                
                if audio_filename:
                    print(f"✅ MULTIPLE STYLES audio generation successful: {audio_filename}")
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
            print(f"🌐 PROCESSING MULTIPLE STYLES TRANSLATION")
            print(f"{'='*80}")
            print(f"📝 Input text: '{text}'")
            print(f"🌍 Detected mother tongue: {detected_mother_tongue}")

            # Create MULTIPLE STYLES prompt 
            enhanced_prompt = self._create_enhanced_multiple_styles_prompt(
                text, detected_mother_tongue, style_preferences
            )
            
            print(f"📤 Sending MULTIPLE STYLES prompt to Gemini AI...")

            try:
                # Use direct model call for more reliable parsing
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

            # Extract ALL translations with enhanced parsing
            translations_data = self._extract_multiple_styles_translations(generated_text, style_preferences)

            audio_filename = None

            # Check if audio should be generated
            should_generate_audio = self._should_generate_audio(translations_data, style_preferences)
            
            # Generate synchronized audio for ALL selected styles
            if should_generate_audio:
                print("🎵 Starting MULTIPLE STYLES audio generation...")
                audio_filename = await self._generate_audio_with_resilience(
                    translations_data, detected_mother_tongue, style_preferences
                )
                
                if audio_filename:
                    print(f"✅ MULTIPLE STYLES audio completed: {audio_filename}")
                else:
                    print("ℹ️ Audio generation failed/skipped - continuing without audio")
            else:
                print("🔇 No audio generated - no translation styles enabled")

            # Create perfect UI-Audio synchronized data for ALL styles
            ui_word_by_word = self._create_perfect_ui_sync_data_multiple_styles(translations_data, style_preferences)

            # Create final translation text with ALL styles
            final_translation_text = self._create_formatted_multiple_styles_text(translations_data)

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

    def _extract_multiple_styles_translations(self, generated_text: str, style_preferences) -> Dict:
        """Enhanced extraction to handle MULTIPLE translation styles per language"""
        result = {
            'translations': [],
            'style_data': []
        }

        print("🔍 EXTRACTING MULTIPLE STYLES TRANSLATIONS")
        print("="*60)
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
                
                # Extract German translations - ALL STYLES
                elif current_language == 'german':
                    if 'German Native:' in line and style_preferences.german_native:
                        translation = self._extract_translation_from_line(line, 'German Native:')
                        if translation:
                            result['translations'].append(translation)
                            result['style_data'].append({
                                'translation': translation,
                                'word_pairs': [],
                                'is_german': True,
                                'is_spanish': False,
                                'style_name': 'german_native',
                                'display_name': 'German Native'
                            })
                            print(f"✅ German Native: {translation[:50]}...")
                    
                    elif 'German Colloquial:' in line and style_preferences.german_colloquial:
                        translation = self._extract_translation_from_line(line, 'German Colloquial:')
                        if translation:
                            result['translations'].append(translation)
                            result['style_data'].append({
                                'translation': translation,
                                'word_pairs': [],
                                'is_german': True,
                                'is_spanish': False,
                                'style_name': 'german_colloquial',
                                'display_name': 'German Colloquial'
                            })
                            print(f"✅ German Colloquial: {translation[:50]}...")
                    
                    elif 'German Informal:' in line and style_preferences.german_informal:
                        translation = self._extract_translation_from_line(line, 'German Informal:')
                        if translation:
                            result['translations'].append(translation)
                            result['style_data'].append({
                                'translation': translation,
                                'word_pairs': [],
                                'is_german': True,
                                'is_spanish': False,
                                'style_name': 'german_informal',
                                'display_name': 'German Informal'
                            })
                            print(f"✅ German Informal: {translation[:50]}...")
                    
                    elif 'German Formal:' in line and style_preferences.german_formal:
                        translation = self._extract_translation_from_line(line, 'German Formal:')
                        if translation:
                            result['translations'].append(translation)
                            result['style_data'].append({
                                'translation': translation,
                                'word_pairs': [],
                                'is_german': True,
                                'is_spanish': False,
                                'style_name': 'german_formal',
                                'display_name': 'German Formal'
                            })
                            print(f"✅ German Formal: {translation[:50]}...")
                    
                    elif 'GERMAN WORD-BY-WORD:' in line.upper():
                        print(f"📍 Found German word-by-word section")
                    
                    elif '[' in line and ']' in line and '(' in line and ')' in line and current_language == 'german':
                        word_by_word_text['german'] = line
                        print(f"📝 German word-by-word: {line[:100]}...")
                
                # Extract English translations - ALL STYLES
                elif current_language == 'english':
                    if 'English Native:' in line and style_preferences.english_native:
                        translation = self._extract_translation_from_line(line, 'English Native:')
                        if translation:
                            result['translations'].append(translation)
                            result['style_data'].append({
                                'translation': translation,
                                'word_pairs': [],
                                'is_german': False,
                                'is_spanish': False,
                                'style_name': 'english_native',
                                'display_name': 'English Native'
                            })
                            print(f"✅ English Native: {translation[:50]}...")
                    
                    elif 'English Colloquial:' in line and style_preferences.english_colloquial:
                        translation = self._extract_translation_from_line(line, 'English Colloquial:')
                        if translation:
                            result['translations'].append(translation)
                            result['style_data'].append({
                                'translation': translation,
                                'word_pairs': [],
                                'is_german': False,
                                'is_spanish': False,
                                'style_name': 'english_colloquial',
                                'display_name': 'English Colloquial'
                            })
                            print(f"✅ English Colloquial: {translation[:50]}...")
                    
                    elif 'English Informal:' in line and style_preferences.english_informal:
                        translation = self._extract_translation_from_line(line, 'English Informal:')
                        if translation:
                            result['translations'].append(translation)
                            result['style_data'].append({
                                'translation': translation,
                                'word_pairs': [],
                                'is_german': False,
                                'is_spanish': False,
                                'style_name': 'english_informal',
                                'display_name': 'English Informal'
                            })
                            print(f"✅ English Informal: {translation[:50]}...")
                    
                    elif 'English Formal:' in line and style_preferences.english_formal:
                        translation = self._extract_translation_from_line(line, 'English Formal:')
                        if translation:
                            result['translations'].append(translation)
                            result['style_data'].append({
                                'translation': translation,
                                'word_pairs': [],
                                'is_german': False,
                                'is_spanish': False,
                                'style_name': 'english_formal',
                                'display_name': 'English Formal'
                            })
                            print(f"✅ English Formal: {translation[:50]}...")
                    
                    elif 'ENGLISH WORD-BY-WORD:' in line.upper():
                        print(f"📍 Found English word-by-word section")
                    
                    elif '[' in line and ']' in line and '(' in line and ')' in line and current_language == 'english':
                        word_by_word_text['english'] = line
                        print(f"📝 English word-by-word: {line[:100]}...")
                
                # Extract Spanish translations
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
                                'style_name': 'spanish_colloquial',
                                'display_name': 'Spanish Colloquial'
                            })
                            print(f"✅ Spanish Colloquial: {translation[:50]}...")

            # Process word-by-word data for ALL German styles if requested
            if 'german' in word_by_word_text and style_preferences.german_word_by_word:
                german_pairs = self._parse_word_by_word_line(word_by_word_text['german'])
                if german_pairs:
                    print(f"✅ Parsed {len(german_pairs)} German word pairs for ALL German styles")
                    # Add word pairs to ALL German style entries
                    for style_entry in result['style_data']:
                        if style_entry['is_german']:
                            style_entry['word_pairs'] = german_pairs

            # Process word-by-word data for ALL English styles if requested
            if 'english' in word_by_word_text and style_preferences.english_word_by_word:
                english_pairs = self._parse_word_by_word_line(word_by_word_text['english'])
                if english_pairs:
                    print(f"✅ Parsed {len(english_pairs)} English word pairs for ALL English styles")
                    # Add word pairs to ALL English style entries
                    for style_entry in result['style_data']:
                        if not style_entry['is_german'] and not style_entry['is_spanish']:
                            style_entry['word_pairs'] = english_pairs

            print(f"✅ Extracted {len(result['translations'])} translations across multiple styles")
            print(f"✅ Extracted {len(result['style_data'])} style entries")
            
        except Exception as e:
            print(f"❌ Error in extraction: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Fallback: create minimal result
            if not result['translations']:
                result['translations'] = [generated_text[:500]]
                result['style_data'] = [{
                    'translation': generated_text[:500],
                    'word_pairs': [],
                    'is_german': False,
                    'is_spanish': False,
                    'style_name': 'fallback',
                    'display_name': 'Fallback Translation'
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

    def _create_perfect_ui_sync_data_multiple_styles(self, translations_data: Dict, style_preferences) -> Dict[str, Dict[str, str]]:
        """Create UI data for MULTIPLE styles with perfect synchronization"""
        ui_data = {}
        
        print("📱 Creating PERFECT UI-Audio synchronization for MULTIPLE STYLES...")
        print("="*70)
        
        for style_info in translations_data.get('style_data', []):
            style_name = style_info['style_name']
            display_name = style_info.get('display_name', style_name)
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
                print(f"🔄 PERFECT SYNC for {display_name}: {len(word_pairs)} pairs")
                
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
                        "display_style": display_name,
                        "order": str(i),
                        "is_phrasal_verb": str(" " in source_clean),
                        "display_format": display_format  # EXACT audio format
                    }
                    
                    print(f"   {i+1:2d}. {display_name}: {display_format}")
                    if " " in source_clean:
                        verb_type = "German Separable Verb" if is_german else "English Phrasal Verb"
                        print(f"       🔗 {verb_type}: Single unit")
        
        print(f"✅ Created PERFECT UI sync data for {len(ui_data)} word pairs across multiple styles")
        print("="*70)
        return ui_data

    def _create_formatted_multiple_styles_text(self, translations_data: Dict) -> str:
        """Create nicely formatted translation text showing ALL translation styles"""
        formatted_parts = []
        
        formatted_parts.append("=" * 60)
        formatted_parts.append("MULTIPLE STYLES TRANSLATION RESULTS:")
        formatted_parts.append("=" * 60)
        
        # Group by language and then by style
        german_styles = []
        english_styles = []
        spanish_styles = []
        
        for style_info in translations_data.get('style_data', []):
            translation = style_info['translation']
            display_name = style_info.get('display_name', style_info['style_name'])
            is_german = style_info.get('is_german', False)
            is_spanish = style_info.get('is_spanish', False)
            
            if is_german:
                german_styles.append(f"• {display_name}: {translation}")
            elif is_spanish:
                spanish_styles.append(f"• {display_name}: {translation}")
            else:
                english_styles.append(f"• {display_name}: {translation}")
        
        # Add German section with ALL styles
        if german_styles:
            formatted_parts.append("\n🇩🇪 GERMAN TRANSLATIONS:")
            formatted_parts.append("-" * 30)
            formatted_parts.extend(german_styles)
        
        # Add English section with ALL styles
        if english_styles:
            formatted_parts.append("\n🇺🇸 ENGLISH TRANSLATIONS:")
            formatted_parts.append("-" * 30)
            formatted_parts.extend(english_styles)
        
        # Add Spanish section with ALL styles
        if spanish_styles:
            formatted_parts.append("\n🇪🇸 SPANISH TRANSLATIONS:")
            formatted_parts.append("-" * 30)
            formatted_parts.extend(spanish_styles)
        
        formatted_parts.append("\n" + "=" * 60)
        
        return "\n".join(formatted_parts)

    # Keep all existing methods unchanged...
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
            "structure": "Enhanced grammar explanation with context for multiple styles",
            "tense": "Tense usage adapted to mother tongue with context for multiple styles",
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