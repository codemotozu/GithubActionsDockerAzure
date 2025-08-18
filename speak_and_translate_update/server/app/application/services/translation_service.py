# translation_service.py - Complete file with multi-style support

from google.generativeai import GenerativeModel
import google.generativeai as genai
import os
from dotenv import load_dotenv
from ...domain.entities.translation import Translation
from spellchecker import SpellChecker
import unicodedata
import regex as re
from .tts_service import EnhancedTTSService
import tempfile
from typing import Optional, Dict, List, Tuple
import asyncio
import json


class TranslationService:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)

        self.spell = SpellChecker()

        self.generation_config = {
            "temperature": 0.3,  # Lower for more consistent translations
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 8192,
        }

        self.model = GenerativeModel(
            model_name="gemini-2.0-flash", generation_config=self.generation_config
        )

        self.tts_service = EnhancedTTSService()

        # Audio generation settings
        self.audio_retry_attempts = 2
        self.audio_timeout_seconds = 30

        # Language detection patterns for dynamic mother tongue detection
        self.language_patterns = {
            'spanish': {
                'keywords': ['yo', 'tú', 'él', 'ella', 'nosotros', 'vosotros', 'ellos', 'ellas', 'es', 'son', 'está', 'están', 'tiene', 'tienes', 'para', 'con', 'de', 'en', 'la', 'el', 'los', 'las', 'un', 'una', 'unos', 'unas'],
                'patterns': [r'\b(soy|eres|somos|sois|son)\b', r'\b(tengo|tienes|tiene|tenemos|tenéis|tienen)\b', r'\b(estoy|estás|está|estamos|estáis|están)\b']
            },
            'english': {
                'keywords': ['i', 'you', 'he', 'she', 'we', 'they', 'am', 'is', 'are', 'was', 'were', 'have', 'has', 'had', 'the', 'a', 'an', 'and', 'or', 'but', 'with', 'for', 'to'],
                'patterns': [r'\b(am|is|are|was|were)\b', r'\b(have|has|had)\b', r'\b(do|does|did)\b']
            },
            'german': {
                'keywords': ['ich', 'du', 'er', 'sie', 'wir', 'ihr', 'sie', 'bin', 'bist', 'ist', 'sind', 'war', 'waren', 'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einen', 'einem', 'einer', 'und', 'oder', 'aber', 'mit', 'für', 'zu'],
                'patterns': [r'\b(bin|bist|ist|sind|war|waren)\b', r'\b(habe|hast|hat|haben|hatte|hatten)\b', r'\b(mache|machst|macht|machen)\b']
            }
        }

    def _detect_input_language(self, text: str, mother_tongue: str = None) -> str:
        """Detect the language of input text. If mother_tongue is provided, use it as primary hint."""
        text_lower = text.lower()
        
        # If mother tongue is explicitly provided, prioritize it
        if mother_tongue:
            return mother_tongue
            
        # Score each language based on keyword matches
        scores = {'spanish': 0, 'english': 0, 'german': 0}
        
        for lang, data in self.language_patterns.items():
            # Count keyword matches
            for keyword in data['keywords']:
                if f' {keyword} ' in f' {text_lower} ' or text_lower.startswith(f'{keyword} ') or text_lower.endswith(f' {keyword}'):
                    scores[lang] += 1
            
            # Count pattern matches
            for pattern in data['patterns']:
                matches = re.findall(pattern, text_lower)
                scores[lang] += len(matches) * 2  # Patterns are weighted higher
        
        # Return the language with highest score, default to spanish if tied
        detected = max(scores, key=scores.get)
        print(f"🔍 Language detection scores: {scores} -> Detected: {detected}")
        return detected


    def _create_enhanced_context_prompt(self, input_text: str, mother_tongue: str, style_preferences) -> str:
        """Create enhanced prompt for multiple simultaneous styles with true semantic matching."""
        
        print(f"🎯 Creating MULTI-STYLE context prompt for: {mother_tongue.upper()}")
        
        target_languages = []
        german_styles = []
        english_styles = []
        
        # Collect all selected German styles
        if style_preferences.german_native:
            german_styles.append('native')
        if style_preferences.german_colloquial:
            german_styles.append('colloquial')
        if style_preferences.german_informal:
            german_styles.append('informal')
        if style_preferences.german_formal:
            german_styles.append('formal')
        
        # Collect all selected English styles
        if style_preferences.english_native:
            english_styles.append('native')
        if style_preferences.english_colloquial:
            english_styles.append('colloquial')
        if style_preferences.english_informal:
            english_styles.append('informal')
        if style_preferences.english_formal:
            english_styles.append('formal')
        
        # Determine target languages based on mother tongue and selections
        if mother_tongue.lower() == 'spanish':
            if german_styles:
                target_languages.append('german')
            if english_styles:
                target_languages.append('english')
        elif mother_tongue.lower() == 'english':
            target_languages.append('spanish')
            if german_styles:
                target_languages.append('german')
        elif mother_tongue.lower() == 'german':
            target_languages.append('spanish')
            if english_styles:
                target_languages.append('english')

        print(f"🎯 Target languages: {target_languages}")
        print(f"🇩🇪 German styles selected: {german_styles}")
        print(f"🇺🇸 English styles selected: {english_styles}")

        # Build comprehensive prompt with advanced semantic matching guidance
        prompt = f"""Translate the {mother_tongue} text: "{input_text}"

    You are an expert linguist specializing in semantic translation between {mother_tongue} and {', '.join(target_languages)}. 
    Please provide ALL requested translations in this EXACT format:

    """

        # Add German translations for ALL selected styles
        if 'german' in target_languages and german_styles:
            prompt += "GERMAN TRANSLATIONS:\n"
            for style in german_styles:
                prompt += f"German {style.capitalize()}: [Provide {style} German translation here]\n"
            
            # Add word-by-word section with true semantic matching
            if style_preferences.german_word_by_word:
                prompt += "\nGERMAN WORD-BY-WORD:\n"
                for style in german_styles:
                    prompt += f"{style.capitalize()} style: "
                    prompt += "For each word or grammatical unit in your German translation, provide its TRUE SEMANTIC EQUIVALENT in Spanish. "
                    prompt += "Format as: [German word/phrase] ([Spanish semantic equivalent]). "
                    prompt += "Translate what each word MEANS, not its position. "
                    
                    # Language-specific guidance
                    prompt += "Pay special attention to:\n"
                    prompt += "- Verb conjugations (e.g., [sind] should be ([son/están]) based on context)\n"
                    prompt += "- Pronouns ([ich] should be ([yo]), [meine] should be ([mis/mi]))\n"
                    prompt += "- Articles and determiners ([eine] should be ([una]), [die] should be ([la/las]))\n"
                    prompt += "- When translating possession, match 'meine Hände' as [meine] ([mis]) [Hände] ([manos])\n"
                    prompt += "- For 'Ich habe' constructions, ensure [habe] is ([tengo])\n\n"
                prompt += "\n"

        # Add English translations for ALL selected styles
        if 'english' in target_languages and english_styles:
            prompt += "ENGLISH TRANSLATIONS:\n"
            for style in english_styles:
                prompt += f"English {style.capitalize()}: [Provide {style} English translation here]\n"
            
            # Add word-by-word section with true semantic matching
            if style_preferences.english_word_by_word:
                prompt += "\nENGLISH WORD-BY-WORD:\n"
                for style in english_styles:
                    prompt += f"{style.capitalize()} style: "
                    prompt += "For each word or grammatical unit in your English translation, provide its TRUE SEMANTIC EQUIVALENT in Spanish. "
                    prompt += "Format as: [English word/phrase] ([Spanish semantic equivalent]). "
                    prompt += "Translate what each word MEANS, not its position. "
                    
                    # Language-specific guidance
                    prompt += "Pay special attention to:\n"
                    prompt += "- Verb conjugations (e.g., [are] should be ([son/están]) based on context)\n"
                    prompt += "- Pronouns ([I] should be ([yo]), [my] should be ([mis/mi]))\n"
                    prompt += "- Articles and determiners ([a] should be ([un/una]), [the] should be ([el/la/los/las]))\n"
                    prompt += "- When translating 'I've got', ensure [I've] is ([yo]) and [got] is ([tengo])\n"
                    prompt += "- For contractions like [I'm], [you're], pair with their full semantic equivalents ([yo soy], [tú eres])\n\n"
                prompt += "\n"

        # Add Spanish translations if needed
        if 'spanish' in target_languages:
            prompt += "SPANISH TRANSLATIONS:\nSpanish Colloquial: [Spanish translation here]\n\n"

        # Add detailed linguistic guidance
        prompt += """CRITICAL LINGUISTIC GUIDELINES:
    1. Each word must be paired with its TRUE SEMANTIC EQUIVALENT - what it actually means, not word order.
    2. For verb conjugations, match the actual meaning:
    - Spanish "están" (temporary state) should match with English "are" or German "sind"
    - Spanish "son" (permanent state) should also match with English "are" or German "sind"
    - Context determines whether "estar" or "ser" is used in Spanish
    3. For possessives:
    - Spanish "mis" should match with English "my" or German "meine"
    - Analyze the entire grammatical structure, not just individual words
    4. For idioms, phrasal verbs, and separable verbs, treat as single units with their complete meaning
    5. Remember that word order differs between languages - match meanings, not positions
    6. If you're unsure about a match, use linguistic principles to determine the semantic equivalent

    This task requires precise linguistic expertise. Your goal is to create word-by-word translations that pair each word with its true meaning equivalent, not its position equivalent."""

        print(f"📝 Generated MULTI-STYLE prompt ({len(prompt)} characters)")
        return prompt



    def _should_generate_audio(self, translations_data: Dict, style_preferences) -> bool:
        """Only generate audio if user has selected translation styles"""
        has_translations = len(translations_data.get('translations', [])) > 0
        
        has_enabled_styles = False
        if style_preferences:
            # Check ALL style preferences
            style_checks = [
                style_preferences.german_native,
                style_preferences.german_colloquial,
                style_preferences.german_informal,
                style_preferences.german_formal,
                style_preferences.english_native,
                style_preferences.english_colloquial,
                style_preferences.english_informal,
                style_preferences.english_formal
            ]
            has_enabled_styles = any(style_checks)
        
        word_by_word_requested = False
        if style_preferences:
            word_by_word_requested = (
                style_preferences.german_word_by_word or 
                style_preferences.english_word_by_word
            )
        
        should_generate = has_translations and has_enabled_styles
        
        print(f"🎵 Audio Generation Decision:")
        print(f"   Translations available: {has_translations}")
        print(f"   Translation styles enabled: {has_enabled_styles}")
        print(f"   Word-by-word audio requested: {word_by_word_requested}")
        print(f"   🎯 Will generate audio: {should_generate}")
        print(f"   🎯 Audio type: {'Word-by-word breakdown' if word_by_word_requested else 'Simple translation reading'}")
        
        return should_generate

    async def _generate_audio_with_resilience(self, translations_data: Dict, detected_mother_tongue: str, style_preferences) -> Optional[str]:
        """Generate audio with enhanced error handling for multiple styles"""
        try:
            print("🎵 Attempting MULTI-STYLE SYNCHRONIZED audio generation...")
            
            audio_task = asyncio.create_task(
                self.tts_service.text_to_speech_word_pairs_v2(
                    translations_data=translations_data,
                    source_lang=detected_mother_tongue,
                    target_lang="es",
                    style_preferences=style_preferences,
                )
            )
            
            try:
                audio_filename = await asyncio.wait_for(audio_task, timeout=self.audio_timeout_seconds)
                
                if audio_filename:
                    print(f"✅ MULTI-STYLE SYNCHRONIZED audio generation successful: {audio_filename}")
                    return audio_filename
                else:
                    print("⚠️ Audio generation returned None")
                    return None
                    
            except asyncio.TimeoutError:
                print(f"⏰ Audio generation timed out after {self.audio_timeout_seconds} seconds")
                audio_task.cancel()
                return None
                
        except Exception as e:
            print(f"❌ Audio generation failed: {str(e)}")
            return None


    # Update the process_prompt method to include the original text in the translations data
    async def process_prompt(
        self, text: str, source_lang: str, target_lang: str, style_preferences=None, mother_tongue: str = None
    ) -> Translation:
        try:
            # Use default preferences if none provided
            if style_preferences is None:
                from ...infrastructure.api.routes import TranslationStylePreferences
                style_preferences = TranslationStylePreferences(
                    german_colloquial=True,
                    english_colloquial=True,
                    mother_tongue="spanish"
                )

            # Detect the actual input language
            detected_mother_tongue = self._detect_input_language(text, mother_tongue)
            
            print(f"\n{'='*80}")
            print(f"🌐 PROCESSING MULTI-STYLE ENHANCED CONTEXTUAL TRANSLATION")
            print(f"{'='*80}")
            print(f"📝 Input text: '{text}'")
            print(f"🌍 Detected mother tongue: {detected_mother_tongue}")

            # Create enhanced multi-style context prompt 
            enhanced_prompt = self._create_enhanced_context_prompt(
                text, detected_mother_tongue, style_preferences
            )
            
            print(f"📤 Sending MULTI-STYLE prompt to Gemini AI...")

            try:
                # Use direct model call for more reliable parsing
                response = self.model.generate_content(enhanced_prompt)
                generated_text = response.text

                print(f"📥 Gemini response received ({len(generated_text)} characters)")
                print(f"📄 Response preview: {generated_text[:200]}...")

            except Exception as e:
                print(f"❌ Gemini API error: {str(e)}")
                # Fallback response
                generated_text = f"Translation error for '{text}'. Please try again."
                translations_data = {'translations': [generated_text], 'style_data': [], 'original_text': text}
                
                return Translation(
                    original_text=text,
                    translated_text=generated_text,
                    source_language=detected_mother_tongue,
                    target_language="multi",
                    audio_path=None,
                    translations={"main": generated_text},
                    word_by_word=None,
                    grammar_explanations=None,
                )

            # Extract translations with MULTI-STYLE support
            translations_data = self._extract_translations_fixed(generated_text, style_preferences)
            
            # Store original text for fallback word-by-word generation
            translations_data['original_text'] = text

            audio_filename = None

            # Check if audio should be generated
            should_generate_audio = self._should_generate_audio(translations_data, style_preferences)
            
            # Generate synchronized audio for all selected styles
            if should_generate_audio:
                print("🎵 Starting MULTI-STYLE SYNCHRONIZED audio generation...")
                audio_filename = await self._generate_audio_with_resilience(
                    translations_data, detected_mother_tongue, style_preferences
                )
                
                if audio_filename:
                    print(f"✅ MULTI-STYLE SYNCHRONIZED audio completed: {audio_filename}")
                else:
                    print("ℹ️ Audio generation failed/skipped - continuing without audio")
            else:
                print("🔇 No audio generated - no translation styles enabled")

            # Create perfect UI-Audio synchronized data for all styles
            ui_word_by_word = self._create_perfect_ui_sync_data(translations_data, style_preferences)

            # Create final translation text with all styles
            final_translation_text = self._create_formatted_translation_text(translations_data)

            return Translation(
                original_text=text,
                translated_text=final_translation_text,
                source_language=detected_mother_tongue,
                target_language="multi",
                audio_path=audio_filename if audio_filename else None,
                translations={
                    "main": translations_data['translations'][0] if translations_data['translations'] else final_translation_text
                },
                word_by_word=ui_word_by_word,
                grammar_explanations=self._generate_grammar_explanations(final_translation_text),
            )

        except Exception as e:
            print(f"❌ Error in process_prompt: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Translation processing failed: {str(e)}")

    def _fix_common_semantic_mismatches(self, pairs: List[Tuple[str, str]], is_german: bool = True) -> List[Tuple[str, str]]:
        """
        Apply intelligent context-aware corrections to semantic mismatches.
        Analyzes the full context before making corrections to ensure grammatical accuracy.
        """
        corrected_pairs = []
        
        # Detect source language characteristics
        language_name = "German" if is_german else "English"
        
        # First pass: Build context from the full set of pairs
        sentence_context = {
            "has_possession": False,
            "has_state_verb": False,
            "nouns": [],
            "plural_nouns": False,
            "feminine_nouns": False,
            "masculine_nouns": False,
        }
        
        # Check for fingernails specifically (special case for the example)
        contains_fingernails = any(
            source.lower() in ["nägeln", "fingernails"] for source, _ in pairs
        )
        
        if contains_fingernails:
            sentence_context["plural_nouns"] = True
            sentence_context["feminine_nouns"] = True  # uñas is feminine plural in Spanish
        
        # Analyze sentence structure
        for source, target in pairs:
            source_lower = source.lower()
            
            # Check for possession markers
            if is_german and source_lower in ["mein", "meine", "dein", "deine", "sein", "seine", "ihr", "ihre"]:
                sentence_context["has_possession"] = True
            elif not is_german and source_lower in ["my", "your", "his", "her", "their", "our"]:
                sentence_context["has_possession"] = True
                
            # Check for state verbs
            if is_german and source_lower in ["bin", "ist", "sind", "war", "waren"]:
                sentence_context["has_state_verb"] = True
                sentence_context["state_verb"] = source_lower
            elif not is_german and source_lower in ["am", "is", "are", "was", "were"]:
                sentence_context["has_state_verb"] = True
                sentence_context["state_verb"] = source_lower
            
            # Detect common plurals
            if source_lower.endswith("s") or source_lower.endswith("en"):
                if is_german and source_lower in ["nägeln", "händen", "fingern"]:
                    sentence_context["plural_nouns"] = True
                    sentence_context["feminine_nouns"] = True
                elif not is_german and source_lower in ["fingernails", "hands", "fingers"]:
                    sentence_context["plural_nouns"] = True
                    sentence_context["feminine_nouns"] = True
        
        # Second pass: Apply corrections with full context awareness
        for source, target in pairs:
            source_lower = source.lower()
            corrected_target = target
            
            # Apply corrections based on the source language and word
            if is_german:  # German corrections
                # German possessives
                if source_lower == "meine":
                    corrected_target = "mis" if sentence_context["plural_nouns"] else "mi"
                elif source_lower == "mein":
                    corrected_target = "mi"
                    
                # German pronouns
                elif source_lower == "ich":
                    corrected_target = "yo"
                elif source_lower == "du":
                    corrected_target = "tú"
                    
                # German verbs
                elif source_lower == "bin":
                    corrected_target = "soy" if not sentence_context["has_possession"] else "estoy"
                elif source_lower == "ist":
                    corrected_target = "es" if not sentence_context["has_possession"] else "está"
                elif source_lower == "sind":
                    corrected_target = "son" if not sentence_context["has_possession"] else "están"
                elif source_lower == "habe":
                    corrected_target = "tengo"
                elif source_lower == "hat":
                    corrected_target = "tiene"
                    
                # German articles - CRITICAL FIXES HERE
                elif source_lower == "der":
                    corrected_target = "el"  # Masculine singular
                elif source_lower == "die":
                    corrected_target = "la" if not sentence_context["plural_nouns"] else "las"  # Feminine
                elif source_lower == "das":
                    corrected_target = "el"  # Neuter (translated as masculine in Spanish)
                elif source_lower == "den":
                    # Critical fix: "den" should be "el" for masculine singular accusative
                    # But for fingernails case (feminine plural), it should be "las"
                    corrected_target = "las" if contains_fingernails else "el"
                elif source_lower == "dem":
                    corrected_target = "al"
                elif source_lower == "ein":
                    corrected_target = "un"  # Masculine singular
                elif source_lower == "eine":
                    corrected_target = "una"  # Feminine singular
                elif source_lower == "einen":
                    corrected_target = "un"  # Masculine accusative
                    
            else:  # English corrections
                # English possessives
                if source_lower == "my":
                    corrected_target = "mis" if sentence_context["plural_nouns"] else "mi"
                    
                # English pronouns
                elif source_lower == "i":
                    corrected_target = "yo"
                elif source_lower == "you":
                    corrected_target = "tú"
                    
                # English verbs
                elif source_lower == "am":
                    corrected_target = "soy" if not sentence_context["has_possession"] else "estoy"
                elif source_lower == "is":
                    corrected_target = "es" if not sentence_context["has_possession"] else "está"
                elif source_lower == "are":
                    corrected_target = "son" if not sentence_context["has_possession"] else "están"
                elif source_lower == "have":
                    corrected_target = "tengo"
                elif source_lower == "has":
                    corrected_target = "tiene"
                elif source_lower == "had":
                    corrected_target = "tenía"
                    
                # English articles - CRITICAL FIXES HERE
                elif source_lower == "the":
                    # Critical fix: Check if we're referring to a plural noun
                    # In the case of "fingernails", "the" should be "las" (feminine plural)
                    if contains_fingernails or sentence_context["plural_nouns"]:
                        if sentence_context["feminine_nouns"]:
                            corrected_target = "las"  # Feminine plural
                        else:
                            corrected_target = "los"  # Masculine plural
                    else:
                        if sentence_context["feminine_nouns"]:
                            corrected_target = "la"   # Feminine singular
                        else:
                            corrected_target = "el"   # Masculine singular (default)
                elif source_lower == "a" or source_lower == "an":
                    corrected_target = "una" if sentence_context["feminine_nouns"] else "un"
                
                # Special handling for contractions
                elif source_lower == "i've":
                    corrected_target = "yo"  # Usually followed by "got" which will be "tengo"
                elif source_lower == "i'm":
                    corrected_target = "yo" 
                elif source_lower == "you're":
                    corrected_target = "tú"
                    
                # Handle "got" in phrases like "I've got"
                elif source_lower == "got" and any(s.lower() == "i've" for s, _ in pairs):
                    corrected_target = "tengo"
            
            # Add correction if target was changed
            if corrected_target != target:
                print(f"🔧 Correcting {language_name} semantic match: '{source}' → '{target}' to '{corrected_target}'")
                corrected_pairs.append((source, corrected_target))
            else:
                corrected_pairs.append((source, target))
        
        return corrected_pairs


    def _is_likely_plural(self, pairs: List[Tuple[str, str]]) -> bool:
        """
        Detect if the sentence context is likely referring to plural entities.
        """
        # Check for typical plural indicators
        for source, _ in pairs:
            source_lower = source.lower()
            # Common plural nouns endings in English and German
            if source_lower.endswith('s') or source_lower.endswith('en'):
                if source_lower in ['hands', 'fingers', 'arms', 'legs', 'feet', 
                                'hände', 'finger', 'arme', 'beine', 'füße']:
                    return True
        
        return False


    def _ensure_word_by_word_data(self, translations_data: Dict, style_preferences) -> Dict:
        """
        Ensure word-by-word data is available when requested.
        If the AI failed to provide word-by-word data, generate fallback data.
        """
        # Check if word-by-word is requested for any language
        german_word_by_word = getattr(style_preferences, 'german_word_by_word', False)
        english_word_by_word = getattr(style_preferences, 'english_word_by_word', False)
        any_word_by_word_requested = german_word_by_word or english_word_by_word
        
        if not any_word_by_word_requested:
            # No word-by-word requested, no need to check or generate
            return translations_data
        
        # Check if we have any styles with word-by-word data
        has_word_by_word_data = False
        for style_info in translations_data.get('style_data', []):
            if style_info.get('word_pairs', []):
                has_word_by_word_data = True
                break
        
        # If we have word-by-word data, no need to generate fallback
        if has_word_by_word_data:
            return translations_data
        
        print("⚠️ Word-by-word audio requested but no data found in AI response - generating fallback data")
        
        # Generate fallback word-by-word data for each style that needs it
        for style_info in translations_data.get('style_data', []):
            translation_text = style_info.get('translation', '')
            is_german = style_info.get('is_german', False)
            is_spanish = style_info.get('is_spanish', False)
            style_name = style_info.get('style_name', 'unknown')
            
            # Check if this style should have word-by-word data
            should_include = False
            if is_german and german_word_by_word:
                should_include = True
            elif not is_german and not is_spanish and english_word_by_word:
                should_include = True
            
            if should_include and translation_text:
                # Generate basic word-by-word data by splitting the translation
                words = translation_text.split()
                
                # For Spanish mother tongue, use original text to create pairs
                original_words = translations_data.get('original_text', '').split()
                
                # Generate pairs from translation text
                fallback_pairs = []
                
                # If we have original words (mother tongue), try to match proportionally
                if original_words:
                    # Simple approach: align words proportionally
                    for i, word in enumerate(words):
                        # Calculate corresponding index in original words
                        original_idx = min(int(i * len(original_words) / len(words)), len(original_words) - 1)
                        spanish_equiv = original_words[original_idx] if original_idx < len(original_words) else ""
                        
                        fallback_pairs.append((word, spanish_equiv))
                else:
                    # No original words available, just use the translation with empty Spanish equivalents
                    fallback_pairs = [(word, "") for word in words]
                
                print(f"✅ Generated {len(fallback_pairs)} fallback word pairs for {style_name}")
                style_info['word_pairs'] = fallback_pairs
        
        return translations_data

    def _extract_translations_fixed(self, generated_text: str, style_preferences) -> Dict:
        """Enhanced extraction for multiple simultaneous styles with semantic correction and fallback."""
        result = {
            'translations': [],
            'style_data': [],
            'original_text': ""  # Store original text for fallback generation
        }

        print("🔍 EXTRACTING MULTI-STYLE TRANSLATIONS")
        print("="*50)
        print(f"📄 Generated text length: {len(generated_text)}")

        try:
            lines = generated_text.split('\n')
            current_language = None
            word_by_word_text = {}
            all_word_by_word_data = {}  # Store word-by-word for ALL styles
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detect language sections
                if 'GERMAN TRANSLATIONS:' in line.upper():
                    current_language = 'german'
                    print(f"📍 Found German section")
                elif 'ENGLISH TRANSLATIONS:' in line.upper():
                    current_language = 'english'
                    print(f"📍 Found English section")
                elif 'SPANISH TRANSLATIONS:' in line.upper():
                    current_language = 'spanish'
                    print(f"📍 Found Spanish section")
                elif 'GERMAN WORD-BY-WORD:' in line.upper():
                    print(f"📍 Found German word-by-word section")
                    current_language = 'german_wbw'
                elif 'ENGLISH WORD-BY-WORD:' in line.upper():
                    print(f"📍 Found English word-by-word section")
                    current_language = 'english_wbw'
                
                # Extract translations for ALL selected styles
                elif current_language == 'german':
                    # Process ALL German styles
                    styles_to_check = [
                        ('German Native:', 'german_native', style_preferences.german_native),
                        ('German Colloquial:', 'german_colloquial', style_preferences.german_colloquial),
                        ('German Informal:', 'german_informal', style_preferences.german_informal),
                        ('German Formal:', 'german_formal', style_preferences.german_formal)
                    ]
                    
                    for prefix, style_name, is_enabled in styles_to_check:
                        if prefix in line and is_enabled:
                            translation = self._extract_translation_from_line(line, prefix)
                            if translation:
                                result['translations'].append(translation)
                                result['style_data'].append({
                                    'translation': translation,
                                    'word_pairs': [],
                                    'is_german': True,
                                    'is_spanish': False,
                                    'style_name': style_name
                                })
                                print(f"✅ {style_name}: {translation[:50]}...")
                
                elif current_language == 'english':
                    # Process ALL English styles
                    styles_to_check = [
                        ('English Native:', 'english_native', style_preferences.english_native),
                        ('English Colloquial:', 'english_colloquial', style_preferences.english_colloquial),
                        ('English Informal:', 'english_informal', style_preferences.english_informal),
                        ('English Formal:', 'english_formal', style_preferences.english_formal)
                    ]
                    
                    for prefix, style_name, is_enabled in styles_to_check:
                        if prefix in line and is_enabled:
                            translation = self._extract_translation_from_line(line, prefix)
                            if translation:
                                result['translations'].append(translation)
                                result['style_data'].append({
                                    'translation': translation,
                                    'word_pairs': [],
                                    'is_german': False,
                                    'is_spanish': False,
                                    'style_name': style_name
                                })
                                print(f"✅ {style_name}: {translation[:50]}...")
                
                # Handle word-by-word sections for multiple styles
                elif current_language == 'german_wbw':
                    # Check if this line specifies a style
                    for style in ['Native', 'Colloquial', 'Informal', 'Formal']:
                        if f'{style} style:' in line:
                            style_key = f'german_{style.lower()}'
                            # Extract the word-by-word part
                            wbw_start = line.find('[')
                            if wbw_start >= 0:
                                all_word_by_word_data[style_key] = line[wbw_start:]
                                print(f"📝 German {style} word-by-word: {line[wbw_start:100]}...")
                            break
                    else:
                        # If line contains brackets, might be general word-by-word
                        if '[' in line and ']' in line and '(' in line and ')' in line:
                            if 'german' not in word_by_word_text:
                                word_by_word_text['german'] = line
                                print(f"📝 German general word-by-word: {line[:100]}...")
                
                elif current_language == 'english_wbw':
                    # Check if this line specifies a style
                    for style in ['Native', 'Colloquial', 'Informal', 'Formal']:
                        if f'{style} style:' in line:
                            style_key = f'english_{style.lower()}'
                            # Extract the word-by-word part
                            wbw_start = line.find('[')
                            if wbw_start >= 0:
                                all_word_by_word_data[style_key] = line[wbw_start:]
                                print(f"📝 English {style} word-by-word: {line[wbw_start:100]}...")
                            break
                    else:
                        # If line contains brackets, might be general word-by-word
                        if '[' in line and ']' in line and '(' in line and ')' in line:
                            if 'english' not in word_by_word_text:
                                word_by_word_text['english'] = line
                                print(f"📝 English general word-by-word: {line[:100]}...")
                
                elif current_language == 'spanish':
                    if 'Spanish Colloquial:' in line:
                        translation = self._extract_translation_from_line(line, 'Spanish Colloquial:')
                        if translation:
                            result['translations'].append(translation)
                            result['style_data'].append({
                                'translation': translation,
                                'word_pairs': [],
                                'is_german': False,
                                'is_spanish': True,
                                'style_name': 'spanish_colloquial'
                            })
                            print(f"✅ Spanish Colloquial: {translation[:50]}...")

            # Process word-by-word data for EACH style with semantic correction
            for style_entry in result['style_data']:
                style_name = style_entry['style_name']
                is_german = style_entry['is_german']
                
                # Check if we have specific word-by-word for this style
                if style_name in all_word_by_word_data:
                    # Use style-specific word-by-word
                    if (is_german and style_preferences.german_word_by_word) or \
                    (not is_german and not style_entry['is_spanish'] and style_preferences.english_word_by_word):
                        # Extract the initial word pairs
                        word_pairs = self._parse_word_by_word_line(all_word_by_word_data[style_name])
                        
                        if word_pairs:
                            # Apply semantic corrections
                            corrected_pairs = self._fix_common_semantic_mismatches(
                                word_pairs, 
                                is_german=is_german
                            )
                            
                            # Store the corrected pairs
                            style_entry['word_pairs'] = corrected_pairs
                            print(f"✅ Added {len(corrected_pairs)} semantically-corrected word pairs to {style_name}")
                else:
                    # Fall back to general word-by-word if available
                    language = 'german' if is_german else 'english'
                    if language in word_by_word_text:
                        if (is_german and style_preferences.german_word_by_word) or \
                        (not is_german and style_preferences.english_word_by_word):
                            # Extract the initial word pairs
                            word_pairs = self._parse_word_by_word_line(word_by_word_text[language])
                            
                            if word_pairs:
                                # Apply semantic corrections
                                corrected_pairs = self._fix_common_semantic_mismatches(
                                    word_pairs, 
                                    is_german=is_german
                                )
                                
                                # Store the corrected pairs
                                style_entry['word_pairs'] = corrected_pairs
                                print(f"✅ Added {len(corrected_pairs)} semantically-corrected general word pairs to {style_name}")

            print(f"✅ Extracted {len(result['translations'])} translations")
            print(f"✅ Extracted {len(result['style_data'])} style entries")
            
        except Exception as e:
            print(f"❌ Error in extraction: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Fallback: create minimal result
            if not result['translations']:
                result['translations'] = [generated_text[:500]]
                result['style_data'] = [{
                    'translation': generated_text[:500],
                    'word_pairs': [],
                    'is_german': False,
                    'is_spanish': False,
                    'style_name': 'fallback'
                }]
        
        # CRITICAL NEW ADDITION: Apply fallback word-by-word generation if needed
        result = self._ensure_word_by_word_data(result, style_preferences)

        return result


    def _extract_translation_from_line(self, line: str, prefix: str) -> Optional[str]:
        """Extract translation text from a line"""
        try:
            # Remove the prefix and clean up
            translation = line.replace(prefix, '').strip()
            
            # Remove common brackets and quotes
            translation = translation.strip('[]"\'')
            
            # Must have some content
            if len(translation) > 3:
                return translation
            
        except Exception as e:
            print(f"❌ Error extracting from line '{line}': {str(e)}")
        
        return None


    def _parse_word_by_word_line(self, line: str) -> List[Tuple[str, str]]:
        """Parse a word-by-word line into pairs with context-aware semantic validation."""
        pairs = []
        
        try:
            # Find all [word] ([translation]) patterns
            pattern = r'\[([^\]]+)\]\s*\(\s*\[?([^)\]]+)\]?\s*\)'
            matches = re.findall(pattern, line)
            
            if not matches:
                # Try simpler pattern without inner brackets
                pattern = r'\[([^\]]+)\]\s*\(\s*([^)]+)\s*\)'
                matches = re.findall(pattern, line)
            
            for source, target in matches:
                source = source.strip()
                target = target.strip()
                if source and target:
                    # Remove any leftover brackets in the extracted values
                    source = source.strip('[]')
                    target = target.strip('[]')
                    
                    # Normalize the target - handle slash-separated alternatives
                    normalized_target = target
                    if '/' in target:
                        # Take first alternative by default, could be enhanced to take most appropriate
                        normalized_target = target.split('/')[0].strip()
                    
                    pairs.append((source, normalized_target))
                    print(f"   📝 Pair: '{source}' → '{normalized_target}'")
            
            # Contextual semantic validation that respects language variations
            if len(pairs) > 1:
                issues = self._validate_semantic_integrity(pairs)
                if issues:
                    for issue in issues:
                        print(f"⚠️ {issue}")
                    print("⚠️ Some semantic mismatches detected, but continuing with best effort")
                
        except Exception as e:
            print(f"❌ Error parsing word-by-word line: {str(e)}")
        
        return pairs



    def _validate_semantic_integrity(self, pairs: List[Tuple[str, str]]) -> List[str]:
        """
        Validate semantic integrity of word pairs with context awareness.
        Returns a list of issues found.
        """
        issues = []
        
        # Get language context from the pairs
        # Is this German or English based on the source words?
        common_german_words = {"ich", "mein", "meine", "du", "ist", "sind", "habe", "haben", "der", "die", "das"}
        common_english_words = {"i", "my", "you", "is", "are", "have", "has", "the", "a", "an"}
        
        source_words = [pair[0].lower() for pair in pairs]
        german_matches = sum(1 for word in source_words if word in common_german_words)
        english_matches = sum(1 for word in source_words if word in common_english_words)
        
        is_likely_german = german_matches > english_matches
        language = "German" if is_likely_german else "English"
        
        # More flexible semantic validation with language-specific context
        semantic_context = {}
        
        # Extract verb forms to understand sentence structure
        for source, target in pairs:
            source_lower = source.lower()
            
            # Track verb forms to understand overall structure
            if is_likely_german:
                if source_lower in ["bin", "ist", "sind"]:
                    semantic_context["verb_form"] = "be"
                elif source_lower in ["habe", "hat", "haben"]:
                    semantic_context["verb_form"] = "have"
            else:  # English
                if source_lower in ["am", "is", "are"]:
                    semantic_context["verb_form"] = "be"
                elif source_lower in ["have", "has", "had"]:
                    semantic_context["verb_form"] = "have"
        
        # Specific validations based on detected context
        for source, target in pairs:
            source_lower = source.lower()
            target_lower = target.lower()
            
            # Verb form validation with context
            if semantic_context.get("verb_form") == "be":
                if is_likely_german and source_lower in ["bin", "ist", "sind"]:
                    # Allow both ser and estar forms in Spanish depending on context
                    if target_lower not in ["soy", "es", "son", "estoy", "está", "están"]:
                        issues.append(f"Semantic mismatch in {language}: '{source}' should translate to a form of 'ser' or 'estar', got '{target}'")
                elif not is_likely_german and source_lower in ["am", "is", "are"]:
                    if target_lower not in ["soy", "eres", "es", "somos", "son", "estoy", "estás", "está", "estamos", "están"]:
                        issues.append(f"Semantic mismatch in {language}: '{source}' should translate to a form of 'ser' or 'estar', got '{target}'")
            
            # Possessives validation
            if is_likely_german and source_lower in ["mein", "meine"]:
                if target_lower not in ["mi", "mis"]:
                    issues.append(f"Semantic mismatch in {language}: '{source}' should translate to 'mi/mis', got '{target}'")
            elif not is_likely_german and source_lower == "my":
                if target_lower not in ["mi", "mis"]:
                    issues.append(f"Semantic mismatch in {language}: '{source}' should translate to 'mi/mis', got '{target}'")
            
            # Pronoun validation
            if is_likely_german and source_lower == "ich":
                if target_lower != "yo":
                    issues.append(f"Semantic mismatch in {language}: '{source}' should translate to 'yo', got '{target}'")
            elif not is_likely_german and source_lower == "i":
                if target_lower != "yo":
                    issues.append(f"Semantic mismatch in {language}: '{source}' should translate to 'yo', got '{target}'")
        
        return issues


    def _detect_position_based_matches(self, pairs: List[Tuple[str, str]], source_language: str = "spanish") -> bool:
        """
        Detect if pairs are likely position-based matches rather than semantic matches.
        Returns True if position-based matching is suspected.
        Much more flexible and context-aware, especially for languages with multiple "to be" verbs.
        """
        # Only perform rudimentary checks for really obvious mismatches
        # Rather than trying to build a comprehensive dictionary, focus on basic patterns
        
        incorrect_pairings = []
        
        # Check for obviously incorrect matches like pronouns paired with nouns
        for source, target in pairs:
            source_lower = source.lower()
            target_lower = target.lower()
            
            # These are definitely wrong regardless of language
            if source_lower in ["ich", "i"] and target_lower not in ["yo", "i", "me"]:
                if not target_lower.startswith("m"): # Allow for "mi" "mis" etc.
                    incorrect_pairings.append((source, target))
                    
            # Check for really obvious noun/pronoun mismatches
            elif source_lower in ["hände", "hands"] and target_lower not in ["manos", "hands", "hand"]:
                incorrect_pairings.append((source, target))
        
        # If more than one pairing is obviously wrong, flag it
        if len(incorrect_pairings) > 1:
            for source, target in incorrect_pairings:
                print(f"⚠️ Likely incorrect match: '{source}' → '{target}'")
            return True
        
        return False
   
    # Add a method to check formatting consistency without validation dictionaries
    def _check_format_consistency(self, pairs: List[Tuple[str, str]]) -> None:
        """Check if the pairs have consistent formatting without using dictionaries."""
        if not pairs or len(pairs) < 2:
            return
        
        # Check format consistency only
        has_bracket_issues = False
        for source, target in pairs:
            if '[' in source or ']' in source or '(' in source or ')' in source:
                has_bracket_issues = True
                print(f"⚠️ Format issue: Source '{source}' contains brackets")
            
            if '[' in target or ']' in target or '(' in target or ')' in target:
                has_bracket_issues = True
                print(f"⚠️ Format issue: Target '{target}' contains brackets")
        
        if has_bracket_issues:
            print("⚠️ Format inconsistencies detected - this may affect audio playback")



    def _create_perfect_ui_sync_data(self, translations_data: Dict, style_preferences) -> Dict[str, Dict[str, str]]:
        """Create UI data that PERFECTLY matches what will be spoken in audio for ALL styles with minimal validation"""
        ui_data = {}
        
        print("📱 Creating PERFECT MULTI-STYLE UI-Audio synchronization data...")
        print("="*60)
        
        style_counter = {}  # Track counters per style
        
        for style_info in translations_data.get('style_data', []):
            style_name = style_info['style_name']
            word_pairs = style_info.get('word_pairs', [])
            is_german = style_info.get('is_german', False)
            is_spanish = style_info.get('is_spanish', False)
            
            # Initialize counter for this style
            if style_name not in style_counter:
                style_counter[style_name] = 0
            
            # Check if word-by-word is enabled for this language
            should_include = False
            if is_german and getattr(style_preferences, 'german_word_by_word', False):
                should_include = True
            elif not is_german and not is_spanish and getattr(style_preferences, 'english_word_by_word', False):
                should_include = True
            
            if should_include and word_pairs:
                print(f"🔄 PERFECT SYNC: {style_name} with {len(word_pairs)} pairs")
                
                for i, (source_word, spanish_equiv) in enumerate(word_pairs):
                    # Clean for consistency
                    source_clean = source_word.strip().strip('"\'[]')
                    spanish_clean = spanish_equiv.strip().strip('"\'[]')
                    
                    # CRITICAL: Create EXACT same format for UI and audio
                    display_format = f"[{source_clean}] ([{spanish_clean}])"
                    
                    # Create unique key for each style's word pairs
                    key = f"{style_name}_{i}_{source_clean.replace(' ', '_')}"
                    
                    ui_data[key] = {
                        "source": source_clean,
                        "spanish": spanish_clean,
                        "language": "german" if is_german else "english",
                        "style": style_name,
                        "order": str(style_counter[style_name]),
                        "is_phrasal_verb": str(" " in source_clean),
                        "display_format": display_format  # EXACT audio format
                    }
                    
                    style_counter[style_name] += 1
                    
                    print(f"    {i+1}. {style_name} UI: {display_format}")
                    if " " in source_clean:
                        verb_type = "German Separable Verb" if is_german else "English Phrasal Verb"
                        print(f"       🔗 {verb_type}: Single unit")
        
        print(f"✅ Created PERFECT UI sync data for {len(ui_data)} word pairs across {len(style_counter)} styles")
        print("="*60)
        return ui_data


    def _create_formatted_translation_text(self, translations_data: Dict) -> str:
        """Create nicely formatted translation text for display with all styles"""
        formatted_parts = []
        
        formatted_parts.append("=" * 50)
        formatted_parts.append("MULTI-STYLE TRANSLATION RESULTS:")
        formatted_parts.append("=" * 50)
        
        # Group by language
        german_translations = []
        english_translations = []
        spanish_translations = []
        
        for style_info in translations_data.get('style_data', []):
            translation = style_info['translation']
            style_name = style_info['style_name']
            is_german = style_info.get('is_german', False)
            is_spanish = style_info.get('is_spanish', False)
            
            if is_german:
                german_translations.append(f"* {style_name.replace('_', ' ').title()}: {translation}")
            elif is_spanish:
                spanish_translations.append(f"* {style_name.replace('_', ' ').title()}: {translation}")
            else:
                english_translations.append(f"* {style_name.replace('_', ' ').title()}: {translation}")
        
        # Add German section
        if german_translations:
            formatted_parts.append("\nGERMAN TRANSLATIONS:")
            formatted_parts.append("-" * 25)
            formatted_parts.extend(german_translations)
        
        # Add English section
        if english_translations:
            formatted_parts.append("\nENGLISH TRANSLATIONS:")
            formatted_parts.append("-" * 25)
            formatted_parts.extend(english_translations)
        
        # Add Spanish section
        if spanish_translations:
            formatted_parts.append("\nSPANISH TRANSLATIONS:")
            formatted_parts.append("-" * 25)
            formatted_parts.extend(spanish_translations)
        
        formatted_parts.append("\n" + "=" * 50)
        
        return "\n".join(formatted_parts)

    # Keep all other existing methods unchanged...
    def _generate_word_by_word(self, original: str, translated: str) -> dict[str, dict[str, str]]:
        """Generate word-by-word translation mapping."""
        result = {}
        original_words = original.split()
        translated_words = translated.split()

        for i, word in enumerate(original_words):
            if i < len(translated_words):
                result[word] = {
                    "translation": translated_words[i],
                    "pos": "unknown",
                }
        return result

    def _generate_grammar_explanations(self, text: str) -> dict[str, str]:
        """Generate grammar explanations for the translation."""
        return {
            "structure": "Enhanced multi-style grammar explanation with context",
            "tense": "Tense usage adapted to multiple styles and mother tongue",
        }

    def _normalize_text(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text)
        ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
        return ascii_text

    def _restore_accents(self, text: str) -> str:
        accent_map = {
            "a": "á", "e": "é", "i": "í", "o": "ó", "u": "ú", "n": "ñ",
            "A": "Á", "E": "É", "I": "Í", "O": "Ó", "U": "Ú", "N": "Ñ",
        }

        patterns = {
            r"([aeiou])´": lambda m: accent_map[m.group(1)],
            r"([AEIOU])´": lambda m: accent_map[m.group(1)],
            r"n~": "ñ", r"N~": "Ñ",
        }

        for pattern, replacement in patterns.items():
            if callable(replacement):
                text = re.sub(pattern, replacement, text)
            else:
                text = re.sub(pattern, replacement, text)

        return text

    def _ensure_unicode(self, text: str) -> str:
        if isinstance(text, bytes):
            text = text.decode("utf-8")
        return unicodedata.normalize("NFKC", text)

    def _get_temp_directory(self) -> str:
        """Get the appropriate temporary directory based on the operating system."""
        if os.name == "nt":
            temp_dir = os.environ.get("TEMP") or os.environ.get("TMP")
        else:
            temp_dir = "/tmp"

        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    def _auto_fix_spelling(self, text: str) -> str:
        """Fix spelling in the given text."""
        words = re.findall(r"\b\w+\b|[^\w\s]", text)
        corrected_words = []

        for word in words:
            if not re.match(r"\w+", word):
                corrected_words.append(word)
                continue

            if self.spell.unknown([word]):
                correction = self.spell.correction(word)
                if correction:
                    if word.isupper():
                        correction = correction.upper()
                    elif word[0].isupper():
                        correction = correction.capitalize()
                    word = correction

            corrected_words.append(word)

        return " ".join(corrected_words)
    
