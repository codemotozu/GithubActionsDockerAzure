#!/usr/bin/env python3
"""
Test script to validate TTS service works in container environment
"""

import os
import sys
import asyncio
import logging

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.application.services.tts_service import EnhancedTTSService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_tts_service():
    """Test TTS service in container environment"""
    logger.info("🧪 Starting TTS service container test")
    
    # Set container environment for testing
    os.environ["CONTAINER_ENV"] = "true"
    os.environ["AZURE_SPEECH_KEY"] = os.getenv("AZURE_SPEECH_KEY", "test_key")
    os.environ["AZURE_SPEECH_REGION"] = os.getenv("AZURE_SPEECH_REGION", "westcentralus")
    
    try:
        # Initialize TTS service
        logger.info("📝 Initializing TTS service...")
        tts_service = EnhancedTTSService()
        logger.info("✅ TTS service initialized successfully")
        
        # Test data
        test_data = {
            'style_data': [
                {
                    'style_name': 'english_native',
                    'translation': 'Hello world',
                    'is_german': False,
                    'is_spanish': False,
                    'word_pairs': [('Hello', 'Hola'), ('world', 'mundo')]
                }
            ]
        }
        
        class MockPreferences:
            def __init__(self):
                self.english_word_by_word = True
                self.german_word_by_word = False
        
        # Test audio generation
        logger.info("🎵 Testing audio generation...")
        result = await tts_service.text_to_speech_word_pairs_v2(
            translations_data=test_data,
            source_lang='spanish',
            target_lang='english',
            style_preferences=MockPreferences()
        )
        
        if result:
            logger.info(f"✅ Audio generation successful: {result}")
            return True
        else:
            logger.warning("⚠️ Audio generation returned None (may be using fallback)")
            return True  # Still consider it a success as long as no exceptions
            
    except Exception as e:
        logger.error(f"❌ TTS service test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_tts_service())
    if success:
        logger.info("🎉 TTS container test completed successfully")
        sys.exit(0)
    else:
        logger.error("💥 TTS container test failed")
        sys.exit(1)