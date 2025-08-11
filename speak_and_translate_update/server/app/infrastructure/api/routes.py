# server/app/infrastructure/api/routes.py - Updated with mother tongue support

import logging
import tempfile
import os
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from ...application.services.speech_service import SpeechService
from ...application.services.translation_service import TranslationService
from ...domain.entities.translation import Translation

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("api.log")
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Starting API server")
    logger.info(f"Temp directory: {tempfile.gettempdir()}")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    yield  # App runs here
    
    # Shutdown logic
    logger.info("Shutting down API server")

app = FastAPI(
    title="Speak and Translate API",
    root_path="",  # Important: This should be empty for Azure Container Apps
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
translation_service = TranslationService()
speech_service = SpeechService()

class TranslationStylePreferences(BaseModel):
    # German styles
    german_native: bool = False
    german_colloquial: bool = False
    german_informal: bool = False
    german_formal: bool = False
    
    # English styles  
    english_native: bool = False
    english_colloquial: bool = False
    english_informal: bool = False
    english_formal: bool = False
    
    # Word-by-word audio preferences
    german_word_by_word: bool = False
    english_word_by_word: bool = False
    
    # Mother tongue setting (NEW)
    mother_tongue: Optional[str] = "spanish"  # spanish, english, german

class PromptRequest(BaseModel):
    text: str
    source_lang: Optional[str] = "en"
    target_lang: Optional[str] = "en"
    style_preferences: Optional[TranslationStylePreferences] = None

# Replace your existing health check endpoint with this comprehensive one
@app.get("/health")
async def health_check():
    """
    Health check endpoint for Azure Container Apps
    Azure expects a 200 response from this endpoint
    """
    # Create audio directory with proper permissions if it doesn't exist
    audio_dir = "/tmp/tts_audio" if os.name != "nt" else os.path.join(os.environ.get("TEMP", ""), "tts_audio")
    try:
        os.makedirs(audio_dir, exist_ok=True)
        os.chmod(audio_dir, 0o755)  # Read/write for owner, read for others
    except Exception as e:
        logger.warning(f"Could not create or set permissions on audio directory: {str(e)}")

    # Check if required environment variables are set
    env_vars = {
        "AZURE_SPEECH_KEY": bool(os.environ.get("AZURE_SPEECH_KEY")),
        "AZURE_SPEECH_REGION": bool(os.environ.get("AZURE_SPEECH_REGION")),
        "GEMINI_API_KEY": bool(os.environ.get("GEMINI_API_KEY")),
        "PORT": os.environ.get("PORT", "8000"),
        "TTS_DEVICE": os.environ.get("TTS_DEVICE", "cpu"),
        "CONTAINER_ENV": os.environ.get("CONTAINER_ENV", "false")
    }

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "temp_dir": tempfile.gettempdir(),
        "audio_dir": audio_dir,
        "environment_vars": env_vars
    }

# Health check endpoint
@app.get("/")
async def root():
    return {"status": "ok from server/app/infrastructure/api/routes.py - Dynamic Mother Tongue Support   48"}

@app.post("/api/conversation", response_model=Translation)
async def start_conversation(prompt: PromptRequest):
    try:
        logger.info(f"📨 NEW DYNAMIC TRANSLATION REQUEST")
        logger.info(f"Text: {prompt.text}")
        
        # Extract mother tongue from style preferences
        mother_tongue = "spanish"  # default
        if prompt.style_preferences and prompt.style_preferences.mother_tongue:
            mother_tongue = prompt.style_preferences.mother_tongue
        
        logger.info(f"🌐 Mother Tongue: {mother_tongue}")
        
        if prompt.style_preferences:
            logger.info("📋 Style Preferences:")
            logger.info(f"  🇩🇪 German: Native={prompt.style_preferences.german_native}, "
                       f"Colloquial={prompt.style_preferences.german_colloquial}, "
                       f"Informal={prompt.style_preferences.german_informal}, "
                       f"Formal={prompt.style_preferences.german_formal}")
            logger.info(f"  🎵 German Word-by-Word: {prompt.style_preferences.german_word_by_word}")
            logger.info(f"  🇺🇸 English: Native={prompt.style_preferences.english_native}, "
                       f"Colloquial={prompt.style_preferences.english_colloquial}, "
                       f"Informal={prompt.style_preferences.english_informal}, "
                       f"Formal={prompt.style_preferences.english_formal}")
            logger.info(f"  🎵 English Word-by-Word: {prompt.style_preferences.english_word_by_word}")
        
        # Validate that at least one style is selected
        if prompt.style_preferences:
            has_any_style = any([
                prompt.style_preferences.german_native,
                prompt.style_preferences.german_colloquial,
                prompt.style_preferences.german_informal,
                prompt.style_preferences.german_formal,
                prompt.style_preferences.english_native,
                prompt.style_preferences.english_colloquial,
                prompt.style_preferences.english_informal,
                prompt.style_preferences.english_formal
            ])
            
            if not has_any_style:
                logger.warning("⚠️ No translation styles selected, using defaults")
                # Apply minimal defaults based on mother tongue
                if mother_tongue == "spanish":
                    prompt.style_preferences.german_colloquial = True
                    prompt.style_preferences.english_colloquial = True
                elif mother_tongue == "english":
                    prompt.style_preferences.german_colloquial = True
                elif mother_tongue == "german":
                    prompt.style_preferences.english_colloquial = True
        
        # Pass mother tongue and style preferences to translation service
        response = await translation_service.process_prompt(
            text=prompt.text, 
            source_lang=prompt.source_lang, 
            target_lang=prompt.target_lang,
            style_preferences=prompt.style_preferences,
            mother_tongue=mother_tongue  # NEW: Pass mother tongue explicitly
        )
        
        logger.info(f"✅ Translation completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"❌ Conversation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/speech-to-text")
async def speech_to_text(file: UploadFile = File(...)):
    tmp_path = None
    try:
        # MIME type handling
        content_type = file.content_type or "audio/wav"
        ext = ".wav"
        mime_map = {
            "audio/wav": ".wav",
            "audio/aac": ".aac",
            "audio/mpeg": ".mp3",
            "audio/ogg": ".ogg"
        }
        
        if content_type in mime_map:
            ext = mime_map[content_type]
        else:
            filename_ext = os.path.splitext(file.filename or "")[1].lower()
            ext = filename_ext if filename_ext in [".wav", ".aac", ".mp3", ".ogg"] else ".wav"

        # Create temp file
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
            logger.debug(f"Created temp file: {tmp_path}")

        # Process audio
        recognized_text = await speech_service.process_audio(tmp_path)
        return {"text": recognized_text}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Speech-to-text error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Audio processing failed. See server logs for details."
        )
    finally:
        # Cleanup temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
                logger.debug(f"Cleaned up temp file: {tmp_path}")
            except Exception as e:
                logger.error(f"Final cleanup failed: {str(e)}")

@app.post("/api/voice-command")
async def process_voice_command(file: UploadFile = File(...)):
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
            
        command_text = await speech_service.process_command(tmp_path)
        return {"command": command_text}
        
    except Exception as e:
        logger.error(f"Voice command error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Command processing failed"
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    try:
        if ".." in filename or "/" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")

        audio_dir = os.path.join(
            os.environ.get("TEMP", ""), 
            "tts_audio"
        ) if os.name == "nt" else "/tmp/tts_audio"

        file_path = os.path.join(audio_dir, filename)
        
        if not os.path.exists(file_path):
            logger.warning(f"Audio file not found: {file_path}")
            raise HTTPException(status_code=404, detail="Audio file not found")

        return FileResponse(
            path=file_path,
            media_type="audio/mp3",
            filename=filename,
            headers={"Cache-Control": "no-cache"}
        )
    except Exception as e:
        logger.error(f"Audio delivery error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))