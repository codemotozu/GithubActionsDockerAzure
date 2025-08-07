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

    def _create_word_pair_mapping(self, word_pairs: List[Tuple[str, str]], is_german: bool) -> Dict[str, str]:
        """
        Create a comprehensive mapping of source words/phrases to translations.
        This handles compound words and phrases properly.
        """
        mapping = {}
        
        # First, add all word pairs to the mapping
        for source, target in word_pairs:
            # Store both original case and lowercase versions
            mapping[source] = target
            mapping[source.lower()] = target
            
            # For compound phrases, also store individual components
            source_words = source.split()
            if len(source_words) > 1:
                # Store the full phrase
                mapping[' '.join(source_words)] = target
                mapping[' '.join(source_words).lower()] = target
        
        logger.info(f"Created word pair mapping with {len(mapping)} entries")
        for key, value in list(mapping.items())[:10]:  # Log first 10 entries for debugging
            logger.debug(f"  '{key}' -> '{value}'")
        
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
        Enhanced version that properly handles style-specific word pairs.
        Ensures that each translation style uses its own correct word pairs.
        """
        try:
            if not output_path:
                temp_dir = self._get_temp_directory()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(temp_dir, f"speech_{timestamp}.mp3")
                logger.info(f"\n📂 Output path: {output_path}")

            # Generate SSML with style-specific word pairs
            ssml = self._generate_style_specific_ssml(
                translations_data=translations_data,
                style_preferences=style_preferences,
            )
            
            # Log the generated SSML for debugging
            logger.info(f"\n📄 Generated SSML:")
            print("Generated SSML:")
            print(ssml)

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

    def _generate_style_specific_ssml(
        self,
        translations_data: Dict,
        style_preferences=None,
    ) -> str:
        """
        Generate SSML with style-specific word pairs.
        Each translation style uses only its corresponding word pairs.
        FIXED: Properly matches compound phrases with their correct translations.
        """
        ssml = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">"""
        
        # Log configuration
        logger.info("\n🎤 TTS STYLE-SPECIFIC GENERATION")
        logger.info("="*60)
        
        # Process each style with its specific word pairs
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
            # Debug: Log word pairs to verify they're correct
            for src, tgt in word_pairs[:5]:  # Show first 5 pairs
                logger.debug(f"   Word pair: '{src}' -> '{tgt}'")
            
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
            
            # Add word-by-word section if word pairs exist for this style
            if word_pairs:
                ssml += """
        <voice name="en-US-JennyMultilingualNeural">
            <prosody rate="0.8">"""
                
                # Clean translation for processing
                translation_clean = translation.strip(".,!?").strip()
                words = translation_clean.split()
                
                # Sort word pairs by length (longer phrases first) to prioritize compound phrases
                sorted_pairs = sorted(word_pairs, key=lambda x: len(x[0].split()), reverse=True)
                
                # Create a mapping of positions to translations
                position_translations = {}
                
                # Match phrases in the translation
                for source, target in sorted_pairs:
                    source_words = source.split()
                    source_len = len(source_words)
                    
                    # Search for this phrase in the translation
                    for i in range(len(words) - source_len + 1):
                        # Check if any position is already occupied
                        if any(j in position_translations for j in range(i, i + source_len)):
                            continue
                        
                        # Try to match the phrase at this position
                        phrase_at_position = " ".join(words[i:i+source_len])
                        
                        # Case-insensitive matching
                        if phrase_at_position.lower() == source.lower():
                            # Found a match! Store it for all positions it covers
                            for j in range(i, i + source_len):
                                position_translations[j] = {
                                    'source': phrase_at_position,  # Use the original case from translation
                                    'target': target,
                                    'start': i,
                                    'end': i + source_len,
                                    'is_start': j == i
                                }
                            logger.debug(f"Matched '{phrase_at_position}' -> '{target}' at position {i}")
                            break  # Move to next word pair after successful match
                
                # Generate SSML based on position mapping
                i = 0
                while i < len(words):
                    if i in position_translations:
                        trans_info = position_translations[i]
                        if trans_info['is_start']:
                            # This is the start of a matched phrase
                            ssml += f"""
            <lang xml:lang="{lang}">{trans_info['source']}</lang>
            <break time="300ms"/>
            <lang xml:lang="es-ES">{trans_info['target']}</lang>
            <break time="500ms"/>"""
                            # Skip to the end of this phrase
                            i = trans_info['end']
                        else:
                            # This word is part of a phrase we already processed
                            i += 1
                    else:
                        # No translation found for this word/position
                        word = words[i]
                        ssml += f"""
            <lang xml:lang="{lang}">{word}</lang>
            <break time="300ms"/><break time="500ms"/>"""
                        i += 1
                
                ssml += """
            <break time="1000ms"/>
            </prosody>
        </voice>"""
        
        ssml += "</speak>"
        
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
        FIXED: Properly associates word pairs with their respective styles.
        """
        # Convert legacy format to new structured format
        translations_data = {
            'translations': [],
            'style_data': []
        }
        
        # Parse complete text to get individual translations and their word pairs
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
                
                # Extract word-by-word pairs for current style
                if 'word by word' in line and current_style:
                    # Extract the word pairs from the line
                    match = re.search(r'"([^"]+)"', line)
                    if match:
                        pairs_text = match.group(1)
                        pairs = []
                        # Parse pairs like "Pineapple juice (jugo de piña)"
                        pair_matches = re.findall(r'([^()]+?)\s*\(([^)]+)\)', pairs_text)
                        for source, target in pair_matches:
                            source = source.strip()
                            target = target.strip()
                            if source and target:
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