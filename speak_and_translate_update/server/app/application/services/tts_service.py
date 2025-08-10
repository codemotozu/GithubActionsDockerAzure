




# tts_service.py - Complete fixed version with AI translation

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

        # Initialize Gemini for intelligent phrase translation
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.translation_model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                generation_config={
                    "temperature": 0.2,  # Lower temperature for more consistent translations
                    "top_p": 0.8,
                    "max_output_tokens": 150,
                }
            )
        else:
            logger.warning("GEMINI_API_KEY not found - fallback translations will be limited")
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

        # Enhanced voice mapping with grammar-aware selection
        self.voice_mapping = {
            "en": "en-US-JennyMultilingualNeural",
            "es": "es-ES-ArabellaMultilingualNeural", 
            "de": "de-DE-SeraphinaMultilingualNeural",
        }

        # Enhanced phrasal verb patterns - more comprehensive
        self.phrasal_verb_patterns = [
            # Common phrasal verbs with particles
            r'\b(turn|switch|put|take|look|pick|set|get|wake|give|come|go|sit|stand|run|bring|call|carry|cut|fill|find|hang|hold|keep|let|make|move|pull|push|send|show|shut|slow|speak|start|stay|throw|try|work)\s+(on|off|up|down|in|out|away|back|over|through|around|about|after|for|into|onto|upon)\b',
            # Phrasal verbs with prepositions
            r'\b(look|care|deal|depend|insist|rely|result|succeed|think|worry|consist|account|approve|arrive|belong|complain|concentrate|congratulate|decide|dream|escape|excuse|forgive|hope|listen|object|participate|pay|prepare|prevent|protect|recover|refer|search|suffer|vote|wait|aim|apologize|apply|argue|ask|believe|choose|complain|decide|hear|know|learn|speak|talk|tell|think|wonder|worry)\s+(for|after|about|at|on|to|with|from|of|in|into|over|under|through|across|along|around|behind|beside|between|beyond|by|during|except|inside|near|outside|since|until|within|without)\b',
            # Multi-word phrasal verbs
            r'\b(come up with|put up with|look forward to|get along with|run out of|keep up with|look down on|catch up with|get rid of|look up to|cut down on|drop out of|face up to|get away with|get back at|get on with|give in to|go along with|live up to|make up for|put up with|run away from|stand up for|turn away from|watch out for)\b',
        ]

        # Enhanced German separable verb patterns
        self.separable_verb_patterns = [
            # Common separable prefixes
            r'\b(ab|an|auf|aus|bei|dar|durch|ein|empor|entgegen|entlang|fort|her|hin|hinter|los|mit|nach|nieder|über|um|unter|vor|weg|weiter|wieder|zu|zurück|zusammen)([a-zäöüß]+)\b',
            # Separated forms (prefix at end)
            r'\b([a-zäöüß]+)\s+(ab|an|auf|aus|bei|dar|durch|ein|empor|entgegen|entlang|fort|her|hin|hinter|los|mit|nach|nieder|über|um|unter|vor|weg|weiter|wieder|zu|zurück|zusammen)\b',
        ]

        # Minimal core translations - only absolute essentials, everything else uses AI
        self.core_translations = {
            # Critical articles (most frequent)
            "the": "el/la", "a": "un/una", "an": "un/una",
            "der": "el", "die": "la", "das": "el/lo", "ein": "un", "eine": "una",
            
            # Critical pronouns
            "i": "yo", "you": "tú", "he": "él", "she": "ella", "we": "nosotros", "they": "ellos",
            "ich": "yo", "du": "tú", "er": "él", "sie": "ella", "wir": "nosotros",
            
            # Critical connectors
            "and": "y", "or": "o", "but": "pero", "und": "y", "oder": "o", "aber": "pero",
            
            # Essential negations
            "not": "no", "no": "no", "nicht": "no",
            
            # Punctuation stays the same
            ".": ".", ",": ",", "!": "!", "?": "?", ";": ";", ":": ":", "(": "(", ")": ")",
        }

        # Enhanced cache for dynamic AI translations - larger cache since we rely on AI more
        self._translation_cache = {}
        self._phrase_cache = {}
        
        # Batch translation for efficiency
        self._batch_translation_queue = []

    def _get_temp_directory(self) -> str:
        """Create and return the temporary directory path"""
        if os.name == "nt":  # Windows
            temp_dir = os.path.join(os.environ.get("TEMP", ""), "tts_audio")
        else:  # Unix/Linux
            temp_dir = "/tmp/tts_audio"
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    @lru_cache(maxsize=2000)
    def _translate_with_ai_comprehensive(self, word_or_phrase: str, source_lang: str, context: str = "") -> str:
        """
        Comprehensive AI translation that builds dynamic dictionary entries.
        This replaces the need for huge static dictionaries.
        """
        if not self.translation_model:
            return f"[{word_or_phrase}]"
        
        try:
            # Determine source language
            lang_map = {"en": "English", "de": "German", "es": "Spanish"}
            lang_name = lang_map.get(source_lang, "Unknown")
            
            # Smart prompt that handles all cases: single words, phrases, phrasal verbs, separable verbs
            prompt = f"""You are a linguistic expert. Translate this {lang_name} word or phrase to Spanish.

RULES:
1. For phrasal verbs (like "turn off", "look up", "give up"), translate the complete meaning as one unit
2. For German separable verbs (like "aufstehen", "ankommen"), translate the complete verb meaning
3. For compound words (like "Krankenhaus", "toothbrush"), translate the complete concept
4. For single words, give the most common Spanish equivalent
5. For articles/pronouns/prepositions, give direct equivalent
6. If multiple meanings exist, choose the most common one
7. Keep response SHORT - just the Spanish translation

Word/phrase: "{word_or_phrase}"
{f"Context: {context}" if context else ""}

Spanish translation:"""

            response = self.translation_model.generate_content(prompt)
            translation = response.text.strip()
            
            # Aggressive cleaning
            translation = translation.replace('"', '').replace("'", '').replace('`', '').strip()
            translation = re.sub(r'^\w+\s*:', '', translation)  # Remove "Spanish:" prefixes
            translation = re.sub(r'\(.*?\)', '', translation)  # Remove parenthetical explanations
            
            # Handle multiple options - take the first reasonable one
            if '/' in translation:
                options = [opt.strip() for opt in translation.split('/')]
                translation = options[0] if options else translation
                
            if ',' in translation and len(translation.split(',')) > 2:
                translation = translation.split(',')[0].strip()
            
            # Validation - ensure it's a reasonable translation
            words = translation.split()
            if len(words) > 5:  # Too verbose
                logger.warning(f"AI translation too long for '{word_or_phrase}': {translation}")
                return f"[{word_or_phrase}]"
                
            # Remove explanation artifacts
            bad_words = ['translation', 'spanish', 'means', 'equivalent', 'would', 'could', 'used']
            if any(bad_word in translation.lower() for bad_word in bad_words):
                return f"[{word_or_phrase}]"
            
            # Clean final result
            translation = translation.strip().strip('.,!?;:')
            
            if translation:
                logger.debug(f"🤖 AI built: '{word_or_phrase}' -> '{translation}'")
                return translation
            else:
                return f"[{word_or_phrase}]"
                
        except Exception as e:
            logger.error(f"AI comprehensive translation failed for '{word_or_phrase}': {str(e)}")
            return f"[{word_or_phrase}]"

    def _detect_phrasal_verbs(self, text: str) -> List[Tuple[int, int, str]]:
        """
        Detect phrasal verbs in English text and return their positions.
        Returns list of (start_pos, end_pos, phrase) tuples.
        """
        phrasal_verbs = []
        
        for pattern in self.phrasal_verb_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                start, end = match.span()
                phrase = match.group()
                phrasal_verbs.append((start, end, phrase))
                logger.debug(f"Detected phrasal verb: '{phrase}' at position {start}-{end}")
        
        # Sort by position and merge overlapping
        phrasal_verbs.sort(key=lambda x: x[0])
        merged = []
        for start, end, phrase in phrasal_verbs:
            if merged and start < merged[-1][1]:
                # Overlapping - take the longer one
                if end > merged[-1][1]:
                    merged[-1] = (merged[-1][0], end, text[merged[-1][0]:end])
            else:
                merged.append((start, end, phrase))
        
        return merged

    def _detect_separable_verbs(self, text: str) -> List[Tuple[int, int, str]]:
        """
        Detect German separable verbs and return their positions.
        Returns list of (start_pos, end_pos, phrase) tuples.
        """
        separable_verbs = []
        
        for pattern in self.separable_verb_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                start, end = match.span()
                phrase = match.group()
                separable_verbs.append((start, end, phrase))
                logger.debug(f"Detected separable verb: '{phrase}' at position {start}-{end}")
        
        # Look for separated forms (verb at beginning, prefix at end)
        # Pattern: "Ich stehe früh auf" - detect "stehe...auf" as "aufstehen"
        words = text.split()
        for i, word in enumerate(words):
            for j in range(i + 2, min(i + 6, len(words))):  # Look ahead 2-5 words
                potential_prefix = words[j]
                if potential_prefix in ['ab', 'an', 'auf', 'aus', 'bei', 'ein', 'mit', 'nach', 'vor', 'zu', 'zurück']:
                    # Check if this could be a separable verb
                    reconstructed = potential_prefix + word
                    if len(reconstructed) > 5:  # Reasonable verb length
                        # Calculate positions
                        start_pos = text.find(word)
                        end_pos = text.find(potential_prefix, start_pos) + len(potential_prefix)
                        if start_pos != -1 and end_pos > start_pos:
                            separable_verbs.append((start_pos, end_pos, f"{word}...{potential_prefix}"))
                            logger.debug(f"Detected separated verb: '{word}...{potential_prefix}' -> '{reconstructed}'")
        
        return separable_verbs

    def _smart_tokenize_with_phrases(self, text: str, is_german: bool) -> List[Tuple[str, bool]]:
        """
        Enhanced tokenization that preserves phrasal verbs and separable verbs as units.
        Returns list of (token, is_phrase) tuples.
        """
        phrases = []
        
        if is_german:
            phrases = self._detect_separable_verbs(text)
        else:
            phrases = self._detect_phrasal_verbs(text)
        
        # If no phrases detected, fall back to regular tokenization
        if not phrases:
            tokens = re.findall(r"\b\w+(?:'[a-z]+)?\b|[.,!?;:()\[\]{}\"'-]", text)
            return [(token.strip(), False) for token in tokens if token.strip()]
        
        # Build tokenization preserving phrases
        result = []
        last_end = 0
        
        for start, end, phrase in phrases:
            # Add tokens before this phrase
            before_text = text[last_end:start]
            if before_text.strip():
                before_tokens = re.findall(r"\b\w+(?:'[a-z]+)?\b|[.,!?;:()\[\]{}\"'-]", before_text)
                for token in before_tokens:
                    if token.strip():
                        result.append((token.strip(), False))
            
            # Add the phrase as a single unit
            clean_phrase = phrase.strip()
            if clean_phrase:
                result.append((clean_phrase, True))
            
            last_end = end
        
        # Add remaining tokens after last phrase
        remaining_text = text[last_end:]
        if remaining_text.strip():
            remaining_tokens = re.findall(r"\b\w+(?:'[a-z]+)?\b|[.,!?;:()\[\]{}\"'-]", remaining_text)
            for token in remaining_tokens:
                if token.strip():
                    result.append((token.strip(), False))
        
        logger.debug(f"Smart tokenization: {len(result)} tokens, {len(phrases)} phrases preserved")
        return result

    def _find_translation_for_phrase(self, phrase: str, mapping: Dict[str, str], is_german: bool, is_phrase: bool) -> str:
        """
        Enhanced translation finder using AI to build dynamic dictionary.
        No more need for huge static dictionaries - AI builds what we need on demand.
        """
        # Clean the phrase
        clean_phrase = phrase.strip().lower().rstrip('.,!?;:()[]{}"\'-')
        
        # Strategy 1: Check if it's just punctuation
        if phrase in ".,!?;:()[]{}\"'-":
            return phrase
        
        # Strategy 2: Numbers stay the same
        if clean_phrase.isdigit():
            return clean_phrase
        
        # Strategy 3: Direct lookup in provided mapping (from word-by-word pairs)
        for variant in [phrase, clean_phrase, phrase.lower()]:
            if variant in mapping:
                logger.debug(f"📋 Explicit mapping: '{phrase}' -> '{mapping[variant]}'")
                return mapping[variant]
        
        # Strategy 4: Check core essentials (very small dictionary)
        if clean_phrase in self.core_translations:
            logger.debug(f"🎯 Core translation: '{phrase}' -> '{self.core_translations[clean_phrase]}'")
            return self.core_translations[clean_phrase]
        
        # Strategy 5: Check cache for previous AI translations
        cache_key = f"{clean_phrase}_{is_german}_{is_phrase}"
        if cache_key in self._translation_cache:
            logger.debug(f"💾 Cached: '{phrase}' -> '{self._translation_cache[cache_key]}'")
            return self._translation_cache[cache_key]
        
        # Strategy 6: Use AI to build translation dynamically
        source_lang = "de" if is_german else "en"
        translation = self._translate_with_ai_comprehensive(clean_phrase, source_lang)
        
        # Cache the translation for future use
        self._translation_cache[cache_key] = translation
        
        # Log the translation type
        if translation.startswith('[') and translation.endswith(']'):
            logger.debug(f"❌ AI failed: '{phrase}' -> '{translation}'")
        else:
            phrase_type = "PHRASE" if is_phrase else "WORD"
            logger.debug(f"🤖 AI built {phrase_type}: '{phrase}' -> '{translation}'")
        
        return translation

    def _create_intelligent_word_mapping(self, word_pairs: List[Tuple[str, str]], is_german: bool) -> Dict[str, str]:
        """
        Create a lightweight mapping that prioritizes explicit pairs.
        AI handles everything else dynamically - no more huge dictionaries!
        """
        mapping = {}
        
        # Add all explicit word pairs with high priority
        for source, target in word_pairs:
            source_clean = source.strip()
            target_clean = target.strip()
            
            # Store multiple variants for better matching
            variants = [
                source_clean,
                source_clean.lower(),
                source_clean.strip('.,!?;:()[]{}"\'-'),
                source_clean.lower().strip('.,!?;:()[]{}"\'-')
            ]
            
            for variant in variants:
                if variant:
                    mapping[variant] = target_clean
                    
            logger.debug(f"📝 Explicit pair: '{source_clean}' -> '{target_clean}'")
        
        # Add only the minimal core translations (AI handles the rest)
        core_added = 0
        for core_word, core_translation in self.core_translations.items():
            if core_word not in mapping:  # Don't override explicit pairs
                mapping[core_word] = core_translation
                core_added += 1
        
        logger.info(f"🏗️  Created lightweight mapping: {len(word_pairs)} explicit pairs + {core_added} core words")
        logger.info(f"🤖 AI will handle all other translations dynamically")
        
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
        Enhanced version with intelligent phrase handling and AI translation.
        """
        try:
            if not output_path:
                temp_dir = self._get_temp_directory()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(temp_dir, f"speech_{timestamp}.mp3")
                logger.info(f"\n📂 Output path: {output_path}")

            # Generate SSML with intelligent phrase coverage
            ssml = self._generate_intelligent_phrase_ssml(
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
            return None

    def _generate_intelligent_phrase_ssml(
        self,
        translations_data: Dict,
        style_preferences=None,
    ) -> str:
        """
        Generate SSML with AI-powered dynamic dictionary - no huge static dictionaries needed!
        """
        # Define punctuation to exclude from detailed logging
        PUNCTUATION = set('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')
        
        ssml = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">"""
        
        logger.info("\n🎤 TTS AI-POWERED DYNAMIC DICTIONARY")
        logger.info("="*60)
        logger.info("🤖 Building translations on-demand with AI")
        logger.info("💾 No huge static dictionaries needed!")
        
        # Track AI usage statistics
        ai_translations_used = 0
        explicit_pairs_used = 0
        core_translations_used = 0
        
        # Process each style with AI-powered dynamic translation
        for style_info in translations_data.get('style_data', []):
            translation = style_info['translation']
            word_pairs = style_info['word_pairs']
            is_german = style_info['is_german']
            style_name = style_info['style_name']
            
            # Escape XML special characters
            translation = translation.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            logger.info(f"\n📝 Processing {style_name}:")
            logger.info(f"   Translation: \"{translation}\"")
            logger.info(f"   Explicit word pairs: {len(word_pairs)}")
            
            # Create lightweight mapping (AI handles most translations)
            mapping = self._create_intelligent_word_mapping(word_pairs, is_german)
            
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
            
            # Add AI-powered word-by-word section
            ssml += """
        <voice name="en-US-JennyMultilingualNeural">
            <prosody rate="0.8">"""
            
            # Smart tokenization that preserves phrases
            tokens = self._smart_tokenize_with_phrases(translation, is_german)
            
            logger.info(f"   Smart tokenization: {len(tokens)} tokens")
            phrase_count = sum(1 for _, is_phrase in tokens if is_phrase)
            logger.info(f"   Preserved phrases: {phrase_count}")
            
            # Process each token/phrase with AI-powered translation
            for i, (token, is_phrase) in enumerate(tokens):
                # Find translation - AI builds what we need dynamically
                spanish_translation = self._find_translation_for_phrase(
                    token, mapping, is_german, is_phrase
                )
                
                # Track translation source for statistics
                if token.lower() in mapping:
                    if token.lower() in self.core_translations:
                        core_translations_used += 1
                    else:
                        explicit_pairs_used += 1
                elif not spanish_translation.startswith('['):
                    ai_translations_used += 1
                
                # Clean for speech
                clean_token = token.strip()
                clean_spanish = spanish_translation.replace("[", "").replace("]", "")
                
                # Add to SSML
                ssml += f"""
            <lang xml:lang="{lang}">{clean_token}</lang>
            <break time="300ms"/>
            <lang xml:lang="es-ES">{clean_spanish}</lang>
            <break time="500ms"/>"""
                
                # Log non-punctuation items with source indication
                if clean_token and clean_token not in PUNCTUATION:
                    source = ""
                    if token.lower() in self.core_translations:
                        source = " [CORE]"
                    elif token.lower() in mapping:
                        source = " [EXPLICIT]"
                    elif not spanish_translation.startswith('['):
                        source = " [AI-BUILT]"
                    
                    phrase_indicator = " [PHRASE]" if is_phrase else ""
                    logger.debug(f"   {i+1:2d}. '{clean_token}'{phrase_indicator}{source} -> '{clean_spanish}'")
            
            ssml += """
            <break time="1000ms"/>
            </prosody>
        </voice>"""
        
        ssml += "</speak>"
        
        # Log AI usage statistics
        total_translations = ai_translations_used + explicit_pairs_used + core_translations_used
        logger.info(f"\n📊 TRANSLATION STATISTICS:")
        logger.info(f"   💫 AI-built translations: {ai_translations_used}")
        logger.info(f"   📋 Explicit pairs used: {explicit_pairs_used}")
        logger.info(f"   🎯 Core translations used: {core_translations_used}")
        logger.info(f"   📈 Total translations: {total_translations}")
        if total_translations > 0:
            ai_percentage = (ai_translations_used / total_translations) * 100
            logger.info(f"   🤖 AI coverage: {ai_percentage:.1f}%")
        
        logger.info(f"\n✅ Generated AI-powered SSML - no huge dictionaries needed!")
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
        """
        # Convert legacy format to new structured format
        translations_data = {
            'translations': [],
            'style_data': []
        }
        
        # Parse complete text to extract translations and word pairs per style
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
                style_patterns = {
                    'native': r'\* Conversational-native:',
                    'colloquial': r'\* Conversational-colloquial:',
                    'informal': r'\* Conversational-informal:',
                    'formal': r'\* Conversational-formal:'
                }
                
                for style_suffix, pattern in style_patterns.items():
                    if pattern in line:
                        current_style = f'{current_language}_{style_suffix}' if current_language else None
                        match = re.search(r'"([^"]+)"', line)
                        if match and current_style:
                            style_translations[current_style] = match.group(1)
                
                # Extract word-by-word pairs
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
                    word_by_word_enabled = getattr(style_preferences, 'german_word_by_word', False)
                else:
                    style_enabled = getattr(style_preferences, f'english_{style_suffix}', False)
                    word_by_word_enabled = getattr(style_preferences, 'english_word_by_word', False)
                
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
        """Convert SSML to speech with enhanced phrase handling"""
        synthesizer = None
        try:
            if not output_path:
                temp_dir = self._get_temp_directory()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(temp_dir, f"speech_{timestamp}.mp3")
                logger.info(f"🎵 Enhanced phrase-aware output path: {output_path}")

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
            logger.error(f"❌ Exception in enhanced text_to_speech: {str(e)}")
            return None
        finally:
            if synthesizer:
                try:
                    synthesizer.stop_speaking_async()
                except:
                    pass