



# tts_service.py - Fixed SSML structure for Azure Speech Services

from azure.cognitiveservices.speech import (
    SpeechConfig,
    SpeechSynthesizer,
    SpeechSynthesisOutputFormat,
    ResultReason,
    CancellationReason,
    PropertyId,
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
        
        logger.info(f"🔧 Initializing TTS service with Azure region: {self.region}")
        logger.info(f"🔑 Azure Speech Key configured with length: {len(self.subscription_key) if self.subscription_key else 0} characters")


        # Rate limiter to prevent 429 errors
        self.rate_limiter = RateLimiter(max_requests_per_minute=12, max_requests_per_second=1)

        # Speech configuration
        self.speech_config = SpeechConfig(
            subscription=self.subscription_key,
            region=self.region
        )

        # Set extended properties for better resilience
        self.speech_config.set_property(
            property_id=PropertyId.Speech_SegmentationSilenceTimeoutMs, 
            value="5000"
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

        # Initialize voice failure tracking
        self._voice_failure_count = {}

        logger.info("✅ TTS service initialized successfully")

    def _get_temp_directory(self) -> str:
        """Create and return the temporary directory path with proper permissions"""
        if os.name == "nt":  # Windows
            temp_dir = os.path.join(os.environ.get("TEMP", ""), "tts_audio")
        else:  # Unix/Linux
            temp_dir = "/tmp/tts_audio"
        
        try:
            # Create directory with proper permissions
            os.makedirs(temp_dir, exist_ok=True)
            
            # Set proper permissions on Unix/Linux
            if os.name != "nt":
                os.chmod(temp_dir, 0o755)
                
            # Verify write permissions with a test file
            test_file = os.path.join(temp_dir, f"test_{int(time.time())}.txt")
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            
            logger.info(f"✅ Audio directory ready: {temp_dir}")
        except Exception as e:
            logger.warning(f"⚠️ Audio directory setup issue: {str(e)}")
            # Fallback to system temp directory
            temp_dir = tempfile.gettempdir()
            logger.info(f"🔄 Using fallback temp directory: {temp_dir}")
        
        return temp_dir

    async def _synthesize_with_retry(self, ssml: str, output_path: str, max_retries: int = 3) -> bool:
        """Synthesize speech with enhanced retry logic and HTTP platform error handling"""
        synthesizer = None
        
        for attempt in range(max_retries):
            try:
                # Apply rate limiting before each attempt
                await self.rate_limiter.wait_if_needed()
                
                # Add delay between attempts (increasing with each retry)
                if attempt > 0:
                    delay = (2 ** attempt) + random.uniform(0.1, 0.5)
                    logger.info(f"🔄 Retry delay: waiting {delay:.2f}s before attempt {attempt + 1}")
                    await asyncio.sleep(delay)
                
                # Explicitly clean up previous synthesizer if it exists
                if synthesizer:
                    try:
                        del synthesizer
                        synthesizer = None
                        # Force garbage collection to ensure resources are released
                        import gc
                        gc.collect()
                        await asyncio.sleep(0.5)  # Short delay to ensure cleanup
                    except Exception as cleanup_error:
                        logger.warning(f"⚠️ Cleanup error (non-critical): {str(cleanup_error)}")
                
                # Create fresh speech config for each attempt
                speech_config = SpeechConfig(
                    subscription=self.subscription_key, region=self.region
                )
                speech_config.set_speech_synthesis_output_format(
                    SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
                )
                
                # Configure connection settings explicitly
                speech_config.set_property(
                    property_id=PropertyId.Speech_SegmentationSilenceTimeoutMs,
                    value="5000"
                )
                
                # Create audio config
                audio_config = AudioOutputConfig(filename=output_path)
                
                # Create synthesizer with explicit cleanup
                logger.info(f"🎤 Creating new synthesizer instance (attempt {attempt + 1}/{max_retries})")
                synthesizer = SpeechSynthesizer(
                    speech_config=speech_config, audio_config=audio_config
                )

                logger.info(f"🔍 Attempting speech synthesis (attempt {attempt + 1}/{max_retries})")
                
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
                        
                        # Handle specific HTTP platform errors
                        if "HTTP platform" in error_details or "Error: 27" in error_details:
                            logger.warning("🔄 HTTP platform initialization error - will retry with new configuration")
                            # Force cleanup before retry
                            if synthesizer:
                                del synthesizer
                                synthesizer = None
                                import gc
                                gc.collect()
                            # Longer delay for HTTP platform errors
                            await asyncio.sleep(3)
                            continue
                            
                        # Handle rate limiting errors
                        elif "429" in error_details or "Too many requests" in error_details:
                            # Exponential backoff for rate limiting
                            base_delay = 5 ** attempt
                            jitter = random.uniform(0.1, 0.5)
                            delay = base_delay + jitter
                            
                            logger.info(f"🔄 Rate limit hit, retrying in {delay:.2f}s...")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            # Other errors - attempt retry with increasing delay
                            delay = 2 + random.uniform(0.1, 0.3) * attempt
                            logger.info(f"🔄 Other error, retrying in {delay:.2f}s...")
                            await asyncio.sleep(delay)
                            continue
                    else:
                        logger.error(f"❌ Synthesis canceled: {cancellation_details.reason}")
                        return False
                else:
                    logger.error(f"❌ Synthesis failed with reason: {result.reason}")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Exception during synthesis attempt {attempt + 1}: {str(e)}")
                # Clean up resources on exception
                if synthesizer:
                    try:
                        del synthesizer
                        synthesizer = None
                    except Exception:
                        pass
                    
                if attempt < max_retries - 1:
                    delay = (3 ** attempt) + random.uniform(0.1, 0.5)
                    logger.info(f"🔄 Exception recovery: retrying in {delay:.2f}s...")
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
        Generate TTS with MULTI-STYLE support and robust error handling.
        """
        try:
            if not output_path:
                temp_dir = self._get_temp_directory()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(temp_dir, f"multi_style_{timestamp}.mp3")

            logger.info(f"🌐 Generating MULTI-STYLE audio for source language: {source_lang}")
            
            # Check what audio mode to use
            german_word_by_word = getattr(style_preferences, 'german_word_by_word', False)
            english_word_by_word = getattr(style_preferences, 'english_word_by_word', False)
            any_word_by_word_requested = german_word_by_word or english_word_by_word
            
            # Count number of styles
            style_count = len(translations_data.get('style_data', []))
            
            logger.info(f"🔍 MULTI-STYLE audio generation mode:")
            logger.info(f"   Number of styles: {style_count}")
            logger.info(f"   German word-by-word requested: {german_word_by_word}")
            logger.info(f"   English word-by-word requested: {english_word_by_word}")
            
            # Check if we have word-by-word data
            has_word_by_word_data = False
            total_word_pairs = 0
            
            for style_info in translations_data.get('style_data', []):
                word_pairs = style_info.get('word_pairs', [])
                if word_pairs and len(word_pairs) > 0:
                    has_word_by_word_data = True
                    total_word_pairs += len(word_pairs)
                    logger.info(f"   Style '{style_info.get('style_name', 'unknown')}': {len(word_pairs)} word pairs")
            
            # Generate SSML based on what data we have
            if style_count > 1:
                # MULTI-STYLE MODE
                logger.info(f"🎵 Generating MULTI-STYLE audio for {style_count} styles")
                if any_word_by_word_requested and has_word_by_word_data:
                    ssml = self._generate_word_by_word_ssml_multi_style(translations_data, style_preferences)
                else:
                    ssml = self._generate_simple_translation_ssml_multi_style(translations_data, style_preferences)
            else:
                # SINGLE STYLE MODE (backward compatibility)
                if any_word_by_word_requested and has_word_by_word_data:
                    logger.info("🎵 Generating single-style word-by-word audio")
                    ssml = self._generate_word_by_word_ssml(translations_data, style_preferences)
                else:
                    logger.info("🎵 Generating single-style simple translation audio")
                    ssml = self._generate_simple_translation_ssml(translations_data, style_preferences)
            
            if not ssml or len(ssml.strip()) < 50:
                logger.warning("⚠️ Generated SSML is too short or empty")
                return None
            
            # Log SSML for debugging
            logger.info(f"📝 Generated MULTI-STYLE SSML ({len(ssml)} characters):")
            logger.info(f"   Preview: {ssml[:200]}...")
            
            # Use retry logic for synthesis
            success = await self._synthesize_with_retry(ssml, output_path, max_retries=3)
            
            if success:
                logger.info(f"✅ MULTI-STYLE audio generated successfully: {os.path.basename(output_path)}")
                return os.path.basename(output_path)
            else:
                logger.error("❌ Failed to generate multi-style audio after all retry attempts")
                return None

        except Exception as e:
            logger.error(f"❌ Error in text_to_speech_word_pairs_v2: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _generate_word_by_word_ssml_multi_style(self, translations_data: Dict, style_preferences=None) -> str:
        """Generate word-by-word SSML for MULTIPLE selected styles with FIXED structure."""
        # Start with proper SSML root - NO breaks at root level
        ssml = '''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">'''
        
        logger.info("🎤 GENERATING MULTI-STYLE WORD-BY-WORD AUDIO")
        logger.info("="*50)
        
        # Process each style that has word-by-word data
        styles_with_audio = []
        
        for style_info in translations_data.get('style_data', []):
            word_pairs = style_info.get('word_pairs', [])
            is_german = style_info.get('is_german', False)
            is_spanish = style_info.get('is_spanish', False)
            style_name = style_info.get('style_name', 'unknown')
            translation_text = style_info.get('translation', '')
            
            # Check if this language/style should be included
            should_include = False
            if is_german and style_preferences.german_word_by_word:
                should_include = True
            elif not is_german and not is_spanish and style_preferences.english_word_by_word:
                should_include = True
            
            if should_include:
                language = 'german' if is_german else 'english'
                voice_config = self._get_voice_config(language)
                
                # Add style announcement - ALL breaks must be inside voice elements
                ssml += f'''
    <voice name="en-US-JennyMultilingualNeural">
        <prosody rate="0.95">
            <break time="500ms"/>
            {self._escape_xml(style_name.replace('_', ' ').title())}:
            <break time="300ms"/>
        </prosody>
    </voice>'''
                
                # First read the full translation
                ssml += f'''
    <voice name="{voice_config['voice']}">
        <prosody rate="1.0">
            <lang xml:lang="{voice_config['language']}">{self._escape_xml(translation_text)}</lang>
            <break time="600ms"/>
        </prosody>
    </voice>'''
                
                # Then add word-by-word if available
                if word_pairs:
                    logger.info(f"🎤 {style_name}: {len(word_pairs)} pairs with voice {voice_config['voice']}")
                    
                    # Add word-by-word announcement
                    ssml += f'''
    <voice name="en-US-JennyMultilingualNeural">
        <prosody rate="0.9">
            <break time="300ms"/>
            Word by word:
            <break time="300ms"/>
        </prosody>
    </voice>'''
                    
                    # Add word-by-word pairs - ALL in one voice block
                    ssml += f'''
    <voice name="en-US-JennyMultilingualNeural">
        <prosody rate="0.9">'''
                    
                    for source, spanish in word_pairs:
                        logger.info(f"   🎵 {source} → {spanish}")
                        
                        # Escape XML and add the word pair
                        source_clean = self._escape_xml(source)
                        spanish_clean = self._escape_xml(spanish)
                        
                        ssml += f'''
            <lang xml:lang="{voice_config['language']}">{source_clean}</lang>
            <break time="200ms"/>
            <lang xml:lang="es-ES">{spanish_clean}</lang>
            <break time="400ms"/>'''
                    
                    # Close the word-by-word voice block
                    ssml += '''
            <break time="600ms"/>
        </prosody>
    </voice>'''
                    
                    styles_with_audio.append(style_name)
                    
                # Add section break between styles - inside a voice element
                ssml += '''
    <voice name="en-US-JennyMultilingualNeural">
        <prosody rate="1.0">
            <break time="800ms"/>
        </prosody>
    </voice>'''
        
        # Close the SSML properly
        ssml += '''
</speak>'''
        
        logger.info(f"✅ Generated multi-style word-by-word SSML for {len(styles_with_audio)} styles")
        return ssml

    def _generate_simple_translation_ssml_multi_style(self, translations_data: Dict, style_preferences=None) -> str:
        """Generate simple SSML for multiple styles with FIXED structure."""
        ssml = '''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">'''
        
        logger.info("🎤 GENERATING MULTI-STYLE SIMPLE TRANSLATION AUDIO")
        logger.info("="*40)
        
        styles_processed = 0
        
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
                
                # Get voice configuration
                voice_config = self._get_voice_config(language)
                voice = voice_config['voice']
                lang_code = voice_config['language']
                
                logger.info(f"📖 {style_name}: {translation_text[:50]}...")
                
                # Add style announcement
                ssml += f'''
    <voice name="en-US-JennyMultilingualNeural">
        <prosody rate="0.95">
            <break time="400ms"/>
            {self._escape_xml(style_name.replace('_', ' ').title())}:
            <break time="300ms"/>
        </prosody>
    </voice>'''
                
                # Add translation
                ssml += f'''
    <voice name="{voice}">
        <prosody rate="1.0">
            <lang xml:lang="{lang_code}">{self._escape_xml(translation_text)}</lang>
            <break time="800ms"/>
        </prosody>
    </voice>'''
                
                styles_processed += 1
        
        ssml += '''
</speak>'''
        
        logger.info(f"✅ Generated multi-style simple SSML for {styles_processed} styles")
        return ssml

    def _generate_word_by_word_ssml(self, translations_data: Dict, style_preferences=None) -> str:
        """Generate SSML for word-by-word audio (single style - backward compatibility) with FIXED structure"""
        # Check if we have multiple styles
        style_count = len(translations_data.get('style_data', []))
        
        if style_count > 1:
            # Use multi-style generation
            return self._generate_word_by_word_ssml_multi_style(translations_data, style_preferences)
        
        # Original single-style logic with fixed SSML structure
        ssml = '''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">'''
        
        logger.info("🎤 GENERATING WORD-BY-WORD AUDIO (Single Style)")
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
        
        # Generate SSML for each language - ALL breaks inside voice elements
        for language, pairs in by_language.items():
            if not pairs:
                continue
            
            voice_config = self._get_voice_config(language)
            voice = voice_config['voice']
            lang_code = voice_config['language']
            
            logger.info(f"🎤 {language.title()}: {len(pairs)} pairs with voice {voice}")
            
            # Add language section introduction
            ssml += f'''
    <voice name="en-US-JennyMultilingualNeural">
        <prosody rate="0.9">
            <break time="300ms"/>
        </prosody>
    </voice>'''
            
            # Add word-by-word pairs - all in one voice block
            ssml += f'''
    <voice name="en-US-JennyMultilingualNeural">
        <prosody rate="0.9">'''
            
            for pair in pairs:
                source = self._escape_xml(pair['source'])
                spanish = self._escape_xml(pair['spanish'])
                
                logger.info(f"   🎵 {pair['source']} → {pair['spanish']}")
                
                # Speak the target language word, then Spanish equivalent
                ssml += f'''
            <lang xml:lang="{lang_code}">{source}</lang>
            <break time="200ms"/>
            <lang xml:lang="es-ES">{spanish}</lang>
            <break time="400ms"/>'''
            
            ssml += '''
            <break time="600ms"/>
        </prosody>
    </voice>'''
        
        ssml += '''
</speak>'''
        
        logger.info(f"✅ Generated word-by-word SSML with {len(all_word_pairs)} pairs")
        return ssml

    def _generate_simple_translation_ssml(self, translations_data: Dict, style_preferences=None) -> str:
        """Generate simple SSML that just reads translations with FIXED structure."""
        # Check if we have multiple styles
        style_count = len(translations_data.get('style_data', []))
        
        if style_count > 1:
            # Use multi-style generation
            return self._generate_simple_translation_ssml_multi_style(translations_data, style_preferences)
        
        # Original single-style logic with fixed structure
        ssml = '''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">'''
        
        logger.info("🎤 GENERATING SIMPLE TRANSLATION AUDIO (Single Style)")
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
            text = self._escape_xml(trans['text'])
            language = trans['language']
            
            # Get voice configuration
            voice_config = self._get_voice_config(language)
            voice = voice_config['voice']
            lang_code = voice_config['language']
            
            logger.info(f"🎤 Reading {language} with voice {voice}")
            
            # Add to SSML
            ssml += f'''
    <voice name="{voice}">
        <prosody rate="1.0">
            <lang xml:lang="{lang_code}">{text}</lang>
            <break time="800ms"/>
        </prosody>
    </voice>'''
        
        ssml += '''
</speak>'''
        
        logger.info(f"✅ Generated simple SSML for {len(translations)} translations")
        return ssml

    def _generate_fallback_ssml(self, translations_data: Dict) -> str:
        """Generate fallback SSML when normal generation fails with FIXED structure"""
        logger.info("🔄 Generating fallback SSML")
        
        ssml = '''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
    <voice name="en-US-JennyMultilingualNeural">
        <prosody rate="1.0">
            Translation completed. Please check the text for results.
            <break time="500ms"/>
        </prosody>
    </voice>
</speak>'''
        
        return ssml

    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters in text"""
        if not text:
            return ""
        
        # Replace XML special characters
        text = str(text)
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&apos;")
        
        return text

    def _get_voice_config(self, language_code: str) -> dict:
        """Get voice configuration with fallback options"""
        lang_map = {
            'spanish': 'es',
            'english': 'en', 
            'german': 'de',
        }
        
        if language_code in lang_map:
            code = lang_map[language_code]
        else:
            code = language_code
        
        config = self.voice_mapping.get(code, self.voice_mapping['en'])
        
        # Check if we've had failures with this voice
        # If this is a retry attempt, use a simpler voice
        if hasattr(self, '_voice_failure_count') and self._voice_failure_count.get(config['voice'], 0) > 0:
            fallback_voice = self._get_fallback_voice(config['language'])
            if fallback_voice:
                logger.info(f"🔄 Using fallback voice {fallback_voice} instead of {config['voice']}")
                config = config.copy()  # Create a copy to avoid modifying the original
                config['voice'] = fallback_voice
        
        return config

    def _get_fallback_voice(self, language_code: str) -> str:
        """Get a fallback voice for a specific language"""
        fallbacks = {
            "es-ES": ["es-ES-AlvaroNeural", "es-ES-HelenaNeural"],
            "en-US": ["en-US-GuyNeural", "en-US-AriaNeural"],
            "de-DE": ["de-DE-ConradNeural", "de-DE-LouisaNeural"]
        }
        
        if language_code in fallbacks:
            return fallbacks[language_code][0]
        
        return None
        
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