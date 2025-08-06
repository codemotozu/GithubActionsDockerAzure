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

    def _group_grammar_phrases(self, word_pairs: List[Tuple[str, str]], is_german: bool) -> Dict[str, str]:
        """Group word pairs into grammar-aware phrases"""
        if not word_pairs:
            return {}
            
        phrase_map = {}
        
        # Convert to lowercase for comparison
        pairs_dict = {src.lower(): (src, tgt) for src, tgt in word_pairs}
        
        if is_german:
            # Handle German separable verbs
            for separable_verb in self.separable_verbs:
                if separable_verb in pairs_dict:
                    original_src, translation = pairs_dict[separable_verb]
                    phrase_map[original_src] = translation
                    logger.info(f"🇩🇪 Found German separable verb: {original_src} → {translation}")
        else:
            # Handle English phrasal verbs
            for phrasal_verb in self.phrasal_verbs:
                if phrasal_verb in pairs_dict:
                    original_src, translation = pairs_dict[phrasal_verb]
                    phrase_map[original_src] = translation
                    logger.info(f"🇺🇸 Found English phrasal verb: {original_src} → {translation}")
        
        # Add remaining individual words
        for src, tgt in word_pairs:
            if src not in phrase_map:
                phrase_map[src] = tgt
        
        return phrase_map

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
                # Group phrases (phrasal verbs, separable verbs)
                phrase_map = self._group_grammar_phrases(word_pairs, is_german)
                
                ssml += """
        <voice name="en-US-JennyMultilingualNeural">
            <prosody rate="0.8">"""
                
                # Match words from translation with the style-specific word pairs
                words = translation.split()
                index = 0
                
                while index < len(words):
                    matched = False
                    
                    # Try to match multi-word phrases first
                    for phrase_len in range(3, 0, -1):  # Try 3-word, 2-word, then 1-word phrases
                        if index + phrase_len <= len(words):
                            current_phrase = " ".join(words[index:index + phrase_len])
                            current_phrase_clean = current_phrase.strip(".,!?")
                            
                            if current_phrase_clean in phrase_map or current_phrase_clean.lower() in phrase_map:
                                translation_text = phrase_map.get(current_phrase_clean) or phrase_map.get(current_phrase_clean.lower())
                                
                                ssml += f"""
            <lang xml:lang="{lang}">{current_phrase_clean}</lang>
            <break time="300ms"/>
            <lang xml:lang="es-ES">{translation_text}</lang>
            <break time="500ms"/>"""
                                
                                index += phrase_len
                                matched = True
                                break
                    
                    # If no match found, handle single word
                    if not matched:
                        word = words[index].strip(".,!?")
                        translation_text = phrase_map.get(word) or phrase_map.get(word.lower())
                        
                        ssml += f"""
            <lang xml:lang="{lang}">{word}</lang>
            <break time="300ms"/>"""
                        
                        if translation_text:
                            ssml += f"""
            <lang xml:lang="es-ES">{translation_text}</lang>
            <break time="500ms"/>"""
                        else:
                            ssml += """<break time="500ms"/>"""
                        
                        index += 1
                
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
            sentences = complete_text.split("\n") if complete_text else []
            sentences = [s.strip() for s in sentences if s.strip()]
            
            # Separate word pairs by language
            german_pairs = [(src, tgt) for src, tgt, is_german in word_pairs if is_german]
            english_pairs = [(src, tgt) for src, tgt, is_german in word_pairs if not is_german]
            
            # Create style data entries based on preferences
            sentence_index = 0
            
            # German styles
            if style_preferences.german_native and sentence_index < len(sentences):
                translations_data['style_data'].append({
                    'translation': sentences[sentence_index],
                    'word_pairs': german_pairs if style_preferences.german_word_by_word else [],
                    'is_german': True,
                    'style_name': 'german_native'
                })
                sentence_index += 1
                
            if style_preferences.german_colloquial and sentence_index < len(sentences):
                translations_data['style_data'].append({
                    'translation': sentences[sentence_index],
                    'word_pairs': german_pairs if style_preferences.german_word_by_word else [],
                    'is_german': True,
                    'style_name': 'german_colloquial'
                })
                sentence_index += 1
                
            if style_preferences.german_informal and sentence_index < len(sentences):
                translations_data['style_data'].append({
                    'translation': sentences[sentence_index],
                    'word_pairs': german_pairs if style_preferences.german_word_by_word else [],
                    'is_german': True,
                    'style_name': 'german_informal'
                })
                sentence_index += 1
                
            if style_preferences.german_formal and sentence_index < len(sentences):
                translations_data['style_data'].append({
                    'translation': sentences[sentence_index],
                    'word_pairs': german_pairs if style_preferences.german_word_by_word else [],
                    'is_german': True,
                    'style_name': 'german_formal'
                })
                sentence_index += 1
            
            # English styles
            if style_preferences.english_native and sentence_index < len(sentences):
                translations_data['style_data'].append({
                    'translation': sentences[sentence_index],
                    'word_pairs': english_pairs if style_preferences.english_word_by_word else [],
                    'is_german': False,
                    'style_name': 'english_native'
                })
                sentence_index += 1
                
            if style_preferences.english_colloquial and sentence_index < len(sentences):
                translations_data['style_data'].append({
                    'translation': sentences[sentence_index],
                    'word_pairs': english_pairs if style_preferences.english_word_by_word else [],
                    'is_german': False,
                    'style_name': 'english_colloquial'
                })
                sentence_index += 1
                
            if style_preferences.english_informal and sentence_index < len(sentences):
                translations_data['style_data'].append({
                    'translation': sentences[sentence_index],
                    'word_pairs': english_pairs if style_preferences.english_word_by_word else [],
                    'is_german': False,
                    'style_name': 'english_informal'
                })
                sentence_index += 1
                
            if style_preferences.english_formal and sentence_index < len(sentences):
                translations_data['style_data'].append({
                    'translation': sentences[sentence_index],
                    'word_pairs': english_pairs if style_preferences.english_word_by_word else [],
                    'is_german': False,
                    'style_name': 'english_formal'
                })
                sentence_index += 1
        
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