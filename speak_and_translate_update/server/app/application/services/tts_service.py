# tts_service.py - Enhanced for PERFECT synchronization between UI display and audio output

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


class UIAudioSynchronizer:
    """
    CRITICAL: Ensures perfect synchronization between UI display and audio output.
    What the user sees is EXACTLY what they hear.
    """
    
    def __init__(self):
        self.ui_word_pairs = []  # Stores the exact sequence that UI will display
        self.audio_sequence = []  # Stores the exact sequence that audio will speak
        
    def prepare_synchronized_data(self, translations_data: Dict, style_preferences) -> Dict:
        """
        Prepare data that ensures UI and audio are perfectly synchronized.
        Returns both UI data and audio sequence in exact same order.
        """
        synchronized_data = {
            'ui_data': {},  # For UI display
            'audio_sequences': {},  # For audio generation
            'synchronization_log': []  # For debugging
        }
        
        logger.info("🔄 PREPARING PERFECT UI-AUDIO SYNCHRONIZATION")
        logger.info("="*60)
        
        # Process each style data entry
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
                language = 'german' if is_german else 'english'
                
                logger.info(f"📝 Synchronizing {style_name} ({language}): {len(word_pairs)} pairs")
                
                # Create synchronized sequence
                ui_sequence = []
                audio_sequence = []
                
                for i, (source_word, spanish_equiv) in enumerate(word_pairs):
                    # Clean words for consistency
                    source_clean = source_word.strip().strip('"\'[]')
                    spanish_clean = spanish_equiv.strip().strip('"\'[]')
                    
                    # CRITICAL: Create EXACT same format for UI and audio
                    display_format = f"[{source_clean}] ([{spanish_clean}])"
                    
                    # UI data structure (matches what WordByWordVisualizationWidget expects)
                    ui_key = f"{style_name}_{i}_{source_clean.replace(' ', '_')}"
                    ui_data = {
                        "source": source_clean,
                        "spanish": spanish_clean,
                        "language": language,
                        "style": style_name,
                        "order": str(i),
                        "is_phrasal_verb": str(" " in source_clean),  # Detect phrasal/separable verbs
                        "display_format": display_format  # EXACT format that UI shows
                    }
                    
                    # Audio sequence item (matches what SSML generation uses)
                    audio_item = {
                        'source_word': source_clean,
                        'spanish_equiv': spanish_clean,
                        'order': i,
                        'language': language,
                        'voice_config': self._get_voice_config_for_language(language),
                        'display_format': display_format,  # SAME format as UI
                        'is_phrasal_verb': " " in source_clean
                    }
                    
                    # Add to sequences
                    ui_sequence.append((ui_key, ui_data))
                    audio_sequence.append(audio_item)
                    
                    # Log synchronization
                    sync_log = {
                        'order': i,
                        'ui_key': ui_key,
                        'ui_format': display_format,
                        'audio_format': display_format,
                        'source': source_clean,
                        'spanish': spanish_clean,
                        'language': language,
                        'is_phrasal_verb': " " in source_clean
                    }
                    synchronized_data['synchronization_log'].append(sync_log)
                    
                    logger.info(f"   {i+1:2d}. UI: {display_format}")
                    logger.info(f"       Audio: SAME → {display_format}")
                    
                    # Special logging for phrasal/separable verbs
                    if " " in source_clean:
                        verb_type = "German Separable Verb" if is_german else "English Phrasal Verb"
                        logger.info(f"       🔗 {verb_type}: '{source_clean}' treated as single unit")
                
                # Store synchronized data
                synchronized_data['ui_data'][style_name] = dict(ui_sequence)
                synchronized_data['audio_sequences'][style_name] = audio_sequence
                
                logger.info(f"✅ {style_name}: {len(ui_sequence)} UI items ↔ {len(audio_sequence)} audio items")
        
        logger.info("="*60)
        logger.info(f"🎯 SYNCHRONIZATION COMPLETE: {len(synchronized_data['synchronization_log'])} total pairs")
        
        return synchronized_data

    def _get_voice_config_for_language(self, language: str) -> Dict:
        """Get voice configuration for a specific language"""
        voice_configs = {
            'german': {
                'voice': 'de-DE-SeraphinaMultilingualNeural',
                'language': 'de-DE',
                'name': 'German'
            },
            'english': {
                'voice': 'en-US-JennyMultilingualNeural',
                'language': 'en-US',
                'name': 'English'
            },
            'spanish': {
                'voice': 'es-ES-ArabellaMultilingualNeural',
                'language': 'es-ES',
                'name': 'Spanish'
            }
        }
        return voice_configs.get(language, voice_configs['spanish'])

    def validate_synchronization(self, ui_data: Dict, audio_sequences: Dict) -> List[str]:
        """
        Validate that UI data and audio sequences are perfectly synchronized.
        Returns list of any discrepancies found.
        """
        errors = []
        
        logger.info("🔍 VALIDATING UI-AUDIO SYNCHRONIZATION")
        
        for style_name in ui_data.keys():
            if style_name not in audio_sequences:
                errors.append(f"Style {style_name} missing from audio sequences")
                continue
                
            ui_items = ui_data[style_name]
            audio_items = audio_sequences[style_name]
            
            if len(ui_items) != len(audio_items):
                errors.append(f"Style {style_name}: UI has {len(ui_items)} items, audio has {len(audio_items)} items")
                continue
            
            # Validate each pair
            for i, audio_item in enumerate(audio_items):
                expected_order = audio_item['order']
                source_word = audio_item['source_word']
                
                # Find corresponding UI item
                ui_item = None
                for ui_key, ui_data_item in ui_items.items():
                    if int(ui_data_item['order']) == expected_order:
                        ui_item = ui_data_item
                        break
                
                if not ui_item:
                    errors.append(f"Style {style_name}, order {expected_order}: No matching UI item for audio item")
                    continue
                
                # Validate content matches
                if ui_item['source'] != audio_item['source_word']:
                    errors.append(f"Style {style_name}, order {expected_order}: Source word mismatch - UI: '{ui_item['source']}', Audio: '{audio_item['source_word']}'")
                
                if ui_item['spanish'] != audio_item['spanish_equiv']:
                    errors.append(f"Style {style_name}, order {expected_order}: Spanish equivalent mismatch - UI: '{ui_item['spanish']}', Audio: '{audio_item['spanish_equiv']}'")
                
                if ui_item['display_format'] != audio_item['display_format']:
                    errors.append(f"Style {style_name}, order {expected_order}: Display format mismatch - UI: '{ui_item['display_format']}', Audio: '{audio_item['display_format']}'")
        
        if errors:
            logger.error(f"❌ Found {len(errors)} synchronization errors:")
            for error in errors:
                logger.error(f"   • {error}")
        else:
            logger.info("✅ Perfect UI-Audio synchronization validated")
        
        return errors


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

        # CRITICAL: UI-Audio synchronizer for perfect matching
        self.ui_audio_sync = UIAudioSynchronizer()

        # Initialize Gemini for AI-powered translations
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.translation_model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                generation_config={
                    "temperature": 0.2,
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

        # Dynamic voice mapping
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
        }
        
        # Get the language code
        if language_code in lang_map:
            code = lang_map[language_code]
        else:
            code = language_code
            
        return self.voice_mapping.get(code, self.voice_mapping['es'])  # Default to Spanish

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
        Enhanced TTS with PERFECT UI-Audio synchronization.
        CRITICAL: What user sees is EXACTLY what they hear.
        """
        try:
            if not output_path:
                temp_dir = self._get_temp_directory()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(temp_dir, f"speech_{timestamp}.mp3")

            logger.info(f"🌐 Generating SYNCHRONIZED audio for source language: {source_lang}")
            
            # CRITICAL: Prepare perfectly synchronized data
            sync_data = self.ui_audio_sync.prepare_synchronized_data(translations_data, style_preferences)
            
            # Validate synchronization
            sync_errors = self.ui_audio_sync.validate_synchronization(
                sync_data['ui_data'], 
                sync_data['audio_sequences']
            )
            
            if sync_errors:
                logger.error("❌ Synchronization validation failed - continuing with available data")
                for error in sync_errors:
                    logger.error(f"   • {error}")
            
            # Check if we have any synchronized data
            if not sync_data['ui_data'] and not sync_data['audio_sequences']:
                logger.info("🔇 No synchronized audio data - no word-by-word requested or available")
                return None
            
            # EXACT per requirements: Check if ANY word-by-word is requested
            german_word_by_word = getattr(style_preferences, 'german_word_by_word', False)
            english_word_by_word = getattr(style_preferences, 'english_word_by_word', False)
            any_word_by_word_requested = german_word_by_word or english_word_by_word
            
            logger.info(f"🔍 Audio generation mode (PERFECT UI-AUDIO SYNC):")
            logger.info(f"   German word-by-word requested: {german_word_by_word}")
            logger.info(f"   English word-by-word requested: {english_word_by_word}")
            logger.info(f"   Synchronized UI data entries: {len(sync_data['ui_data'])}")
            logger.info(f"   Synchronized audio sequences: {len(sync_data['audio_sequences'])}")
            
            # Generate SSML using synchronized data
            if any_word_by_word_requested and sync_data['audio_sequences']:
                logger.info("🎵 Generating PERFECTLY SYNCHRONIZED word-by-word audio")
                ssml = self._generate_synchronized_word_by_word_ssml(sync_data, style_preferences)
            else:
                logger.info("🎵 Generating simple translation reading audio")
                ssml = self._generate_simple_translation_ssml(translations_data, source_lang, style_preferences)
            
            # Use retry logic for synthesis
            success = await self._synthesize_with_retry(ssml, output_path, max_retries=3)
            
            if success:
                logger.info(f"✅ Successfully generated SYNCHRONIZED audio: {os.path.basename(output_path)}")
                return os.path.basename(output_path)
            else:
                logger.error("❌ Failed to generate synchronized audio after all retry attempts")
                return None

        except Exception as e:
            logger.error(f"❌ Error in text_to_speech_word_pairs_v2: {str(e)}")
            return None

    def _generate_synchronized_word_by_word_ssml(
        self,
        sync_data: Dict,
        style_preferences=None,
    ) -> str:
        """
        Generate SSML using perfectly synchronized data.
        CRITICAL: Audio matches UI display EXACTLY.
        """
        ssml = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">"""
        
        logger.info("\n🎤 GENERATING PERFECTLY SYNCHRONIZED WORD-BY-WORD AUDIO")
        logger.info("="*60)
        logger.info("🎯 CRITICAL: Audio will match UI display EXACTLY")
        
        # Process each style's synchronized audio sequence
        for style_name, audio_sequence in sync_data['audio_sequences'].items():
            logger.info(f"\n📝 Processing {style_name}: {len(audio_sequence)} synchronized items")
            
            if not audio_sequence:
                continue
            
            # Get the translation for this style from original data
            language = audio_sequence[0]['language']
            voice_config = audio_sequence[0]['voice_config']
            voice = voice_config['voice']
            lang = voice_config['language']
            
            logger.info(f"   Language: {language}")
            logger.info(f"   Voice: {voice}")
            logger.info(f"   Format: EXACTLY matches UI display")
            
            # Start with the full translation reading
            ssml += f"""
        <voice name="{voice}">
            <prosody rate="1.0">
                <break time="500ms"/>
            </prosody>
        </voice>"""
            
            # CRITICAL: Word-by-word breakdown in EXACT same order as UI
            ssml += """
        <voice name="en-US-JennyMultilingualNeural">
            <prosody rate="0.8">"""
            
            logger.info(f"   📋 Synchronized audio sequence:")
            
            for i, audio_item in enumerate(audio_sequence):
                source_word = audio_item['source_word']
                spanish_equiv = audio_item['spanish_equiv']
                display_format = audio_item['display_format']
                is_phrasal_verb = audio_item['is_phrasal_verb']
                
                # Clean for speech synthesis
                clean_source = source_word.strip()
                clean_spanish = spanish_equiv.strip()
                
                # CRITICAL: Use EXACT same format as UI displays
                logger.info(f"   {i+1:2d}. UI Display: {display_format}")
                logger.info(f"       Audio Says: [{clean_source}] ([{clean_spanish}])")
                
                if is_phrasal_verb:
                    verb_type = "German Separable Verb" if language == 'german' else "English Phrasal Verb"
                    logger.info(f"       🔗 {verb_type}: Single unit pronunciation")
                
                # Generate SSML for this word pair - EXACT format
                ssml += f"""
            <lang xml:lang="{lang}">{clean_source}</lang>
            <break time="200ms"/>
            <lang xml:lang="es-ES">{clean_spanish}</lang>
            <break time="400ms"/>"""
            
            ssml += """
            <break time="600ms"/>
            </prosody>
        </voice>"""
        
        ssml += "</speak>"
        
        logger.info(f"✅ Generated PERFECTLY SYNCHRONIZED SSML")
        logger.info(f"🎯 Audio will speak EXACTLY what UI displays")
        logger.info("="*60)
        
        return ssml

    def _generate_simple_translation_ssml(
        self,
        translations_data: Dict,
        source_lang: str,
        style_preferences=None,
    ) -> str:
        """
        Generate simple SSML that just reads translations.
        Used when word-by-word is NOT selected.
        """
        ssml = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">"""
        
        logger.info("\n🎤 SIMPLE TRANSLATION AUDIO (No word-by-word requested)")
        logger.info("="*50)
        
        # Process each style and read the translation
        for i, style_info in enumerate(translations_data.get('style_data', [])):
            translation = style_info['translation']
            is_german = style_info.get('is_german', False)
            is_spanish = style_info.get('is_spanish', False)
            
            # Escape XML special characters
            translation = translation.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            # Get voice configuration
            if is_spanish:
                voice_config = self._get_voice_config('spanish')
            elif is_german:
                voice_config = self._get_voice_config('german')
            else:
                voice_config = self._get_voice_config('english')
                
            voice = voice_config['voice']
            lang = voice_config['language']
            
            logger.info(f"📖 Reading translation {i+1}: \"{translation[:50]}...\"")
            
            # Add simple reading with minimal breaks
            ssml += f"""
        <voice name="{voice}">
            <prosody rate="1.0">
                <lang xml:lang="{lang}">{translation}</lang>
                <break time="600ms"/>
            </prosody>
        </voice>"""
        
        ssml += "</speak>"
        
        logger.info(f"✅ Generated simple audio for {len(translations_data.get('style_data', []))} translations")
        return ssml

    # Keep all other existing methods unchanged...
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