
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
            
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.speech_region
        )
        self.speech_config.speech_recognition_language = "en-EN"
        
        # Initialize speech recognizer for general audio processing
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        
        # Define wake words/commands
        self.WAKE_WORDS = {
            "open": "START_RECORDING",
            "stop": "STOP_RECORDING"
        }
        
        # Audio format configuration
        self.supported_formats = [".wav", ".aac", ".mp3", ".ogg", ".mp4", ".m4a"]
        self.valid_mime_types = [
            "audio/wav", "audio/aac", "audio/mpeg", "audio/ogg",
            "audio/mp4", "audio/x-m4a"
        ]
        
        self.translation_service = TranslationService()

    async def process_command(self, audio_path: str) -> str:
        """Process audio for wake word detection using Azure Speech Services"""
        working_path = audio_path
        converted_path = None
        
        try:
            # Convert to WAV if needed
            if not working_path.lower().endswith(".wav"):
                converted_path = await self._convert_to_wav(working_path)
                working_path = converted_path

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

            # Check if recognized text matches any wake words
            if recognized_text in self.WAKE_WORDS:
                return recognized_text
            
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

    async def process_audio(self, audio_file_path: str) -> str:
        """Process audio file and return recognized text only"""
        working_path = audio_file_path
        converted_path = None
        
        try:
            # Validate file existence
            if not os.path.exists(working_path):
                raise HTTPException(status_code=400, detail="File not found")

            # Convert non-WAV files
            if not working_path.lower().endswith(".wav"):
                converted_path = await self._convert_to_wav(working_path)
                working_path = converted_path

            # Speech recognition
            with sr.AudioFile(working_path) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio, language="es-ES")
                
            return text

        finally:
            # Cleanup converted files
            await self._cleanup_temp_files(converted_path)
        
        
