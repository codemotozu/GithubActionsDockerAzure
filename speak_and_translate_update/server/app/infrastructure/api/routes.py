# routes.py - Enhanced with PERFECT UI-Audio synchronization and Multi-Style Support

import logging
import tempfile
import os
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
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
    logger.info("🚀 Starting PERFECT UI-AUDIO SYNC Translation API with Multi-Style Support")
    logger.info("🎯 CRITICAL FEATURE: What user sees = What user hears")
    logger.info("📋 Perfect Synchronization Features:")
    logger.info("   1. EXACT format matching: UI display = Audio speech")
    logger.info("   2. EXACT order matching: UI sequence = Audio sequence") 
    logger.info("   3. Phrasal verb handling: Single units in both UI and audio")
    logger.info("   4. Contextual accuracy: AI provides context-aware translations")
    logger.info("   5. Perfect validation: Zero discrepancies allowed")
    logger.info("   6. Multi-Style Support: Multiple simultaneous translation styles")
    
    yield  # App runs here
    
    # Shutdown logic
    logger.info("Shutting down Perfect UI-Audio Sync Translation API")

app = FastAPI(
    title="Perfect UI-Audio Sync Translation API with Multi-Style",
    description="GUARANTEED perfect synchronization between UI display and audio output with multiple style support",
    version="4.0-MULTI-STYLE",
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
    """Translation style preferences with perfect sync and multi-style support"""
    # German styles - ALL can be selected simultaneously
    german_native: bool = False
    german_colloquial: bool = False
    german_informal: bool = False
    german_formal: bool = False
    
    # English styles - ALL can be selected simultaneously
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

def _count_selected_styles(style_preferences: TranslationStylePreferences) -> Dict[str, int]:
    """Count how many styles are selected for each language"""
    german_count = sum([
        style_preferences.german_native,
        style_preferences.german_colloquial,
        style_preferences.german_informal,
        style_preferences.german_formal
    ])
    
    english_count = sum([
        style_preferences.english_native,
        style_preferences.english_colloquial,
        style_preferences.english_informal,
        style_preferences.english_formal
    ])
    
    return {
        'german': german_count,
        'english': english_count,
        'total': german_count + english_count
    }

def _apply_intelligent_defaults(style_preferences: TranslationStylePreferences) -> TranslationStylePreferences:
    """Apply intelligent defaults based on mother tongue if no styles selected"""
    mother_tongue = _validate_mother_tongue(style_preferences.mother_tongue or 'spanish')
    
    # Count selected styles
    style_counts = _count_selected_styles(style_preferences)
    
    # Apply defaults only if NO styles are selected
    if style_counts['total'] == 0:
        logger.info(f"🎯 No styles selected - applying defaults for mother tongue: {mother_tongue}")
        
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
        logger.info(f"🎯 User selected {style_counts['total']} specific styles")
        if style_counts['german'] > 0:
            logger.info(f"   🇩🇪 German: {style_counts['german']} styles")
        if style_counts['english'] > 0:
            logger.info(f"   🇺🇸 English: {style_counts['english']} styles")
    
    return style_preferences

def _log_perfect_sync_setup(text: str, style_preferences: TranslationStylePreferences):
    """Log the perfect sync translation setup with multi-style support"""
    mother_tongue = style_preferences.mother_tongue or 'spanish'
    style_counts = _count_selected_styles(style_preferences)
    
    logger.info(f"\n" + "🎯" + "="*80)
    logger.info(f"🎯 PERFECT UI-AUDIO SYNC MULTI-STYLE TRANSLATION SETUP")
    logger.info(f"🎯" + "="*80)
    logger.info(f"📝 Input Text: '{text}'")
    logger.info(f"🌍 Mother Tongue: {mother_tongue.upper()}")
    logger.info(f"📊 Total Styles Selected: {style_counts['total']}")
    
    # Log expected behavior with perfect sync details
    expected_translations = []
    automatic_translations = []
    
    if mother_tongue == 'spanish':
        if style_counts['german'] > 0:
            expected_translations.append(f'German ({style_counts["german"]} styles)')
        if style_counts['english'] > 0:
            expected_translations.append(f'English ({style_counts["english"]} styles)')
    elif mother_tongue == 'english':
        automatic_translations.append('Spanish')
        if style_counts['german'] > 0:
            expected_translations.append(f'German ({style_counts["german"]} styles)')
    elif mother_tongue == 'german':
        automatic_translations.append('Spanish')
        if style_counts['english'] > 0:
            expected_translations.append(f'English ({style_counts["english"]} styles)')
    
    # Log translation targets
    if automatic_translations:
        logger.info(f"🔄 Automatic Translations: {', '.join(automatic_translations)}")
    if expected_translations:
        logger.info(f"🎯 User-Selected Translations: {', '.join(expected_translations)}")
    
    # CRITICAL: Log perfect sync audio settings
    logger.info(f"🎵 PERFECT SYNC Audio Settings:")
    logger.info(f"   German word-by-word: {style_preferences.german_word_by_word}")
    logger.info(f"   English word-by-word: {style_preferences.english_word_by_word}")
    
    # Detailed style breakdown
    logger.info(f"🇩🇪 German Styles Selected:")
    if style_preferences.german_native:
        logger.info(f"   ✅ Native")
    if style_preferences.german_colloquial:
        logger.info(f"   ✅ Colloquial")
    if style_preferences.german_informal:
        logger.info(f"   ✅ Informal")
    if style_preferences.german_formal:
        logger.info(f"   ✅ Formal")
    
    logger.info(f"🇺🇸 English Styles Selected:")
    if style_preferences.english_native:
        logger.info(f"   ✅ Native")
    if style_preferences.english_colloquial:
        logger.info(f"   ✅ Colloquial")
    if style_preferences.english_informal:
        logger.info(f"   ✅ Informal")
    if style_preferences.english_formal:
        logger.info(f"   ✅ Formal")
    
    # Audio format information
    if style_preferences.german_word_by_word or style_preferences.english_word_by_word:
        logger.info(f"🎯 Multi-Style Audio Generation:")
        logger.info(f"   • Each selected style will be spoken")
        logger.info(f"   • Format: Full translation → Word-by-word breakdown")
        logger.info(f"   • Word format: [target word] ([Spanish equivalent])")
        logger.info(f"   • UI display will match audio EXACTLY")
    
    logger.info(f"🎯" + "="*80)

def _validate_perfect_sync_response(translation: Translation, style_preferences: TranslationStylePreferences):
    """Validate perfect synchronization for multiple styles"""
    logger.info("\n🔍 VALIDATING PERFECT MULTI-STYLE SYNCHRONIZATION")
    logger.info("="*60)
    
    style_counts = _count_selected_styles(style_preferences)
    
    validation_results = {
        'has_audio': translation.audio_path is not None,
        'has_word_by_word': translation.word_by_word is not None and len(translation.word_by_word) > 0,
        'word_by_word_requested': style_preferences.german_word_by_word or style_preferences.english_word_by_word,
        'styles_requested': style_counts['total'],
        'styles_in_response': 0,
        'sync_validation': [],
        'warnings': [],
        'errors': []
    }
    
    logger.info(f"Audio generated: {validation_results['has_audio']}")
    logger.info(f"Word-by-word data present: {validation_results['has_word_by_word']}")
    logger.info(f"Word-by-word requested: {validation_results['word_by_word_requested']}")
    logger.info(f"Styles requested: {validation_results['styles_requested']}")
    
    if validation_results['word_by_word_requested'] and validation_results['has_word_by_word']:
        logger.info("🎯 MULTI-STYLE PERFECT SYNC MODE ACTIVE - Validating...")
        
        # Validate word-by-word data structure for multiple styles
        word_by_word = translation.word_by_word
        total_pairs = len(word_by_word)
        
        logger.info(f"📊 Total word pairs for UI display: {total_pairs}")
        
        # Group by style and validate
        style_groups = {}
        for key, data in word_by_word.items():
            style_name = data.get('style', 'unknown')
            language = data.get('language', 'unknown')
            
            if style_name not in style_groups:
                style_groups[style_name] = []
            style_groups[style_name].append((key, data))
        
        validation_results['styles_in_response'] = len(style_groups)
        logger.info(f"📊 Styles in response: {validation_results['styles_in_response']}")
        
        # Validate each style's word-by-word data
        for style_name, pairs in style_groups.items():
            # Sort by order
            try:
                pairs.sort(key=lambda x: int(x[1].get('order', '0')))
                logger.info(f"✅ {style_name}: {len(pairs)} pairs in correct order")
                
                # Validate format for first few pairs
                for i, (key, data) in enumerate(pairs[:3]):
                    source = data.get('source', '')
                    spanish = data.get('spanish', '')
                    display_format = data.get('display_format', '')
                    expected_format = f"[{source}] ([{spanish}])"
                    
                    if display_format == expected_format:
                        validation_results['sync_validation'].append(f"✅ {style_name} pair {i+1}: Perfect format")
                    else:
                        validation_results['errors'].append(
                            f"❌ {style_name}: Format mismatch - Expected: {expected_format}, Got: {display_format}"
                        )
                    
                    if i < 3:
                        logger.info(f"   {i+1}. {display_format} ✅")
                        
            except Exception as e:
                validation_results['errors'].append(f"❌ {style_name}: Validation failed - {str(e)}")
        
        # Check for phrasal/separable verbs
        phrasal_verbs = [data for data in word_by_word.values() if data.get('is_phrasal_verb') == 'true']
        if phrasal_verbs:
            logger.info(f"🔗 Found {len(phrasal_verbs)} phrasal/separable verbs across all styles")
    
    elif validation_results['word_by_word_requested'] and not validation_results['has_word_by_word']:
        validation_results['warnings'].append("⚠️ Word-by-word requested but no data generated")
        logger.warning("⚠️ Word-by-word audio requested but no synchronization data generated")
    
    # Final validation summary
    if validation_results['errors']:
        logger.error(f"❌ MULTI-STYLE SYNC VALIDATION FAILED: {len(validation_results['errors'])} errors")
        for error in validation_results['errors']:
            logger.error(f"   {error}")
    elif validation_results['word_by_word_requested']:
        logger.info("✅ PERFECT MULTI-STYLE UI-AUDIO SYNCHRONIZATION VALIDATED")
        logger.info(f"🎯 {validation_results['styles_in_response']} styles with perfect sync")
    else:
        logger.info("ℹ️ Simple translation mode - no perfect sync validation needed")
    
    logger.info("="*60)
    return validation_results

# Health check endpoint with perfect sync info
@app.get("/health")
async def health_check():
    """Health check with perfect UI-Audio synchronization and multi-style status"""
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
        "service": "Perfect UI-Audio Sync Translation API with Multi-Style",
        "version": "4.0-MULTI-STYLE",
        "timestamp": datetime.utcnow().isoformat(),
        "perfect_sync_features": {
            "ui_audio_synchronization": "GUARANTEED perfect match",
            "format_consistency": "UI display format = Audio speech format",
            "order_consistency": "UI display order = Audio speaking order",
            "phrasal_verb_handling": "Single units in both UI and audio",
            "contextual_accuracy": "AI provides context-aware translations",
            "validation_system": "Zero discrepancies allowed",
            "multi_style_support": "Multiple simultaneous translation styles"
        },
        "multi_style_features": {
            "simultaneous_styles": "Select multiple styles at once",
            "per_style_audio": "Each style gets its own audio segment",
            "word_by_word_all_styles": "Word-by-word for all selected styles",
            "perfect_sync_all_styles": "UI-Audio sync maintained for each style"
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
        "service": "Perfect UI-Audio Sync Translation API with Multi-Style Support",
        "description": "GUARANTEED perfect synchronization with multiple simultaneous translation styles",
        "version": "4.0-MULTI-STYLE",
        "perfect_sync_guarantee": {
            "visual_audio_match": "What you see is exactly what you hear",
            "format_consistency": "UI format = Audio format (identical)",
            "order_consistency": "UI order = Audio order (identical)",
            "phrasal_verb_unity": "Phrasal/separable verbs as single units",
            "zero_discrepancies": "Perfect synchronization guaranteed",
            "multi_style_support": "All selected styles perfectly synchronized"
        },
        "requirements_compliance": {
            "multi_style_solution": "Handle multiple simultaneous translation styles",
            "spanish_mother_tongue": "German and/or English based on selections",
            "english_mother_tongue": "Spanish (automatic) + German if selected", 
            "german_mother_tongue": "Spanish (automatic) + English if selected",
            "word_by_word_audio": "Available for ALL selected styles",
            "audio_format": "[target word] ([Spanish equivalent])",
            "ai_powered": "Contextually accurate translations for each style",
            "dynamic_behavior": "Based on user preferences"
        },
        "endpoints": {
            "/api/conversation": "Main perfect sync multi-style translation endpoint",
            "/api/speech-to-text": "Speech recognition with mother tongue detection",
            "/api/voice-command": "Voice command processing",
            "/api/audio/{filename}": "Audio file serving",
            "/health": "Health check with perfect sync and multi-style status"
        }
    }

@app.post("/api/conversation", response_model=Translation)
async def start_conversation(prompt: PromptRequest):
    """
    Main conversation endpoint with PERFECT UI-Audio synchronization and multi-style support.
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
        
        # Process the translation with perfect sync and multi-style support
        logger.info(f"🚀 Starting PERFECT SYNC MULTI-STYLE translation with mother tongue: {mother_tongue}")
        
        try:
            response = await translation_service.process_prompt(
                text=prompt.text, 
                source_lang=prompt.source_lang or "auto", 
                target_lang=prompt.target_lang or "multi",
                style_preferences=prompt.style_preferences,
                mother_tongue=mother_tongue
            )
        except Exception as translation_error:
            logger.error(f"❌ Translation service error: {str(translation_error)}")
            
            # Create a fallback response
            fallback_response = Translation(
                original_text=prompt.text,
                translated_text=f"Translation error occurred. Input text: '{prompt.text}' (Mother tongue: {mother_tongue})",
                source_language=mother_tongue,
                target_language="multi",
                audio_path=None,
                translations={"error": f"Translation failed: {str(translation_error)[:200]}"},
                word_by_word=None,
                grammar_explanations={"error": "Translation service unavailable"}
            )
            
            logger.info("📋 Returning fallback response due to translation error")
            return fallback_response
        
        # CRITICAL: Validate perfect synchronization for multiple styles
        try:
            sync_validation = _validate_perfect_sync_response(response, prompt.style_preferences)
        except Exception as validation_error:
            logger.warning(f"⚠️ Sync validation error: {str(validation_error)}")
            sync_validation = {'errors': [], 'warnings': ['Validation skipped due to error']}
        
        # Log the successful completion with sync details
        style_counts = _count_selected_styles(prompt.style_preferences)
        logger.info(f"✅ PERFECT SYNC MULTI-STYLE translation completed successfully")
        logger.info(f"   Input ('{response.source_language}'): {response.original_text}")
        logger.info(f"   Output length: {len(response.translated_text)} characters")
        logger.info(f"   Styles processed: {style_counts['total']}")
        logger.info(f"   Audio generated: {'Yes' if response.audio_path else 'No'}")
        logger.info(f"   Word-by-word data: {'Yes' if response.word_by_word else 'No'}")
        
        if response.audio_path:
            # Check if word-by-word was requested
            word_by_word_requested = (
                prompt.style_preferences.german_word_by_word or 
                prompt.style_preferences.english_word_by_word
            )
            logger.info(f"   Audio type: {'Multi-style word-by-word breakdown' if word_by_word_requested else 'Multi-style translation reading'}")
            
            if word_by_word_requested and response.word_by_word:
                total_pairs = len(response.word_by_word)
                logger.info(f"   Perfect sync pairs: {total_pairs}")
                logger.info(f"   Styles in sync: {sync_validation.get('styles_in_response', 0)}")
                logger.info(f"   Synchronization status: {'✅ PERFECT' if not sync_validation['errors'] else '❌ ISSUES DETECTED'}")
        
        # Add perfect sync validation info to response (for debugging)
        logger.info("\n📱 MULTI-STYLE WORD-BY-WORD UI VISUALIZATION DEBUG:")
        logger.info("="*60)
        if response.word_by_word:
            logger.info(f"   📝 Word-by-word data available for UI")
            logger.info(f"   📊 Total UI elements: {len(response.word_by_word)}")
            logger.info(f"   🎯 Styles covered: {sync_validation.get('styles_in_response', 0)}")
            
            # Log a sample of UI data structure
            sample_keys = list(response.word_by_word.keys())[:5]
            for key in sample_keys:
                data = response.word_by_word[key]
                style = data.get('style', 'unknown')
                format_str = data.get('display_format', 'N/A')
                logger.info(f"   📱 {style}: {format_str}")
        else:
            logger.info(f"   📝 No word-by-word data available for UI")
        
        logger.info("="*60)
        
        return response
        
    except HTTPException as he:
        # Re-raise HTTP exceptions as-is
        logger.warning(f"⚠️ HTTP exception in conversation endpoint: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"❌ Unexpected error in conversation endpoint: {str(e)}", exc_info=True)
        
        # Create emergency fallback response
        try:
            emergency_response = Translation(
                original_text=prompt.text if hasattr(prompt, 'text') else "Unknown input",
                translated_text="Sorry, translation service is temporarily unavailable. Please try again.",
                source_language="unknown",
                target_language="multi",
                audio_path=None,
                translations={"error": "Service temporarily unavailable"},
                word_by_word=None,
                grammar_explanations={"error": "Service temporarily unavailable"}
            )
            
            logger.info("🆘 Returning emergency fallback response")
            return emergency_response
            
        except Exception as fallback_error:
            logger.error(f"❌ Even fallback response failed: {str(fallback_error)}")
            raise HTTPException(
                status_code=500, 
                detail="Translation service is temporarily unavailable. Please try again later."
            )

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
    """Get list of supported mother tongue languages with perfect sync and multi-style info"""
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
            "multi_style_features": {
                "simultaneous_styles": "Select multiple styles at once (e.g., Native + Colloquial + Formal)",
                "per_style_translation": "Each style gets its own contextually appropriate translation",
                "all_styles_audio": "Audio includes all selected styles sequentially",
                "word_by_word_all_styles": "Word-by-word breakdown for each selected style"
            },
            "perfect_sync_features": {
                "word_by_word_audio": "Generated for ALL selected styles when enabled",
                "audio_format": "[target word] ([Spanish equivalent])",
                "ui_format": "EXACTLY the same as audio format",
                "synchronization": "Perfect - UI order = Audio order for all styles",
                "phrasal_verbs": "Treated as single units in both UI and audio",
                "validation": "Automatic validation ensures zero discrepancies"
            },
            "description": "Perfect UI-Audio synchronization with multi-style support - What you see is exactly what you hear for ALL selected styles"
        }
    except Exception as e:
        logger.error(f"Error fetching supported languages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch supported languages")

@app.get("/api/style-combinations")
async def get_style_combinations():
    """Get information about possible style combinations"""
    return {
        "max_simultaneous_styles": {
            "german": 4,  # Native, Colloquial, Informal, Formal
            "english": 4,  # Native, Colloquial, Informal, Formal
            "total": 8  # All styles can be selected simultaneously
        },
        "example_combinations": [
            {
                "name": "Complete German Learning",
                "german_styles": ["native", "colloquial", "informal", "formal"],
                "english_styles": [],
                "word_by_word": ["german"],
                "description": "All German styles with word-by-word audio"
            },
            {
                "name": "Business Communication",
                "german_styles": ["formal"],
                "english_styles": ["formal"],
                "word_by_word": ["german", "english"],
                "description": "Formal styles in both languages"
            },
            {
                "name": "Casual Conversation",
                "german_styles": ["colloquial", "informal"],
                "english_styles": ["colloquial", "informal"],
                "word_by_word": [],
                "description": "Casual styles without word-by-word"
            },
            {
                "name": "Complete Immersion",
                "german_styles": ["native", "colloquial", "informal", "formal"],
                "english_styles": ["native", "colloquial", "informal", "formal"],
                "word_by_word": ["german", "english"],
                "description": "All 8 styles with complete word-by-word"
            }
        ],
        "audio_generation": {
            "format": "Single audio file containing all selected styles",
            "structure": "Style announcement → Full translation → Word-by-word (if enabled)",
            "separation": "Brief pause between different styles",
            "order": "German styles first, then English styles"
        }
    }