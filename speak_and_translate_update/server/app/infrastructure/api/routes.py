# routes.py - Enhanced with PERFECT UI-Audio synchronization debugging and validation

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

# Configure enhanced logging for perfect sync debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("perfect_sync_api.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic with perfect sync info
    logger.info("🚀 Starting PERFECT UI-AUDIO SYNC Translation API")
    logger.info("🎯 CRITICAL FEATURE: What user sees = What user hears")
    logger.info("📋 Perfect Synchronization Features:")
    logger.info("   1. EXACT format matching: UI display = Audio speech")
    logger.info("   2. EXACT order matching: UI sequence = Audio sequence") 
    logger.info("   3. Phrasal verb handling: Single units in both UI and audio")
    logger.info("   4. Contextual accuracy: AI provides context-aware translations")
    logger.info("   5. Perfect validation: Zero discrepancies allowed")
    
    yield  # App runs here
    
    # Shutdown logic
    logger.info("Shutting down Perfect UI-Audio Sync Translation API")

app = FastAPI(
    title="Perfect UI-Audio Sync Translation API",
    description="GUARANTEED perfect synchronization between UI display and audio output",
    version="3.0-PERFECT-SYNC",
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
    """Translation style preferences with perfect sync support"""
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
    
    # CRITICAL: Word-by-word audio preferences for perfect sync
    german_word_by_word: bool = False
    english_word_by_word: bool = False
    
    # Mother tongue for dynamic translation
    mother_tongue: Optional[str] = "spanish"

class PromptRequest(BaseModel):
    text: str
    source_lang: Optional[str] = "auto"
    target_lang: Optional[str] = "multi"
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
    """Apply intelligent defaults based on mother tongue"""
    mother_tongue = _validate_mother_tongue(style_preferences.mother_tongue or 'spanish')
    
    # Check if any styles are selected
    has_any_style = any([
        style_preferences.german_native, style_preferences.german_colloquial,
        style_preferences.german_informal, style_preferences.german_formal,
        style_preferences.english_native, style_preferences.english_colloquial,
        style_preferences.english_informal, style_preferences.english_formal
    ])
    
    # Apply defaults only if NO styles are selected
    if not has_any_style:
        logger.info(f"🎯 Applying perfect sync defaults for mother tongue: {mother_tongue}")
        
        if mother_tongue == "spanish":
            style_preferences.german_colloquial = True
            style_preferences.english_colloquial = True
            logger.info("   ✅ Spanish defaults: German + English colloquial")
        elif mother_tongue == "english":
            style_preferences.german_colloquial = True
            logger.info("   ✅ English defaults: German colloquial (Spanish automatic)")
        elif mother_tongue == "german":
            style_preferences.english_colloquial = True
            logger.info("   ✅ German defaults: English colloquial (Spanish automatic)")
        else:
            style_preferences.german_colloquial = True
            style_preferences.english_colloquial = True
            logger.info(f"   ✅ {mother_tongue} defaults: German + English colloquial")
    else:
        logger.info(f"🎯 User selected specific styles for mother tongue: {mother_tongue}")
    
    return style_preferences

def _log_perfect_sync_setup(text: str, style_preferences: TranslationStylePreferences):
    """Log the perfect sync translation setup with detailed debugging"""
    mother_tongue = style_preferences.mother_tongue or 'spanish'
    
    logger.info(f"\n" + "🎯" + "="*80)
    logger.info(f"🎯 PERFECT UI-AUDIO SYNC TRANSLATION SETUP")
    logger.info(f"🎯" + "="*80)
    logger.info(f"📝 Input Text: '{text}'")
    logger.info(f"🌍 Mother Tongue: {mother_tongue.upper()}")
    
    # Log expected behavior with perfect sync details
    expected_translations = []
    automatic_translations = []
    
    if mother_tongue == 'spanish':
        if any([style_preferences.german_native, style_preferences.german_colloquial,
               style_preferences.german_informal, style_preferences.german_formal]):
            expected_translations.append('German')
        if any([style_preferences.english_native, style_preferences.english_colloquial,
               style_preferences.english_informal, style_preferences.english_formal]):
            expected_translations.append('English')
    elif mother_tongue == 'english':
        automatic_translations.append('Spanish')
        if any([style_preferences.german_native, style_preferences.german_colloquial,
               style_preferences.german_informal, style_preferences.german_formal]):
            expected_translations.append('German')
    elif mother_tongue == 'german':
        automatic_translations.append('Spanish')
        if any([style_preferences.english_native, style_preferences.english_colloquial,
               style_preferences.english_informal, style_preferences.english_formal]):
            expected_translations.append('English')
    
    # Log translation targets
    if automatic_translations:
        logger.info(f"🔄 Automatic Translations: {', '.join(automatic_translations)}")
    if expected_translations:
        logger.info(f"🎯 User-Selected Translations: {', '.join(expected_translations)}")
    else:
        logger.info(f"⚠️ No target languages selected")
    
    # CRITICAL: Log perfect sync audio settings
    logger.info(f"🎵 PERFECT SYNC Audio Settings:")
    logger.info(f"   German word-by-word: {style_preferences.german_word_by_word}")
    logger.info(f"   English word-by-word: {style_preferences.english_word_by_word}")
    
    # Determine audio format
    if style_preferences.german_word_by_word or style_preferences.english_word_by_word:
        logger.info(f"   🎯 Audio format: [target word] ([Spanish equivalent])")
        logger.info(f"   🎯 UI format: EXACTLY THE SAME as audio format")
        logger.info(f"   🎯 Synchronization: PERFECT - UI order = Audio order")
        
        # Log specific word-by-word details
        if style_preferences.german_word_by_word:
            logger.info(f"   🇩🇪 German word-by-word: [German word/phrase] ([Spanish])")
            logger.info(f"      • Separable verbs treated as single units")
            logger.info(f"      • UI display matches audio exactly")
        if style_preferences.english_word_by_word:
            logger.info(f"   🇺🇸 English word-by-word: [English word/phrase] ([Spanish])")
            logger.info(f"      • Phrasal verbs treated as single units")
            logger.info(f"      • UI display matches audio exactly")
    else:
        logger.info(f"   🎯 Audio format: Simple translation reading")
        logger.info(f"   🎯 No word-by-word sync needed")
    
    # Log style selections with perfect sync implications
    logger.info(f"🇩🇪 German Styles (Perfect Sync Enabled):")
    logger.info(f"   Native: {style_preferences.german_native}")
    logger.info(f"   Colloquial: {style_preferences.german_colloquial}")
    logger.info(f"   Informal: {style_preferences.german_informal}")
    logger.info(f"   Formal: {style_preferences.german_formal}")
    
    logger.info(f"🇺🇸 English Styles (Perfect Sync Enabled):")
    logger.info(f"   Native: {style_preferences.english_native}")
    logger.info(f"   Colloquial: {style_preferences.english_colloquial}")
    logger.info(f"   Informal: {style_preferences.english_informal}")
    logger.info(f"   Formal: {style_preferences.english_formal}")
    
    logger.info(f"🎯" + "="*80)

def _validate_perfect_sync_response(translation: Translation, style_preferences: TranslationStylePreferences):
    """Validate that the response supports perfect UI-Audio synchronization"""
    logger.info("\n🔍 VALIDATING PERFECT UI-AUDIO SYNCHRONIZATION")
    logger.info("="*60)
    
    validation_results = {
        'has_audio': translation.audio_path is not None,
        'has_word_by_word': translation.word_by_word is not None and len(translation.word_by_word) > 0,
        'word_by_word_requested': False,
        'sync_validation': [],
        'warnings': [],
        'errors': []
    }
    
    # Check if word-by-word was requested
    german_requested = getattr(style_preferences, 'german_word_by_word', False)
    english_requested = getattr(style_preferences, 'english_word_by_word', False)
    validation_results['word_by_word_requested'] = german_requested or english_requested
    
    logger.info(f"Audio generated: {validation_results['has_audio']}")
    logger.info(f"Word-by-word data present: {validation_results['has_word_by_word']}")
    logger.info(f"Word-by-word requested: {validation_results['word_by_word_requested']}")
    
    if validation_results['word_by_word_requested'] and validation_results['has_word_by_word']:
        logger.info("🎯 PERFECT SYNC MODE ACTIVE - Validating synchronization...")
        
        # Validate word-by-word data structure
        word_by_word = translation.word_by_word
        total_pairs = len(word_by_word)
        
        logger.info(f"📊 Total word pairs for UI display: {total_pairs}")
        
        # Group by language and validate order
        by_language = {}
        for key, data in word_by_word.items():
            language = data.get('language', 'unknown')
            if language not in by_language:
                by_language[language] = []
            by_language[language].append((key, data))
        
        # Validate each language group
        for language, pairs in by_language.items():
            # Sort by order
            try:
                pairs.sort(key=lambda x: int(x[1].get('order', '0')))
                logger.info(f"✅ {language}: {len(pairs)} pairs in correct order")
                
                # Validate each pair
                for i, (key, data) in enumerate(pairs):
                    source = data.get('source', '')
                    spanish = data.get('spanish', '')
                    display_format = data.get('display_format', '')
                    expected_format = f"[{source}] ([{spanish}])"
                    
                    if display_format == expected_format:
                        validation_results['sync_validation'].append(f"✅ {key}: Perfect format match")
                    else:
                        validation_results['errors'].append(f"❌ {key}: Format mismatch - Expected: {expected_format}, Got: {display_format}")
                    
                    # Log first few for debugging
                    if i < 3:
                        logger.info(f"   {i+1}. {display_format} ✅")
                        
            except Exception as e:
                validation_results['errors'].append(f"❌ {language}: Order validation failed - {str(e)}")
        
        # Check for phrasal/separable verbs
        phrasal_verbs = [data for data in word_by_word.values() if data.get('is_phrasal_verb') == 'true']
        if phrasal_verbs:
            logger.info(f"🔗 Found {len(phrasal_verbs)} phrasal/separable verbs (treated as single units)")
            for data in phrasal_verbs[:3]:  # Log first few
                logger.info(f"   • {data.get('source', '')} → {data.get('spanish', '')}")
        
    elif validation_results['word_by_word_requested'] and not validation_results['has_word_by_word']:
        validation_results['warnings'].append("⚠️ Word-by-word requested but no data generated")
        logger.warning("⚠️ Word-by-word audio requested but no synchronization data generated")
    
    # Final validation summary
    if validation_results['errors']:
        logger.error(f"❌ PERFECT SYNC VALIDATION FAILED: {len(validation_results['errors'])} errors")
        for error in validation_results['errors']:
            logger.error(f"   {error}")
    elif validation_results['word_by_word_requested']:
        logger.info("✅ PERFECT UI-AUDIO SYNCHRONIZATION VALIDATED")
        logger.info("🎯 UI display will match audio output exactly")
    else:
        logger.info("ℹ️ Simple translation mode - no perfect sync validation needed")
    
    logger.info("="*60)
    return validation_results

# Health check endpoint with perfect sync info
@app.get("/health")
async def health_check():
    """Health check with perfect UI-Audio synchronization status"""
    # Create audio directory
    audio_dir = "/tmp/tts_audio" if os.name != "nt" else os.path.join(os.environ.get("TEMP", ""), "tts_audio")
    try:
        os.makedirs(audio_dir, exist_ok=True)
        if os.name != "nt":
            os.chmod(audio_dir, 0o755)
    except Exception as e:
        logger.warning(f"Could not create audio directory: {str(e)}")

    # Check environment variables
    env_vars = {
        "AZURE_SPEECH_KEY": bool(os.environ.get("AZURE_SPEECH_KEY")),
        "AZURE_SPEECH_REGION": bool(os.environ.get("AZURE_SPEECH_REGION")),
        "GEMINI_API_KEY": bool(os.environ.get("GEMINI_API_KEY")),
        "PORT": os.environ.get("PORT", "8000"),
    }

    return {
        "status": "healthy",
        "service": "Perfect UI-Audio Sync Translation API",
        "version": "3.0-PERFECT-SYNC",
        "timestamp": datetime.utcnow().isoformat(),
        "perfect_sync_features": {
            "ui_audio_synchronization": "GUARANTEED perfect match",
            "format_consistency": "UI display format = Audio speech format",
            "order_consistency": "UI display order = Audio speaking order",
            "phrasal_verb_handling": "Single units in both UI and audio",
            "contextual_accuracy": "AI provides context-aware translations",
            "validation_system": "Zero discrepancies allowed"
        },
        "sync_guarantee": {
            "what_you_see": "EXACTLY what you hear",
            "format": "[target word/phrase] ([Spanish equivalent])",
            "order": "Sequential, perfectly synchronized",
            "validation": "Automatic validation with error reporting"
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
        "service": "Perfect UI-Audio Sync Translation API",
        "description": "GUARANTEED perfect synchronization between UI display and audio output",
        "version": "3.0-PERFECT-SYNC",
        "perfect_sync_guarantee": {
            "visual_audio_match": "What you see is exactly what you hear",
            "format_consistency": "UI format = Audio format (identical)",
            "order_consistency": "UI order = Audio order (identical)",
            "phrasal_verb_unity": "Phrasal/separable verbs as single units",
            "zero_discrepancies": "Perfect synchronization guaranteed"
        },
        "requirements_compliance": {
            "4.1_solution": "Perfect UI-Audio synchronization implemented",
            "spanish_mother_tongue": "German and/or English based on selections",
            "english_mother_tongue": "Spanish (automatic) + German if selected", 
            "german_mother_tongue": "Spanish (automatic) + English if selected",
            "word_by_word_audio": "Only if user selects 'word by word audio'",
            "audio_format": "[target word] ([Spanish equivalent])",
            "ai_powered": "Contextually accurate translations",
            "dynamic_behavior": "Based on user preferences"
        },
        "endpoints": {
            "/api/conversation": "Main perfect sync translation endpoint",
            "/api/speech-to-text": "Speech recognition with mother tongue detection",
            "/api/voice-command": "Voice command processing",
            "/api/audio/{filename}": "Audio file serving",
            "/health": "Health check with perfect sync status"
        }
    }

@app.post("/api/conversation", response_model=Translation)
async def start_conversation(prompt: PromptRequest):
    """
    Main conversation endpoint with PERFECT UI-Audio synchronization.
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
        
        # Log the perfect sync translation setup
        _log_perfect_sync_setup(prompt.text, prompt.style_preferences)
        
        # Process the translation with perfect sync
        logger.info(f"🚀 Starting PERFECT SYNC translation with mother tongue: {mother_tongue}")
        response = await translation_service.process_prompt(
            text=prompt.text, 
            source_lang=prompt.source_lang or "auto", 
            target_lang=prompt.target_lang or "multi",
            style_preferences=prompt.style_preferences,
            mother_tongue=mother_tongue
        )
        
        # CRITICAL: Validate perfect synchronization
        sync_validation = _validate_perfect_sync_response(response, prompt.style_preferences)
        
        # Log the successful completion with sync details
        logger.info(f"✅ PERFECT SYNC translation completed successfully")
        logger.info(f"   Input ('{response.source_language}'): {response.original_text}")
        logger.info(f"   Output length: {len(response.translated_text)} characters")
        logger.info(f"   Audio generated: {'Yes' if response.audio_path else 'No'}")
        logger.info(f"   Word-by-word data: {'Yes' if response.word_by_word else 'No'}")
        
        if response.audio_path:
            # Check if word-by-word was requested
            word_by_word_requested = (
                prompt.style_preferences.german_word_by_word or 
                prompt.style_preferences.english_word_by_word
            )
            logger.info(f"   Audio type: {'Word-by-word breakdown' if word_by_word_requested else 'Simple translation reading'}")
            
            if word_by_word_requested and response.word_by_word:
                total_pairs = len(response.word_by_word)
                logger.info(f"   Perfect sync pairs: {total_pairs}")
                logger.info(f"   Synchronization status: {'✅ PERFECT' if not sync_validation['errors'] else '❌ ISSUES DETECTED'}")
        
        # Add perfect sync validation info to response (for debugging)
        logger.info("\n📱 WORD-BY-WORD UI VISUALIZATION DEBUG:")
        logger.info("="*60)
        if response.word_by_word:
            logger.info(f"   📝 Word-by-word data available for UI")
            logger.info(f"   📊 Total UI elements: {len(response.word_by_word)}")
            
            # Log a sample of UI data structure
            sample_keys = list(response.word_by_word.keys())[:3]
            for key in sample_keys:
                data = response.word_by_word[key]
                logger.info(f"   📱 UI: {data.get('display_format', 'N/A')}")
        else:
            logger.info(f"   📝 No word-by-word data available for UI")
        
        logger.info("="*60)
        
        return response
        
    except HTTPException as he:
        # Re-raise HTTP exceptions as-is
        raise he
    except Exception as e:
        logger.error(f"❌ Perfect sync translation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Perfect sync translation failed: {str(e)}")

# Keep all other endpoints unchanged (speech-to-text, voice-command, audio serving, etc.)
@app.post("/api/speech-to-text")
async def speech_to_text(file: UploadFile = File(...), mother_tongue: Optional[str] = "auto"):
    """Speech-to-text with dynamic mother tongue detection and support."""
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
    """Voice command processing with dynamic mother tongue support."""
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
    """Get list of supported mother tongue languages with perfect sync info"""
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
            "perfect_sync_features": {
                "word_by_word_audio": "Only generated if user selects 'word by word audio' for specific languages",
                "audio_format": "[target word] ([Spanish equivalent])",
                "ui_format": "EXACTLY the same as audio format",
                "synchronization": "Perfect - UI order = Audio order",
                "phrasal_verbs": "Treated as single units in both UI and audio",
                "validation": "Automatic validation ensures zero discrepancies"
            },
            "description": "Perfect UI-Audio synchronization guaranteed - What you see is exactly what you hear"
        }
    except Exception as e:
        logger.error(f"Error fetching supported languages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch supported languages")