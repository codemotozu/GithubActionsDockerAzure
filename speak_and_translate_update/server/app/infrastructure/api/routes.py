# server/app/infrastructure/api/routes.py - Enhanced with word-by-word debugging and validation

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
    logger.info("🚀 Starting Dynamic Mother Tongue Translation API with Enhanced UI Visualization")
    logger.info("📋 EXACT Implementation per Requirements:")
    logger.info("   1. Spanish mother tongue → German and/or English based on selections")
    logger.info("   2. English mother tongue → Spanish (automatic) + German if selected")
    logger.info("   3. German mother tongue → Spanish (automatic) + English if selected")
    logger.info("   4. Word-by-word audio ONLY if user selects 'word by word audio'")
    logger.info("   5. Format: [target word] ([Spanish equivalent])")
    logger.info("   6. Dynamic behavior - no static code")
    logger.info("   7. AI-powered translations - no huge dictionaries")
    logger.info("   8. 📱 ENHANCED: UI visualization matches audio exactly")
    
    yield  # App runs here
    
    # Shutdown logic
    logger.info("Shutting down Dynamic Mother Tongue Translation API")

app = FastAPI(
    title="Enhanced Dynamic Mother Tongue Translation API",
    description="EXACT implementation per requirements: Dynamic translation with UI visualization that matches audio exactly",
    root_path="",
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
    """
    Translation style preferences with EXACT mother tongue support per requirements.
    """
    # German styles - user has complete freedom
    german_native: bool = False
    german_colloquial: bool = False
    german_informal: bool = False
    german_formal: bool = False
    
    # English styles - user has complete freedom
    english_native: bool = False
    english_colloquial: bool = False
    english_informal: bool = False
    english_formal: bool = False
    
    # EXACT per requirements: Word-by-word audio preferences
    german_word_by_word: bool = False  # Only generate if user selects this
    english_word_by_word: bool = False  # Only generate if user selects this
    
    # CRITICAL: Mother tongue setting for dynamic translation
    mother_tongue: Optional[str] = "spanish"  # spanish, english, german, french, italian, portuguese

class PromptRequest(BaseModel):
    text: str
    source_lang: Optional[str] = "auto"  # Auto-detect or explicit
    target_lang: Optional[str] = "multi"  # Multiple targets based on mother tongue
    style_preferences: Optional[TranslationStylePreferences] = None

def _validate_mother_tongue(mother_tongue: str) -> str:
    """Validate and normalize mother tongue input"""
    valid_languages = ['spanish', 'english', 'german', 'french', 'italian', 'portuguese']
    normalized = mother_tongue.lower().strip()
    
    if normalized not in valid_languages:
        logger.warning(f"Invalid mother tongue '{mother_tongue}', defaulting to Spanish")
        return 'spanish'
    
    return normalized

def _apply_intelligent_defaults(style_preferences: TranslationStylePreferences) -> TranslationStylePreferences:
    """
    Apply intelligent defaults based on mother tongue.
    EXACT implementation per requirements - completely dynamic.
    """
    mother_tongue = _validate_mother_tongue(style_preferences.mother_tongue or 'spanish')
    
    # Check if any styles are selected
    has_any_style = any([
        style_preferences.german_native,
        style_preferences.german_colloquial,
        style_preferences.german_informal,
        style_preferences.german_formal,
        style_preferences.english_native,
        style_preferences.english_colloquial,
        style_preferences.english_informal,
        style_preferences.english_formal
    ])
    
    # EXACT per requirements: Apply defaults only if NO styles are selected
    if not has_any_style:
        logger.info(f"🎯 Applying intelligent defaults for mother tongue: {mother_tongue}")
        
        if mother_tongue == "spanish":
            # EXACT requirement: Spanish → German and English based on selections
            # Default: Enable both German and English colloquial
            style_preferences.german_colloquial = True
            style_preferences.english_colloquial = True
            logger.info("   ✅ Spanish defaults: German colloquial + English colloquial")
            
        elif mother_tongue == "english":
            # EXACT requirement: English → Spanish (automatic) + German if selected
            # Default: Enable German colloquial (Spanish is automatic)
            style_preferences.german_colloquial = True
            logger.info("   ✅ English defaults: German colloquial (Spanish automatic)")
            
        elif mother_tongue == "german":
            # EXACT requirement: German → Spanish (automatic) + English if selected
            # Default: Enable English colloquial (Spanish is automatic)
            style_preferences.english_colloquial = True
            logger.info("   ✅ German defaults: English colloquial (Spanish automatic)")
            
        else:
            # Other languages → Default to German and English
            style_preferences.german_colloquial = True
            style_preferences.english_colloquial = True
            logger.info(f"   ✅ {mother_tongue} defaults: German + English colloquial")
    else:
        logger.info(f"🎯 User has selected specific styles for mother tongue: {mother_tongue}")
    
    return style_preferences

def _log_dynamic_translation_setup(text: str, style_preferences: TranslationStylePreferences):
    """Log the EXACT translation setup per requirements"""
    mother_tongue = style_preferences.mother_tongue or 'spanish'
    
    logger.info(f"\n" + "="*80)
    logger.info(f"🌐 DYNAMIC MOTHER TONGUE TRANSLATION SETUP (EXACT per requirements)")
    logger.info(f"="*80)
    logger.info(f"📝 Input Text: '{text}'")
    logger.info(f"🌍 Mother Tongue: {mother_tongue.upper()}")
    
    # EXACT per requirements: Determine expected translations based on mother tongue
    expected_translations = []
    automatic_translations = []
    
    if mother_tongue == 'spanish':
        # EXACT: Spanish → German and/or English based on selections
        if any([style_preferences.german_native, style_preferences.german_colloquial,
               style_preferences.german_informal, style_preferences.german_formal]):
            expected_translations.append('German')
        if any([style_preferences.english_native, style_preferences.english_colloquial,
               style_preferences.english_informal, style_preferences.english_formal]):
            expected_translations.append('English')
            
    elif mother_tongue == 'english':
        # EXACT: English → Spanish (automatic) + German if selected
        automatic_translations.append('Spanish')
        if any([style_preferences.german_native, style_preferences.german_colloquial,
               style_preferences.german_informal, style_preferences.german_formal]):
            expected_translations.append('German')
            
    elif mother_tongue == 'german':
        # EXACT: German → Spanish (automatic) + English if selected
        automatic_translations.append('Spanish')
        if any([style_preferences.english_native, style_preferences.english_colloquial,
               style_preferences.english_informal, style_preferences.english_formal]):
            expected_translations.append('English')
    
    # Log expected behavior
    if automatic_translations:
        logger.info(f"🔄 Automatic Translations: {', '.join(automatic_translations)}")
    if expected_translations:
        logger.info(f"🎯 User-Selected Translations: {', '.join(expected_translations)}")
    else:
        logger.info(f"⚠️ No target languages selected")
    
    # EXACT per requirements: Log word-by-word audio settings
    logger.info(f"🎵 Word-by-Word Audio Settings:")
    logger.info(f"   German word-by-word: {style_preferences.german_word_by_word}")
    logger.info(f"   English word-by-word: {style_preferences.english_word_by_word}")
    
    if style_preferences.german_word_by_word or style_preferences.english_word_by_word:
        logger.info(f"   🎯 Audio format: [target word] ([Spanish equivalent])")
        logger.info(f"   📱 UI Visualization: Visual breakdown will match audio exactly")
    else:
        logger.info(f"   🎯 Audio format: Simple translation reading")
        logger.info(f"   📱 UI Visualization: No word-by-word breakdown shown")
    
    # Log style selections
    logger.info(f"🇩🇪 German Styles:")
    logger.info(f"   Native: {style_preferences.german_native}")
    logger.info(f"   Colloquial: {style_preferences.german_colloquial}")
    logger.info(f"   Informal: {style_preferences.german_informal}")
    logger.info(f"   Formal: {style_preferences.german_formal}")
    
    logger.info(f"🇺🇸 English Styles:")
    logger.info(f"   Native: {style_preferences.english_native}")
    logger.info(f"   Colloquial: {style_preferences.english_colloquial}")
    logger.info(f"   Informal: {style_preferences.english_informal}")
    logger.info(f"   Formal: {style_preferences.english_formal}")
    
    logger.info(f"="*80)

def _validate_dynamic_setup(style_preferences: TranslationStylePreferences) -> bool:
    """
    Validate that the dynamic setup makes sense per requirements.
    Returns True if valid, False if invalid.
    """
    mother_tongue = style_preferences.mother_tongue or 'spanish'
    
    # Check if at least one target language is selected
    has_german = any([
        style_preferences.german_native,
        style_preferences.german_colloquial,
        style_preferences.german_informal,
        style_preferences.german_formal
    ])
    
    has_english = any([
        style_preferences.english_native,
        style_preferences.english_colloquial,
        style_preferences.english_informal,
        style_preferences.english_formal
    ])
    
    # EXACT per requirements: Validate based on mother tongue
    if mother_tongue == 'spanish':
        # Spanish can translate to German and/or English
        return has_german or has_english
    elif mother_tongue == 'english':
        # English always gets Spanish (automatic), German is optional
        return True  # Spanish is automatic, so always valid
    elif mother_tongue == 'german':
        # German always gets Spanish (automatic), English is optional
        return True  # Spanish is automatic, so always valid
    else:
        # Other languages need at least one target
        return has_german or has_english

def _log_word_by_word_debug_info(translation: Translation):
    """Log detailed debug information about word-by-word structure"""
    logger.info("\n📱 WORD-BY-WORD UI VISUALIZATION DEBUG:")
    logger.info("="*60)
    
    if not translation.word_by_word:
        logger.info("   📝 No word-by-word data available for UI")
        return
    
    # Log summary
    languages = translation.get_available_languages()
    counts = translation.count_word_pairs_by_language()
    
    logger.info(f"   📊 Available languages: {', '.join(languages)}")
    logger.info(f"   📊 Word pair counts: {counts}")
    
    # Log phrasal verbs
    for language in languages:
        phrasal_verbs = translation.get_phrasal_verbs_by_language(language)
        if phrasal_verbs:
            logger.info(f"   🔗 {language.title()} phrasal/separable verbs: {len(phrasal_verbs)}")
            for verb in phrasal_verbs[:3]:  # Show first 3 examples
                logger.info(f"      - {verb['display_format']}")
    
    # Log detailed structure
    logger.info("   📝 Detailed word-by-word structure:")
    for key, data in list(translation.word_by_word.items())[:5]:  # Show first 5 entries
        logger.info(f"      Key: {key}")
        logger.info(f"         Source: {data.get('source')}")
        logger.info(f"         Spanish: {data.get('spanish')}")
        logger.info(f"         Display: {data.get('display_format')}")
        logger.info(f"         Language: {data.get('language')}")
        logger.info(f"         Phrasal: {data.get('is_phrasal_verb')}")
    
    if len(translation.word_by_word) > 5:
        logger.info(f"      ... and {len(translation.word_by_word) - 5} more entries")
    
    logger.info("="*60)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check with dynamic translation info"""
    # Create audio directory with proper permissions
    audio_dir = "/tmp/tts_audio" if os.name != "nt" else os.path.join(os.environ.get("TEMP", ""), "tts_audio")
    try:
        os.makedirs(audio_dir, exist_ok=True)
        if os.name != "nt":
            os.chmod(audio_dir, 0o755)
    except Exception as e:
        logger.warning(f"Could not create or set permissions on audio directory: {str(e)}")

    # Check environment variables
    env_vars = {
        "AZURE_SPEECH_KEY": bool(os.environ.get("AZURE_SPEECH_KEY")),
        "AZURE_SPEECH_REGION": bool(os.environ.get("AZURE_SPEECH_REGION")),
        "GEMINI_API_KEY": bool(os.environ.get("GEMINI_API_KEY")),
        "PORT": os.environ.get("PORT", "8000"),
    }

    return {
        "status": "healthy",
        "service": "Enhanced Dynamic Mother Tongue Translation API",
        "version": "2.1 - UI Visualization Enhancement",
        "timestamp": datetime.utcnow().isoformat(),
        "requirements_implementation": {
            "spanish_mother_tongue": "German and/or English based on selections",
            "english_mother_tongue": "Spanish (automatic) + German if selected",
            "german_mother_tongue": "Spanish (automatic) + English if selected",
            "word_by_word_audio": "Only if user selects 'word by word audio'",
            "audio_format": "[target word] ([Spanish equivalent])",
            "ui_visualization": "Visual display matches audio exactly",
            "phrasal_verbs": "Treated as single units: [wake up] ([despertar])",
            "separable_verbs": "Treated as single units: [stehe auf] ([me levanto])",
            "ai_powered": "No huge dictionaries - rely on AI",
            "dynamic_behavior": "No static code - based on user preferences"
        },
        "temp_dir": tempfile.gettempdir(),
        "audio_dir": audio_dir,
        "environment_vars": env_vars,
        "supported_languages": speech_service.get_supported_languages()
    }

@app.get("/")
async def root():
    return {
        "status": "ok", 
        "service": "Enhanced Dynamic Mother Tongue Translation API",
        "description": "EXACT implementation per requirements: Dynamic translation with UI visualization matching audio",
        "version": "2.1",
        "requirements": {
            "1": "Spanish mother tongue → German and/or English based on selections",
            "2": "English mother tongue → Spanish (automatic) + German if selected", 
            "3": "German mother tongue → Spanish (automatic) + English if selected",
            "4": "Word-by-word audio ONLY if user selects 'word by word audio'",
            "4.1": "UI visualization matches audio exactly - what you see is what you hear",
            "5": "Format: [target word] ([Spanish equivalent])",
            "6": "Dynamic behavior - no static code",
            "7": "AI-powered translations - no huge dictionaries",
            "8": "Phrasal verbs: [wake up] ([despertar]) - single units",
            "9": "German separable verbs: [stehe auf] ([me levanto]) - single units"
        },
        "ui_features": {
            "word_by_word_visualization": "Shows exactly what is heard in audio",
            "phrasal_verb_detection": "Identifies and highlights phrasal/separable verbs",
            "language_grouping": "Groups word pairs by language and style",
            "audio_format_display": "Shows the exact [word] ([spanish]) format",
            "expandable_interface": "Collapsible sections for better UX"
        },
        "endpoints": {
            "/api/conversation": "Main dynamic translation endpoint with enhanced UI data",
            "/api/speech-to-text": "Speech recognition with mother tongue detection",
            "/api/voice-command": "Voice command processing",
            "/api/audio/{filename}": "Audio file serving",
            "/health": "Health check with requirements status",
            "/debug/word-by-word": "Debug endpoint for word-by-word structure"
        }
    }

@app.post("/api/conversation", response_model=Translation)
async def start_conversation(prompt: PromptRequest):
    """
    Main conversation endpoint with EXACT dynamic mother tongue translation per requirements.
    Enhanced with detailed UI visualization data.
    """
    try:
        # Set up default style preferences if none provided
        if prompt.style_preferences is None:
            prompt.style_preferences = TranslationStylePreferences(
                german_colloquial=True,
                english_colloquial=True,
                mother_tongue="spanish"
            )
        
        # Validate and normalize mother tongue
        mother_tongue = _validate_mother_tongue(prompt.style_preferences.mother_tongue or 'spanish')
        prompt.style_preferences.mother_tongue = mother_tongue
        
        # Apply intelligent defaults if no styles selected
        prompt.style_preferences = _apply_intelligent_defaults(prompt.style_preferences)
        
        # Log the EXACT translation setup per requirements
        _log_dynamic_translation_setup(prompt.text, prompt.style_preferences)
        
        # EXACT per requirements: Validate the dynamic setup
        if not _validate_dynamic_setup(prompt.style_preferences):
            logger.error("❌ Invalid dynamic translation setup")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid translation setup for mother tongue '{mother_tongue}'. Please select appropriate target languages."
            )
        
        # Process the translation with EXACT dynamic mother tongue logic
        logger.info(f"🚀 Starting dynamic translation with mother tongue: {mother_tongue}")
        response = await translation_service.process_prompt(
            text=prompt.text, 
            source_lang=prompt.source_lang or "auto", 
            target_lang=prompt.target_lang or "multi",
            style_preferences=prompt.style_preferences,
            mother_tongue=mother_tongue
        )
        
        # Log the successful completion with UI debug info
        logger.info(f"✅ Dynamic translation completed successfully")
        logger.info(f"   Input ('{response.source_language}'): {response.original_text}")
        logger.info(f"   Output length: {len(response.translated_text)} characters")
        logger.info(f"   Audio generated: {'Yes' if response.audio_path else 'No'}")
        
        if response.audio_path:
            # Check if word-by-word was requested
            word_by_word_requested = (
                prompt.style_preferences.german_word_by_word or 
                prompt.style_preferences.english_word_by_word
            )
            logger.info(f"   Audio type: {'Word-by-word breakdown' if word_by_word_requested else 'Simple translation reading'}")
        
        # ENHANCED: Log word-by-word debug information for UI
        _log_word_by_word_debug_info(response)
        
        return response
        
    except HTTPException as he:
        # Re-raise HTTP exceptions as-is
        raise he
    except Exception as e:
        logger.error(f"❌ Dynamic translation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Dynamic translation failed: {str(e)}")

@app.get("/debug/word-by-word")
async def debug_word_by_word_structure():
    """
    Debug endpoint to show word-by-word data structure.
    Useful for frontend developers to understand the data format.
    """
    try:
        # Create a sample translation with word-by-word data
        sample_translation = Translation(
            original_text="I want to wake up early and go out",
            translated_text="Sample translation with word-by-word data",
            source_language="english",
            target_language="multi"
        )
        
        # Add sample word-by-word entries
        sample_translation.add_word_by_word_entry(
            key="english_colloquial_0_wake_up",
            source="wake up",
            spanish="despertar",
            language="english",
            style="english_colloquial",
            order=0,
            is_phrasal_verb=True
        )
        
        sample_translation.add_word_by_word_entry(
            key="english_colloquial_1_go_out",
            source="go out",
            spanish="salir",
            language="english",
            style="english_colloquial",
            order=1,
            is_phrasal_verb=True
        )
        
        sample_translation.add_word_by_word_entry(
            key="english_colloquial_2_early",
            source="early",
            spanish="temprano",
            language="english",
            style="english_colloquial",
            order=2,
            is_phrasal_verb=False
        )
        
        # Generate debug information
        debug_info = sample_translation.debug_word_by_word_structure()
        
        return {
            "debug_info": debug_info,
            "sample_data": sample_translation.word_by_word,
            "available_languages": sample_translation.get_available_languages(),
            "word_pair_counts": sample_translation.count_word_pairs_by_language(),
            "phrasal_verbs": {
                lang: sample_translation.get_phrasal_verbs_by_language(lang)
                for lang in sample_translation.get_available_languages()
            },
            "ui_format_explanation": {
                "description": "Each entry contains all data needed for UI visualization",
                "key_format": "language_style_order_sourceword",
                "display_format": "Exactly what user hears: [source] ([spanish])",
                "is_phrasal_verb": "Boolean flag for special highlighting",
                "order": "Sequence number for audio playback order"
            }
        }
        
    except Exception as e:
        logger.error(f"Debug endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Debug endpoint failed: {str(e)}")

# Keep all other existing endpoints unchanged...
@app.post("/api/speech-to-text")
async def speech_to_text(file: UploadFile = File(...), mother_tongue: Optional[str] = "auto"):
    """
    Speech-to-text with dynamic mother tongue detection and support.
    """
    tmp_path = None
    try:
        # Validate mother tongue if provided
        if mother_tongue and mother_tongue != "auto":
            mother_tongue = _validate_mother_tongue(mother_tongue)
        else:
            mother_tongue = "spanish"  # Default for auto-detection
        
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

        # Process audio with mother tongue support
        logger.info(f"🎤 Processing speech-to-text with mother tongue: {mother_tongue}")
        recognized_text = await speech_service.process_audio(tmp_path, mother_tongue)
        
        # Detect actual language if auto-detection was requested
        if mother_tongue == "spanish" and recognized_text:  # Default case
            detected_tongue = speech_service._detect_mother_tongue_from_text(recognized_text)
            if detected_tongue != mother_tongue:
                logger.info(f"🔍 Auto-detected mother tongue: {detected_tongue}")
                return {
                    "text": recognized_text,
                    "detected_language": detected_tongue,
                    "confidence": "high" if len(recognized_text) > 10 else "medium"
                }
        
        return {
            "text": recognized_text,
            "language": mother_tongue,
            "confidence": "high" if len(recognized_text) > 10 else "medium"
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Speech-to-text error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Audio processing failed. Please check audio format and try again."
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
async def process_voice_command(file: UploadFile = File(...), mother_tongue: Optional[str] = "auto"):
    """
    Voice command processing with dynamic mother tongue support.
    """
    tmp_path = None
    try:
        # Validate mother tongue
        if mother_tongue and mother_tongue != "auto":
            mother_tongue = _validate_mother_tongue(mother_tongue)
        else:
            mother_tongue = "spanish"  # Default
            
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
            
        logger.info(f"🎙️ Processing voice command with mother tongue: {mother_tongue}")
        command_text = await speech_service.process_command(tmp_path, mother_tongue)
        
        return {
            "command": command_text,
            "language": mother_tongue,
            "supported_commands": speech_service.language_configs[mother_tongue]['wake_words']
        }
        
    except Exception as e:
        logger.error(f"Voice command error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Voice command processing failed"
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    """Serve generated audio files"""
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
            headers={
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": "*"
            }
        )
    except Exception as e:
        logger.error(f"Audio delivery error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/supported-languages")
async def get_supported_languages():
    """Get list of supported mother tongue languages with dynamic behavior info"""
    try:
        languages = speech_service.get_supported_languages()
        return {
            "supported_languages": languages,
            "default": "spanish",
            "behavior": {
                "spanish": "Translates to German and/or English based on user selections",
                "english": "Translates to Spanish (automatic) + German if selected",
                "german": "Translates to Spanish (automatic) + English if selected",
                "others": "Translate to German and/or English based on user selections"
            },
            "word_by_word_audio": "Only generated if user selects 'word by word audio' for specific languages",
            "audio_format": "[target word] ([Spanish equivalent])",
            "ui_visualization": "Visual display matches audio exactly",
            "description": "EXACT implementation per requirements - completely dynamic based on user preferences"
        }
    except Exception as e:
        logger.error(f"Error fetching supported languages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch supported languages")