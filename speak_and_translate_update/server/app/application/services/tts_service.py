from azure.cognitiveservices.speech import (
    SpeechConfig,
    SpeechSynthesizer,
    SpeechSynthesisOutputFormat,
    ResultReason,
    CancellationReason,
)
from azure.cognitiveservices.speech.audio import AudioOutputConfig
import os
from typing import Optional
from datetime import datetime
import asyncio
import re

from asyncio import Semaphore
import time
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

    async def _execute_speech_synthesis(
        self, ssml: str, output_path: Optional[str] = None
    ) -> Optional[str]:
        """Execute the speech synthesis with proper resource cleanup"""
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

            if result.reason == ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                error_message = (
                    f"Speech synthesis canceled: {cancellation_details.reason}"
                )
                if cancellation_details.reason == CancellationReason.Error:
                    error_message += (
                        f"\nError details: {cancellation_details.error_details}"
                    )
                raise Exception(error_message)

            return None

        finally:
            if synthesizer:
                try:
                    synthesizer.stop_speaking_async()
                except:
                    pass

    def _get_temp_directory(self) -> str:
        """Create and return the temporary directory path"""
        if os.name == "nt":  # Windows
            temp_dir = os.path.join(os.environ.get("TEMP", ""), "tts_audio")
        else:  # Unix/Linux
            temp_dir = "/tmp/tts_audio"
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    def _detect_language(self, text: str) -> str:
        """Detect the primary language of the text"""
        if re.search(r"[äöüßÄÖÜ]", text):
            return "de"
        elif re.search(r"[áéíóúñ¿¡]", text):
            return "es"
        return "en"

    def _identify_phrasal_verb(self, text: str) -> list[str]:
        """Identify phrasal verbs in English text"""
        found_phrasal_verbs = []
        text_lower = text.lower()
        
        for phrasal_verb in self.phrasal_verbs:
            if phrasal_verb in text_lower:
                found_phrasal_verbs.append(phrasal_verb)
        
        return found_phrasal_verbs

    def _identify_separable_verb(self, text: str) -> list[str]:
        """Identify separable verbs in German text"""
        found_separable_verbs = []
        text_lower = text.lower()
        
        for separable_verb in self.separable_verbs:
            if separable_verb in text_lower:
                found_separable_verbs.append(separable_verb)
        
        return found_separable_verbs

    def _group_grammar_phrases(self, word_pairs: list[tuple[str, str]], is_german: bool) -> dict[str, str]:
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

    def _log_word_by_word_section(self, language: str, sentence: str, word_pairs: list[tuple[str, str]], enabled: bool):
        """Log detailed word-by-word pronunciation information"""
        if not enabled:
            logger.info(f"\n{'='*60}")
            logger.info(f"📢 {language} Word-by-Word Audio: DISABLED")
            logger.info(f"   Sentence: {sentence}")
            logger.info(f"{'='*60}\n")
            return
            
        logger.info(f"\n{'='*60}")
        logger.info(f"🎯 {language} WORD-BY-WORD PRONUNCIATION")
        logger.info(f"{'='*60}")
        logger.info(f"📝 Full Sentence: {sentence}")
        logger.info(f"🔤 Word Pairs ({len(word_pairs)} total):")
        
        # Group by grammar type
        if language == "German":
            separable_verbs = []
            regular_words = []
            
            for src, tgt in word_pairs:
                if src.lower() in [v.lower() for v in self.separable_verbs]:
                    separable_verbs.append((src, tgt))
                else:
                    regular_words.append((src, tgt))
            
            if separable_verbs:
                logger.info("\n   🔹 SEPARABLE VERBS:")
                for src, tgt in separable_verbs:
                    logger.info(f"      • {src} → {tgt}")
            
            if regular_words:
                logger.info("\n   🔸 REGULAR WORDS:")
                for src, tgt in regular_words:
                    logger.info(f"      • {src} → {tgt}")
                    
        elif language == "English":
            phrasal_verbs = []
            regular_words = []
            
            for src, tgt in word_pairs:
                if src.lower() in [v.lower() for v in self.phrasal_verbs]:
                    phrasal_verbs.append((src, tgt))
                else:
                    regular_words.append((src, tgt))
            
            if phrasal_verbs:
                logger.info("\n   🔹 PHRASAL VERBS:")
                for src, tgt in phrasal_verbs:
                    logger.info(f"      • {src} → {tgt}")
            
            if regular_words:
                logger.info("\n   🔸 REGULAR WORDS:")
                for src, tgt in regular_words:
                    logger.info(f"      • {src} → {tgt}")
        
        logger.info(f"\n🎵 Pronunciation Order:")
        logger.info(f"   1. Full sentence in {language}")
        logger.info(f"   2. Word-by-word: {language} word → Spanish translation")
        logger.info(f"{'='*60}\n")

    def generate_enhanced_ssml(
        self,
        text: Optional[str] = None,
        word_pairs: Optional[list[tuple[str, str, bool]]] = None,
        source_lang: str = "de",
        target_lang: str = "es",
        style_preferences=None,
    ) -> str:
        """Generate SSML with grammar-aware phrase handling and detailed logging"""
        logger.info("\n" + "="*80)
        logger.info("🎤 TTS WORD-BY-WORD PRONUNCIATION GENERATION")
        logger.info("="*80)
        
        ssml = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">"""

        if text and style_preferences:
            # Log preferences
            logger.info(f"\n📋 Word-by-Word Audio Preferences:")
            logger.info(f"   • German word-by-word: {'ENABLED' if style_preferences.german_word_by_word else 'DISABLED'}")
            logger.info(f"   • English word-by-word: {'ENABLED' if style_preferences.english_word_by_word else 'DISABLED'}")
            
            # Split text into lines and process based on style preferences
            sentences = text.split("\n")
            sentences = [s.strip() for s in sentences if s.strip()]
            
            sentence_index = 0
            
            def get_next_sentence():
                nonlocal sentence_index
                if sentence_index < len(sentences):
                    sentence = sentences[sentence_index].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    sentence_index += 1
                    return sentence
                return ""

            if word_pairs:
                # Separate pairs with language flag
                german_pairs = [(src, tgt) for src, tgt, is_german in word_pairs if is_german]
                english_pairs = [(src, tgt) for src, tgt, is_german in word_pairs if not is_german]
                
                # Log pair counts
                logger.info(f"\n📊 Word Pair Statistics:")
                logger.info(f"   • German pairs: {len(german_pairs)}")
                logger.info(f"   • English pairs: {len(english_pairs)}")
                
                # Apply grammar-aware grouping
                german_phrase_map = self._group_grammar_phrases(german_pairs, is_german=True)
                english_phrase_map = self._group_grammar_phrases(english_pairs, is_german=False)
                
            else:
                german_phrase_map = {}
                english_phrase_map = {}

            # Process German sections with detailed logging
            if style_preferences.german_native:
                german_native = get_next_sentence()
                if german_native:
                    self._log_word_by_word_section("German Native", german_native, 
                                                   list(german_phrase_map.items()), 
                                                   style_preferences.german_word_by_word)
                    ssml += self._generate_grammar_aware_section(
                        german_native,
                        german_phrase_map,
                        voice="de-DE-SeraphinaMultilingualNeural",
                        lang="de-DE",
                        include_word_by_word=style_preferences.german_word_by_word,
                        is_german=True,
                    )

            if style_preferences.german_colloquial:
                german_colloquial = get_next_sentence()
                if german_colloquial:
                    self._log_word_by_word_section("German Colloquial", german_colloquial, 
                                                   list(german_phrase_map.items()), 
                                                   style_preferences.german_word_by_word)
                    ssml += self._generate_grammar_aware_section(
                        german_colloquial,
                        german_phrase_map,
                        voice="de-DE-SeraphinaMultilingualNeural",
                        lang="de-DE",
                        include_word_by_word=style_preferences.german_word_by_word,
                        is_german=True,
                    )

            if style_preferences.german_informal:
                german_informal = get_next_sentence()
                if german_informal:
                    self._log_word_by_word_section("German Informal", german_informal, 
                                                   list(german_phrase_map.items()), 
                                                   style_preferences.german_word_by_word)
                    ssml += self._generate_grammar_aware_section(
                        german_informal,
                        german_phrase_map,
                        voice="de-DE-KatjaNeural",
                        lang="de-DE",
                        include_word_by_word=style_preferences.german_word_by_word,
                        is_german=True,
                    )

            if style_preferences.german_formal:
                german_formal = get_next_sentence()
                if german_formal:
                    self._log_word_by_word_section("German Formal", german_formal, 
                                                   list(german_phrase_map.items()), 
                                                   style_preferences.german_word_by_word)
                    ssml += self._generate_grammar_aware_section(
                        german_formal,
                        german_phrase_map,
                        voice="de-DE-SeraphinaMultilingualNeural",
                        lang="de-DE",
                        include_word_by_word=style_preferences.german_word_by_word,
                        is_german=True,
                    )

            # Process English sections with detailed logging
            if style_preferences.english_native:
                english_native = get_next_sentence()
                if english_native:
                    self._log_word_by_word_section("English Native", english_native, 
                                                   list(english_phrase_map.items()), 
                                                   style_preferences.english_word_by_word)
                    ssml += self._generate_grammar_aware_section(
                        english_native,
                        english_phrase_map,
                        voice="en-US-JennyMultilingualNeural",
                        lang="en-US",
                        include_word_by_word=style_preferences.english_word_by_word,
                        is_german=False,
                    )

            if style_preferences.english_colloquial:
                english_colloquial = get_next_sentence()
                if english_colloquial:
                    self._log_word_by_word_section("English Colloquial", english_colloquial, 
                                                   list(english_phrase_map.items()), 
                                                   style_preferences.english_word_by_word)
                    ssml += self._generate_grammar_aware_section(
                        english_colloquial,
                        english_phrase_map,
                        voice="en-US-JennyMultilingualNeural",
                        lang="en-US",
                        include_word_by_word=style_preferences.english_word_by_word,
                        is_german=False,
                    )

            if style_preferences.english_informal:
                english_informal = get_next_sentence()
                if english_informal:
                    self._log_word_by_word_section("English Informal", english_informal, 
                                                   list(english_phrase_map.items()), 
                                                   style_preferences.english_word_by_word)
                    ssml += self._generate_grammar_aware_section(
                        english_informal,
                        english_phrase_map,
                        voice="en-US-JennyNeural",
                        lang="en-US",
                        include_word_by_word=style_preferences.english_word_by_word,
                        is_german=False,
                    )

            if style_preferences.english_formal:
                english_formal = get_next_sentence()
                if english_formal:
                    self._log_word_by_word_section("English Formal", english_formal, 
                                                   list(english_phrase_map.items()), 
                                                   style_preferences.english_word_by_word)
                    ssml += self._generate_grammar_aware_section(
                        english_formal,
                        english_phrase_map,
                        voice="en-US-JennyMultilingualNeural",
                        lang="en-US",
                        include_word_by_word=style_preferences.english_word_by_word,
                        is_german=False,
                    )

        # Final cleanup of SSML
        ssml = re.sub(r'(<break time="500ms"\s*/>\s*)+', '<break time="500ms"/>', ssml)
        ssml += "</speak>"
        
        logger.info("\n" + "="*80)
        logger.info("✅ TTS GENERATION COMPLETE")
        logger.info("="*80 + "\n")
        
        return ssml

    def _generate_grammar_aware_section(
        self, 
        sentence: str, 
        phrase_map: dict[str, str], 
        voice: str, 
        lang: str,
        include_word_by_word: bool = True,
        is_german: bool = True
    ) -> str:
        """Generate language section with grammar-aware phrase handling"""
        section = f"""
        <voice name="{voice}">
            <prosody rate="1.0">
                <lang xml:lang="{lang}">{sentence}</lang>
                <break time="1000ms"/>
            </prosody>
        </voice>"""

        # Only include word-by-word section if enabled and phrase map exists
        if phrase_map and include_word_by_word:
            section += """
        <voice name="en-US-JennyMultilingualNeural">
            <prosody rate="0.8">"""

            # Sort phrases by length (longest first) for better matching
            sorted_phrases = sorted(phrase_map.keys(), key=len, reverse=True)
            
            words = sentence.split()
            index = 0

            while index < len(words):
                matched = False

                # Try to match multi-word phrases first (phrasal verbs, separable verbs)
                for phrase in sorted_phrases:
                    phrase_words = phrase.split()
                    if index + len(phrase_words) <= len(words):
                        # Check if current position matches this phrase
                        current_phrase = " ".join(words[index:index + len(phrase_words)])
                        if current_phrase.lower() == phrase.lower():
                            translation = phrase_map[phrase]
                            
                            # Add special emphasis for grammar structures
                            if is_german and phrase.lower() in [v.lower() for v in self.separable_verbs]:
                                section += f"""
            <emphasis level="moderate">
                <lang xml:lang="{lang}">{phrase}</lang>
            </emphasis>
            <break time="300ms"/>
            <lang xml:lang="es-ES">{translation}</lang>
            <break time="500ms"/>"""
                            elif not is_german and phrase.lower() in [v.lower() for v in self.phrasal_verbs]:
                                section += f"""
            <emphasis level="moderate">
                <lang xml:lang="{lang}">{phrase}</lang>
            </emphasis>
            <break time="300ms"/>
            <lang xml:lang="es-ES">{translation}</lang>
            <break time="500ms"/>"""
                            else:
                                section += f"""
            <lang xml:lang="{lang}">{phrase}</lang>
            <break time="300ms"/>
            <lang xml:lang="es-ES">{translation}</lang>
            <break time="500ms"/>"""
                            
                            index += len(phrase_words)
                            matched = True
                            break

                # Single word fallback
                if not matched:
                    word = words[index].strip(".,!?")
                    translation = phrase_map.get(word, phrase_map.get(word.lower(), None))
                    
                    section += f"""
            <lang xml:lang="{lang}">{word}</lang>
            <break time="300ms"/>"""
                    
                    if translation:
                        section += f"""
            <lang xml:lang="es-ES">{translation}</lang>
            <break time="500ms"/>"""
                    else:
                        section += """<break time="500ms"/>"""
                    
                    index += 1

            section += """
            <break time="1000ms"/>
            </prosody>
        </voice>"""

        return section

    async def text_to_speech_word_pairs(
        self,
        word_pairs: list[tuple[str, str]],
        source_lang: str,
        target_lang: str,
        output_path: Optional[str] = None,
        complete_text: Optional[str] = None,
        style_preferences=None,
    ) -> Optional[str]:
        try:
            if not output_path:
                temp_dir = self._get_temp_directory()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(temp_dir, f"speech_{timestamp}.mp3")
                logger.info(f"🎵 Grammar-enhanced audio output: {output_path}")

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

            # Use the enhanced SSML generator with grammar awareness
            ssml = self.generate_enhanced_ssml(
                text=complete_text,
                word_pairs=word_pairs,
                source_lang=source_lang,
                target_lang=target_lang,
                style_preferences=style_preferences,
            )
            
            logger.info(f"🎯 Generated grammar-aware SSML with {len(word_pairs) if word_pairs else 0} word pairs")

            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: synthesizer.speak_ssml_async(ssml).get()
            )

            if result.reason == ResultReason.SynthesizingAudioCompleted:
                logger.info(f"✅ Grammar-enhanced audio synthesis completed successfully")
                return os.path.basename(output_path)

            if result.reason == ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                logger.error(f"❌ Grammar-enhanced synthesis canceled: {cancellation_details.reason}")
                if cancellation_details.reason == CancellationReason.Error:
                    logger.error(f"❌ Error details: {cancellation_details.error_details}")

            return None
        except Exception as e:
            logger.error(f"❌ Error in grammar-enhanced text_to_speech_word_pairs: {str(e)}")
            return None

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