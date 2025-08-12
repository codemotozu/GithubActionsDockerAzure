# translation_service.py - Enhanced with resilient audio handling for Azure Speech 429 errors

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
        EXACT implementation of the requirements from paste.txt
        """
        
        print(f"🎯 Creating prompt for mother tongue: {mother_tongue.upper()}")
        
        # EXACT LOGIC FROM REQUIREMENTS:
        # 1. Spanish mother tongue -> German and/or English based on selections
        # 2. English mother tongue -> Spanish (automatic) + German if selected
        # 3. German mother tongue -> Spanish (automatic) + English if selected
        
        target_languages = []
        audio_instructions = []
        
        if mother_tongue.lower() == 'spanish':
            print("🇪🇸 Spanish mother tongue - checking German and English selections")
            
            # Check German selections
            german_styles = [
                style_preferences.german_native,
                style_preferences.german_colloquial, 
                style_preferences.german_informal,
                style_preferences.german_formal
            ]
            if any(german_styles):
                target_languages.append('german')
                print("   ✅ German translation enabled")
                
                # Check German word-by-word audio
                if style_preferences.german_word_by_word:
                    audio_instructions.append("German word-by-word audio with Spanish equivalents")
                    print("   🎵 German word-by-word audio enabled")
            
            # Check English selections  
            english_styles = [
                style_preferences.english_native,
                style_preferences.english_colloquial,
                style_preferences.english_informal,
                style_preferences.english_formal
            ]
            if any(english_styles):
                target_languages.append('english')
                print("   ✅ English translation enabled")
                
                # Check English word-by-word audio
                if style_preferences.english_word_by_word:
                    audio_instructions.append("English word-by-word audio with Spanish equivalents")
                    print("   🎵 English word-by-word audio enabled")
                    
        elif mother_tongue.lower() == 'english':
            print("🇺🇸 English mother tongue - automatic Spanish + optional German")
            
            # Spanish is AUTOMATIC for English speakers
            target_languages.append('spanish')
            print("   ✅ Spanish translation enabled (automatic)")
            
            # Check German selections
            german_styles = [
                style_preferences.german_native,
                style_preferences.german_colloquial,
                style_preferences.german_informal, 
                style_preferences.german_formal
            ]
            if any(german_styles):
                target_languages.append('german')
                print("   ✅ German translation enabled")
                
                # Check German word-by-word audio
                if style_preferences.german_word_by_word:
                    audio_instructions.append("German word-by-word audio with Spanish equivalents")
                    print("   🎵 German word-by-word audio enabled")
                    
        elif mother_tongue.lower() == 'german':
            print("🇩🇪 German mother tongue - automatic Spanish + optional English")
            
            # Spanish is AUTOMATIC for German speakers
            target_languages.append('spanish')
            print("   ✅ Spanish translation enabled (automatic)")
            
            # Check English selections
            english_styles = [
                style_preferences.english_native,
                style_preferences.english_colloquial,
                style_preferences.english_informal,
                style_preferences.english_formal
            ]
            if any(english_styles):
                target_languages.append('english') 
                print("   ✅ English translation enabled")
                
                # Check English word-by-word audio
                if style_preferences.english_word_by_word:
                    audio_instructions.append("English word-by-word audio with Spanish equivalents")
                    print("   🎵 English word-by-word audio enabled")

        print(f"🎯 Final target languages: {target_languages}")
        print(f"🎵 Audio instructions: {audio_instructions}")

        # Build the dynamic prompt - EXACT format from requirements
        prompt_parts = [
            f"""You are an expert multilingual translator. The user's mother tongue is {mother_tongue.upper()}.

CRITICAL DYNAMIC TRANSLATION RULES:
- Input text is in {mother_tongue.upper()}
- Translate ONLY to the specifically requested target languages
- For word-by-word breakdowns: [target word/phrase] ([Spanish equivalent])
- Group phrasal verbs, separable verbs, and compound expressions as single units
- ONLY generate word-by-word if specifically requested for that language

Text to translate: "{input_text}"

REQUIRED TRANSLATIONS:"""
        ]

        # EXACT IMPLEMENTATION: Add translations based on mother tongue and selections
        if 'german' in target_languages:
            prompt_parts.append(f"\n{'='*50}")
            prompt_parts.append("GERMAN TRANSLATIONS:")
            prompt_parts.append(f"{'='*50}")
            
            if style_preferences.german_native:
                prompt_parts.append('* German Native Style:\n"[Natural German translation]"')
                if style_preferences.german_word_by_word:
                    prompt_parts.append('* German Native Word-by-Word German-Spanish:\n"[German word/phrase] ([Spanish translation]) [next German word/phrase] ([Spanish translation]) ..."')
                    
            if style_preferences.german_colloquial:
                prompt_parts.append('* German Colloquial Style:\n"[Colloquial German translation]"')
                if style_preferences.german_word_by_word:
                    prompt_parts.append('* German Colloquial Word-by-Word German-Spanish:\n"[German word/phrase] ([Spanish translation]) [next German word/phrase] ([Spanish translation]) ..."')
                    
            if style_preferences.german_informal:
                prompt_parts.append('* German Informal Style:\n"[Informal German translation]"')
                if style_preferences.german_word_by_word:
                    prompt_parts.append('* German Informal Word-by-Word German-Spanish:\n"[German word/phrase] ([Spanish translation]) [next German word/phrase] ([Spanish translation]) ..."')
                    
            if style_preferences.german_formal:
                prompt_parts.append('* German Formal Style:\n"[Formal German translation]"')
                if style_preferences.german_word_by_word:
                    prompt_parts.append('* German Formal Word-by-Word German-Spanish:\n"[German word/phrase] ([Spanish translation]) [next German word/phrase] ([Spanish translation]) ..."')

        if 'english' in target_languages:
            prompt_parts.append(f"\n{'='*50}")
            prompt_parts.append("ENGLISH TRANSLATIONS:")
            prompt_parts.append(f"{'='*50}")
            
            if style_preferences.english_native:
                prompt_parts.append('* English Native Style:\n"[Natural English translation]"')
                if style_preferences.english_word_by_word:
                    prompt_parts.append('* English Native Word-by-Word English-Spanish:\n"[English word/phrase] ([Spanish translation]) [next English word/phrase] ([Spanish translation]) ..."')
                    
            if style_preferences.english_colloquial:
                prompt_parts.append('* English Colloquial Style:\n"[Colloquial English translation]"')
                if style_preferences.english_word_by_word:
                    prompt_parts.append('* English Colloquial Word-by-Word English-Spanish:\n"[English word/phrase] ([Spanish translation]) [next English word/phrase] ([Spanish translation]) ..."')
                    
            if style_preferences.english_informal:
                prompt_parts.append('* English Informal Style:\n"[Informal English translation]"')
                if style_preferences.english_word_by_word:
                    prompt_parts.append('* English Informal Word-by-Word English-Spanish:\n"[English word/phrase] ([Spanish translation]) [next English word/phrase] ([Spanish translation]) ..."')
                    
            if style_preferences.english_formal:
                prompt_parts.append('* English Formal Style:\n"[Formal English translation]"')
                if style_preferences.english_word_by_word:
                    prompt_parts.append('* English Formal Word-by-Word English-Spanish:\n"[English word/phrase] ([Spanish translation]) [next English word/phrase] ([Spanish translation]) ..."')

        if 'spanish' in target_languages:
            prompt_parts.append(f"\n{'='*50}")
            prompt_parts.append("SPANISH TRANSLATIONS:")
            prompt_parts.append(f"{'='*50}")
            prompt_parts.append('* Spanish Colloquial Style:\n"[Natural Spanish translation]"')
            # Note: Spanish doesn't need word-by-word since it's the reference language

        # Add specific instructions for word-by-word format
        if audio_instructions:
            prompt_parts.append(f"\n{'='*50}")
            prompt_parts.append("WORD-BY-WORD FORMAT REQUIREMENTS:")
            prompt_parts.append(f"{'='*50}")
            prompt_parts.append("- Use EXACT format: [target word/phrase] ([Spanish equivalent])")
            prompt_parts.append("- Group phrasal verbs as single units: [wake up] ([despertar])")
            prompt_parts.append("- Group separable verbs as single units: [stehe auf] ([me levanto])")
            prompt_parts.append("- Use Spanish as the reference language for ALL word-by-word breakdowns")

        final_prompt = "\n".join(prompt_parts)
        print(f"📝 Generated dynamic prompt ({len(final_prompt)} characters)")
        return final_prompt

    def _should_generate_audio(self, translations_data: Dict, style_preferences) -> bool:
        """
        EXACT implementation: Only generate audio if user has selected word-by-word audio
        OR if user has selected translation styles (for simple reading audio)
        """
        # Check if we have any translations
        has_translations = len(translations_data.get('translations', [])) > 0
        
        # Check if any translation styles are enabled
        has_enabled_styles = False
        if style_preferences:
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
        
        # Check if word-by-word audio is requested
        word_by_word_requested = False
        if style_preferences:
            word_by_word_requested = (
                style_preferences.german_word_by_word or 
                style_preferences.english_word_by_word
            )
        
        # EXACT per requirements: Generate audio if we have translations AND any styles enabled
        should_generate = has_translations and has_enabled_styles
        
        print(f"🎵 Audio Generation Decision (EXACT per requirements):")
        print(f"   Translations available: {has_translations}")
        print(f"   Translation styles enabled: {has_enabled_styles}")
        print(f"   Word-by-word audio requested: {word_by_word_requested}")
        print(f"   🎯 Will generate audio: {should_generate}")
        print(f"   🎯 Audio type: {'Word-by-word breakdown' if word_by_word_requested else 'Simple translation reading'}")
        
        return should_generate

    async def _generate_audio_with_resilience(self, translations_data: Dict, detected_mother_tongue: str, style_preferences) -> Optional[str]:
        """
        Generate audio with resilience to Azure Speech API rate limiting and errors.
        """
        try:
            print("🎵 Attempting audio generation with enhanced error handling...")
            
            # Try to generate audio with timeout
            audio_task = asyncio.create_task(
                self.tts_service.text_to_speech_word_pairs_v2(
                    translations_data=translations_data,
                    source_lang=detected_mother_tongue,
                    target_lang="es",  # Spanish is always the reference
                    style_preferences=style_preferences,
                )
            )
            
            # Wait for completion with timeout
            try:
                audio_filename = await asyncio.wait_for(audio_task, timeout=self.audio_timeout_seconds)
                
                if audio_filename:
                    print(f"✅ Audio generation successful: {audio_filename}")
                    return audio_filename
                else:
                    print("⚠️ Audio generation returned None (likely due to rate limiting)")
                    return None
                    
            except asyncio.TimeoutError:
                print(f"⏰ Audio generation timed out after {self.audio_timeout_seconds} seconds")
                audio_task.cancel()
                return None
                
        except Exception as e:
            print(f"❌ Audio generation failed with exception: {str(e)}")
            
            # Check if it's a rate limiting error
            if "429" in str(e) or "Too many requests" in str(e):
                print("🔄 Rate limiting detected - audio generation skipped")
            elif "WebSocket" in str(e):
                print("🔄 Connection issue detected - audio generation skipped")
            else:
                print(f"🔄 Unknown audio error - audio generation skipped: {type(e).__name__}")
            
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

            # Detect the actual input language (can override source_lang)
            detected_mother_tongue = self._detect_input_language(text, mother_tongue)
            
            print(f"\n{'='*80}")
            print(f"🌐 PROCESSING DYNAMIC MOTHER TONGUE TRANSLATION")
            print(f"{'='*80}")
            print(f"📝 Input text: '{text}'")
            print(f"🌍 Detected mother tongue: {detected_mother_tongue}")

            # Create dynamic prompt based on EXACT requirements
            dynamic_prompt = self._create_dynamic_mother_tongue_prompt(
                text, detected_mother_tongue, style_preferences
            )
            
            print(f"📤 Sending dynamic prompt to Gemini AI...")

            # Create a new chat session with the dynamic prompt
            chat_session = self.model.start_chat(
                history=[{
                    "role": "user", 
                    "parts": [dynamic_prompt],
                }]
            )

            response = chat_session.send_message(text)
            generated_text = response.text

            print(f"📥 Gemini response received ({len(generated_text)} characters)")

            # Extract translations and word pairs
            translations_data = self._extract_text_and_pairs_v2(generated_text, style_preferences)

            audio_filename = None

            # EXACT per requirements: Check if audio should be generated
            should_generate_audio = self._should_generate_audio(translations_data, style_preferences)
            
            # Generate audio with enhanced error handling and resilience
            if should_generate_audio:
                print("🎵 Starting resilient audio generation...")
                audio_filename = await self._generate_audio_with_resilience(
                    translations_data, detected_mother_tongue, style_preferences
                )
                
                if audio_filename:
                    print(f"✅ Audio generation completed successfully: {audio_filename}")
                else:
                    print("ℹ️ Audio generation failed/skipped - continuing without audio")
                    print("💡 This is normal if Azure Speech API is rate limited or unavailable")
            else:
                if not translations_data.get('translations'):
                    print("🔇 No audio generated - no translations available")
                else:
                    print("🔇 No audio generated - no translation styles enabled")

            # Always return the translation, even if audio failed
            return Translation(
                original_text=text,
                translated_text=generated_text,
                source_language=detected_mother_tongue,
                target_language="multi",  # Multiple target languages based on mother tongue
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
        EXACT implementation per requirements.
        """
        result = {
            'translations': [],
            'style_data': []
        }

        # Detect what language sections we have
        has_german = ("GERMAN TRANSLATIONS:" in generated_text or 
                     "German Native Style:" in generated_text or
                     "German Colloquial Style:" in generated_text)
        has_english = ("ENGLISH TRANSLATIONS:" in generated_text or
                      "English Native Style:" in generated_text or
                      "English Colloquial Style:" in generated_text)
        has_spanish = ("SPANISH TRANSLATIONS:" in generated_text or
                      "Spanish Colloquial Style:" in generated_text)
        
        print(f"🔍 Detected sections: German={has_german}, English={has_english}, Spanish={has_spanish}")

        # Split into sections more precisely
        sections = {}
        if has_german:
            german_start = generated_text.find("GERMAN TRANSLATIONS:")
            if german_start == -1:
                # Fallback to style markers
                for marker in ["German Native Style:", "German Colloquial Style:", "German Informal Style:", "German Formal Style:"]:
                    pos = generated_text.find(marker)
                    if pos != -1:
                        german_start = pos
                        break
            
            if german_start != -1:
                # Find the end of German section
                german_end = len(generated_text)
                for next_marker in ["ENGLISH TRANSLATIONS:", "SPANISH TRANSLATIONS:"]:
                    pos = generated_text.find(next_marker, german_start + 1)
                    if pos != -1:
                        german_end = pos
                        break
                sections['german'] = generated_text[german_start:german_end]
                
        if has_english:
            english_start = generated_text.find("ENGLISH TRANSLATIONS:")
            if english_start == -1:
                # Fallback to style markers
                for marker in ["English Native Style:", "English Colloquial Style:", "English Informal Style:", "English Formal Style:"]:
                    pos = generated_text.find(marker)
                    if pos != -1:
                        english_start = pos
                        break
                        
            if english_start != -1:
                # Find the end of English section
                english_end = len(generated_text)
                for next_marker in ["SPANISH TRANSLATIONS:", "WORD-BY-WORD FORMAT"]:
                    pos = generated_text.find(next_marker, english_start + 1)
                    if pos != -1:
                        english_end = pos
                        break
                sections['english'] = generated_text[english_start:english_end]
                
        if has_spanish:
            spanish_start = generated_text.find("SPANISH TRANSLATIONS:")
            if spanish_start == -1:
                pos = generated_text.find("Spanish Colloquial Style:")
                if pos != -1:
                    spanish_start = pos
                    
            if spanish_start != -1:
                sections['spanish'] = generated_text[spanish_start:]

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
            spanish_match = re.search(r'Spanish Colloquial Style:\s*"([^"]+)"', sections['spanish'], re.IGNORECASE)
            if spanish_match:
                result['translations'].append(spanish_match.group(1))
                result['style_data'].append({
                    'translation': spanish_match.group(1),
                    'word_pairs': [],  # Spanish doesn't need word-by-word per requirements
                    'is_german': False,
                    'is_spanish': True,
                    'style_name': 'spanish_colloquial'
                })

        print(f"🎵 Final extraction: {len(result['translations'])} translations, {len(result['style_data'])} style entries")
        
        return result

    def _process_language_section(self, section: str, language: str, style_preferences, result: Dict):
        """Process a specific language section (German or English) with EXACT format matching"""
        is_german = (language == 'german')
        
        styles_to_check = ['native', 'colloquial', 'informal', 'formal']
        
        for style in styles_to_check:
            # Check if this style is enabled
            enabled = getattr(style_preferences, f'{language}_{style}', False)
            word_by_word_enabled = getattr(style_preferences, f'{language}_word_by_word', False)
            
            if enabled:
                style_data = self._extract_single_style(
                    section,
                    rf'{language.title()} {style.title()} Style:\s*"([^"]+)"',
                    rf'{language.title()} {style.title()} Word-by-Word.*?:\s*"([^"]+)"',
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
        """Extract translation and word pairs for a single style - EXACT format matching"""
        
        # Extract main translation
        text_match = re.search(text_pattern, text_section, re.IGNORECASE | re.DOTALL)
        if not text_match:
            print(f"   ⚠️ No translation found for {style_name}")
            return None
            
        translation_text = text_match.group(1).strip()
        print(f"   ✅ Found translation for {style_name}: '{translation_text[:50]}...'")
        
        # Extract word pairs ONLY if enabled - EXACT per requirements
        word_pairs = []
        if word_by_word_enabled:
            print(f"   🔍 Looking for word pairs for {style_name} (user requested word-by-word audio)...")
            
            # Enhanced pattern to match EXACT format: [word] ([translation])
            pairs_patterns = [
                pairs_pattern,
                rf'{style_name.split("_")[0].title()}.*?Word-by-Word.*?:\s*"([^"\n]+)"',
                rf'Word-by-Word.*?{style_name.split("_")[1].title()}.*?:\s*"([^"\n]+)"',
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
                # EXACT format parsing: [word/phrase] ([translation])
                pair_patterns = [
                    r'\[([^\]]+)\]\s*\(([^)]+)\)',  # [word] (translation)
                    r'([^()]+?)\s*\(([^)]+?)\)',    # word (translation)
                ]
                
                for pair_pattern in pair_patterns:
                    try:
                        pair_matches = re.findall(pair_pattern, pairs_text)
                        if pair_matches:
                            for source, target in pair_matches:
                                # Clean up the extracted pairs
                                source = source.strip().strip('"\'[]').rstrip('.,!?;:')
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
        else:
            print(f"   ⏭️ Skipping word-by-word for {style_name} - user did not request word-by-word audio")
                                
        print(f"   📊 {style_name}: Found translation + {len(word_pairs)} word pairs")
        
        return {
            'translation': translation_text,
            'word_pairs': word_pairs,
            'is_german': is_german,
            'is_spanish': False,
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