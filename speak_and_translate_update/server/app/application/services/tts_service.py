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
        FIXED: Properly matches compound phrases like "blackberry juice" with their correct translations.
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
                # Create comprehensive word pair mapping
                word_pair_dict = self._create_word_pair_mapping(word_pairs, is_german)
                
                ssml += """
        <voice name="en-US-JennyMultilingualNeural">
            <prosody rate="0.8">"""
                
                # FIXED: Process translation text with proper phrase matching
                translation_clean = translation.strip(".")
                words = translation_clean.split()
                processed_indices = set()
                
                # First pass: identify all multi-word phrases
                phrase_matches = []
                for length in range(4, 0, -1):  # Check up to 4-word phrases
                    for i in range(len(words) - length + 1):
                        if i in processed_indices:
                            continue
                        
                        phrase = " ".join(words[i:i+length])
                        phrase_lower = phrase.lower()
                        
                        # Check if this phrase exists in our word pairs
                        if phrase in word_pair_dict or phrase_lower in word_pair_dict:
                            spanish_translation = word_pair_dict.get(phrase) or word_pair_dict.get(phrase_lower)
                            phrase_matches.append((i, i+length, phrase, spanish_translation))
                            # Mark these indices as processed
                            for idx in range(i, i+length):
                                processed_indices.add(idx)
                            logger.debug(f"Matched phrase: '{phrase}' -> '{spanish_translation}'")
                
                # Sort matches by starting index
                phrase_matches.sort(key=lambda x: x[0])
                
                # Generate SSML for matched phrases and individual words
                current_index = 0
                for start_idx, end_idx, phrase, spanish_trans in phrase_matches:
                    # Process any unmatched words before this phrase
                    while current_index < start_idx:
                        word = words[current_index]
                        word_lower = word.lower()
                        
                        # Try to find translation for individual word
                        if word in word_pair_dict or word_lower in word_pair_dict:
                            spanish_word = word_pair_dict.get(word) or word_pair_dict.get(word_lower)
                            ssml += f"""
            <lang xml:lang="{lang}">{word}</lang>
            <break time="300ms"/>
            <lang xml:lang="es-ES">{spanish_word}</lang>
            <break time="500ms"/>"""
                        else:
                            # No translation found for this word
                            ssml += f"""
            <lang xml:lang="{lang}">{word}</lang>
            <break time="300ms"/><break time="500ms"/>"""
                        
                        current_index += 1
                    
                    # Add the matched phrase
                    ssml += f"""
            <lang xml:lang="{lang}">{phrase}</lang>
            <break time="300ms"/>
            <lang xml:lang="es-ES">{spanish_trans}</lang>
            <break time="500ms"/>"""
                    
                    current_index = end_idx
                
                # Process any remaining words
                while current_index < len(words):
                    word = words[current_index]
                    word_lower = word.lower()
                    
                    if word in word_pair_dict or word_lower in word_pair_dict:
                        spanish_word = word_pair_dict.get(word) or word_pair_dict.get(word_lower)
                        ssml += f"""
            <lang xml:lang="{lang}">{word}</lang>
            <break time="300ms"/>
            <lang xml:lang="es-ES">{spanish_word}</lang>
            <break time="500ms"/>"""
                    else:
                        ssml += f"""
            <lang xml:lang="{lang}">{word}</lang>
            <break time="300ms"/><break time="500ms"/>"""
                    
                    current_index += 1
                
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
        """
        # Convert legacy format to new structured format
        translations_data = {
            'translations': [],
            'style_data': []
        }
        
        # Parse complete text to get individual translations
        if complete_text:
            # Extract individual translations from the complete text
            # Look for patterns like "Pineapple juice for the girl and blackberry juice for the lady."
            translation_patterns = [
                r'"([^"]+)"',  # Quoted text
            ]
            
            extracted_translations = []
            for pattern in translation_patterns:
                matches = re.findall(pattern, complete_text)
                extracted_translations.extend(matches)
            
            # Filter to get actual translations (not word-by-word sections)
            actual_translations = []
            for trans in extracted_translations:
                # Skip if it looks like a word-by-word section (contains parentheses)
                if '(' not in trans and ')' not in trans and len(trans) > 10:
                    actual_translations.append(trans)
            
            # Separate word pairs by language
            german_pairs = [(src, tgt) for src, tgt, is_german in word_pairs if is_german]
            english_pairs = [(src, tgt) for src, tgt, is_german in word_pairs if not is_german]
            
            # Create style data entries based on preferences and actual translations
            translation_index = 0
            
            # German styles
            if style_preferences.german_native and translation_index < len(actual_translations):
                translations_data['style_data'].append({
                    'translation': actual_translations[translation_index],
                    'word_pairs': german_pairs if style_preferences.german_word_by_word else [],
                    'is_german': True,
                    'style_name': 'german_native'
                })
                translation_index += 1
                
            if style_preferences.german_colloquial and translation_index < len(actual_translations):
                translations_data['style_data'].append({
                    'translation': actual_translations[translation_index],
                    'word_pairs': german_pairs if style_preferences.german_word_by_word else [],
                    'is_german': True,
                    'style_name': 'german_colloquial'
                })
                translation_index += 1
                
            if style_preferences.german_informal and translation_index < len(actual_translations):
                translations_data['style_data'].append({
                    'translation': actual_translations[translation_index],
                    'word_pairs': german_pairs if style_preferences.german_word_by_word else [],
                    'is_german': True,
                    'style_name': 'german_informal'
                })
                translation_index += 1
                
            if style_preferences.german_formal and translation_index < len(actual_translations):
                translations_data['style_data'].append({
                    'translation': actual_translations[translation_index],
                    'word_pairs': german_pairs if style_preferences.german_word_by_word else [],
                    'is_german': True,
                    'style_name': 'german_formal'
                })
                translation_index += 1
            
            # English styles
            if style_preferences.english_native and translation_index < len(actual_translations):
                translations_data['style_data'].append({
                    'translation': actual_translations[translation_index],
                    'word_pairs': english_pairs if style_preferences.english_word_by_word else [],
                    'is_german': False,
                    'style_name': 'english_native'
                })
                translation_index += 1
                
            if style_preferences.english_colloquial and translation_index < len(actual_translations):
                translations_data['style_data'].append({
                    'translation': actual_translations[translation_index],
                    'word_pairs': english_pairs if style_preferences.english_word_by_word else [],
                    'is_german': False,
                    'style_name': 'english_colloquial'
                })
                translation_index += 1
                
            if style_preferences.english_informal and translation_index < len(actual_translations):
                translations_data['style_data'].append({
                    'translation': actual_translations[translation_index],
                    'word_pairs': english_pairs if style_preferences.english_word_by_word else [],
                    'is_german': False,
                    'style_name': 'english_informal'
                })
                translation_index += 1
                
            if style_preferences.english_formal and translation_index < len(actual_translations):
                translations_data['style_data'].append({
                    'translation': actual_translations[translation_index],
                    'word_pairs': english_pairs if style_preferences.english_word_by_word else [],
                    'is_german': False,
                    'style_name': 'english_formal'
                })
                translation_index += 1
        
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