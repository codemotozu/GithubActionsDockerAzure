# tts_service.py - FIXED SSML generation for Azure Speech Services

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

    def _clean_text_for_ssml(self, text: str) -> str:
        """Clean text for SSML compliance"""
        # Replace problematic characters
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&apos;")
        
        # Remove any existing SSML tags to prevent conflicts
        text = re.sub(r'<[^>]+>', '', text)
        
        # Ensure text is not empty
        if not text.strip():
            text = "Translation content"
            
        return text.strip()

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
                        elif "1007" in error_details or "should not contain" in error_details:
                            # SSML validation error - don't retry
                            logger.error(f"❌ SSML validation error: {error_details}")
                            return False
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

    async def text_to_speech_multiple_styles_v3(
        self,
        translations_data: Dict,
        source_lang: str,
        target_lang: str,
        style_preferences=None,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate TTS for MULTIPLE translation styles with comprehensive audio.
        Handles both complete sentences and word-by-word breakdown based on user preferences.
        """
        try:
            if not output_path:
                temp_dir = self._get_temp_directory()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(temp_dir, f"multiple_styles_speech_{timestamp}.mp3")

            logger.info(f"🌐 Generating MULTIPLE STYLES audio for source language: {source_lang}")
            
            # Check what audio modes to use
            german_word_by_word = getattr(style_preferences, 'german_word_by_word', False)
            english_word_by_word = getattr(style_preferences, 'english_word_by_word', False)
            
            logger.info(f"🔍 MULTIPLE STYLES audio generation mode:")
            logger.info(f"   German word-by-word audio: {german_word_by_word}")
            logger.info(f"   English word-by-word audio: {english_word_by_word}")
            logger.info(f"   Style data available: {len(translations_data.get('style_data', []))}")
            
            # Generate comprehensive SSML for all styles
            ssml = self._generate_multiple_styles_ssml_fixed(translations_data, style_preferences)
            
            if not ssml or len(ssml.strip()) < 50:
                logger.warning("⚠️ Generated SSML is too short or empty")
                return None
            
            # Validate SSML structure before sending
            if not self._validate_ssml_structure(ssml):
                logger.error("❌ SSML validation failed - structure issues detected")
                return None
            
            # Log SSML for debugging
            logger.info(f"📝 Generated MULTIPLE STYLES SSML ({len(ssml)} characters):")
            logger.info(f"   Preview: {ssml[:300]}...")
            
            # Use retry logic for synthesis
            success = await self._synthesize_with_retry(ssml, output_path, max_retries=3)
            
            if success:
                logger.info(f"✅ MULTIPLE STYLES audio generated successfully: {os.path.basename(output_path)}")
                return os.path.basename(output_path)
            else:
                logger.error("❌ Failed to generate multiple styles audio after all retry attempts")
                return None

        except Exception as e:
            logger.error(f"❌ Error in text_to_speech_multiple_styles_v3: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _validate_ssml_structure(self, ssml: str) -> bool:
        """Validate SSML structure to prevent Azure Speech errors"""
        try:
            # Check for breaks outside voice elements
            lines = ssml.split('\n')
            inside_speak = False
            inside_voice = False
            
            for line in lines:
                line = line.strip()
                
                if '<speak' in line:
                    inside_speak = True
                elif '</speak>' in line:
                    inside_speak = False
                elif '<voice' in line:
                    inside_voice = True
                elif '</voice>' in line:
                    inside_voice = False
                elif '<break' in line:
                    if inside_speak and not inside_voice:
                        logger.error(f"❌ SSML Validation Error: Break element outside voice: {line}")
                        return False
            
            # Check for required elements
            if '<speak' not in ssml:
                logger.error("❌ SSML Validation Error: Missing speak element")
                return False
                
            if '<voice' not in ssml:
                logger.error("❌ SSML Validation Error: Missing voice element")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ SSML validation error: {str(e)}")
            return False

    def _generate_multiple_styles_ssml_fixed(self, translations_data: Dict, style_preferences=None) -> str:
        """Generate FIXED SSML for MULTIPLE translation styles - Azure Speech compliant"""
        
        logger.info("🎤 GENERATING MULTIPLE STYLES AUDIO (FIXED SSML)")
        logger.info("="*60)
        
        # Group translations by language
        german_translations = []
        english_translations = []
        spanish_translations = []
        
        for style_info in translations_data.get('style_data', []):
            translation_text = style_info.get('translation', '')
            display_name = style_info.get('display_name', style_info.get('style_name', 'Unknown'))
            word_pairs = style_info.get('word_pairs', [])
            is_german = style_info.get('is_german', False)
            is_spanish = style_info.get('is_spanish', False)
            
            if translation_text and len(translation_text.strip()) > 5:
                if is_german:
                    german_translations.append({
                        'text': translation_text,
                        'display_name': display_name,
                        'word_pairs': word_pairs
                    })
                elif is_spanish:
                    spanish_translations.append({
                        'text': translation_text,
                        'display_name': display_name,
                        'word_pairs': word_pairs
                    })
                else:
                    english_translations.append({
                        'text': translation_text,
                        'display_name': display_name,
                        'word_pairs': word_pairs
                    })
        
        # Start SSML with proper structure - NO breaks outside voice elements
        ssml = '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">'
        
        # Add initial pause inside first voice element
        ssml += '''
        <voice name="en-US-JennyMultilingualNeural">
            <prosody rate="0.9">
                <break time="500ms"/>
            </prosody>
        </voice>'''
        
        # Process German translations
        if german_translations:
            logger.info(f"🇩🇪 Processing {len(german_translations)} German translation styles")
            
            for translation in german_translations:
                display_name = translation['display_name']
                text = translation['text']
                word_pairs = translation['word_pairs']
                
                logger.info(f"   📖 {display_name}: {text[:50]}...")
                
                # Clean text for SSML
                clean_text = self._clean_text_for_ssml(text)
                
                # Add style introduction and complete sentence - ALL breaks inside voice elements
                ssml += f'''
        <voice name="en-US-JennyMultilingualNeural">
            <prosody rate="0.9">
                <break time="300ms"/>
            </prosody>
        </voice>
        <voice name="de-DE-SeraphinaMultilingualNeural">
            <prosody rate="1.0">
                <lang xml:lang="de-DE">{clean_text}</lang>
                <break time="800ms"/>
            </prosody>
        </voice>'''
                
                # Add word-by-word breakdown if requested and available
                if getattr(style_preferences, 'german_word_by_word', False) and word_pairs:
                    logger.info(f"   🎵 Adding word-by-word for {display_name}: {len(word_pairs)} pairs")
                    
                    # Pre-process word pairs to ensure they're clean
                    clean_pairs = []
                    for source, spanish in word_pairs:
                        clean_source = self._clean_text_for_ssml(str(source))
                        clean_spanish = self._clean_text_for_ssml(str(spanish))
                        if clean_source and clean_spanish:
                            clean_pairs.append((clean_source, clean_spanish))
                    
                    if clean_pairs:
                        ssml += '''
        <voice name="en-US-JennyMultilingualNeural">
            <prosody rate="0.9">
                <break time="400ms"/>
            </prosody>
        </voice>'''
                        
                        for clean_source, clean_spanish in clean_pairs:
                            ssml += f'''
        <voice name="en-US-JennyMultilingualNeural">
            <prosody rate="0.8">
                <lang xml:lang="de-DE">{clean_source}</lang>
                <break time="200ms"/>
                <lang xml:lang="es-ES">{clean_spanish}</lang>
                <break time="400ms"/>
            </prosody>
        </voice>'''
        
        # Process English translations
        if english_translations:
            logger.info(f"🇺🇸 Processing {len(english_translations)} English translation styles")
            
            for translation in english_translations:
                display_name = translation['display_name']
                text = translation['text']
                word_pairs = translation['word_pairs']
                
                logger.info(f"   📖 {display_name}: {text[:50]}...")
                
                # Clean text for SSML
                clean_text = self._clean_text_for_ssml(text)
                
                # Add style introduction and complete sentence
                ssml += f'''
        <voice name="en-US-JennyMultilingualNeural">
            <prosody rate="0.9">
                <break time="300ms"/>
            </prosody>
        </voice>
        <voice name="en-US-JennyMultilingualNeural">
            <prosody rate="1.0">
                <lang xml:lang="en-US">{clean_text}</lang>
                <break time="800ms"/>
            </prosody>
        </voice>'''
                
                # Add word-by-word breakdown if requested and available
                if getattr(style_preferences, 'english_word_by_word', False) and word_pairs:
                    logger.info(f"   🎵 Adding word-by-word for {display_name}: {len(word_pairs)} pairs")
                    
                    # Pre-process word pairs to ensure they're clean
                    clean_pairs = []
                    for source, spanish in word_pairs:
                        clean_source = self._clean_text_for_ssml(str(source))
                        clean_spanish = self._clean_text_for_ssml(str(spanish))
                        if clean_source and clean_spanish:
                            clean_pairs.append((clean_source, clean_spanish))
                    
                    if clean_pairs:
                        ssml += '''
        <voice name="en-US-JennyMultilingualNeural">
            <prosody rate="0.9">
                <break time="400ms"/>
            </prosody>
        </voice>'''
                        
                        for clean_source, clean_spanish in clean_pairs:
                            ssml += f'''
        <voice name="en-US-JennyMultilingualNeural">
            <prosody rate="0.8">
                <lang xml:lang="en-US">{clean_source}</lang>
                <break time="200ms"/>
                <lang xml:lang="es-ES">{clean_spanish}</lang>
                <break time="400ms"/>
            </prosody>
        </voice>'''
        
        # Process Spanish translations (if any)
        if spanish_translations:
            logger.info(f"🇪🇸 Processing {len(spanish_translations)} Spanish translation styles")
            
            for translation in spanish_translations:
                display_name = translation['display_name']
                text = translation['text']
                
                logger.info(f"   📖 {display_name}: {text[:50]}...")
                
                # Clean text for SSML
                clean_text = self._clean_text_for_ssml(text)
                
                ssml += f'''
        <voice name="es-ES-ArabellaMultilingualNeural">
            <prosody rate="1.0">
                <lang xml:lang="es-ES">{clean_text}</lang>
                <break time="800ms"/>
            </prosody>
        </voice>'''
        
        # Final pause inside voice element, then close
        ssml += '''
        <voice name="en-US-JennyMultilingualNeural">
            <prosody rate="0.9">
                <break time="500ms"/>
            </prosody>
        </voice>
        </speak>'''
        
        total_translations = len(german_translations) + len(english_translations) + len(spanish_translations)
        logger.info(f"✅ Generated FIXED MULTIPLE STYLES SSML for {total_translations} translation styles")
        
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

    # Keep existing methods for backwards compatibility
    async def text_to_speech_word_pairs_v2(
        self,
        translations_data: Dict,
        source_lang: str,
        target_lang: str,
        style_preferences=None,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Legacy method - redirects to new multiple styles method
        """
        logger.info("🔄 Redirecting to new multiple styles TTS method")
        return await self.text_to_speech_multiple_styles_v3(
            translations_data, source_lang, target_lang, style_preferences, output_path
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

            # Validate SSML before attempting synthesis
            if not self._validate_ssml_structure(ssml):
                logger.error("❌ SSML validation failed")
                return None

            success = await self._synthesize_with_retry(ssml, output_path)
            return os.path.basename(output_path) if success else None

        except Exception as e:
            logger.error(f"❌ Exception in text_to_speech: {str(e)}")
            return None