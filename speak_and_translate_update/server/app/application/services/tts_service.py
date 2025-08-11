# tts_service.py - Updated with enhanced word-by-word audio logic per requirements

from azure.cognitiveservices.speech import (
    SpeechConfig,
    SpeechSynthesizer,
    SpeechSynthesisOutputFormat,
    ResultReason,
    CancellationReason,
)
from azure.cognitiveservices.speech.audio import AudioOutputConfig
import os
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import asyncio
import re
import logging
import google.generativeai as genai
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedTTSService:
    def __init__(self):
        # Initialize Speech Config
        self.subscription_key = os.getenv("AZURE_SPEECH_KEY")
        self.region = os.getenv("AZURE_SPEECH_REGION")

        if not self.subscription_key or not self.region:
            raise ValueError(
                "Azure Speech credentials not found in environment variables"
            )

        # Initialize Gemini for intelligent phrase translation
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.translation_model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                generation_config={
                    "temperature": 0.2,  # Lower temperature for more consistent translations
                    "top_p": 0.8,
                    "max_output_tokens": 150,
                }
            )
        else:
            logger.warning("GEMINI_API_KEY not found - fallback translations will be limited")
            self.translation_model = None

        # Add this before creating SpeechConfig
        os.environ["SPEECH_CONTAINER_OPTION"] = "1"
        os.environ["SPEECH_SYNTHESIS_PLATFORM_CONFIG"] = "container"
        
        # Create speech config with endpoint
        self.speech_host = f"wss://{self.region}.tts.speech.microsoft.com/cognitiveservices/websocket/v1"
        self.speech_config = SpeechConfig(
            subscription=self.subscription_key,
            endpoint=self.speech_host
        )
        
        self.speech_config.set_speech_synthesis_output_format(
            SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
        )

        # Dynamic voice mapping with support for multiple mother tongues
        self.voice_mapping = {
            "es": {
                "voice": "es-ES-ArabellaMultilingualNeural",
                "language": "es-ES",
                "name": "Spanish"
            },
            "en": {
                "voice": "en-US-JennyMultilingualNeural", 
                "language": "en-US",
                "name": "English"
            },
            "de": {
                "voice": "de-DE-SeraphinaMultilingualNeural",
                "language": "de-DE", 
                "name": "German"
            },
            "fr": {
                "voice": "fr-FR-DeniseMultilingualNeural",
                "language": "fr-FR",
                "name": "French"
            },
            "it": {
                "voice": "it-IT-ElsaMultilingualNeural",
                "language": "it-IT",
                "name": "Italian"
            },
            "pt": {
                "voice": "pt-PT-RaquelMultilingualNeural",
                "language": "pt-PT",
                "name": "Portuguese"
            },
        }

        # Enhanced core translations for multiple languages
        self.core_translations = {
            # Critical articles (most frequent)
            "the": "el/la", "a": "un/una", "an": "un/una",
            "der": "el", "die": "la", "das": "el/lo", "ein": "un", "eine": "una",
            "el": "the", "la": "the", "un": "a", "una": "a",
            
            # Critical pronouns
            "i": "yo", "you": "tú", "he": "él", "she": "ella", "we": "nosotros", "they": "ellos",
            "ich": "yo", "du": "tú", "er": "él", "sie": "ella", "wir": "nosotros",
            "yo": "I", "tú": "you", "él": "he", "ella": "she", "nosotros": "we", "ellos": "they",
            
            # Critical connectors
            "and": "y", "or": "o", "but": "pero", "und": "y", "oder": "o", "aber": "pero",
            "y": "and", "o": "or", "pero": "but",
            
            # Essential negations
            "not": "no", "no": "no", "nicht": "no",
            
            # Punctuation stays the same
            ".": ".", ",": ",", "!": "!", "?": "?", ";": ";", ":": ":", "(": "(", ")": ")",
        }

        # Enhanced cache for dynamic AI translations
        self._translation_cache = {}

    def _get_temp_directory(self) -> str:
        """Create and return the temporary directory path"""
        if os.name == "nt":  # Windows
            temp_dir = os.path.join(os.environ.get("TEMP", ""), "tts_audio")
        else:  # Unix/Linux
            temp_dir = "/tmp/tts_audio"
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    def _get_voice_config(self, language_code: str) -> dict:
        """Get voice configuration for a language"""
        # Map full language names to codes
        lang_map = {
            'spanish': 'es',
            'english': 'en', 
            'german': 'de',
            'french': 'fr',
            'italian': 'it',
            'portuguese': 'pt'
        }
        
        # Get the language code
        if language_code in lang_map:
            code = lang_map[language_code]
        else:
            code = language_code
            
        return self.voice_mapping.get(code, self.voice_mapping['es'])  # Default to Spanish

    @lru_cache(maxsize=2000)
    def _translate_with_ai_comprehensive(self, word_or_phrase: str, source_lang: str, context: str = "") -> str:
        """
        Comprehensive AI translation for word-by-word breakdown.
        """
        if not self.translation_model:
            return f"[{word_or_phrase}]"
        
        try:
            # Determine source language
            lang_map = {"en": "English", "de": "German", "es": "Spanish", "fr": "French", "it": "Italian", "pt": "Portuguese"}
            lang_name = lang_map.get(source_lang, "Unknown")
            
            # Smart prompt for word-by-word translation
            prompt = f"""Translate this {lang_name} word or phrase to Spanish for word-by-word pronunciation practice.

RULES:
1. For phrasal verbs (like "turn off", "look up"), translate the complete meaning as one unit
2. For German separable verbs (like "aufstehen", "ankommen"), translate the complete verb meaning
3. For compound words, translate the complete concept
4. For single words, give the most common Spanish equivalent
5. Keep response SHORT - just the Spanish translation

Word/phrase: "{word_or_phrase}"
{f"Context: {context}" if context else ""}

Spanish translation:"""

            response = self.translation_model.generate_content(prompt)
            translation = response.text.strip()
            
            # Clean the response
            translation = translation.replace('"', '').replace("'", '').replace('`', '').strip()
            translation = re.sub(r'^\w+\s*:', '', translation)  # Remove "Spanish:" prefixes
            translation = re.sub(r'\(.*?\)', '', translation)  # Remove parenthetical explanations
            
            # Handle multiple options - take the first reasonable one
            if '/' in translation:
                options = [opt.strip() for opt in translation.split('/')]
                translation = options[0] if options else translation
                
            if ',' in translation and len(translation.split(',')) > 2:
                translation = translation.split(',')[0].strip()
            
            # Clean final result
            translation = translation.strip().strip('.,!?;:')
            
            if translation and len(translation.split()) <= 3:  # Reasonable length
                logger.debug(f"🤖 AI translated: '{word_or_phrase}' -> '{translation}'")
                return translation
            else:
                return f"[{word_or_phrase}]"
                
        except Exception as e:
            logger.error(f"AI translation failed for '{word_or_phrase}': {str(e)}")
            return f"[{word_or_phrase}]"

    def _find_translation_for_phrase(self, phrase: str, mapping: Dict[str, str], source_lang: str) -> str:
        """Find translation using explicit mapping first, then AI fallback."""
        # Clean the phrase
        clean_phrase = phrase.strip().lower().rstrip('.,!?;:()[]{}"\'-')
        
        # Strategy 1: Check if it's just punctuation
        if phrase in ".,!?;:()[]{}\"'-":
            return phrase
        
        # Strategy 2: Numbers stay the same
        if clean_phrase.isdigit():
            return clean_phrase
        
        # Strategy 3: Direct lookup in provided mapping (from word-by-word pairs)
        for variant in [phrase, clean_phrase, phrase.lower()]:
            if variant in mapping:
                logger.debug(f"📋 Explicit mapping: '{phrase}' -> '{mapping[variant]}'")
                return mapping[variant]
        
        # Strategy 4: Check core essentials (very small dictionary)
        if clean_phrase in self.core_translations:
            logger.debug(f"🎯 Core translation: '{phrase}' -> '{self.core_translations[clean_phrase]}'")
            return self.core_translations[clean_phrase]
        
        # Strategy 5: Check cache for previous AI translations
        cache_key = f"{clean_phrase}_{source_lang}"
        if cache_key in self._translation_cache:
            logger.debug(f"💾 Cached: '{phrase}' -> '{self._translation_cache[cache_key]}'")
            return self._translation_cache[cache_key]
        
        # Strategy 6: Use AI to build translation dynamically
        translation = self._translate_with_ai_comprehensive(clean_phrase, source_lang)
        
        # Cache the translation for future use
        self._translation_cache[cache_key] = translation
        
        return translation

    def _create_intelligent_word_mapping(self, word_pairs: List[Tuple[str, str]], source_lang: str) -> Dict[str, str]:
        """Create mapping that prioritizes explicit pairs."""
        mapping = {}
        
        # Add all explicit word pairs with high priority
        for source, target in word_pairs:
            source_clean = source.strip()
            target_clean = target.strip()
            
            # Store multiple variants for better matching
            variants = [
                source_clean,
                source_clean.lower(),
                source_clean.strip('.,!?;:()[]{}"\'-'),
                source_clean.lower().strip('.,!?;:()[]{}"\'-')
            ]
            
            for variant in variants:
                if variant:
                    mapping[variant] = target_clean
                    
            logger.debug(f"📝 Explicit pair: '{source_clean}' -> '{target_clean}'")
        
        # Add core translations (AI handles the rest)
        core_added = 0
        for core_word, core_translation in self.core_translations.items():
            if core_word not in mapping:  # Don't override explicit pairs
                mapping[core_word] = core_translation
                core_added += 1
        
        logger.info(f"🏗️  Created mapping: {len(word_pairs)} explicit pairs + {core_added} core words")
        
        return mapping

    async def text_to_speech_word_pairs_v2(
        self,
        translations_data: Dict,
        source_lang: str,
        target_lang: str,
        style_preferences=None,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Enhanced TTS with EXACT word-by-word requirements implementation.
        """
        try:
            if not output_path:
                temp_dir = self._get_temp_directory()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(temp_dir, f"speech_{timestamp}.mp3")

            logger.info(f"🌐 Generating audio for source language: {source_lang}")
            
            # Extract word-by-word settings from requirements
            german_word_by_word = False
            english_word_by_word = False
            
            if style_preferences:
                german_word_by_word = getattr(style_preferences, 'german_word_by_word', False)
                english_word_by_word = getattr(style_preferences, 'english_word_by_word', False)
                
                logger.info(f"🎵 Word-by-Word Audio Settings (EXACT per requirements):")
                logger.info(f"   German word-by-word: {german_word_by_word}")
                logger.info(f"   English word-by-word: {english_word_by_word}")
            
            # Check if we have any translations to work with
            if not translations_data.get('translations'):
                logger.info("🔇 No audio generated - no translations available")
                return None
            
            # EXACT implementation: Check if ANY word-by-word is requested
            any_word_by_word_requested = german_word_by_word or english_word_by_word
            
            logger.info(f"🔍 Audio generation mode (per requirements):")
            logger.info(f"   Style data entries: {len(translations_data.get('style_data', []))}")
            logger.info(f"   Any word-by-word requested: {any_word_by_word_requested}")
            
            # EXACT per requirements: Generate different audio based on word-by-word setting
            if any_word_by_word_requested:
                logger.info("🎵 Generating WORD-BY-WORD breakdown audio (per requirements)")
                ssml = self._generate_word_by_word_ssml(
                    translations_data=translations_data,
                    source_lang=source_lang,
                    style_preferences=style_preferences,
                )
            else:
                logger.info("🎵 Generating SIMPLE translation reading audio (NOT word-by-word)")
                ssml = self._generate_simple_translation_ssml(
                    translations_data=translations_data,
                    source_lang=source_lang,
                    style_preferences=style_preferences,
                )
            
            # Create audio config and synthesizer
            audio_config = AudioOutputConfig(filename=output_path)
            speech_config = SpeechConfig(
                subscription=self.subscription_key, region=self.region
            )
            speech_config.set_speech_synthesis_output_format(
                SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
            )

            synthesizer = SpeechSynthesizer(
                speech_config=speech_config, audio_config=audio_config
            )

            # Synthesize speech
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: synthesizer.speak_ssml_async(ssml).get()
            )

            if result.reason == ResultReason.SynthesizingAudioCompleted:
                logger.info(f"✅ Successfully generated audio: {os.path.basename(output_path)}")
                return os.path.basename(output_path)

            if result.reason == ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                logger.error(f"❌ Synthesis canceled: {cancellation_details.reason}")
                if cancellation_details.reason == CancellationReason.Error:
                    logger.error(f"❌ Error details: {cancellation_details.error_details}")

            return None

        except Exception as e:
            logger.error(f"❌ Error in text_to_speech_word_pairs_v2: {str(e)}")
            return None

    def _generate_simple_translation_ssml(
        self,
        translations_data: Dict,
        source_lang: str,
        style_preferences=None,
    ) -> str:
        """
        Generate simple SSML that just reads translations (when word-by-word is NOT selected).
        EXACT per requirements: "otherwise is not necessary"
        """
        ssml = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">"""
        
        logger.info("\n🎤 SIMPLE TRANSLATION AUDIO (No word-by-word)")
        logger.info("="*60)
        logger.info("📖 Reading translations normally - no detailed breakdown")
        
        # Process each style and read the translation
        for i, style_info in enumerate(translations_data.get('style_data', [])):
            translation = style_info['translation']
            is_german = style_info['is_german']
            style_name = style_info['style_name']
            
            # Escape XML special characters
            translation = translation.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            # Get voice configuration for the target language
            voice_config = self._get_voice_config('german' if is_german else 'english')
            voice = voice_config['voice']
            lang = voice_config['language']
            
            logger.info(f"📖 Reading {style_name}: \"{translation}\"")
            
            # Add a simple reading of the translation
            ssml += f"""
        <voice name="{voice}">
            <prosody rate="1.0">
                <lang xml:lang="{lang}">{translation}</lang>
                <break time="1500ms"/>
            </prosody>
        </voice>"""
        
        ssml += "</speak>"
        
        logger.info(f"✅ Generated simple audio for {len(translations_data.get('style_data', []))} translations")
        return ssml

    def _generate_word_by_word_ssml(
        self,
        translations_data: Dict,
        source_lang: str,
        style_preferences=None,
    ) -> str:
        """
        Generate SSML with EXACT word-by-word breakdown per requirements.
        Format: [target word] ([Spanish equivalent])
        """
        ssml = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">"""
        
        logger.info("\n🎤 WORD-BY-WORD BREAKDOWN AUDIO (per requirements)")
        logger.info("="*60)
        logger.info(f"🌐 Source Language: {source_lang}")
        logger.info("🎯 Format: [target word] ([Spanish equivalent])")
        
        # Check which languages have word-by-word enabled
        german_word_by_word = getattr(style_preferences, 'german_word_by_word', False)
        english_word_by_word = getattr(style_preferences, 'english_word_by_word', False)
        
        # Process each style 
        for style_info in translations_data.get('style_data', []):
            translation = style_info['translation']
            word_pairs = style_info.get('word_pairs', [])
            is_german = style_info['is_german']
            style_name = style_info['style_name']
            
            # EXACT per requirements: Check if word-by-word is requested for this language
            should_do_word_by_word = (
                (is_german and german_word_by_word) or 
                (not is_german and english_word_by_word)
            )
            
            logger.info(f"\n📝 Processing {style_name}:")
            logger.info(f"   Translation: \"{translation}\"")
            logger.info(f"   Word pairs available: {len(word_pairs)}")
            logger.info(f"   Should do word-by-word: {should_do_word_by_word}")
            
            # EXACT per requirements: Skip if word-by-word is not requested for this language
            if not should_do_word_by_word:
                logger.info(f"   ⏭️ Skipping word-by-word for {style_name} - not requested")
                # Still read the translation simply
                voice_config = self._get_voice_config('german' if is_german else 'english')
                voice = voice_config['voice']
                lang = voice_config['language']
                
                clean_translation = translation.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                
                ssml += f"""
        <voice name="{voice}">
            <prosody rate="1.0">
                <lang xml:lang="{lang}">{clean_translation}</lang>
                <break time="1000ms"/>
            </prosody>
        </voice>"""
                continue
            
            # Escape XML special characters
            translation = translation.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            # Create mapping with explicit pairs
            lang_code = 'de' if is_german else 'en'
            mapping = self._create_intelligent_word_mapping(word_pairs, lang_code)
            
            # Get voice configuration
            voice_config = self._get_voice_config('german' if is_german else 'english')
            voice = voice_config['voice']
            lang = voice_config['language']
            
            # First, read the complete translation
            ssml += f"""
        <voice name="{voice}">
            <prosody rate="1.0">
                <lang xml:lang="{lang}">{translation}</lang>
                <break time="1000ms"/>
            </prosody>
        </voice>"""
            
            # EXACT per requirements: Word-by-word breakdown
            ssml += """
        <voice name="en-US-JennyMultilingualNeural">
            <prosody rate="0.8">"""
            
            # Tokenize the translation for word-by-word
            tokens = re.findall(r"\b\w+(?:'[a-z]+)?\b|[.,!?;:()\[\]{}\"'-]", translation)
            
            logger.info(f"   📝 Tokenized into {len(tokens)} tokens for word-by-word")
            
            # Process each token with EXACT format: [word] ([Spanish])
            for i, token in enumerate(tokens):
                token = token.strip()
                if not token:
                    continue
                
                # Find Spanish translation for this token
                spanish_translation = self._find_translation_for_phrase(token, mapping, lang_code)
                
                # Clean for speech
                clean_token = token.strip()
                clean_spanish = spanish_translation.replace("[", "").replace("]", "")
                
                # EXACT format per requirements: [target word] ([Spanish equivalent])
                ssml += f"""
            <lang xml:lang="{lang}">{clean_token}</lang>
            <break time="300ms"/>
            <lang xml:lang="es-ES">{clean_spanish}</lang>
            <break time="500ms"/>"""
                
                # Log the word-by-word pair
                if clean_token and clean_token not in ".,!?;:()[]{}\"'-":
                    logger.debug(f"   {i+1:2d}. '{clean_token}' -> '{clean_spanish}'")
            
            ssml += """
            <break time="1000ms"/>
            </prosody>
        </voice>"""
        
        ssml += "</speak>"
        
        logger.info(f"✅ Generated word-by-word breakdown SSML")
        return ssml

    # Keep legacy method for backward compatibility
    async def text_to_speech_word_pairs(
        self,
        word_pairs: List[Tuple[str, str, bool]],
        source_lang: str,
        target_lang: str,
        output_path: Optional[str] = None,
        complete_text: Optional[str] = None,
        style_preferences=None,
    ) -> Optional[str]:
        """Legacy method - converts to new format and calls v2."""
        # Convert legacy format to new structured format
        translations_data = {
            'translations': [],
            'style_data': []
        }
        
        # If we have complete_text, try to extract structured data
        if complete_text:
            # Basic parsing to maintain compatibility
            translations_data['translations'] = [complete_text]
            translations_data['style_data'] = [{
                'translation': complete_text,
                'word_pairs': [(src, tgt) for src, tgt, _ in word_pairs],
                'is_german': source_lang == 'german',
                'style_name': f'{source_lang}_colloquial'
            }]
        
        # Call the v2 method
        return await self.text_to_speech_word_pairs_v2(
            translations_data=translations_data,
            source_lang=source_lang,
            target_lang=target_lang,
            style_preferences=style_preferences,
            output_path=output_path,
        )

    async def text_to_speech(
        self, ssml: str, output_path: Optional[str] = None
    ) -> Optional[str]:
        """Convert SSML to speech"""
        synthesizer = None
        try:
            if not output_path:
                temp_dir = self._get_temp_directory()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(temp_dir, f"speech_{timestamp}.mp3")

            audio_config = AudioOutputConfig(filename=output_path)
            synthesizer = SpeechSynthesizer(
                speech_config=self.speech_config, audio_config=audio_config
            )

            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: synthesizer.speak_ssml_async(ssml).get()
            )

            if result.reason == ResultReason.SynthesizingAudioCompleted:
                return os.path.basename(output_path)

            return None

        except Exception as e:
            logger.error(f"❌ Exception in text_to_speech: {str(e)}")
            return None
        finally:
            if synthesizer:
                try:
                    synthesizer.stop_speaking_async()
                except:
                    pass