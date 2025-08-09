# tts_service.py - FIXED VERSION WITH ASYNC LOOP ISSUE RESOLVED

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

        # Initialize Gemini for AI translations
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.translation_model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                generation_config={
                    "temperature": 0.3,  # Lower temperature for consistent translations
                    "top_p": 0.8,
                    "max_output_tokens": 100,
                }
            )
        else:
            logger.warning("GEMINI_API_KEY not found - AI translations will be unavailable")
            self.translation_model = None

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

        # Voice mapping
        self.voice_mapping = {
            "en": "en-US-JennyMultilingualNeural",
            "es": "es-ES-ArabellaMultilingualNeural", 
            "de": "de-DE-SeraphinaMultilingualNeural",
        }

        # Cache for AI translations
        self._translation_cache = {}

    def _get_temp_directory(self) -> str:
        """Create and return the temporary directory path"""
        if os.name == "nt":  # Windows
            temp_dir = os.path.join(os.environ.get("TEMP", ""), "tts_audio")
        else:  # Unix/Linux
            temp_dir = "/tmp/tts_audio"
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    def _identify_phrasal_verbs(self, words: List[str]) -> List[Tuple[int, int, str]]:
        """
        Identify phrasal verbs in a list of words using pattern recognition.
        Returns list of (start_index, end_index, phrasal_verb_string)
        """
        found_phrases = []
        
        # Common phrasal verb particles (for pattern detection only)
        phrasal_patterns = [
            "up", "down", "in", "out", "on", "off", "away", "back", 
            "over", "through", "along", "around", "forward", "after", "into"
        ]
        
        i = 0
        while i < len(words):
            # Check if current word could be a verb
            if i + 1 < len(words):
                next_word = words[i + 1].lower().rstrip('.,!?;:')
                
                # Check for 3-word phrasal verbs first
                if i + 2 < len(words):
                    third_word = words[i + 2].lower().rstrip('.,!?;:')
                    # Common 3-word patterns: "come up with", "put up with", "look forward to"
                    if next_word in phrasal_patterns and third_word in ["with", "to", "for", "at"]:
                        phrase = f"{words[i]} {words[i + 1]} {words[i + 2]}"
                        found_phrases.append((i, i + 2, phrase.lower()))
                        i += 3
                        continue
                
                # Check for 2-word phrasal verbs
                if next_word in phrasal_patterns:
                    phrase = f"{words[i]} {next_word}"
                    found_phrases.append((i, i + 1, phrase.lower()))
                    i += 2
                    continue
            
            i += 1
        
        return found_phrases

    def _identify_separable_verbs(self, words: List[str], is_german: bool) -> List[Tuple[int, int, str]]:
        """
        Identify German separable verbs in their separated form.
        Returns list of (start_index, end_index, verb_string)
        """
        found_verbs = []
        
        if not is_german:
            return found_verbs
        
        # Common German separable prefixes (for pattern detection only)
        separable_prefixes = [
            'auf', 'aus', 'an', 'ab', 'bei', 'ein', 'mit', 'nach', 
            'vor', 'zu', 'zurück', 'weg', 'weiter', 'fort', 'her', 
            'hin', 'los', 'nieder', 'um', 'unter', 'über', 'wieder'
        ]
        
        # Look for verb...prefix pattern
        for i in range(len(words)):
            # Check next few words for separable prefix
            for j in range(i + 1, min(i + 6, len(words))):  # Check within 5 words
                prefix = words[j].lower().rstrip('.,!?;:')
                
                if prefix in separable_prefixes:
                    # Found potential separable verb
                    verb_phrase = f"{words[i]} {words[j]}"
                    found_verbs.append((i, j, verb_phrase))
                    break
        
        return found_verbs

    def _smart_tokenize_with_phrases(self, text: str, is_german: bool = False) -> List[Tuple[str, bool]]:
        """
        Smart tokenization that preserves phrasal verbs and separable verbs as units.
        Returns list of (token, is_phrase) tuples.
        """
        # First, do basic tokenization
        tokens = re.findall(r"\b\w+(?:'\w+)?\b|[.,!?;:()\[\]{}\"'-]", text)
        
        # Identify phrasal verbs and separable verbs
        phrasal_verbs = self._identify_phrasal_verbs(tokens)
        separable_verbs = self._identify_separable_verbs(tokens, is_german) if is_german else []
        
        # Combine all multi-word units
        all_phrases = phrasal_verbs + separable_verbs
        all_phrases.sort(key=lambda x: x[0])  # Sort by start index
        
        # Build final token list with phrases grouped
        result = []
        i = 0
        
        while i < len(tokens):
            # Check if current position starts a phrase
            phrase_found = False
            for start, end, phrase_text in all_phrases:
                if i == start:
                    # Reconstruct the actual phrase from original tokens (preserving case)
                    actual_phrase = ' '.join(tokens[start:end + 1])
                    result.append((actual_phrase, True))
                    i = end + 1
                    phrase_found = True
                    break
            
            if not phrase_found:
                # Add single token
                result.append((tokens[i], False))
                i += 1
        
        return result

    @lru_cache(maxsize=1000)
    def _translate_word_with_ai(self, word: str, source_lang: str) -> str:
        """
        Use Gemini AI to translate a single word to Spanish.
        Cached to avoid repeated API calls for the same words.
        """
        if not self.translation_model:
            return f"[{word}]"  # Fallback if no AI model available
        
        try:
            # Determine source language name
            lang_name = "English" if source_lang == "en" else "German"
            
            # Create a focused prompt for single word translation
            prompt = f"""Translate this {lang_name} word to Spanish. 
Only respond with the Spanish translation, nothing else.

Word: "{word}"

Spanish:"""

            response = self.translation_model.generate_content(prompt)
            translation = response.text.strip().strip('"').strip()
            
            # Validate the response
            if len(translation.split()) > 10:  # Likely got an explanation instead
                logger.warning(f"AI translation too long for '{word}': {translation}")
                return f"[{word}]"
            
            logger.debug(f"AI translated word: '{word}' -> '{translation}'")
            return translation
            
        except Exception as e:
            logger.error(f"AI translation failed for '{word}': {str(e)}")
            return f"[{word}]"

    def _translate_phrase_with_ai(self, phrase: str, is_german: bool) -> str:
        """
        Use Gemini AI to translate a phrase to Spanish.
        This is now a SYNCHRONOUS method to avoid async loop issues.
        """
        # Check cache first
        cache_key = f"phrase_{phrase}_{is_german}"
        if cache_key in self._translation_cache:
            return self._translation_cache[cache_key]
        
        if not self.translation_model:
            return f"[{phrase}]"
        
        try:
            source_lang = "German" if is_german else "English"
            
            # Create a simple, focused prompt
            prompt = f"""Translate this {source_lang} phrase to Spanish. 
Response with ONLY the Spanish translation, nothing else.

Phrase: "{phrase}"

Spanish:"""

            response = self.translation_model.generate_content(prompt)
            translation = response.text.strip().strip('"').strip()
            
            # Validate response length
            if len(translation.split()) > len(phrase.split()) * 3:  # Sanity check
                logger.warning(f"Translation seems too long for '{phrase}': {translation}")
                translation = f"[{phrase}]"
            else:
                logger.debug(f"AI translated phrase: '{phrase}' -> '{translation}'")
            
            # Cache the result
            self._translation_cache[cache_key] = translation
            return translation
            
        except Exception as e:
            logger.error(f"AI translation failed for phrase '{phrase}': {str(e)}")
            return f"[{phrase}]"

    def _find_translation_for_word_or_phrase(self, token: str, is_phrase: bool, mapping: Dict[str, str], is_german: bool) -> str:
        """
        Find translation for a word or phrase, using AI for all translations.
        Fixed to handle async properly.
        """
        # Clean the token
        clean_token = token.strip().lower().rstrip('.,!?;:()[]{}"\'-')
        
        # Check if it's just punctuation
        if token in ".,!?;:()[]{}\"'-":
            return token
        
        # Check if it's a number
        if clean_token.isdigit():
            return clean_token
        
        # Check mapping first (for provided word pairs)
        if token in mapping:
            return mapping[token]
        if clean_token in mapping:
            return mapping[clean_token]
        
        # Check cache
        cache_key = f"{clean_token}_{is_german}_{is_phrase}"
        if cache_key in self._translation_cache:
            return self._translation_cache[cache_key]
        
        # Use AI for translation
        source_lang = "de" if is_german else "en"
        
        if is_phrase:
            # Now using synchronous method for phrase translation
            translation = self._translate_phrase_with_ai(clean_token, is_german)
        else:
            # Use existing method for single words
            translation = self._translate_word_with_ai(clean_token, source_lang)
        
        # Cache the result
        self._translation_cache[cache_key] = translation
        
        return translation

    def _generate_complete_coverage_ssml(
        self,
        translations_data: Dict,
        style_preferences=None,
    ) -> str:
        """
        Generate SSML with complete word coverage using AI for translations.
        """
        PUNCTUATION = set('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')
        
        ssml = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">"""
        
        logger.info("\n🎤 TTS GENERATION WITH AI-POWERED PHRASE TRANSLATION")
        logger.info("="*60)
        
        for style_info in translations_data.get('style_data', []):
            translation = style_info['translation']
            word_pairs = style_info['word_pairs']
            is_german = style_info['is_german']
            style_name = style_info['style_name']
            
            # Escape XML special characters
            translation = translation.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            logger.info(f"\n📝 Processing {style_name}:")
            logger.info(f"   Translation: \"{translation}\"")
            logger.info(f"   Provided word pairs: {len(word_pairs)}")
            
            # Create basic mapping from provided word pairs
            mapping = {}
            for source, target in word_pairs:
                mapping[source.strip()] = target.strip()
                mapping[source.lower().strip()] = target.strip()
            
            # Add punctuation
            punctuation_map = {
                ".": ".", ",": ",", "!": "!", "?": "?", ";": ";", ":": ":", 
                "(": "(", ")": ")", "'": "'", '"': '"'
            }
            mapping.update(punctuation_map)
            
            # Determine voice and language
            if is_german:
                voice = "de-DE-SeraphinaMultilingualNeural"
                lang = "de-DE"
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
            
            # Add word-by-word section with AI-powered translation
            ssml += """
        <voice name="en-US-JennyMultilingualNeural">
            <prosody rate="0.8">"""
            
            # Smart tokenize with phrase awareness
            token_pairs = self._smart_tokenize_with_phrases(translation, is_german)
            
            logger.info(f"   Tokenized into {len(token_pairs)} units")
            
            for i, (token, is_phrase) in enumerate(token_pairs):
                # Get translation using AI
                spanish_translation = self._find_translation_for_word_or_phrase(
                    token, is_phrase, mapping, is_german
                )
                
                # Clean for speech
                clean_token = token.strip()
                clean_spanish = spanish_translation.replace("[", "").replace("]", "")
                
                # Add to SSML with appropriate timing
                if is_phrase:
                    # Longer pause after phrases
                    ssml += f"""
            <lang xml:lang="{lang}">{clean_token}</lang>
            <break time="400ms"/>
            <lang xml:lang="es-ES">{clean_spanish}</lang>
            <break time="600ms"/>"""
                else:
                    # Normal timing for single words
                    ssml += f"""
            <lang xml:lang="{lang}">{clean_token}</lang>
            <break time="300ms"/>
            <lang xml:lang="es-ES">{clean_spanish}</lang>
            <break time="500ms"/>"""
            
                # Log non-punctuation items
                if clean_token and clean_token not in PUNCTUATION:
                    if is_phrase:
                        logger.debug(f"   {i+1:2d}. [PHRASE-AI] '{clean_token}' -> '{clean_spanish}'")
                    else:
                        logger.debug(f"   {i+1:2d}. [AI] '{clean_token}' -> '{clean_spanish}'")
            
            ssml += """
            <break time="1000ms"/>
            </prosody>
        </voice>"""
        
        ssml += "</speak>"
        
        logger.info(f"\n✅ Generated SSML with AI-powered translations")
        return ssml

    async def text_to_speech_word_pairs_v2(
        self,
        translations_data: Dict,
        source_lang: str,
        target_lang: str,
        style_preferences=None,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Enhanced version that uses AI for all word and phrase translations.
        """
        try:
            if not output_path:
                temp_dir = self._get_temp_directory()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(temp_dir, f"speech_{timestamp}.mp3")
                logger.info(f"\n📂 Output path: {output_path}")

            # Generate SSML with AI-powered translations
            ssml = self._generate_complete_coverage_ssml(
                translations_data=translations_data,
                style_preferences=style_preferences,
            )
            
            # Log the generated SSML for debugging
            logger.info(f"\n📄 Generated SSML preview:")
            print("Generated SSML preview (first 500 chars):")
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
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

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
            lines = complete_text.split('\n')
            current_language = None
            current_style = None
            
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
                    match = re.search(r'"([^"]+)"', line)
                    if match:
                        pairs_text = match.group(1)
                        pairs = []
                        pair_matches = re.findall(r'([^()]+?)\s*\(([^)]+)\)', pairs_text)
                        for source, target in pair_matches:
                            source = source.strip()
                            target = target.strip()
                            if source and target:
                                pairs.append((source, target))
                        style_word_pairs[current_style] = pairs
            
            # Create style data entries
            for style_name in ['german_native', 'german_colloquial', 'german_informal', 'german_formal',
                              'english_native', 'english_colloquial', 'english_informal', 'english_formal']:
                
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
        """Convert SSML to speech"""
        synthesizer = None
        try:
            if not output_path:
                temp_dir = self._get_temp_directory()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(temp_dir, f"speech_{timestamp}.mp3")
                logger.info(f"🎵 Output path: {output_path}")

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
            logger.error(f"❌ Exception in text_to_speech: {str(e)}")
            return None
        finally:
            if synthesizer:
                try:
                    synthesizer.stop_speaking_async()
                except:
                    pass




















### THIS CODE DO WORD FOR WORD DETECTION WITHOUT AI (FOR TESTING PURPOSES) ###
### DOSENT COUNT PHRASAL VERBS OR GERMAN SEPARABLE VERBS ###
### THATS WHY IT IS COMMENTED OUT ###



# # tts_service.py - Enhanced with real translation fallback

# from azure.cognitiveservices.speech import (
#     SpeechConfig,
#     SpeechSynthesizer,
#     SpeechSynthesisOutputFormat,
#     ResultReason,
#     CancellationReason,
# )
# from azure.cognitiveservices.speech.audio import AudioOutputConfig
# import os
# from typing import Optional, Dict, List, Tuple
# from datetime import datetime
# import asyncio
# import re
# import logging
# import google.generativeai as genai
# from functools import lru_cache

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# class EnhancedTTSService:
#     def __init__(self):
#         # Initialize Speech Config
#         self.subscription_key = os.getenv("AZURE_SPEECH_KEY")
#         self.region = os.getenv("AZURE_SPEECH_REGION")

#         if not self.subscription_key or not self.region:
#             raise ValueError(
#                 "Azure Speech credentials not found in environment variables"
#             )

#         # Initialize Gemini for fallback translations
#         self.gemini_api_key = os.getenv("GEMINI_API_KEY")
#         if self.gemini_api_key:
#             genai.configure(api_key=self.gemini_api_key)
#             self.translation_model = genai.GenerativeModel(
#                 model_name="gemini-2.0-flash",
#                 generation_config={
#                     "temperature": 0.3,  # Lower temperature for more consistent translations
#                     "top_p": 0.8,
#                     "max_output_tokens": 100,
#                 }
#             )
#         else:
#             logger.warning("GEMINI_API_KEY not found - fallback translations will be limited")
#             self.translation_model = None

#         # Add this before creating SpeechConfig
#         os.environ["SPEECH_CONTAINER_OPTION"] = "1"
#         os.environ["SPEECH_SYNTHESIS_PLATFORM_CONFIG"] = "container"
        
#         # Create speech config with endpoint
#         self.speech_host = f"wss://{self.region}.tts.speech.microsoft.com/cognitiveservices/websocket/v1"
#         self.speech_config = SpeechConfig(
#             subscription=self.subscription_key,
#             endpoint=self.speech_host
#         )
        
#         self.speech_config.set_speech_synthesis_output_format(
#             SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
#         )

#         # Force CPU usage in container environment
#         tts_device = os.getenv("TTS_DEVICE", "cpu").lower()
#         if os.getenv("CONTAINER_ENV", "false").lower() == "true":
#             tts_device = "cpu"
            
#         logger.info(f"Using TTS device: {tts_device}")

#         # Enhanced voice mapping with grammar-aware selection
#         self.voice_mapping = {
#             "en": "en-US-JennyMultilingualNeural",
#             "es": "es-ES-ArabellaMultilingualNeural", 
#             "de": "de-DE-SeraphinaMultilingualNeural",
#         }

#         # Grammar patterns for enhanced grouping
#         self.phrasal_verbs = [
#             "turn off", "turn on", "look up", "look for", "come up with", "put up with",
#             "get up", "wake up", "give up", "pick up", "set up", "take off", "put on",
#             "go out", "come in", "sit down", "stand up", "run into", "look after"
#         ]
        
#         self.separable_verbs = [
#             "aufstehen", "mitkommen", "ausgehen", "nachschauen", "einladen", "vorstellen",
#             "anrufen", "aufmachen", "zumachen", "abholen", "fernsehen", "einkaufen",
#             "mitbringen", "vorlesen", "zurückkommen", "weggehen"
#         ]

#         # Extended common word translations (significantly expanded)
#         self.common_translations = {
#             # English articles, pronouns, prepositions
#             "i": "yo", "you": "tú/usted", "he": "él", "she": "ella", "it": "eso/lo", 
#             "we": "nosotros", "they": "ellos/ellas", "me": "me/mí", "him": "él/lo", 
#             "her": "ella/la", "us": "nosotros", "them": "ellos/los",
            
#             # Articles
#             "the": "el/la", "a": "un/una", "an": "un/una", "this": "este/esta", 
#             "that": "ese/esa", "these": "estos/estas", "those": "esos/esas",
            
#             # Common verbs
#             "is": "es/está", "are": "son/están", "was": "era/estaba", "were": "eran/estaban",
#             "be": "ser/estar", "been": "sido/estado", "being": "siendo/estando",
#             "have": "tener/haber", "has": "tiene/ha", "had": "tenía/había",
#             "do": "hacer", "does": "hace", "did": "hizo", "done": "hecho",
#             "will": "será/va", "would": "sería/iría", "shall": "deberá", "should": "debería",
#             "may": "puede", "might": "podría", "must": "debe", "can": "puede", "could": "podría",
#             "go": "ir", "goes": "va", "went": "fue", "gone": "ido", "going": "yendo",
#             "come": "venir", "comes": "viene", "came": "vino", "coming": "viniendo",
#             "make": "hacer", "makes": "hace", "made": "hizo", "making": "haciendo",
#             "take": "tomar", "takes": "toma", "took": "tomó", "taken": "tomado",
#             "give": "dar", "gives": "da", "gave": "dio", "given": "dado",
#             "get": "obtener", "gets": "obtiene", "got": "obtuvo", "gotten": "obtenido",
#             "say": "decir", "says": "dice", "said": "dijo", "saying": "diciendo",
#             "see": "ver", "sees": "ve", "saw": "vio", "seen": "visto",
#             "know": "saber", "knows": "sabe", "knew": "sabía", "known": "sabido",
#             "think": "pensar", "thinks": "piensa", "thought": "pensó", "thinking": "pensando",
#             "want": "querer", "wants": "quiere", "wanted": "quería", "wanting": "queriendo",
#             "look": "mirar", "looks": "mira", "looked": "miró", "looking": "mirando",
#             "use": "usar", "uses": "usa", "used": "usó", "using": "usando",
#             "find": "encontrar", "finds": "encuentra", "found": "encontró", "finding": "encontrando",
#             "tell": "decir", "tells": "dice", "told": "dijo", "telling": "diciendo",
#             "ask": "preguntar", "asks": "pregunta", "asked": "preguntó", "asking": "preguntando",
#             "work": "trabajar", "works": "trabaja", "worked": "trabajó", "working": "trabajando",
#             "seem": "parecer", "seems": "parece", "seemed": "pareció", "seeming": "pareciendo",
#             "feel": "sentir", "feels": "siente", "felt": "sintió", "feeling": "sintiendo",
#             "try": "intentar", "tries": "intenta", "tried": "intentó", "trying": "intentando",
#             "leave": "dejar", "leaves": "deja", "left": "dejó", "leaving": "dejando",
#             "call": "llamar", "calls": "llama", "called": "llamó", "calling": "llamando",
            
#             # Prepositions and conjunctions
#             "in": "en", "on": "sobre/en", "at": "en", "to": "a/para", "for": "para/por",
#             "of": "de", "with": "con", "by": "por", "from": "de/desde", "up": "arriba",
#             "about": "sobre/acerca", "into": "dentro", "through": "a través", "after": "después",
#             "over": "sobre", "between": "entre", "out": "fuera", "against": "contra",
#             "during": "durante", "without": "sin", "before": "antes", "under": "bajo",
#             "around": "alrededor", "among": "entre", 
            
#             "and": "y", "or": "o", "but": "pero", "if": "si", "because": "porque",
#             "as": "como", "until": "hasta", "while": "mientras", "since": "desde",
#             "although": "aunque", "though": "aunque", "when": "cuando", "where": "donde",
#             "so": "así/entonces", "than": "que", "too": "también", "very": "muy",
#             "just": "solo/justo", "there": "allí/ahí", "here": "aquí", "then": "entonces",
#             "now": "ahora", "only": "solo", "also": "también", "well": "bien",
#             "even": "incluso", "back": "atrás", "still": "todavía", "why": "por qué",
#             "how": "cómo", "what": "qué", "which": "cuál", "who": "quién",
#             "all": "todo", "some": "algo/algunos", "no": "no", "not": "no",
#             "more": "más", "other": "otro", "another": "otro", "much": "mucho",
#             "many": "muchos", "such": "tal", "own": "propio", "same": "mismo",
#             "each": "cada", "every": "cada/todo", "both": "ambos", "few": "pocos",
#             "most": "mayoría", "any": "cualquier", "several": "varios",
#             "therein": "allí/en eso", "thereof": "de eso", "whereby": "por lo cual",
            
#             # German common words
#             "ich": "yo", "du": "tú", "er": "él", "sie": "ella/ellos", "es": "eso",
#             "wir": "nosotros", "ihr": "vosotros", "mich": "me", "dich": "te",
#             "sich": "se", "mir": "me", "dir": "te", "uns": "nos",
            
#             "der": "el", "die": "la/las", "das": "el/lo", "ein": "un", "eine": "una",
#             "den": "el", "dem": "el", "des": "del", "einen": "un", "einem": "un",
#             "einer": "una", "eines": "un",
            
#             "und": "y", "oder": "o", "aber": "pero", "denn": "pues", "weil": "porque",
#             "wenn": "si/cuando", "dass": "que", "ob": "si", "als": "cuando/como",
#             "wie": "como", "wo": "donde", "wann": "cuándo", "warum": "por qué",
#             "was": "qué", "wer": "quién", "welcher": "cuál",
            
#             "nicht": "no", "kein": "ningún", "keine": "ninguna", "nie": "nunca",
#             "nichts": "nada", "niemand": "nadie",
            
#             "zu": "a/para", "von": "de", "mit": "con", "bei": "en/con", "nach": "después/hacia",
#             "aus": "de/desde", "auf": "sobre", "an": "en", "in": "en", "über": "sobre",
#             "unter": "bajo", "vor": "antes", "hinter": "detrás", "neben": "al lado",
#             "zwischen": "entre", "für": "para", "gegen": "contra", "ohne": "sin",
#             "um": "alrededor/para", "durch": "a través",
            
#             "haben": "tener", "hat": "tiene", "hatte": "tenía", "gehabt": "tenido",
#             "sein": "ser/estar", "ist": "es", "sind": "son", "war": "era", "waren": "eran",
#             "werden": "llegar a ser", "wird": "será", "wurde": "fue", "geworden": "llegado a ser",
#             "können": "poder", "kann": "puede", "konnte": "podía", "gekonnt": "podido",
#             "müssen": "deber", "muss": "debe", "musste": "debía", "gemusst": "debido",
#             "wollen": "querer", "will": "quiere", "wollte": "quería", "gewollt": "querido",
#             "sollen": "deber", "soll": "debe", "sollte": "debería", "gesollt": "debido",
#             "dürfen": "poder/permitir", "darf": "puede", "durfte": "podía", "gedurft": "podido",
#             "mögen": "gustar", "mag": "gusta", "mochte": "gustaba", "gemocht": "gustado",
#             "gehen": "ir", "geht": "va", "ging": "fue", "gegangen": "ido",
#             "kommen": "venir", "kommt": "viene", "kam": "vino", "gekommen": "venido",
#             "machen": "hacer", "macht": "hace", "machte": "hizo", "gemacht": "hecho",
#             "sehen": "ver", "sieht": "ve", "sah": "vio", "gesehen": "visto",
#             "geben": "dar", "gibt": "da", "gab": "dio", "gegeben": "dado",
#             "nehmen": "tomar", "nimmt": "toma", "nahm": "tomó", "genommen": "tomado",
#             "finden": "encontrar", "findet": "encuentra", "fand": "encontró", "gefunden": "encontrado",
#             "sagen": "decir", "sagt": "dice", "sagte": "dijo", "gesagt": "dicho",
#             "wissen": "saber", "weiß": "sabe", "wusste": "sabía", "gewusst": "sabido",
#             "denken": "pensar", "denkt": "piensa", "dachte": "pensó", "gedacht": "pensado",
#         }

#         # Cache for dynamic translations
#         self._translation_cache = {}

#     def _get_temp_directory(self) -> str:
#         """Create and return the temporary directory path"""
#         if os.name == "nt":  # Windows
#             temp_dir = os.path.join(os.environ.get("TEMP", ""), "tts_audio")
#         else:  # Unix/Linux
#             temp_dir = "/tmp/tts_audio"
#         os.makedirs(temp_dir, exist_ok=True)
#         return temp_dir

#     @lru_cache(maxsize=1000)
#     def _translate_word_with_ai(self, word: str, source_lang: str) -> str:
#         """
#         Use Gemini AI to translate a single word or short phrase to Spanish.
#         Cached to avoid repeated API calls for the same words.
#         """
#         if not self.translation_model:
#             return f"[{word}]"  # Fallback if no AI model available
        
#         try:
#             # Determine source language name
#             lang_name = "English" if source_lang == "en" else "German"
            
#             # Create a focused prompt for single word/phrase translation
#             prompt = f"""Translate this {lang_name} word or phrase to Spanish. 
# Only respond with the Spanish translation, nothing else.
# If there are multiple possible translations, give the most common one.

# Word/phrase: "{word}"

# Spanish translation:"""

#             response = self.translation_model.generate_content(prompt)
#             translation = response.text.strip()
            
#             # Clean up the response
#             translation = translation.replace('"', '').replace("'", "").strip()
            
#             # Validate the response (should be relatively short for a word/phrase)
#             if len(translation.split()) > 10:  # Likely got an explanation instead of translation
#                 logger.warning(f"AI translation too long for '{word}': {translation}")
#                 return f"[{word}]"
            
#             logger.debug(f"AI translated: '{word}' -> '{translation}'")
#             return translation
            
#         except Exception as e:
#             logger.error(f"AI translation failed for '{word}': {str(e)}")
#             return f"[{word}]"

#     def _find_translation_for_word(self, word: str, mapping: Dict[str, str], is_german: bool) -> str:
#         """
#         Find translation for a word with multiple fallback strategies.
#         Now includes real translation as the final fallback.
#         """
#         # Clean the word (remove punctuation for lookup)
#         clean_word = word.strip().lower().rstrip('.,!?;:()[]{}"\'-')
        
#         # Strategy 1: Direct lookup in provided mapping
#         if word in mapping:
#             return mapping[word]
#         if clean_word in mapping:
#             return mapping[clean_word]
#         if word.lower() in mapping:
#             return mapping[word.lower()]
            
#         # Strategy 2: Try without punctuation
#         if clean_word in mapping:
#             return mapping[clean_word]
            
#         # Strategy 3: Check if it's just punctuation
#         if word in ".,!?;:()[]{}\"'-":
#             return word  # Keep punctuation as is
            
#         # Strategy 4: Numbers stay the same
#         if clean_word.isdigit():
#             return clean_word
            
#         # Strategy 5: Check translation cache
#         cache_key = f"{clean_word}_{is_german}"
#         if cache_key in self._translation_cache:
#             return self._translation_cache[cache_key]
            
#         # Strategy 6: Use AI translation for missing words
#         source_lang = "de" if is_german else "en"
#         translation = self._translate_word_with_ai(clean_word, source_lang)
        
#         # Cache the translation
#         self._translation_cache[cache_key] = translation
        
#         # Log the translation
#         if translation.startswith('[') and translation.endswith(']'):
#             logger.debug(f"🔄 Fallback (no translation found): '{word}' -> '{translation}'")
#         else:
#             logger.debug(f"✅ AI translated: '{word}' -> '{translation}'")
            
#         return translation

#     def _create_comprehensive_word_mapping(self, word_pairs: List[Tuple[str, str]], is_german: bool) -> Dict[str, str]:
#         """
#         Create a comprehensive mapping that ensures ALL words have translations.
#         """
#         mapping = {}
        
#         # First, add all explicit word pairs
#         for source, target in word_pairs:
#             # Store both original case and lowercase versions
#             mapping[source.strip()] = target.strip()
#             mapping[source.lower().strip()] = target.strip()
            
#             # Handle compound phrases
#             source_words = source.strip().split()
#             if len(source_words) > 1:
#                 # Store the full phrase
#                 mapping[' '.join(source_words)] = target.strip()
#                 mapping[' '.join(source_words).lower()] = target.strip()
                
#         # Add common word translations as fallback
#         mapping.update(self.common_translations)
        
#         # Add punctuation handling
#         punctuation_map = {
#             ".": ".", ",": ",", "!": "!", "?": "?", ";": ";", ":": ":", 
#             "(": "(", ")": ")", "'": "'", '"': '"'
#         }
#         mapping.update(punctuation_map)
        
#         logger.info(f"Created comprehensive word mapping with {len(mapping)} entries")
#         return mapping

#     async def text_to_speech_word_pairs_v2(
#         self,
#         translations_data: Dict,
#         source_lang: str,
#         target_lang: str,
#         style_preferences=None,
#         output_path: Optional[str] = None,
#     ) -> Optional[str]:
#         """
#         Enhanced version that ensures ALL words are translated using AI when needed.
#         """
#         try:
#             if not output_path:
#                 temp_dir = self._get_temp_directory()
#                 timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#                 output_path = os.path.join(temp_dir, f"speech_{timestamp}.mp3")
#                 logger.info(f"\n📂 Output path: {output_path}")

#             # Generate SSML with comprehensive word coverage
#             ssml = self._generate_complete_coverage_ssml(
#                 translations_data=translations_data,
#                 style_preferences=style_preferences,
#             )
            
#             # Log the generated SSML for debugging
#             logger.info(f"\n📄 Generated SSML preview:")
#             print("Generated SSML preview (first 500 chars):")
#             print(ssml[:500] + "..." if len(ssml) > 500 else ssml)

#             # Create audio config and synthesizer
#             audio_config = AudioOutputConfig(filename=output_path)
#             speech_config = SpeechConfig(
#                 subscription=self.subscription_key, region=self.region
#             )
#             speech_config.set_speech_synthesis_output_format(
#                 SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
#             )

#             synthesizer = SpeechSynthesizer(
#                 speech_config=speech_config, audio_config=audio_config
#             )

#             # Synthesize speech
#             result = await asyncio.get_event_loop().run_in_executor(
#                 None, lambda: synthesizer.speak_ssml_async(ssml).get()
#             )

#             if result.reason == ResultReason.SynthesizingAudioCompleted:
#                 logger.info(f"\n✅ Successfully generated audio: {os.path.basename(output_path)}")
#                 return os.path.basename(output_path)

#             if result.reason == ResultReason.Canceled:
#                 cancellation_details = result.cancellation_details
#                 logger.error(f"❌ Synthesis canceled: {cancellation_details.reason}")
#                 if cancellation_details.reason == CancellationReason.Error:
#                     logger.error(f"❌ Error details: {cancellation_details.error_details}")

#             return None

#         except Exception as e:
#             logger.error(f"❌ Error in text_to_speech_word_pairs_v2: {str(e)}")
#             return None

#     # def _generate_complete_coverage_ssml(
#     #     self,
#     #     translations_data: Dict,
#     #     style_preferences=None,
#     # ) -> str:
#     #     """
#     #     Generate SSML with complete word coverage - every word gets properly translated.
#     #     """
#     #     ssml = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">"""
        
#     #     # Log configuration
#     #     logger.info("\n🎤 TTS COMPLETE COVERAGE GENERATION")
#     #     logger.info("="*60)
        
#     #     # Process each style with comprehensive word coverage
#     #     for style_info in translations_data.get('style_data', []):
#     #         translation = style_info['translation']
#     #         word_pairs = style_info['word_pairs']
#     #         is_german = style_info['is_german']
#     #         style_name = style_info['style_name']
            
#     #         # Escape XML special characters in translation
#     #         translation = translation.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
#     #         logger.info(f"\n📝 Processing {style_name}:")
#     #         logger.info(f"   Translation: \"{translation}\"")
#     #         logger.info(f"   Word pairs count: {len(word_pairs)}")
            
#     #         # Create comprehensive mapping
#     #         mapping = self._create_comprehensive_word_mapping(word_pairs, is_german)
            
#     #         # Determine voice and language
#     #         if is_german:
#     #             voice = "de-DE-SeraphinaMultilingualNeural"
#     #             lang = "de-DE"
#     #         else:
#     #             voice = "en-US-JennyMultilingualNeural"
#     #             lang = "en-US"
            
#     #         # Add main translation
#     #         ssml += f"""
#     #     <voice name="{voice}">
#     #         <prosody rate="1.0">
#     #             <lang xml:lang="{lang}">{translation}</lang>
#     #             <break time="1000ms"/>
#     #         </prosody>
#     #     </voice>"""
            
#     #         # Add comprehensive word-by-word section
#     #         ssml += """
#     #     <voice name="en-US-JennyMultilingualNeural">
#     #         <prosody rate="0.8">"""
            
#     #         # Tokenize the translation properly
#     #         words = self._smart_tokenize(translation)
            
#     #         logger.info(f"   Tokenized into {len(words)} words/tokens")
            
#     #         # Process each word/token
#     #         for i, word in enumerate(words):
#     #             # Find translation for this word (now with real translation fallback)
#     #             spanish_translation = self._find_translation_for_word(word, mapping, is_german)
                
#     #             # Clean word for speech (remove brackets if added by fallback)
#     #             clean_word = word.strip()
#     #             clean_spanish = spanish_translation.replace("[", "").replace("]", "")
                
#     #             # Add to SSML
#     #             ssml += f"""
#     #         <lang xml:lang="{lang}">{clean_word}</lang>
#     #         <break time="300ms"/>
#     #         <lang xml:lang="es-ES">{clean_spanish}</lang>
#     #         <break time="500ms"/>"""
            
#     #             logger.debug(f"   {i+1:2d}. '{clean_word}' -> '{clean_spanish}'")
            
#     #         ssml += """
#     #         <break time="1000ms"/>
#     #         </prosody>
#     #     </voice>"""
        
#     #     ssml += "</speak>"
        
#     #     logger.info(f"\n✅ Generated complete SSML with full word coverage")
#     #     return ssml


#     def _generate_complete_coverage_ssml(
#         self,
#         translations_data: Dict,
#         style_preferences=None,
#     ) -> str:
#         """
#         Generate SSML with complete word coverage - every word gets properly translated.
#         """
#         # Define punctuation characters to exclude from logging
#         PUNCTUATION = set('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')
        
#         ssml = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">"""
        
#         # Log configuration
#         logger.info("\n🎤 TTS COMPLETE COVERAGE GENERATION")
#         logger.info("="*60)
        
#         # Process each style with comprehensive word coverage
#         for style_info in translations_data.get('style_data', []):
#             translation = style_info['translation']
#             word_pairs = style_info['word_pairs']
#             is_german = style_info['is_german']
#             style_name = style_info['style_name']
            
#             # Escape XML special characters in translation
#             translation = translation.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
#             logger.info(f"\n📝 Processing {style_name}:")
#             logger.info(f"   Translation: \"{translation}\"")
#             logger.info(f"   Word pairs count: {len(word_pairs)}")
            
#             # Create comprehensive mapping
#             mapping = self._create_comprehensive_word_mapping(word_pairs, is_german)
            
#             # Determine voice and language
#             if is_german:
#                 voice = "de-DE-SeraphinaMultilingualNeural"
#                 lang = "de-DE"
#             else:
#                 voice = "en-US-JennyMultilingualNeural"
#                 lang = "en-US"
            
#             # Add main translation
#             ssml += f"""
#         <voice name="{voice}">
#             <prosody rate="1.0">
#                 <lang xml:lang="{lang}">{translation}</lang>
#                 <break time="1000ms"/>
#             </prosody>
#         </voice>"""
            
#             # Add comprehensive word-by-word section
#             ssml += """
#         <voice name="en-US-JennyMultilingualNeural">
#             <prosody rate="0.8">"""
            
#             # Tokenize the translation properly
#             words = self._smart_tokenize(translation)
            
#             logger.info(f"   Tokenized into {len(words)} words/tokens")
            
#             # Process each word/token
#             for i, word in enumerate(words):
#                 # Find translation for this word (now with real translation fallback)
#                 spanish_translation = self._find_translation_for_word(word, mapping, is_german)
                
#                 # Clean word for speech (remove brackets if added by fallback)
#                 clean_word = word.strip()
#                 clean_spanish = spanish_translation.replace("[", "").replace("]", "")
                
#                 # Add to SSML
#                 ssml += f"""
#             <lang xml:lang="{lang}">{clean_word}</lang>
#             <break time="300ms"/>
#             <lang xml:lang="es-ES">{clean_spanish}</lang>
#             <break time="500ms"/>"""
            
#                 # Only log non-punctuation words
#                 if clean_word and clean_word not in PUNCTUATION:
#                     logger.debug(f"   {i+1:2d}. '{clean_word}' -> '{clean_spanish}'")
            
#             ssml += """
#             <break time="1000ms"/>
#             </prosody>
#         </voice>"""
        
#         ssml += "</speak>"
        
#         logger.info(f"\n✅ Generated complete SSML with full word coverage")
#         return ssml

#     def _smart_tokenize(self, text: str) -> List[str]:
#         """
#         Smart tokenization that preserves meaningful phrases and handles punctuation.
#         """
#         # First, handle common contractions and phrases
#         text = text.replace("don't", "do not").replace("won't", "will not").replace("can't", "cannot")
#         text = text.replace("I'm", "I am").replace("you're", "you are").replace("it's", "it is")
#         text = text.replace("we're", "we are").replace("they're", "they are")
#         text = text.replace("I've", "I have").replace("you've", "you have").replace("we've", "we have")
#         text = text.replace("hasn't", "has not").replace("haven't", "have not").replace("hadn't", "had not")
#         text = text.replace("isn't", "is not").replace("aren't", "are not").replace("wasn't", "was not")
#         text = text.replace("weren't", "were not").replace("doesn't", "does not").replace("didn't", "did not")
        
#         # Use regex to split while preserving punctuation
#         tokens = re.findall(r"\b\w+\b|[.,!?;:()\[\]{}\"'-]", text)
        
#         # Filter out empty tokens
#         tokens = [token.strip() for token in tokens if token.strip()]
        
#         return tokens

#     async def text_to_speech_word_pairs(
#         self,
#         word_pairs: List[Tuple[str, str, bool]],
#         source_lang: str,
#         target_lang: str,
#         output_path: Optional[str] = None,
#         complete_text: Optional[str] = None,
#         style_preferences=None,
#     ) -> Optional[str]:
#         """
#         Legacy method for backward compatibility.
#         Converts old format to new format and calls the v2 method.
#         """
#         # Convert legacy format to new structured format
#         translations_data = {
#             'translations': [],
#             'style_data': []
#         }
        
#         # Parse complete text to get individual translations and their word pairs
#         if complete_text:
#             # Parse the complete text to extract translations and word-by-word pairs per style
#             lines = complete_text.split('\n')
#             current_language = None
#             current_style = None
            
#             # Track which translation and word pairs belong to which style
#             style_translations = {}
#             style_word_pairs = {}
            
#             for line in lines:
#                 line = line.strip()
                
#                 # Detect language section
#                 if 'German Translation:' in line:
#                     current_language = 'german'
#                 elif 'English Translation:' in line:
#                     current_language = 'english'
                
#                 # Detect style and extract translation
#                 if '* Conversational-native:' in line:
#                     current_style = f'{current_language}_native' if current_language else None
#                     match = re.search(r'"([^"]+)"', line)
#                     if match and current_style:
#                         style_translations[current_style] = match.group(1)
#                 elif '* Conversational-colloquial:' in line:
#                     current_style = f'{current_language}_colloquial' if current_language else None
#                     match = re.search(r'"([^"]+)"', line)
#                     if match and current_style:
#                         style_translations[current_style] = match.group(1)
#                 elif '* Conversational-informal:' in line:
#                     current_style = f'{current_language}_informal' if current_language else None
#                     match = re.search(r'"([^"]+)"', line)
#                     if match and current_style:
#                         style_translations[current_style] = match.group(1)
#                 elif '* Conversational-formal:' in line:
#                     current_style = f'{current_language}_formal' if current_language else None
#                     match = re.search(r'"([^"]+)"', line)
#                     if match and current_style:
#                         style_translations[current_style] = match.group(1)
                
#                 # Extract word-by-word pairs for current style
#                 if 'word by word' in line and current_style:
#                     # Extract the word pairs from the line
#                     match = re.search(r'"([^"]+)"', line)
#                     if match:
#                         pairs_text = match.group(1)
#                         pairs = []
#                         # Parse pairs like "Pineapple juice (jugo de piña)"
#                         pair_matches = re.findall(r'([^()]+?)\s*\(([^)]+)\)', pairs_text)
#                         for source, target in pair_matches:
#                             source = source.strip()
#                             target = target.strip()
#                             if source and target:
#                                 pairs.append((source, target))
#                         style_word_pairs[current_style] = pairs
            
#             # Now create style data entries with correct associations
#             for style_name in ['german_native', 'german_colloquial', 'german_informal', 'german_formal',
#                               'english_native', 'english_colloquial', 'english_informal', 'english_formal']:
                
#                 # Check if this style is enabled and has data
#                 is_german = style_name.startswith('german')
#                 style_suffix = style_name.split('_')[1]
                
#                 # Check if style is enabled
#                 style_enabled = False
#                 if is_german:
#                     style_enabled = getattr(style_preferences, f'german_{style_suffix}', False)
#                     word_by_word_enabled = style_preferences.german_word_by_word
#                 else:
#                     style_enabled = getattr(style_preferences, f'english_{style_suffix}', False)
#                     word_by_word_enabled = style_preferences.english_word_by_word
                
#                 if style_enabled and style_name in style_translations:
#                     translations_data['style_data'].append({
#                         'translation': style_translations[style_name],
#                         'word_pairs': style_word_pairs.get(style_name, []) if word_by_word_enabled else [],
#                         'is_german': is_german,
#                         'style_name': style_name
#                     })
        
#         # Call the v2 method with structured data
#         return await self.text_to_speech_word_pairs_v2(
#             translations_data=translations_data,
#             source_lang=source_lang,
#             target_lang=target_lang,
#             style_preferences=style_preferences,
#             output_path=output_path,
#         )

#     async def text_to_speech(
#         self, ssml: str, output_path: Optional[str] = None
#     ) -> Optional[str]:
#         """Convert SSML to speech with grammar-aware language handling"""
#         synthesizer = None
#         try:
#             if not output_path:
#                 temp_dir = self._get_temp_directory()
#                 timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#                 output_path = os.path.join(temp_dir, f"speech_{timestamp}.mp3")
#                 logger.info(f"🎵 Grammar-enhanced output path: {output_path}")

#             audio_config = AudioOutputConfig(filename=output_path)
#             synthesizer = SpeechSynthesizer(
#                 speech_config=self.speech_config, audio_config=audio_config
#             )

#             result = await asyncio.get_event_loop().run_in_executor(
#                 None, lambda: synthesizer.speak_ssml_async(ssml).get()
#             )

#             if result.reason == ResultReason.SynthesizingAudioCompleted:
#                 return os.path.basename(output_path)

#             return None

#         except Exception as e:
#             logger.error(f"❌ Exception in grammar-enhanced text_to_speech: {str(e)}")
#             return None
#         finally:
#             if synthesizer:
#                 try:
#                     synthesizer.stop_speaking_async()
#                 except:
#                     pass
