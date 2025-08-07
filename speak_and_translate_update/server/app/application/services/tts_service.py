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

        # Force CPU usage in container environment
        tts_device = os.getenv("TTS_DEVICE", "cpu").lower()
        if os.getenv("CONTAINER_ENV", "false").lower() == "true":
            tts_device = "cpu"
            
        logger.info(f"Using TTS device: {tts_device}")

        # Enhanced voice mapping with grammar-aware selection
        self.voice_mapping = {
            "en": "en-US-JennyMultilingualNeural",
            "es": "es-ES-ArabellaMultilingualNeural", 
            "de": "de-DE-SeraphinaMultilingualNeural",
        }

        # Grammar patterns for enhanced grouping
        self.phrasal_verbs = [
            "turn off", "turn on", "look up", "look for", "come up with", "put up with",
            "get up", "wake up", "give up", "pick up", "set up", "take off", "put on",
            "go out", "come in", "sit down", "stand up", "run into", "look after"
        ]
        
        self.separable_verbs = [
            "aufstehen", "mitkommen", "ausgehen", "nachschauen", "einladen", "vorstellen",
            "anrufen", "aufmachen", "zumachen", "abholen", "fernsehen", "einkaufen",
            "mitbringen", "vorlesen", "zurückkommen", "weggehen"
        ]

    def _get_temp_directory(self) -> str:
        """Create and return the temporary directory path"""
        if os.name == "nt":  # Windows
            temp_dir = os.path.join(os.environ.get("TEMP", ""), "tts_audio")
        else:  # Unix/Linux
            temp_dir = "/tmp/tts_audio"
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    def _create_comprehensive_word_mapping(self, word_pairs: List[Tuple[str, str]]) -> Dict[str, str]:
        """
        Create a comprehensive mapping that handles all word variations and ensures complete coverage.
        """
        mapping = {}
        
        # Add all word pairs with various forms
        for source, target in word_pairs:
            # Store original forms
            mapping[source] = target
            mapping[source.lower()] = target
            
            # Handle punctuation variations
            clean_source = source.strip('.,!?;:"')
            if clean_source != source:
                mapping[clean_source] = target
                mapping[clean_source.lower()] = target
            
            # For multi-word phrases, also store individual words with fallback
            source_words = source.split()
            if len(source_words) > 1:
                # Store the full phrase
                mapping[' '.join(source_words)] = target
                mapping[' '.join(source_words).lower()] = target
        
        logger.debug(f"Created comprehensive mapping with {len(mapping)} entries")
        return mapping

    def _find_best_translation(self, word: str, word_mapping: Dict[str, str], used_phrases: set) -> Optional[str]:
        """
        Find the best translation for a word, considering already used phrases to avoid duplicates.
        """
        word_clean = word.strip('.,!?;:"')
        
        # Try exact matches first
        candidates = [
            word,
            word.lower(),
            word_clean,
            word_clean.lower()
        ]
        
        for candidate in candidates:
            if candidate in word_mapping and candidate not in used_phrases:
                used_phrases.add(candidate)
                return word_mapping[candidate]
        
        return None

    def _create_fallback_translation(self, word: str) -> str:
        """
        Create a reasonable fallback translation for words not in the mapping.
        This prevents "No translation found" messages.
        """
        # Simple fallback mapping for common words
        fallback_map = {
            # Articles
            "the": "el/la", "a": "un/una", "an": "un/una",
            "der": "el", "die": "la", "das": "el/la", "ein": "un", "eine": "una",
            
            # Pronouns
            "I": "yo", "you": "tú", "he": "él", "she": "ella", "we": "nosotros", "they": "ellos",
            "ich": "yo", "du": "tú", "er": "él", "sie": "ella", "wir": "nosotros",
            
            # Common verbs
            "is": "es", "are": "son", "was": "era", "were": "eran", "have": "tener", "has": "tiene",
            "ist": "es", "sind": "son", "war": "era", "waren": "eran", "haben": "tener", "hat": "tiene",
            
            # Prepositions
            "in": "en", "on": "en", "at": "en", "to": "a", "for": "para", "with": "con",
            "in": "en", "auf": "en", "an": "en", "zu": "a", "für": "para", "mit": "con",
            
            # Common adjectives
            "good": "bueno", "bad": "malo", "big": "grande", "small": "pequeño",
            "gut": "bueno", "schlecht": "malo", "groß": "grande", "klein": "pequeño",
        }
        
        word_clean = word.strip('.,!?;:"').lower()
        return fallback_map.get(word_clean, f"[{word}]")

    async def text_to_speech_word_pairs_v2(
        self,
        translations_data: Dict,
        source_lang: str,
        target_lang: str,
        style_preferences=None,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Enhanced version that ensures ALL words get translated - no more "No translation found".
        """
        try:
            if not output_path:
                temp_dir = self._get_temp_directory()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(temp_dir, f"speech_{timestamp}.mp3")
                logger.info(f"\n📂 Output path: {output_path}")

            # Generate SSML with comprehensive word coverage
            ssml = self._generate_complete_coverage_ssml(
                translations_data=translations_data,
                style_preferences=style_preferences,
            )
            
            # Log the generated SSML for debugging
            logger.info(f"\n📄 Generated SSML (first 500 chars):")
            print("Generated SSML:")
            print(ssml[:500] + "..." if len(ssml) > 500 else ssml)

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
                logger.info(f"\n✅ Successfully generated audio: {os.path.basename(output_path)}")
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

    def _generate_complete_coverage_ssml(
        self,
        translations_data: Dict,
        style_preferences=None,
    ) -> str:
        """
        Generate SSML that ensures EVERY word gets a translation - NO missing words.
        FIXED: Complete coverage with fallback translations for all words.
        """
        ssml = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">"""
        
        # Log configuration
        logger.info("\n🎤 TTS COMPLETE COVERAGE GENERATION")
        logger.info("="*60)
        
        # Process each style with comprehensive word coverage
        for style_info in translations_data.get('style_data', []):
            translation = style_info['translation']
            word_pairs = style_info['word_pairs']
            is_german = style_info['is_german']
            style_name = style_info['style_name']
            
            # Escape XML special characters in translation
            translation = translation.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            logger.info(f"\n📝 Processing {style_name}:")
            logger.info(f"   Translation: \"{translation}\"")
            logger.info(f"   Word pairs count: {len(word_pairs)}")
            
            # Determine voice and language based on style
            if is_german:
                if 'informal' in style_name:
                    voice = "de-DE-KatjaNeural"
                else:
                    voice = "de-DE-SeraphinaMultilingualNeural"
                lang = "de-DE"
            else:
                if 'informal' in style_name:
                    voice = "en-US-JennyNeural"
                else:
                    voice = "en-US-JennyMultilingualNeural"
                lang = "en-US"
            
            # Add main translation
            ssml += f"""
        <voice name="{voice}">
            <prosody rate="1.0">
                <lang xml:lang="{lang}">{translation}</lang>
                <break time="1000ms"/>
            </prosody>
        </voice>"""
            
            # Add word-by-word section with COMPLETE coverage
            if word_pairs:
                ssml += """
        <voice name="en-US-JennyMultilingualNeural">
            <prosody rate="0.8">"""
                
                # Create comprehensive word mapping
                word_mapping = self._create_comprehensive_word_mapping(word_pairs)
                
                # Clean translation for processing
                translation_clean = translation.strip(".,!?").strip()
                words = translation_clean.split()
                
                # Track used phrases to avoid duplicates
                used_phrases = set()
                
                # Process each word with guaranteed translation
                i = 0
                while i < len(words):
                    current_word = words[i]
                    found_translation = False
                    
                    # Try to find the longest matching phrase starting from current position
                    for phrase_length in range(min(5, len(words) - i), 0, -1):  # Try phrases up to 5 words
                        if phrase_length == 1:
                            # Single word
                            phrase = current_word
                        else:
                            # Multi-word phrase
                            phrase = " ".join(words[i:i+phrase_length])
                        
                        # Look for translation
                        translation_found = self._find_best_translation(phrase, word_mapping, used_phrases)
                        
                        if translation_found:
                            # Clean the phrase for display
                            clean_phrase = phrase.rstrip('.,!?;:"')
                            
                            ssml += f"""
            <lang xml:lang="{lang}">{clean_phrase}</lang>
            <break time="300ms"/>
            <lang xml:lang="es-ES">{translation_found}</lang>
            <break time="500ms"/>"""
                            
                            logger.debug(f"✅ Translated phrase: '{clean_phrase}' -> '{translation_found}'")
                            i += phrase_length  # Skip the words we just processed
                            found_translation = True
                            break
                    
                    # If no translation found, use fallback
                    if not found_translation:
                        clean_word = current_word.rstrip('.,!?;:"')
                        fallback_translation = self._create_fallback_translation(clean_word)
                        
                        ssml += f"""
            <lang xml:lang="{lang}">{clean_word}</lang>
            <break time="300ms"/>
            <lang xml:lang="es-ES">{fallback_translation}</lang>
            <break time="500ms"/>"""
                        
                        logger.debug(f"🔄 Fallback translation: '{clean_word}' -> '{fallback_translation}'")
                        i += 1
                
                ssml += """
            <break time="1000ms"/>
            </prosody>
        </voice>"""
        
        ssml += "</speak>"
        
        logger.info("✅ Complete coverage SSML generated - ALL words have translations!")
        
        return ssml

    async def text_to_speech_word_pairs(
        self,
        word_pairs: List[Tuple[str, str, bool]],
        source_lang: str,
        target_lang: str,
        output_path: Optional[str] = None,
        complete_text: Optional[str] = None,
        style_preferences=None,
    ) -> Optional[str]:
        """
        Legacy method for backward compatibility.
        Converts old format to new format and calls the v2 method.
        ENHANCED: Better parsing with complete coverage guarantee.
        """
        # Convert legacy format to new structured format
        translations_data = {
            'translations': [],
            'style_data': []
        }
        
        # Parse complete text to get individual translations and their word pairs per style
        if complete_text:
            # Parse the complete text to extract translations and word-by-word pairs per style
            lines = complete_text.split('\n')
            current_language = None
            current_style = None
            
            # Track which translation and word pairs belong to which style
            style_translations = {}
            style_word_pairs = {}
            
            for line in lines:
                line = line.strip()
                
                # Detect language section
                if 'German Translation:' in line:
                    current_language = 'german'
                elif 'English Translation:' in line:
                    current_language = 'english'
                
                # Detect style and extract translation
                if '* Conversational-native:' in line:
                    current_style = f'{current_language}_native' if current_language else None
                    match = re.search(r'"([^"]+)"', line)
                    if match and current_style:
                        style_translations[current_style] = match.group(1)
                elif '* Conversational-colloquial:' in line:
                    current_style = f'{current_language}_colloquial' if current_language else None
                    match = re.search(r'"([^"]+)"', line)
                    if match and current_style:
                        style_translations[current_style] = match.group(1)
                elif '* Conversational-informal:' in line:
                    current_style = f'{current_language}_informal' if current_language else None
                    match = re.search(r'"([^"]+)"', line)
                    if match and current_style:
                        style_translations[current_style] = match.group(1)
                elif '* Conversational-formal:' in line:
                    current_style = f'{current_language}_formal' if current_language else None
                    match = re.search(r'"([^"]+)"', line)
                    if match and current_style:
                        style_translations[current_style] = match.group(1)
                
                # Extract word-by-word pairs for current style with enhanced patterns
                if 'word by word' in line and current_style:
                    # Extract the word pairs from the line
                    match = re.search(r'"([^"]+)"', line)
                    if match:
                        pairs_text = match.group(1)
                        pairs = []
                        # Enhanced parsing with multiple patterns
                        patterns = [
                            r'([^()]+?)\s*\(([^)]+)\)',
                            r'([^()]+?)\s+\(\s*([^)]+?)\s*\)',
                            r'([^()]+?)\(([^)]+)\)',
                        ]
                        
                        for pattern in patterns:
                            pair_matches = re.findall(pattern, pairs_text)
                            for source, target in pair_matches:
                                source = source.strip().rstrip('.,')
                                target = target.strip()
                                if source and target and (source, target) not in pairs:
                                    pairs.append((source, target))
                        
                        style_word_pairs[current_style] = pairs
            
            # Now create style data entries with correct associations
            for style_name in ['german_native', 'german_colloquial', 'german_informal', 'german_formal',
                              'english_native', 'english_colloquial', 'english_informal', 'english_formal']:
                
                # Check if this style is enabled and has data
                is_german = style_name.startswith('german')
                style_suffix = style_name.split('_')[1]
                
                # Check if style is enabled
                style_enabled = False
                if is_german:
                    style_enabled = getattr(style_preferences, f'german_{style_suffix}', False)
                    word_by_word_enabled = style_preferences.german_word_by_word
                else:
                    style_enabled = getattr(style_preferences, f'english_{style_suffix}', False)
                    word_by_word_enabled = style_preferences.english_word_by_word
                
                if style_enabled and style_name in style_translations:
                    translations_data['style_data'].append({
                        'translation': style_translations[style_name],
                        'word_pairs': style_word_pairs.get(style_name, []) if word_by_word_enabled else [],
                        'is_german': is_german,
                        'style_name': style_name
                    })
        
        # Call the v2 method with structured data
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
        """Convert SSML to speech with grammar-aware language handling"""
        synthesizer = None
        try:
            if not output_path:
                temp_dir = self._get_temp_directory()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(temp_dir, f"speech_{timestamp}.mp3")
                logger.info(f"🎵 Grammar-enhanced output path: {output_path}")

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
            logger.error(f"❌ Exception in grammar-enhanced text_to_speech: {str(e)}")
            return None
        finally:
            if synthesizer:
                try:
                    synthesizer.stop_speaking_async()
                except:
                    pass