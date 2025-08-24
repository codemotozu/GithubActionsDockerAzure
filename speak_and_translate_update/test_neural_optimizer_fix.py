# test_neural_optimizer_fix.py - Test the neural optimizer fix

import asyncio
import sys
import os

# Add the server directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

async def test_neural_optimizer():
    """Test the neural optimizer with the fixed function signature"""
    
    try:
        from server.app.application.services.ultra_ai_translation_system import ultra_ai_translation_system
        from server.app.domain.entities.translation_style_preferences import TranslationStylePreferences
        
        print("🧪 Testing Neural Optimizer Fix...")
        print("="*50)
        
        # Create test style preferences
        style_prefs = TranslationStylePreferences(
            mother_tongue="spanish",
            german_native=True,
            german_word_by_word=True,
            english_native=True,
            english_word_by_word=False
        )
        
        # Test the translation system
        result = await ultra_ai_translation_system.translate_with_full_ai_stack(
            text="Jugo de piña para la niña",
            source_lang="spanish", 
            target_lang="multi",
            style_preferences=style_prefs,
            mother_tongue="spanish",
            include_audio=True
        )
        
        print(f"✅ Test PASSED - No 'unexpected keyword argument' error!")
        print(f"⏱️  Processing time: {result.processing_time:.1f}ms")
        print(f"🧠 AI enhancements: {len(result.ai_enhancements)}")
        print(f"🎯 Confidence: {result.confidence_summary.get('average_confidence', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        return False

async def test_basic_translation():
    """Test basic translation without neural optimizer"""
    
    try:
        from server.app.application.services.enhanced_translation_service import EnhancedTranslationService
        from server.app.domain.entities.translation_style_preferences import TranslationStylePreferences
        
        print("\n🧪 Testing Basic Enhanced Translation...")
        print("="*50)
        
        service = EnhancedTranslationService()
        
        # Create test style preferences
        style_prefs = TranslationStylePreferences(
            mother_tongue="spanish",
            german_native=True,
            german_formal=True
        )
        
        # Test translation
        result = await service.process_prompt(
            text="Hola mundo",
            source_lang="spanish",
            target_lang="german", 
            style_preferences=style_prefs,
            mother_tongue="spanish"
        )
        
        print(f"✅ Basic translation PASSED!")
        print(f"📝 Original: {result.original_text}")
        print(f"🔄 Translated: {result.translated_text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic translation FAILED: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Neural Optimizer Error Fix Testing")
    print("="*60)
    
    # Test 1: Basic translation
    basic_test = await test_basic_translation()
    
    # Test 2: Full AI stack (this was failing before)
    if basic_test:
        ai_test = await test_neural_optimizer()
    else:
        ai_test = False
    
    print("\n" + "="*60)
    print("📊 TEST SUMMARY:")
    print(f"   Basic Translation: {'✅ PASSED' if basic_test else '❌ FAILED'}")
    print(f"   Neural Optimizer:  {'✅ PASSED' if ai_test else '❌ FAILED'}")
    
    if basic_test and ai_test:
        print("🎉 ALL TESTS PASSED - Neural optimizer error is FIXED!")
    else:
        print("⚠️ Some tests failed - check the error messages above")
    
    return basic_test and ai_test

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)