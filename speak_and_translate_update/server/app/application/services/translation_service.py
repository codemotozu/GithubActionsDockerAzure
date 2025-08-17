# translation_service.py - Complete file with multi-style support

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

#     def _create_enhanced_context_prompt(self, input_text: str, mother_tongue: str, style_preferences) -> str:
#         """Create enhanced prompt for multiple simultaneous styles."""
        
#         print(f"🎯 Creating MULTI-STYLE context prompt for: {mother_tongue.upper()}")
        
#         target_languages = []
#         german_styles = []
#         english_styles = []
        
#         # Collect all selected German styles
#         if style_preferences.german_native:
#             german_styles.append('native')
#         if style_preferences.german_colloquial:
#             german_styles.append('colloquial')
#         if style_preferences.german_informal:
#             german_styles.append('informal')
#         if style_preferences.german_formal:
#             german_styles.append('formal')
        
#         # Collect all selected English styles
#         if style_preferences.english_native:
#             english_styles.append('native')
#         if style_preferences.english_colloquial:
#             english_styles.append('colloquial')
#         if style_preferences.english_informal:
#             english_styles.append('informal')
#         if style_preferences.english_formal:
#             english_styles.append('formal')
        
#         # Determine target languages based on mother tongue and selections
#         if mother_tongue.lower() == 'spanish':
#             if german_styles:
#                 target_languages.append('german')
#             if english_styles:
#                 target_languages.append('english')
#         elif mother_tongue.lower() == 'english':
#             target_languages.append('spanish')
#             if german_styles:
#                 target_languages.append('german')
#         elif mother_tongue.lower() == 'german':
#             target_languages.append('spanish')
#             if english_styles:
#                 target_languages.append('english')

#         print(f"🎯 Target languages: {target_languages}")
#         print(f"🇩🇪 German styles selected: {german_styles}")
#         print(f"🇺🇸 English styles selected: {english_styles}")

#         # Build comprehensive prompt for multiple styles
#         prompt = f"""Translate the {mother_tongue} text: "{input_text}"

# Please provide ALL requested translations in this EXACT format:

# """

#         # Add German translations for ALL selected styles
#         if 'german' in target_languages and german_styles:
#             prompt += "GERMAN TRANSLATIONS:\n"
#             for style in german_styles:
#                 prompt += f"German {style.capitalize()}: [Provide {style} German translation here]\n"
            
#             # Add word-by-word section if enabled
#             if style_preferences.german_word_by_word:
#                 prompt += "\nGERMAN WORD-BY-WORD:\n"
#                 for style in german_styles:
#                     prompt += f"{style.capitalize()} style: "
#                     prompt += "Format each word as [German word] ([Spanish equivalent]). "
#                     prompt += "Example: [Ich] ([Yo]) [gehe] ([voy]) [nach] ([a]) [Hause] ([casa])\n"
#             prompt += "\n"

#         # Add English translations for ALL selected styles
#         if 'english' in target_languages and english_styles:
#             prompt += "ENGLISH TRANSLATIONS:\n"
#             for style in english_styles:
#                 prompt += f"English {style.capitalize()}: [Provide {style} English translation here]\n"
            
#             # Add word-by-word section if enabled
#             if style_preferences.english_word_by_word:
#                 prompt += "\nENGLISH WORD-BY-WORD:\n"
#                 for style in english_styles:
#                     prompt += f"{style.capitalize()} style: "
#                     prompt += "Format each word as [English word] ([Spanish equivalent]). "
#                     prompt += "Example: [I] ([Yo]) [go] ([voy]) [home] ([casa])\n"
#             prompt += "\n"

#         # Add Spanish translations if needed
#         if 'spanish' in target_languages:
#             prompt += "SPANISH TRANSLATIONS:\nSpanish Colloquial: [Spanish translation here]\n\n"

#         prompt += """IMPORTANT RULES:
# 1. Provide translations for ALL selected styles
# 2. Each style should have a distinct translation appropriate to its formality level
# 3. For phrasal verbs (like "wake up"), treat as ONE unit: [wake up] ([despertar])
# 4. For German separable verbs (like "stehe auf"), treat as ONE unit: [stehe auf] ([me levanto])
# 5. Keep word-by-word translations on ONE line per style
# 6. Use contextually correct Spanish translations for each word/phrase
# 7. Native style: Most natural expression a native speaker would use
# 8. Colloquial style: Conversational, everyday language
# 9. Informal style: Relaxed, casual, friendly tone
# 10. Formal style: Professional, polite, structured language"""

#         print(f"📝 Generated MULTI-STYLE prompt ({len(prompt)} characters)")
#         return prompt

# Enhanced translation_service.py with NO manual dictionaries - rely fully on AI

    def _create_enhanced_context_prompt(self, input_text: str, mother_tongue: str, style_preferences) -> str:
        """Create enhanced prompt for multiple simultaneous styles with EXACT word-by-word alignment."""
        
        print(f"🎯 Creating MULTI-STYLE context prompt for: {mother_tongue.upper()}")
        
        target_languages = []
        german_styles = []
        english_styles = []
        
        # Collect all selected German styles
        if style_preferences.german_native:
            german_styles.append('native')
        if style_preferences.german_colloquial:
            german_styles.append('colloquial')
        if style_preferences.german_informal:
            german_styles.append('informal')
        if style_preferences.german_formal:
            german_styles.append('formal')
        
        # Collect all selected English styles
        if style_preferences.english_native:
            english_styles.append('native')
        if style_preferences.english_colloquial:
            english_styles.append('colloquial')
        if style_preferences.english_informal:
            english_styles.append('informal')
        if style_preferences.english_formal:
            english_styles.append('formal')
        
        # Determine target languages based on mother tongue and selections
        if mother_tongue.lower() == 'spanish':
            if german_styles:
                target_languages.append('german')
            if english_styles:
                target_languages.append('english')
        elif mother_tongue.lower() == 'english':
            target_languages.append('spanish')
            if german_styles:
                target_languages.append('german')
        elif mother_tongue.lower() == 'german':
            target_languages.append('spanish')
            if english_styles:
                target_languages.append('english')

        print(f"🎯 Target languages: {target_languages}")
        print(f"🇩🇪 German styles selected: {german_styles}")
        print(f"🇺🇸 English styles selected: {english_styles}")

        # Build comprehensive prompt for multiple styles - NO MANUAL DICTIONARIES
        prompt = f"""Translate the {mother_tongue} text: "{input_text}"

    Please provide ALL requested translations in this EXACT format:

    """

        # Add German translations for ALL selected styles
        if 'german' in target_languages and german_styles:
            prompt += "GERMAN TRANSLATIONS:\n"
            for style in german_styles:
                prompt += f"German {style.capitalize()}: [Provide {style} German translation here]\n"
            
            # Add word-by-word section if enabled with ENHANCED INSTRUCTIONS
            if style_preferences.german_word_by_word:
                prompt += "\nGERMAN WORD-BY-WORD:\n"
                for style in german_styles:
                    prompt += f"{style.capitalize()} style: "
                    prompt += "Format each word precisely as [German word] ([EXACT Spanish equivalent]). "
                    prompt += "CRITICAL: Each German word MUST be paired with its PRECISE Spanish translation equivalent. "
                    prompt += "Example: [Ich] ([Yo]) [trinke] ([bebo]) [Wasser] ([agua])\n"
                prompt += "\n"

        # Add English translations for ALL selected styles
        if 'english' in target_languages and english_styles:
            prompt += "ENGLISH TRANSLATIONS:\n"
            for style in english_styles:
                prompt += f"English {style.capitalize()}: [Provide {style} English translation here]\n"
            
            # Add word-by-word section if enabled with ENHANCED INSTRUCTIONS
            if style_preferences.english_word_by_word:
                prompt += "\nENGLISH WORD-BY-WORD:\n"
                for style in english_styles:
                    prompt += f"{style.capitalize()} style: "
                    prompt += "Format each word precisely as [English word] ([EXACT Spanish equivalent]). "
                    prompt += "CRITICAL: Each English word MUST be paired with its PRECISE Spanish translation equivalent. "
                    prompt += "Example: [I] ([Yo]) [drink] ([bebo]) [water] ([agua])\n"
                prompt += "\n"

        # Add Spanish translations if needed
        if 'spanish' in target_languages:
            prompt += "SPANISH TRANSLATIONS:\nSpanish Colloquial: [Spanish translation here]\n\n"

        prompt += """IMPORTANT RULES FOR WORD-BY-WORD TRANSLATION ACCURACY:
    1. Provide translations for ALL selected styles
    2. Each style should have a distinct translation appropriate to its formality level
    3. For phrasal verbs (like "wake up"), treat as ONE unit: [wake up] ([despertar])
    4. For German separable verbs (like "stehe auf"), treat as ONE unit: [stehe auf] ([me levanto])
    5. CRITICAL: Every word pairing MUST be semantically correct translations of each other
    6. Word order might differ between languages - match words by MEANING, not position
    7. Personal pronouns must be correctly translated (e.g., "ich" → "yo", "du" → "tú")
    8. Articles must correspond correctly (e.g., "der/die/das" → "el/la")
    9. Verb forms must match in meaning (e.g., "bin" → "soy", "hast" → "tienes")
    10. For words with multiple meanings, use the meaning that fits the context
    11. Native style: Most natural expression a native speaker would use
    12. Colloquial style: Conversational, everyday language
    13. Informal style: Relaxed, casual, friendly tone
    14. Formal style: Professional, polite, structured language

    This task requires your linguistic expertise to create accurate word-by-word translations that precisely match each word with its true translation equivalent."""

        print(f"📝 Generated MULTI-STYLE prompt ({len(prompt)} characters)")
        return prompt


    def _should_generate_audio(self, translations_data: Dict, style_preferences) -> bool:
        """Only generate audio if user has selected translation styles"""
        has_translations = len(translations_data.get('translations', [])) > 0
        
        has_enabled_styles = False
        if style_preferences:
            # Check ALL style preferences
            style_checks = [
                style_preferences.german_native,
                style_preferences.german_colloquial,
                style_preferences.german_informal,
                style_preferences.german_formal,
                style_preferences.english_native,
                style_preferences.english_colloquial,
                style_preferences.english_informal,
                style_preferences.english_formal
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
        """Generate audio with enhanced error handling for multiple styles"""
        try:
            print("🎵 Attempting MULTI-STYLE SYNCHRONIZED audio generation...")
            
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
                    print(f"✅ MULTI-STYLE SYNCHRONIZED audio generation successful: {audio_filename}")
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
            print(f"🌐 PROCESSING MULTI-STYLE ENHANCED CONTEXTUAL TRANSLATION")
            print(f"{'='*80}")
            print(f"📝 Input text: '{text}'")
            print(f"🌍 Detected mother tongue: {detected_mother_tongue}")

            # Create enhanced multi-style context prompt 
            enhanced_prompt = self._create_enhanced_context_prompt(
                text, detected_mother_tongue, style_preferences
            )
            
            print(f"📤 Sending MULTI-STYLE prompt to Gemini AI...")

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

            # Extract translations with MULTI-STYLE support
            translations_data = self._extract_translations_fixed(generated_text, style_preferences)

            audio_filename = None

            # Check if audio should be generated
            should_generate_audio = self._should_generate_audio(translations_data, style_preferences)
            
            # Generate synchronized audio for all selected styles
            if should_generate_audio:
                print("🎵 Starting MULTI-STYLE SYNCHRONIZED audio generation...")
                audio_filename = await self._generate_audio_with_resilience(
                    translations_data, detected_mother_tongue, style_preferences
                )
                
                if audio_filename:
                    print(f"✅ MULTI-STYLE SYNCHRONIZED audio completed: {audio_filename}")
                else:
                    print("ℹ️ Audio generation failed/skipped - continuing without audio")
            else:
                print("🔇 No audio generated - no translation styles enabled")

            # Create perfect UI-Audio synchronized data for all styles
            ui_word_by_word = self._create_perfect_ui_sync_data(translations_data, style_preferences)

            # Create final translation text with all styles
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

    # def _extract_translations_fixed(self, generated_text: str, style_preferences) -> Dict:
    #     """ENHANCED extraction for multiple simultaneous styles with perfect sync."""
    #     result = {
    #         'translations': [],
    #         'style_data': []
    #     }

    #     print("🔍 EXTRACTING MULTI-STYLE TRANSLATIONS")
    #     print("="*50)
    #     print(f"📄 Generated text length: {len(generated_text)}")

    #     try:
    #         lines = generated_text.split('\n')
    #         current_language = None
    #         word_by_word_text = {}
    #         all_word_by_word_data = {}  # Store word-by-word for ALL styles
            
    #         for line in lines:
    #             line = line.strip()
    #             if not line:
    #                 continue
                
    #             # Detect language sections
    #             if 'GERMAN TRANSLATIONS:' in line.upper():
    #                 current_language = 'german'
    #                 print(f"📍 Found German section")
    #             elif 'ENGLISH TRANSLATIONS:' in line.upper():
    #                 current_language = 'english'
    #                 print(f"📍 Found English section")
    #             elif 'SPANISH TRANSLATIONS:' in line.upper():
    #                 current_language = 'spanish'
    #                 print(f"📍 Found Spanish section")
    #             elif 'GERMAN WORD-BY-WORD:' in line.upper():
    #                 print(f"📍 Found German word-by-word section")
    #                 current_language = 'german_wbw'
    #             elif 'ENGLISH WORD-BY-WORD:' in line.upper():
    #                 print(f"📍 Found English word-by-word section")
    #                 current_language = 'english_wbw'
                
    #             # Extract translations for ALL selected styles
    #             elif current_language == 'german':
    #                 # Process ALL German styles
    #                 styles_to_check = [
    #                     ('German Native:', 'german_native', style_preferences.german_native),
    #                     ('German Colloquial:', 'german_colloquial', style_preferences.german_colloquial),
    #                     ('German Informal:', 'german_informal', style_preferences.german_informal),
    #                     ('German Formal:', 'german_formal', style_preferences.german_formal)
    #                 ]
                    
    #                 for prefix, style_name, is_enabled in styles_to_check:
    #                     if prefix in line and is_enabled:
    #                         translation = self._extract_translation_from_line(line, prefix)
    #                         if translation:
    #                             result['translations'].append(translation)
    #                             result['style_data'].append({
    #                                 'translation': translation,
    #                                 'word_pairs': [],
    #                                 'is_german': True,
    #                                 'is_spanish': False,
    #                                 'style_name': style_name
    #                             })
    #                             print(f"✅ {style_name}: {translation[:50]}...")
                
    #             elif current_language == 'english':
    #                 # Process ALL English styles
    #                 styles_to_check = [
    #                     ('English Native:', 'english_native', style_preferences.english_native),
    #                     ('English Colloquial:', 'english_colloquial', style_preferences.english_colloquial),
    #                     ('English Informal:', 'english_informal', style_preferences.english_informal),
    #                     ('English Formal:', 'english_formal', style_preferences.english_formal)
    #                 ]
                    
    #                 for prefix, style_name, is_enabled in styles_to_check:
    #                     if prefix in line and is_enabled:
    #                         translation = self._extract_translation_from_line(line, prefix)
    #                         if translation:
    #                             result['translations'].append(translation)
    #                             result['style_data'].append({
    #                                 'translation': translation,
    #                                 'word_pairs': [],
    #                                 'is_german': False,
    #                                 'is_spanish': False,
    #                                 'style_name': style_name
    #                             })
    #                             print(f"✅ {style_name}: {translation[:50]}...")
                
    #             # Handle word-by-word sections for multiple styles
    #             elif current_language == 'german_wbw':
    #                 # Check if this line specifies a style
    #                 for style in ['Native', 'Colloquial', 'Informal', 'Formal']:
    #                     if f'{style} style:' in line:
    #                         style_key = f'german_{style.lower()}'
    #                         # Extract the word-by-word part
    #                         wbw_start = line.find('[')
    #                         if wbw_start >= 0:
    #                             all_word_by_word_data[style_key] = line[wbw_start:]
    #                             print(f"📝 German {style} word-by-word: {line[wbw_start:100]}...")
    #                         break
    #                 else:
    #                     # If line contains brackets, might be general word-by-word
    #                     if '[' in line and ']' in line and '(' in line and ')' in line:
    #                         if 'german' not in word_by_word_text:
    #                             word_by_word_text['german'] = line
    #                             print(f"📝 German general word-by-word: {line[:100]}...")
                
    #             elif current_language == 'english_wbw':
    #                 # Check if this line specifies a style
    #                 for style in ['Native', 'Colloquial', 'Informal', 'Formal']:
    #                     if f'{style} style:' in line:
    #                         style_key = f'english_{style.lower()}'
    #                         # Extract the word-by-word part
    #                         wbw_start = line.find('[')
    #                         if wbw_start >= 0:
    #                             all_word_by_word_data[style_key] = line[wbw_start:]
    #                             print(f"📝 English {style} word-by-word: {line[wbw_start:100]}...")
    #                         break
    #                 else:
    #                     # If line contains brackets, might be general word-by-word
    #                     if '[' in line and ']' in line and '(' in line and ')' in line:
    #                         if 'english' not in word_by_word_text:
    #                             word_by_word_text['english'] = line
    #                             print(f"📝 English general word-by-word: {line[:100]}...")
                
    #             elif current_language == 'spanish':
    #                 if 'Spanish Colloquial:' in line:
    #                     translation = self._extract_translation_from_line(line, 'Spanish Colloquial:')
    #                     if translation:
    #                         result['translations'].append(translation)
    #                         result['style_data'].append({
    #                             'translation': translation,
    #                             'word_pairs': [],
    #                             'is_german': False,
    #                             'is_spanish': True,
    #                             'style_name': 'spanish_colloquial'
    #                         })
    #                         print(f"✅ Spanish Colloquial: {translation[:50]}...")

    #         # Process word-by-word data for EACH style
    #         for style_entry in result['style_data']:
    #             style_name = style_entry['style_name']
    #             is_german = style_entry['is_german']
                
    #             # Check if we have specific word-by-word for this style
    #             if style_name in all_word_by_word_data:
    #                 # Use style-specific word-by-word
    #                 if (is_german and style_preferences.german_word_by_word) or \
    #                    (not is_german and not style_entry['is_spanish'] and style_preferences.english_word_by_word):
    #                     word_pairs = self._parse_word_by_word_line(all_word_by_word_data[style_name])
    #                     if word_pairs:
    #                         style_entry['word_pairs'] = word_pairs
    #                         print(f"✅ Added {len(word_pairs)} word pairs to {style_name}")
    #             else:
    #                 # Fall back to general word-by-word if available
    #                 language = 'german' if is_german else 'english'
    #                 if language in word_by_word_text:
    #                     if (is_german and style_preferences.german_word_by_word) or \
    #                        (not is_german and style_preferences.english_word_by_word):
    #                         word_pairs = self._parse_word_by_word_line(word_by_word_text[language])
    #                         if word_pairs:
    #                             style_entry['word_pairs'] = word_pairs
    #                             print(f"✅ Added {len(word_pairs)} general word pairs to {style_name}")

    #         print(f"✅ Extracted {len(result['translations'])} translations")
    #         print(f"✅ Extracted {len(result['style_data'])} style entries")
            
    #     except Exception as e:
    #         print(f"❌ Error in extraction: {str(e)}")
    #         import traceback
    #         traceback.print_exc()
            
    #         # Fallback: create minimal result
    #         if not result['translations']:
    #             result['translations'] = [generated_text[:500]]
    #             result['style_data'] = [{
    #                 'translation': generated_text[:500],
    #                 'word_pairs': [],
    #                 'is_german': False,
    #                 'is_spanish': False,
    #                 'style_name': 'fallback'
    #             }]

    #     return result





    def _extract_translations_fixed(self, generated_text: str, style_preferences) -> Dict:
        """ENHANCED extraction for multiple simultaneous styles with perfect sync without manual dictionaries."""
        result = {
            'translations': [],
            'style_data': []
        }

        print("🔍 EXTRACTING MULTI-STYLE TRANSLATIONS")
        print("="*50)
        print(f"📄 Generated text length: {len(generated_text)}")

        try:
            lines = generated_text.split('\n')
            current_language = None
            word_by_word_text = {}
            all_word_by_word_data = {}  # Store word-by-word for ALL styles
            
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
                elif 'GERMAN WORD-BY-WORD:' in line.upper():
                    print(f"📍 Found German word-by-word section")
                    current_language = 'german_wbw'
                elif 'ENGLISH WORD-BY-WORD:' in line.upper():
                    print(f"📍 Found English word-by-word section")
                    current_language = 'english_wbw'
                
                # Extract translations for ALL selected styles
                elif current_language == 'german':
                    # Process ALL German styles
                    styles_to_check = [
                        ('German Native:', 'german_native', style_preferences.german_native),
                        ('German Colloquial:', 'german_colloquial', style_preferences.german_colloquial),
                        ('German Informal:', 'german_informal', style_preferences.german_informal),
                        ('German Formal:', 'german_formal', style_preferences.german_formal)
                    ]
                    
                    for prefix, style_name, is_enabled in styles_to_check:
                        if prefix in line and is_enabled:
                            translation = self._extract_translation_from_line(line, prefix)
                            if translation:
                                result['translations'].append(translation)
                                result['style_data'].append({
                                    'translation': translation,
                                    'word_pairs': [],
                                    'is_german': True,
                                    'is_spanish': False,
                                    'style_name': style_name
                                })
                                print(f"✅ {style_name}: {translation[:50]}...")
                
                elif current_language == 'english':
                    # Process ALL English styles
                    styles_to_check = [
                        ('English Native:', 'english_native', style_preferences.english_native),
                        ('English Colloquial:', 'english_colloquial', style_preferences.english_colloquial),
                        ('English Informal:', 'english_informal', style_preferences.english_informal),
                        ('English Formal:', 'english_formal', style_preferences.english_formal)
                    ]
                    
                    for prefix, style_name, is_enabled in styles_to_check:
                        if prefix in line and is_enabled:
                            translation = self._extract_translation_from_line(line, prefix)
                            if translation:
                                result['translations'].append(translation)
                                result['style_data'].append({
                                    'translation': translation,
                                    'word_pairs': [],
                                    'is_german': False,
                                    'is_spanish': False,
                                    'style_name': style_name
                                })
                                print(f"✅ {style_name}: {translation[:50]}...")
                
                # Handle word-by-word sections for multiple styles
                elif current_language == 'german_wbw':
                    # Check if this line specifies a style
                    for style in ['Native', 'Colloquial', 'Informal', 'Formal']:
                        if f'{style} style:' in line:
                            style_key = f'german_{style.lower()}'
                            # Extract the word-by-word part
                            wbw_start = line.find('[')
                            if wbw_start >= 0:
                                all_word_by_word_data[style_key] = line[wbw_start:]
                                print(f"📝 German {style} word-by-word: {line[wbw_start:100]}...")
                            break
                    else:
                        # If line contains brackets, might be general word-by-word
                        if '[' in line and ']' in line and '(' in line and ')' in line:
                            if 'german' not in word_by_word_text:
                                word_by_word_text['german'] = line
                                print(f"📝 German general word-by-word: {line[:100]}...")
                
                elif current_language == 'english_wbw':
                    # Check if this line specifies a style
                    for style in ['Native', 'Colloquial', 'Informal', 'Formal']:
                        if f'{style} style:' in line:
                            style_key = f'english_{style.lower()}'
                            # Extract the word-by-word part
                            wbw_start = line.find('[')
                            if wbw_start >= 0:
                                all_word_by_word_data[style_key] = line[wbw_start:]
                                print(f"📝 English {style} word-by-word: {line[wbw_start:100]}...")
                            break
                    else:
                        # If line contains brackets, might be general word-by-word
                        if '[' in line and ']' in line and '(' in line and ')' in line:
                            if 'english' not in word_by_word_text:
                                word_by_word_text['english'] = line
                                print(f"📝 English general word-by-word: {line[:100]}...")
                
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

            # Process word-by-word data for EACH style with AI-only approach (no validation dictionaries)
            for style_entry in result['style_data']:
                style_name = style_entry['style_name']
                is_german = style_entry['is_german']
                
                # Check if we have specific word-by-word for this style
                if style_name in all_word_by_word_data:
                    # Use style-specific word-by-word
                    if (is_german and style_preferences.german_word_by_word) or \
                    (not is_german and not style_entry['is_spanish'] and style_preferences.english_word_by_word):
                        word_pairs = self._parse_word_by_word_line(all_word_by_word_data[style_name])
                        if word_pairs:
                            # Store the pairs - NO MANUAL VALIDATION
                            style_entry['word_pairs'] = word_pairs
                            print(f"✅ Added {len(word_pairs)} word pairs to {style_name}")
                else:
                    # Fall back to general word-by-word if available
                    language = 'german' if is_german else 'english'
                    if language in word_by_word_text:
                        if (is_german and style_preferences.german_word_by_word) or \
                        (not is_german and style_preferences.english_word_by_word):
                            word_pairs = self._parse_word_by_word_line(word_by_word_text[language])
                            if word_pairs:
                                # Store the pairs - NO MANUAL VALIDATION
                                style_entry['word_pairs'] = word_pairs
                                print(f"✅ Added {len(word_pairs)} general word pairs to {style_name}")

            print(f"✅ Extracted {len(result['translations'])} translations")
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

    # def _parse_word_by_word_line(self, line: str) -> List[Tuple[str, str]]:
    #     """Parse a word-by-word line into pairs"""
    #     pairs = []
        
    #     try:
    #         # Find all [word] ([translation]) patterns
    #         pattern = r'\[([^\]]+)\]\s*\(\s*\[([^\]]+)\]\s*\)'
    #         matches = re.findall(pattern, line)
            
    #         if not matches:
    #             # Try simpler pattern without inner brackets
    #             pattern = r'\[([^\]]+)\]\s*\(\s*([^)]+)\s*\)'
    #             matches = re.findall(pattern, line)
            
    #         for source, target in matches:
    #             source = source.strip()
    #             target = target.strip()
    #             if source and target:
    #                 pairs.append((source, target))
    #                 print(f"   📝 Pair: '{source}' → '{target}'")
            
    #     except Exception as e:
    #         print(f"❌ Error parsing word-by-word line: {str(e)}")
        
    #     return pairs


    def _parse_word_by_word_line(self, line: str) -> List[Tuple[str, str]]:
        """Parse a word-by-word line into pairs - simplified without manual validation."""
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

    # Add a method to check formatting consistency without validation dictionaries
    def _check_format_consistency(self, pairs: List[Tuple[str, str]]) -> None:
        """Check if the pairs have consistent formatting without using dictionaries."""
        if not pairs or len(pairs) < 2:
            return
        
        # Check format consistency only
        has_bracket_issues = False
        for source, target in pairs:
            if '[' in source or ']' in source or '(' in source or ')' in source:
                has_bracket_issues = True
                print(f"⚠️ Format issue: Source '{source}' contains brackets")
            
            if '[' in target or ']' in target or '(' in target or ')' in target:
                has_bracket_issues = True
                print(f"⚠️ Format issue: Target '{target}' contains brackets")
        
        if has_bracket_issues:
            print("⚠️ Format inconsistencies detected - this may affect audio playback")


    def _create_perfect_ui_sync_data(self, translations_data: Dict, style_preferences) -> Dict[str, Dict[str, str]]:
        """Create UI data that PERFECTLY matches what will be spoken in audio for ALL styles"""
        ui_data = {}
        
        print("📱 Creating PERFECT MULTI-STYLE UI-Audio synchronization data...")
        print("="*60)
        
        style_counter = {}  # Track counters per style
        
        for style_info in translations_data.get('style_data', []):
            style_name = style_info['style_name']
            word_pairs = style_info.get('word_pairs', [])
            is_german = style_info.get('is_german', False)
            is_spanish = style_info.get('is_spanish', False)
            
            # Initialize counter for this style
            if style_name not in style_counter:
                style_counter[style_name] = 0
            
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
                    
                    # Create unique key for each style's word pairs
                    key = f"{style_name}_{i}_{source_clean.replace(' ', '_')}"
                    
                    ui_data[key] = {
                        "source": source_clean,
                        "spanish": spanish_clean,
                        "language": "german" if is_german else "english",
                        "style": style_name,
                        "order": str(style_counter[style_name]),
                        "is_phrasal_verb": str(" " in source_clean),
                        "display_format": display_format  # EXACT audio format
                    }
                    
                    style_counter[style_name] += 1
                    
                    print(f"   {i+1:2d}. {style_name} UI: {display_format}")
                    if " " in source_clean:
                        verb_type = "German Separable Verb" if is_german else "English Phrasal Verb"
                        print(f"       🔗 {verb_type}: Single unit")
        
        print(f"✅ Created PERFECT UI sync data for {len(ui_data)} word pairs across {len(style_counter)} styles")
        print("="*60)
        return ui_data

    def _create_formatted_translation_text(self, translations_data: Dict) -> str:
        """Create nicely formatted translation text for display with all styles"""
        formatted_parts = []
        
        formatted_parts.append("=" * 50)
        formatted_parts.append("MULTI-STYLE TRANSLATION RESULTS:")
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
            "structure": "Enhanced multi-style grammar explanation with context",
            "tense": "Tense usage adapted to multiple styles and mother tongue",
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
    


