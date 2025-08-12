# tts_service.py - Enhanced with rate limiting and retry logic to fix Azure Speech 429 errors

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
import time
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter to prevent Azure Speech API 429 errors"""
    
    def __init__(self, max_requests_per_minute=15, max_requests_per_second=2):
        self.max_requests_per_minute = max_requests_per_minute
        self.max_requests_per_second = max_requests_per_second
        self.requests_this_minute = []
        self.requests_this_second = []
        self.last_request_time = 0
        
    async def wait_if_needed(self):
        """Wait if we're hitting rate limits"""
        current_time = time.time()
        
        # Clean old requests
        self.requests_this_minute = [t for t in self.requests_this_minute if current_time - t < 60]
        self.requests_this_second = [t for t in self.requests_this_second if current_time - t < 1]
        
        # Check per-second limit
        if len(self.requests_this_second) >= self.max_requests_per_second:
            wait_time = 1.0 - (current_time - min(self.requests_this_second))
            if wait_time > 0:
                logger.info(f"⏳ Rate limiting: waiting {wait_time:.2f}s (per-second limit)")
                await asyncio.sleep(wait_time)
                current_time = time.time()
        
        # Check per-minute limit
        if len(self.requests_this_minute) >= self.max_requests_per_minute:
            wait_time = 60.0 - (current_time - min(self.requests_this_minute))
            if wait_time > 0:
                logger.info(f"⏳ Rate limiting: waiting {wait_time:.2f}s (per-minute limit)")
                await asyncio.sleep(wait_time)
                current_time = time.time()
        
        # Ensure minimum gap between requests
        time_since_last = current_time - self.last_request_time
        min_gap = 0.5  # Minimum 500ms between requests
        if time_since_last < min_gap:
            wait_time = min_gap - time_since_last
            logger.info(f"⏳ Rate limiting: minimum gap wait {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
            current_time = time.time()
        
        # Record this request
        self.requests_this_minute.append(current_time)
        self.requests_this_second.append(current_time)
        self.last_request_time = current_time


class EnhancedTTSService:
    def __init__(self):
        # Initialize Speech Config
        self.subscription_key = os.getenv("AZURE_SPEECH_KEY")
        self.region = os.getenv("AZURE_SPEECH_REGION")

        if not self.subscription_key or not self.region:
            raise ValueError(
                "Azure Speech credentials not found in environment variables"
            )

        # Rate limiter to prevent 429 errors
        self.rate_limiter = RateLimiter(max_requests_per_minute=12, max_requests_per_second=1)

        # Initialize Gemini for AI-powered translations (not dictionaries per requirements)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.translation_model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                generation_config={
                    "temperature": 0.2,  # Lower temperature for more consistent translations-----
                    "top_p": 0.8,
                    "max_output_tokens": 150,
                }
            )
        else:
            logger.warning("GEMINI_API_KEY not found - AI translations will be limited")
            self.translation_model = None

        # Speech configuration
        self.speech_config = SpeechConfig(
            subscription=self.subscription_key,
            region=self.region
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

        # CRITICAL: Minimal essential dictionary - rely on AI per requirements
        self.essential_words = {
            # Only the most critical articles and connectors
            "the": "el/la", "a": "un/una", "and": "y", "or": "o", "but": "pero",
            "der": "el", "die": "la", "das": "el/lo", "ein": "un", "eine": "una", "und": "y",
            "el": "the", "la": "the", "un": "a", "una": "a", "y": "and",
            # Punctuation stays the same
            ".": ".", ",": ",", "!": "!", "?": "?", ";": ";", ":": ":",
        }

        # Cache for AI translations to avoid repeated API calls
        self._ai_translation_cache = {}

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
    def _translate_with_ai(self, word_or_phrase: str, source_lang: str, context: str = "") -> str:
        """
        AI-powered translation for word-by-word breakdown.
        EXACT per requirements: Don't make huge dictionaries - rely on AI
        """
        if not self.translation_model:
            return f"[{word_or_phrase}]"
        
        # Check cache first
        cache_key = f"{word_or_phrase}_{source_lang}_{context[:20]}"
        if cache_key in self._ai_translation_cache:
            return self._ai_translation_cache[cache_key]
        
        try:
            # Language mapping
            lang_map = {"en": "English", "de": "German", "es": "Spanish", "fr": "French", "it": "Italian", "pt": "Portuguese"}
            lang_name = lang_map.get(source_lang, "Unknown")
            
            # EXACT per requirements: AI-powered translation without dictionaries
            prompt = f"""Translate this {lang_name} word or phrase to Spanish for pronunciation practice.

CRITICAL RULES:
1. For phrasal verbs (like "turn off", "look up"), translate the complete meaning as one unit
2. For German separable verbs (like "aufstehen", "ankommen"), translate the complete verb meaning  
3. For compound words, translate the complete concept
4. For single words, give the most common Spanish equivalent
5. Keep response SHORT - just the Spanish translation, no explanations

Word/phrase: "{word_or_phrase}"
{f"Context: {context}" if context else ""}

Spanish translation:"""

            response = self.translation_model.generate_content(prompt)
            translation = response.text.strip()
            
            # Clean the AI response
            translation = translation.replace('"', '').replace("'", '').replace('`', '').strip()
            translation = re.sub(r'^\w+\s*:', '', translation)  # Remove "Spanish:" prefixes
            translation = re.sub(r'\(.*?\)', '', translation)  # Remove explanations
            
            # Handle multiple options - take the first reasonable one
            if '/' in translation:
                options = [opt.strip() for opt in translation.split('/')]
                translation = options[0] if options else translation
                
            if ',' in translation and len(translation.split(',')) > 2:
                translation = translation.split(',')[0].strip()
            
            # Final cleanup
            translation = translation.strip().strip('.,!?;:')
            
            # Validate result length
            if translation and len(translation.split()) <= 3:
                # Cache the result
                self._ai_translation_cache[cache_key] = translation
                logger.debug(f"🤖 AI translated: '{word_or_phrase}' -> '{translation}'")
                return translation
            else:
                return f"[{word_or_phrase}]"
                
        except Exception as e:
            logger.error(f"AI translation failed for '{word_or_phrase}': {str(e)}")
            return f"[{word_or_phrase}]"

    def _find_translation_for_phrase(self, phrase: str, explicit_mapping: Dict[str, str], source_lang: str) -> str:
        """
        Find translation using EXACT logic per requirements:
        1. Check explicit word-by-word pairs first
        2. Check minimal essential words
        3. Use AI for everything else (no huge dictionaries)
        """
        # Clean the phrase
        clean_phrase = phrase.strip().lower().rstrip('.,!?;:()[]{}"\'-')
        
        # Strategy 1: Punctuation stays the same
        if phrase in ".,!?;:()[]{}\"'-":
            return phrase
        
        # Strategy 2: Numbers stay the same
        if clean_phrase.isdigit():
            return clean_phrase
        
        # Strategy 3: Check explicit word-by-word pairs (highest priority)
        for variant in [phrase, clean_phrase, phrase.lower()]:
            if variant in explicit_mapping:
                logger.debug(f"📋 Explicit mapping: '{phrase}' -> '{explicit_mapping[variant]}'")
                return explicit_mapping[variant]
        
        # Strategy 4: Check minimal essential words ONLY
        if clean_phrase in self.essential_words:
            logger.debug(f"🎯 Essential word: '{phrase}' -> '{self.essential_words[clean_phrase]}'")
            return self.essential_words[clean_phrase]
        
        # Strategy 5: EXACT per requirements - Use AI, not dictionaries
        translation = self._translate_with_ai(clean_phrase, source_lang)
        
        return translation

    def _create_word_mapping_from_pairs(self, word_pairs: List[Tuple[str, str]], source_lang: str) -> Dict[str, str]:
        """
        Create mapping prioritizing explicit word-by-word pairs.
        EXACT per requirements: Don't make huge dictionaries manually - rely on AI
        """
        mapping = {}
        
        # Add all explicit word pairs with highest priority
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
        
        # Add ONLY essential words (minimal set per requirements)
        essential_added = 0
        for essential_word, essential_translation in self.essential_words.items():
            if essential_word not in mapping:  # Don't override explicit pairs
                mapping[essential_word] = essential_translation
                essential_added += 1
        
        logger.info(f"🏗️  Created mapping: {len(word_pairs)} explicit pairs + {essential_added} essential words (AI handles the rest)")
        
        return mapping

    async def _synthesize_with_retry(self, ssml: str, output_path: str, max_retries: int = 3) -> bool:
        """
        Synthesize speech with retry logic and exponential backoff to handle 429 errors
        """
        for attempt in range(max_retries):
            try:
                # Apply rate limiting before each attempt
                await self.rate_limiter.wait_if_needed()
                
                # Create fresh synthesizer for each attempt
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

                logger.info(f"🎤 Attempting speech synthesis (attempt {attempt + 1}/{max_retries})")
                
                # Synthesize with timeout
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: synthesizer.speak_ssml_async(ssml).get()
                )

                if result.reason == ResultReason.SynthesizingAudioCompleted:
                    logger.info(f"✅ Speech synthesis successful on attempt {attempt + 1}")
                    return True

                elif result.reason == ResultReason.Canceled:
                    cancellation_details = result.cancellation_details
                    
                    if cancellation_details.reason == CancellationReason.Error:
                        error_details = cancellation_details.error_details
                        logger.warning(f"⚠️ Synthesis error (attempt {attempt + 1}): {error_details}")
                        
                        # Handle specific error types
                        if "429" in error_details or "Too many requests" in error_details:
                            # Exponential backoff for rate limiting
                            base_delay = 2 ** attempt
                            jitter = random.uniform(0.1, 0.5)
                            delay = base_delay + jitter
                            
                            logger.info(f"🔄 Rate limit hit, retrying in {delay:.2f}s...")
                            await asyncio.sleep(delay)
                            continue
                            
                        elif "WebSocket" in error_details:
                            # Connection issues - shorter delay
                            delay = 1 + random.uniform(0.1, 0.3)
                            logger.info(f"🔄 Connection issue, retrying in {delay:.2f}s...")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            # Other errors - don't retry
                            logger.error(f"❌ Non-retryable error: {error_details}")
                            return False
                    else:
                        logger.error(f"❌ Synthesis canceled: {cancellation_details.reason}")
                        return False
                else:
                    logger.error(f"❌ Synthesis failed with reason: {result.reason}")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Exception during synthesis attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    delay = (2 ** attempt) + random.uniform(0.1, 0.5)
                    logger.info(f"🔄 Retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    return False
        
        logger.error(f"❌ All {max_retries} synthesis attempts failed")
        return False

    async def text_to_speech_word_pairs_v2(
        self,
        translations_data: Dict,
        source_lang: str,
        target_lang: str,
        style_preferences=None,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Enhanced TTS with EXACT word-by-word requirements implementation and improved error handling.
        """
        try:
            if not output_path:
                temp_dir = self._get_temp_directory()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(temp_dir, f"speech_{timestamp}.mp3")

            logger.info(f"🌐 Generating audio for source language: {source_lang}")
            
            # EXACT per requirements: Extract word-by-word settings
            german_word_by_word = False
            english_word_by_word = False
            
            if style_preferences:
                german_word_by_word = getattr(style_preferences, 'german_word_by_word', False)
                english_word_by_word = getattr(style_preferences, 'english_word_by_word', False)
                
                logger.info(f"🎵 Word-by-Word Audio Settings (EXACT per requirements):")
                logger.info(f"   German word-by-word: {german_word_by_word}")
                logger.info(f"   English word-by-word: {english_word_by_word}")
                logger.info(f"   Format: [target word] ([Spanish equivalent])")
            
            # Check if we have any translations
            if not translations_data.get('translations'):
                logger.info("🔇 No audio generated - no translations available")
                return None
            
            # EXACT per requirements: Check if ANY word-by-word is requested
            any_word_by_word_requested = german_word_by_word or english_word_by_word
            
            logger.info(f"🔍 Audio generation mode (EXACT per requirements):")
            logger.info(f"   Style data entries: {len(translations_data.get('style_data', []))}")
            logger.info(f"   Any word-by-word requested: {any_word_by_word_requested}")
            
            # EXACT per requirements: Generate different audio based on word-by-word setting
            if any_word_by_word_requested:
                logger.info("🎵 Generating WORD-BY-WORD breakdown audio (user selected word-by-word audio)")
                ssml = self._generate_word_by_word_ssml(
                    translations_data=translations_data,
                    source_lang=source_lang,
                    style_preferences=style_preferences,
                )
            else:
                logger.info("🎵 Generating SIMPLE translation reading audio (user did NOT select word-by-word audio)")
                ssml = self._generate_simple_translation_ssml(
                    translations_data=translations_data,
                    source_lang=source_lang,
                    style_preferences=style_preferences,
                )
            
            # Use retry logic for synthesis
            success = await self._synthesize_with_retry(ssml, output_path, max_retries=3)
            
            if success:
                logger.info(f"✅ Successfully generated audio: {os.path.basename(output_path)}")
                return os.path.basename(output_path)
            else:
                logger.error("❌ Failed to generate audio after all retry attempts")
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
        Generate simple SSML that just reads translations.
        EXACT per requirements: "otherwise is not necessary" (when word-by-word not selected)
        """
        ssml = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">"""
        
        logger.info("\n🎤 SIMPLE TRANSLATION AUDIO (User did NOT select word-by-word)")
        logger.info("="*60)
        logger.info("📖 Reading translations normally - no detailed breakdown")
        
        # Process each style and read the translation
        for i, style_info in enumerate(translations_data.get('style_data', [])):
            translation = style_info['translation']
            is_german = style_info.get('is_german', False)
            is_spanish = style_info.get('is_spanish', False)
            style_name = style_info['style_name']
            
            # Escape XML special characters
            translation = translation.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            # Get voice configuration for the target language
            if is_spanish:
                voice_config = self._get_voice_config('spanish')
            elif is_german:
                voice_config = self._get_voice_config('german')
            else:
                voice_config = self._get_voice_config('english')
                
            voice = voice_config['voice']
            lang = voice_config['language']
            
            logger.info(f"📖 Reading {style_name}: \"{translation}\"")
            
            # Add a simple reading of the translation with reduced breaks to minimize API calls
            ssml += f"""
        <voice name="{voice}">
            <prosody rate="1.0">
                <lang xml:lang="{lang}">{translation}</lang>
                <break time="800ms"/>
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
        EXACT format: [target word] ([Spanish equivalent])
        EXACT condition: Only if user selected "word by word audio"
        """
        ssml = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">"""
        
        logger.info("\n🎤 WORD-BY-WORD BREAKDOWN AUDIO (User selected word-by-word audio)")
        logger.info("="*60)
        logger.info(f"🌐 Source Language: {source_lang}")
        logger.info("🎯 EXACT Format: [target word] ([Spanish equivalent])")
        
        # EXACT per requirements: Check which languages have word-by-word enabled
        german_word_by_word = getattr(style_preferences, 'german_word_by_word', False)
        english_word_by_word = getattr(style_preferences, 'english_word_by_word', False)
        
        # Process each style 
        for style_info in translations_data.get('style_data', []):
            translation = style_info['translation']
            word_pairs = style_info.get('word_pairs', [])
            is_german = style_info.get('is_german', False)
            is_spanish = style_info.get('is_spanish', False)
            style_name = style_info['style_name']
            
            # EXACT per requirements: Check if word-by-word is requested for this specific language
            should_do_word_by_word = False
            if is_german and german_word_by_word:
                should_do_word_by_word = True
            elif not is_german and not is_spanish and english_word_by_word:
                should_do_word_by_word = True
            elif is_spanish:
                # Spanish never needs word-by-word (it's the reference language)
                should_do_word_by_word = False
            
            logger.info(f"\n📝 Processing {style_name}:")
            logger.info(f"   Translation: \"{translation}\"")
            logger.info(f"   Word pairs available: {len(word_pairs)}")
            logger.info(f"   Is German: {is_german}, Is Spanish: {is_spanish}")
            logger.info(f"   User requested word-by-word for this language: {should_do_word_by_word}")
            
            # EXACT per requirements: Skip if word-by-word is not requested for this language
            if not should_do_word_by_word:
                logger.info(f"   ⏭️ Skipping word-by-word for {style_name} - user did not request it for this language")
                # Still read the translation simply
                if is_spanish:
                    voice_config = self._get_voice_config('spanish')
                elif is_german:
                    voice_config = self._get_voice_config('german')
                else:
                    voice_config = self._get_voice_config('english')
                
                voice = voice_config['voice']
                lang = voice_config['language']
                
                clean_translation = translation.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                
                ssml += f"""
        <voice name="{voice}">
            <prosody rate="1.0">
                <lang xml:lang="{lang}">{clean_translation}</lang>
                <break time="600ms"/>
            </prosody>
        </voice>"""
                continue
            
            # EXACT per requirements: Generate word-by-word breakdown
            logger.info(f"   🎵 Generating word-by-word breakdown for {style_name}")
            
            # Escape XML special characters
            translation = translation.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            # Create mapping with explicit pairs + AI for the rest
            lang_code = 'de' if is_german else 'en'
            mapping = self._create_word_mapping_from_pairs(word_pairs, lang_code)
            
            # Get voice configuration
            if is_german:
                voice_config = self._get_voice_config('german')
            else:
                voice_config = self._get_voice_config('english')
                
            voice = voice_config['voice']
            lang = voice_config['language']
            
            # First, read the complete translation
            ssml += f"""
        <voice name="{voice}">
            <prosody rate="1.0">
                <lang xml:lang="{lang}">{translation}</lang>
                <break time="800ms"/>
            </prosody>
        </voice>"""
            
            # EXACT per requirements: Word-by-word breakdown with format [word] ([Spanish])
            # Limit the number of words to prevent too many API calls
            tokens = re.findall(r"\b\w+(?:'[a-z]+)?\b|[.,!?;:()\[\]{}\"'-]", translation)
            
            # Limit tokens to prevent rate limiting (max 10 word pairs for audio)
            if len(tokens) > 10:
                logger.info(f"   ⚠️ Limiting word-by-word to first 10 tokens (was {len(tokens)}) to prevent rate limiting")
                tokens = tokens[:10]
            
            logger.info(f"   📝 Processing {len(tokens)} tokens for word-by-word breakdown")
            
            ssml += """
        <voice name="en-US-JennyMultilingualNeural">
            <prosody rate="0.8">"""
            
            # EXACT per requirements: Process each token with format [word] ([Spanish])
            for i, token in enumerate(tokens):
                token = token.strip()
                if not token:
                    continue
                
                # Find Spanish translation using AI (not dictionaries per requirements)
                spanish_translation = self._find_translation_for_phrase(token, mapping, lang_code)
                
                # Clean for speech
                clean_token = token.strip()
                clean_spanish = spanish_translation.replace("[", "").replace("]", "")
                
                # EXACT format per requirements: [target word] ([Spanish equivalent])
                # Reduce breaks to minimize synthesis time
                ssml += f"""
            <lang xml:lang="{lang}">{clean_token}</lang>
            <break time="200ms"/>
            <lang xml:lang="es-ES">{clean_spanish}</lang>
            <break time="400ms"/>"""
                
                # Log the word-by-word pair
                if clean_token and clean_token not in ".,!?;:()[]{}\"'-":
                    logger.debug(f"   {i+1:2d}. [{clean_token}] ([{clean_spanish}])")
            
            ssml += """
            <break time="600ms"/>
            </prosody>
        </voice>"""
        
        ssml += "</speak>"
        
        logger.info(f"✅ Generated word-by-word breakdown SSML per EXACT requirements")
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
                'is_spanish': source_lang == 'spanish',
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
        """Convert SSML to speech with retry logic"""
        try:
            if not output_path:
                temp_dir = self._get_temp_directory()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(temp_dir, f"speech_{timestamp}.mp3")

            success = await self._synthesize_with_retry(ssml, output_path)
            return os.path.basename(output_path) if success else None

        except Exception as e:
            logger.error(f"❌ Exception in text_to_speech: {str(e)}")
            return None