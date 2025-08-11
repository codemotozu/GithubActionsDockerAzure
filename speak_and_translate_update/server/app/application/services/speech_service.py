# speech_service.py - Updated with enhanced dynamic mother tongue support

from ...domain.entities.translation import Translation
from ..services.translation_service import TranslationService
from pydub import AudioSegment
import speech_recognition as sr
import azure.cognitiveservices.speech as speechsdk
import tempfile
import os
import asyncio
from fastapi import HTTPException
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class SpeechService:
    def __init__(self):
        self.speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.speech_region = os.getenv("AZURE_SPEECH_REGION")
        
        if not self.speech_key or not self.speech_region:
            raise ValueError("Azure Speech credentials not found")
            
        # Enhanced language configuration for dynamic mother tongue support
        self.language_configs = {
            'spanish': {
                'azure_code': 'es-ES',
                'google_code': 'es-ES',
                'display_name': 'Spanish (Spain)',
                'fallback_codes': ['es-MX', 'es-AR', 'es-CO', 'es-US'],
                'wake_words': ['abrir', 'parar', 'comenzar', 'terminar', 'empezar', 'detener']
            },
            'english': {
                'azure_code': 'en-US',
                'google_code': 'en-US',
                'display_name': 'English (US)',
                'fallback_codes': ['en-GB', 'en-AU', 'en-CA'],
                'wake_words': ['open', 'stop', 'start', 'begin', 'end', 'close']
            },
            'german': {
                'azure_code': 'de-DE',
                'google_code': 'de-DE',
                'display_name': 'German (Germany)',
                'fallback_codes': ['de-AT', 'de-CH'],
                'wake_words': ['öffnen', 'stopp', 'anfangen', 'beenden', 'starten', 'schließen']
            },
            'french': {
                'azure_code': 'fr-FR',
                'google_code': 'fr-FR',
                'display_name': 'French (France)',
                'fallback_codes': ['fr-CA', 'fr-BE'],
                'wake_words': ['ouvrir', 'arrêter', 'commencer', 'finir', 'démarrer', 'fermer']
            },
            'italian': {
                'azure_code': 'it-IT',
                'google_code': 'it-IT',
                'display_name': 'Italian (Italy)',
                'fallback_codes': [],
                'wake_words': ['aprire', 'fermare', 'iniziare', 'finire', 'cominciare', 'chiudere']
            },
            'portuguese': {
                'azure_code': 'pt-PT',
                'google_code': 'pt-PT',
                'display_name': 'Portuguese (Portugal)',
                'fallback_codes': ['pt-BR'],
                'wake_words': ['abrir', 'parar', 'começar', 'terminar', 'iniciar', 'fechar']
            },
        }
        
        # Default speech config (will be updated dynamically)
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.speech_region
        )
        self.speech_config.speech_recognition_language = "es-ES"  # Default to Spanish
        
        # Initialize speech recognizer for general audio processing
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        
        # Enhanced wake words/commands with multi-language support
        self.WAKE_WORDS = {
            # English
            "open": "START_RECORDING",
            "stop": "STOP_RECORDING",
            "start": "START_RECORDING",
            "begin": "START_RECORDING",
            "end": "STOP_RECORDING",
            "close": "STOP_RECORDING",
            
            # Spanish 
            "abrir": "START_RECORDING",
            "parar": "STOP_RECORDING",
            "comenzar": "START_RECORDING",
            "terminar": "STOP_RECORDING",
            "empezar": "START_RECORDING",
            "detener": "STOP_RECORDING",
            
            # German
            "öffnen": "START_RECORDING",
            "stopp": "STOP_RECORDING",
            "anfangen": "START_RECORDING",
            "beenden": "STOP_RECORDING",
            "starten": "START_RECORDING",
            "schließen": "STOP_RECORDING",
            
            # French
            "ouvrir": "START_RECORDING",
            "arrêter": "STOP_RECORDING",
            "commencer": "START_RECORDING",
            "finir": "STOP_RECORDING",
            "démarrer": "START_RECORDING",
            "fermer": "STOP_RECORDING",
            
            # Italian
            "aprire": "START_RECORDING",
            "fermare": "STOP_RECORDING",
            "iniziare": "START_RECORDING",
            "finire": "STOP_RECORDING",
            "cominciare": "START_RECORDING",
            "chiudere": "STOP_RECORDING",
            
            # Portuguese
            "começar": "START_RECORDING",
            "iniciar": "START_RECORDING",
            "fechar": "STOP_RECORDING",
        }
        
        # Audio format configuration
        self.supported_formats = [".wav", ".aac", ".mp3", ".ogg", ".mp4", ".m4a"]
        self.valid_mime_types = [
            "audio/wav", "audio/aac", "audio/mpeg", "audio/ogg",
            "audio/mp4", "audio/x-m4a"
        ]
        
        self.translation_service = TranslationService()

    def _get_language_config(self, mother_tongue: str) -> dict:
        """Get language configuration for the specified mother tongue"""
        return self.language_configs.get(mother_tongue, self.language_configs['spanish'])

    def _update_speech_config_for_language(self, mother_tongue: str):
        """Update Azure Speech Config for the specified mother tongue"""
        lang_config = self._get_language_config(mother_tongue)
        self.speech_config.speech_recognition_language = lang_config['azure_code']
        logger.info(f"🌐 Speech recognition updated to: {lang_config['display_name']} ({lang_config['azure_code']})")

    def _detect_mother_tongue_from_text(self, text: str) -> str:
        """
        Detect mother tongue from recognized text using keyword analysis.
        This helps when mother_tongue parameter is not provided.
        """
        text_lower = text.lower()
        scores = {}
        
        for lang, config in self.language_configs.items():
            score = 0
            # Check wake words for this language
            for wake_word in config['wake_words']:
                if wake_word in text_lower:
                    score += 5  # High weight for wake words
            
            # Check for language-specific patterns
            if lang == 'spanish':
                spanish_patterns = ['ñ', 'á', 'é', 'í', 'ó', 'ú', 'para', 'con', 'de', 'en', 'la', 'el']
                for pattern in spanish_patterns:
                    if pattern in text_lower:
                        score += 1
                        
            elif lang == 'german':
                german_patterns = ['ü', 'ö', 'ä', 'ß', 'der', 'die', 'das', 'und', 'ich', 'du']
                for pattern in german_patterns:
                    if pattern in text_lower:
                        score += 1
                        
            elif lang == 'french':
                french_patterns = ['ç', 'è', 'é', 'à', 'ù', 'le', 'la', 'et', 'ou', 'je', 'tu']
                for pattern in french_patterns:
                    if pattern in text_lower:
                        score += 1
            
            scores[lang] = score
        
        # Return the language with highest score, default to spanish
        detected = max(scores, key=scores.get) if max(scores.values()) > 0 else 'spanish'
        logger.info(f"🔍 Mother tongue detection scores: {scores} -> Detected: {detected}")
        return detected

    async def process_command(self, audio_path: str, mother_tongue: str = 'spanish') -> str:
        """Process audio for wake word detection with dynamic mother tongue support"""
        working_path = audio_path
        converted_path = None
        
        try:
            # Convert to WAV if needed
            if not working_path.lower().endswith(".wav"):
                converted_path = await self._convert_to_wav(working_path)
                working_path = converted_path

            # Update speech config for the mother tongue
            self._update_speech_config_for_language(mother_tongue)

            # Set up Azure speech recognition
            audio_config = speechsdk.AudioConfig(filename=working_path)
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )

            # Use promise for async recognition
            done = False
            recognized_text = None

            def handle_result(evt):
                nonlocal done, recognized_text
                if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    recognized_text = evt.result.text.lower().strip()
                done = True

            speech_recognizer.recognized.connect(handle_result)
            
            # Start recognition
            speech_recognizer.start_continuous_recognition()
            
            # Wait for result with timeout
            timeout = 5  # 5 seconds timeout
            start_time = asyncio.get_event_loop().time()
            
            while not done:
                if asyncio.get_event_loop().time() - start_time > timeout:
                    speech_recognizer.stop_continuous_recognition()
                    raise HTTPException(
                        status_code=408,
                        detail="Recognition timeout"
                    )
                await asyncio.sleep(0.1)
            
            speech_recognizer.stop_continuous_recognition()

            logger.info(f"🎤 Command recognized in {mother_tongue}: '{recognized_text}'")

            # Check if recognized text matches any wake words (multi-language)
            if recognized_text in self.WAKE_WORDS:
                return recognized_text
            
            # Also check for partial matches with wake words
            for wake_word in self.WAKE_WORDS:
                if wake_word in recognized_text:
                    logger.info(f"🎯 Found wake word '{wake_word}' in '{recognized_text}'")
                    return wake_word
            
            return "UNKNOWN_COMMAND"

        except Exception as e:
            logger.error(f"Command processing error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Command processing failed: {str(e)}"
            )
        finally:
            # Cleanup temporary files
            await self._cleanup_temp_files(converted_path)

    async def _convert_to_wav(self, audio_path: str) -> str:
        """Convert any audio format to WAV using pydub"""
        try:
            logger.debug(f"Converting {audio_path} to WAV")
            
            ext = os.path.splitext(audio_path)[1].lower().replace(".", "")
            if ext not in ["mp3", "aac", "ogg", "m4a", "mp4"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported conversion format: {ext}"
                )

            try:
                sound = AudioSegment.from_file(audio_path, format=ext)
            except Exception as e:
                logger.error(f"Error loading {ext} file: {str(e)}")
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid {ext.upper()} file structure"
                )

            wav_path = f"{os.path.splitext(audio_path)[0]}.wav"
            sound.export(wav_path, format="wav", parameters=[
                "-ar", "16000",     # Set sample rate
                "-ac", "1",         # Set mono channel
                "-bits_per_raw_sample", "16"
            ])
            
            return wav_path
            
        except Exception as e:
            logger.error(f"Conversion error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Audio conversion failed: {str(e)}")

    async def _cleanup_temp_files(self, *files):
        """Clean up temporary files"""
        for f in files:
            try:
                if f and os.path.exists(f):
                    os.remove(f)
                    logger.debug(f"Cleaned up file: {f}")
            except Exception as e:
                logger.error(f"Error cleaning up file {f}: {str(e)}")

    async def process_audio(self, audio_file_path: str, mother_tongue: str = 'spanish') -> str:
        """
        Process audio file and return recognized text with dynamic mother tongue support
        """
        working_path = audio_file_path
        converted_path = None
        lang_config = self._get_language_config(mother_tongue)
        
        try:
            # Validate file existence
            if not os.path.exists(working_path):
                raise HTTPException(status_code=400, detail="File not found")

            logger.info(f"🎤 Processing audio in {lang_config['display_name']}")

            # Convert non-WAV files
            if not working_path.lower().endswith(".wav"):
                converted_path = await self._convert_to_wav(working_path)
                working_path = converted_path

            # Try Azure Speech-to-Text first (more accurate for supported languages)
            try:
                recognized_text = await self._process_with_azure(working_path, mother_tongue)
                if recognized_text and len(recognized_text.strip()) > 0:
                    logger.info(f"✅ Azure recognition successful: '{recognized_text[:50]}...'")
                    
                    # If mother_tongue was not explicitly provided, try to detect it
                    if mother_tongue == 'spanish':  # Default value
                        detected_tongue = self._detect_mother_tongue_from_text(recognized_text)
                        if detected_tongue != mother_tongue:
                            logger.info(f"🔄 Re-processing with detected mother tongue: {detected_tongue}")
                            # Re-process with detected language for better accuracy
                            reprocessed_text = await self._process_with_azure(working_path, detected_tongue)
                            if reprocessed_text and len(reprocessed_text.strip()) > len(recognized_text.strip()):
                                recognized_text = reprocessed_text
                    
                    return recognized_text
            except Exception as azure_error:
                logger.warning(f"⚠️ Azure recognition failed: {azure_error}")

            # Fallback to Google Speech Recognition
            logger.info("🔄 Falling back to Google Speech Recognition")
            recognized_text = await self._process_with_google(working_path, mother_tongue)
            
            if recognized_text and len(recognized_text.strip()) > 0:
                logger.info(f"✅ Google recognition successful: '{recognized_text[:50]}...'")
                return recognized_text
            else:
                logger.warning("⚠️ No speech detected in audio")
                return "No speech detected"

        except Exception as e:
            logger.error(f"❌ Audio processing error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Audio processing failed: {str(e)}"
            )
        finally:
            # Cleanup converted files
            await self._cleanup_temp_files(converted_path)

    async def _process_with_azure(self, audio_path: str, mother_tongue: str) -> str:
        """Process audio using Azure Speech Services with dynamic language support"""
        lang_config = self._get_language_config(mother_tongue)
        
        # Create a new speech config for this specific request
        speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.speech_region
        )
        speech_config.speech_recognition_language = lang_config['azure_code']
        
        # Set up audio and recognizer
        audio_config = speechsdk.AudioConfig(filename=audio_path)
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        
        # Perform recognition
        result = speech_recognizer.recognize_once()
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            logger.warning(f"Azure: No speech matched for {mother_tongue}")
            raise Exception("No speech matched")
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            logger.error(f"Azure recognition canceled: {cancellation.reason}")
            if cancellation.reason == speechsdk.CancellationReason.Error:
                logger.error(f"Azure error details: {cancellation.error_details}")
            raise Exception(f"Azure recognition failed: {cancellation.reason}")
        else:
            raise Exception("Azure recognition failed with unknown reason")

    async def _process_with_google(self, audio_path: str, mother_tongue: str) -> str:
        """Process audio using Google Speech Recognition as fallback with dynamic language support"""
        lang_config = self._get_language_config(mother_tongue)
        
        # Speech recognition with primary language
        try:
            with sr.AudioFile(audio_path) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.record(source)
                
                # Try primary language code
                text = self.recognizer.recognize_google(
                    audio, 
                    language=lang_config['google_code']
                )
                return text
                
        except sr.UnknownValueError:
            # Try fallback language codes if available
            for fallback_code in lang_config.get('fallback_codes', []):
                try:
                    logger.info(f"🔄 Trying fallback language: {fallback_code}")
                    with sr.AudioFile(audio_path) as source:
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        audio = self.recognizer.record(source)
                        
                        text = self.recognizer.recognize_google(audio, language=fallback_code)
                        logger.info(f"✅ Fallback recognition successful with {fallback_code}")
                        return text
                        
                except sr.UnknownValueError:
                    continue
                except Exception as e:
                    logger.warning(f"Fallback {fallback_code} failed: {e}")
                    continue
            
            # If all attempts fail
            raise Exception(f"Could not understand audio in {mother_tongue} or fallback languages")
            
        except sr.RequestError as e:
            logger.error(f"Google Speech Recognition service error: {e}")
            raise Exception(f"Speech recognition service error: {e}")

    def get_supported_languages(self) -> dict:
        """Return dictionary of supported languages and their configurations"""
        return {
            lang: {
                'display_name': config['display_name'],
                'azure_code': config['azure_code'],
                'google_code': config['google_code'],
                'wake_words': config['wake_words']
            }
            for lang, config in self.language_configs.items()
        }

    async def detect_language_from_audio(self, audio_path: str) -> str:
        """
        Attempt to detect the language of spoken audio by trying multiple languages.
        """
        best_language = 'spanish'  # Default
        best_confidence = 0
        
        for language in self.language_configs.keys():
            try:
                text = await self._process_with_azure(audio_path, language)
                if text and len(text.strip()) > 3:
                    # Simple heuristic: longer recognized text suggests better match
                    confidence = len(text.strip())
                    logger.debug(f"Language {language}: '{text[:30]}...' (confidence: {confidence})")
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_language = language
                        
            except Exception as e:
                logger.debug(f"Language detection failed for {language}: {e}")
                continue
        
        logger.info(f"🔍 Detected language: {best_language} (confidence: {best_confidence})")
        return best_language