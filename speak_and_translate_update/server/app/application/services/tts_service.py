# tts_service.py - Fixed for reliable audio generation

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

        # Speech configuration
        self.speech_config = SpeechConfig(
            subscription=self.subscription_key,
            region=self.region
        )
        self.speech_config.set_speech_synthesis_output_format(
            SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
        )

        # Voice mapping
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
        }

    def _get_temp_directory(self) -> str:
        """Create and return the temporary directory path"""
        if os.name == "nt":  # Windows
            temp_dir = os.path.join(os.environ.get("TEMP", ""), "tts_audio")
        else:  # Unix/Linux
            temp_dir = "/tmp/tts_audio"
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    async def _synthesize_with_retry(self, ssml: str, output_path: str, max_retries: int = 3) -> bool:
        """Synthesize speech with retry logic and exponential backoff"""
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
        Generate TTS with ROBUST error handling and fallback modes.
        """
        try:
            if not output_path:
                temp_dir = self._get_temp_directory()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(temp_dir, f"speech_{timestamp}.mp3")

            logger.info(f"🌐 Generating audio for source language: {source_lang}")
            
            # Check what audio mode to use
            german_word_by_word = getattr(style_preferences, 'german_word_by_word', False)
            english_word_by_word = getattr(style_preferences, 'english_word_by_word', False)
            any_word_by_word_requested = german_word_by_word or english_word_by_word
            
            logger.info(f"🔍 Audio generation mode:")
            logger.info(f"   German word-by-word requested: {german_word_by_word}")
            logger.info(f"   English word-by-word requested: {english_word_by_word}")
            logger.info(f"   Style data available: {len(translations_data.get('style_data', []))}")
            
            # Check if we have word-by-word data
            has_word_by_word_data = False
            word_by_word_pairs = []
            
            for style_info in translations_data.get('style_data', []):
                word_pairs = style_info.get('word_pairs', [])
                if word_pairs and len(word_pairs) > 0:
                    has_word_by_word_data = True
                    word_by_word_pairs.extend(word_pairs)
                    logger.info(f"   Found {len(word_pairs)} word pairs in {style_info.get('style_name', 'unknown')}")
            
            # Generate SSML based on what data we have
            if any_word_by_word_requested and has_word_by_word_data:
                logger.info("🎵 Generating word-by-word audio")
                ssml = self._generate_word_by_word_ssml(translations_data, style_preferences)
            else:
                logger.info("🎵 Generating simple translation audio")
                ssml = self._generate_simple_translation_ssml(translations_data, style_preferences)
            
            if not ssml or len(ssml.strip()) < 50:
                logger.warning("⚠️ Generated SSML is too short or empty")
                return None
            
            # Log SSML for debugging
            logger.info(f"📝 Generated SSML ({len(ssml)} characters):")
            logger.info(f"   Preview: {ssml[:200]}...")
            
            # Use retry logic for synthesis
            success = await self._synthesize_with_retry(ssml, output_path, max_retries=3)
            
            if success:
                logger.info(f"✅ Audio generated successfully: {os.path.basename(output_path)}")
                return os.path.basename(output_path)
            else:
                logger.error("❌ Failed to generate audio after all retry attempts")
                return None

        except Exception as e:
            logger.error(f"❌ Error in text_to_speech_word_pairs_v2: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _generate_word_by_word_ssml(self, translations_data: Dict, style_preferences=None) -> str:
        """Generate SSML for word-by-word audio"""
        ssml = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">"""
        
        logger.info("🎤 GENERATING WORD-BY-WORD AUDIO")
        logger.info("="*50)
        
        # Collect all word pairs from all styles
        all_word_pairs = []
        
        for style_info in translations_data.get('style_data', []):
            word_pairs = style_info.get('word_pairs', [])
            is_german = style_info.get('is_german', False)
            is_spanish = style_info.get('is_spanish', False)
            style_name = style_info.get('style_name', 'unknown')
            
            # Check if this language should be included
            should_include = False
            if is_german and getattr(style_preferences, 'german_word_by_word', False):
                should_include = True
            elif not is_german and not is_spanish and getattr(style_preferences, 'english_word_by_word', False):
                should_include = True
            
            if should_include and word_pairs:
                language = 'german' if is_german else 'english'
                logger.info(f"📝 Including {len(word_pairs)} pairs from {style_name} ({language})")
                
                for i, (source, spanish) in enumerate(word_pairs):
                    all_word_pairs.append({
                        'source': source,
                        'spanish': spanish,
                        'language': language,
                        'order': i
                    })
        
        if not all_word_pairs:
            logger.warning("⚠️ No word pairs found for audio generation")
            return self._generate_fallback_ssml(translations_data)
        
        logger.info(f"🎵 Generating audio for {len(all_word_pairs)} word pairs")
        
        # Group by language for better audio flow
        by_language = {}
        for pair in all_word_pairs:
            lang = pair['language']
            if lang not in by_language:
                by_language[lang] = []
            by_language[lang].append(pair)
        
        # Generate SSML for each language
        for language, pairs in by_language.items():
            if not pairs:
                continue
            
            voice_config = self._get_voice_config(language)
            voice = voice_config['voice']
            lang_code = voice_config['language']
            
            logger.info(f"🎤 {language.title()}: {len(pairs)} pairs with voice {voice}")
            
            # Add language section with introduction
            ssml += f"""
        <voice name="en-US-JennyMultilingualNeural">
            <prosody rate="0.9">
                <break time="300ms"/>
            </prosody>
        </voice>"""
            
            # Add word-by-word pairs
            ssml += f"""
        <voice name="en-US-JennyMultilingualNeural">
            <prosody rate="0.9">"""
            
            for pair in pairs:
                source = pair['source']
                spanish = pair['spanish']
                
                logger.info(f"   🎵 {source} → {spanish}")
                
                # Speak the target language word, then Spanish equivalent
                ssml += f"""
            <lang xml:lang="{lang_code}">{source}</lang>
            <break time="200ms"/>
            <lang xml:lang="es-ES">{spanish}</lang>
            <break time="400ms"/>"""
            
            ssml += """
            <break time="600ms"/>
            </prosody>
        </voice>"""
        
        ssml += "</speak>"
        
        logger.info(f"✅ Generated word-by-word SSML with {len(all_word_pairs)} pairs")
        return ssml

    def _generate_simple_translation_ssml(self, translations_data: Dict, style_preferences=None) -> str:
        """Generate simple SSML that just reads translations."""
        ssml = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">"""
        
        logger.info("🎤 GENERATING SIMPLE TRANSLATION AUDIO")
        logger.info("="*40)
        
        # Get all available translations
        translations = []
        for style_info in translations_data.get('style_data', []):
            translation_text = style_info.get('translation', '')
            if translation_text and len(translation_text.strip()) > 5:
                is_german = style_info.get('is_german', False)
                is_spanish = style_info.get('is_spanish', False)
                style_name = style_info.get('style_name', 'unknown')
                
                # Determine language
                if is_german:
                    language = 'german'
                elif is_spanish:
                    language = 'spanish'
                else:
                    language = 'english'
                
                translations.append({
                    'text': translation_text,
                    'language': language,
                    'style': style_name
                })
                
                logger.info(f"📖 {language.title()}: {translation_text[:50]}...")
        
        # If no translations found, try to get from main translations list
        if not translations:
            main_translations = translations_data.get('translations', [])
            if main_translations:
                for i, text in enumerate(main_translations):
                    if text and len(text.strip()) > 5:
                        translations.append({
                            'text': text,
                            'language': 'english',  # Default
                            'style': f'translation_{i}'
                        })
                        logger.info(f"📖 Fallback translation: {text[:50]}...")
        
        if not translations:
            logger.warning("⚠️ No translations found for audio generation")
            return self._generate_fallback_ssml(translations_data)
        
        # Generate SSML for each translation
        for i, trans in enumerate(translations):
            text = trans['text']
            language = trans['language']
            
            # Escape XML special characters
            text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            # Get voice configuration
            voice_config = self._get_voice_config(language)
            voice = voice_config['voice']
            lang_code = voice_config['language']
            
            logger.info(f"🎤 Reading {language} with voice {voice}")
            
            # Add to SSML
            ssml += f"""
        <voice name="{voice}">
            <prosody rate="1.0">
                <lang xml:lang="{lang_code}">{text}</lang>
                <break time="800ms"/>
            </prosody>
        </voice>"""
        
        ssml += "</speak>"
        
        logger.info(f"✅ Generated simple SSML for {len(translations)} translations")
        return ssml

    def _generate_fallback_ssml(self, translations_data: Dict) -> str:
        """Generate fallback SSML when normal generation fails"""
        logger.info("🔄 Generating fallback SSML")
        
        ssml = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
        <voice name="en-US-JennyMultilingualNeural">
            <prosody rate="1.0">
                Translation completed. Please check the text for results.
                <break time="500ms"/>
            </prosody>
        </voice>
        </speak>"""
        
        return ssml

    def _get_voice_config(self, language_code: str) -> dict:
        """Get voice configuration for a language"""
        lang_map = {
            'spanish': 'es',
            'english': 'en', 
            'german': 'de',
        }
        
        if language_code in lang_map:
            code = lang_map[language_code]
        else:
            code = language_code
            
        return self.voice_mapping.get(code, self.voice_mapping['en'])

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