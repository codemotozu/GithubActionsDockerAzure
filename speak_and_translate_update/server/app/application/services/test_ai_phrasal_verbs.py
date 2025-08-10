# # test_ai_phrasal_verbs.py
# # Test script for AI-powered phrasal verb detection and translation

# import re
# from typing import List, Tuple

# class AIPhrasalVerbTester:
#     """
#     Test the AI-based phrasal verb detection system.
#     This demonstrates detection without hardcoded dictionaries.
#     """
    
#     def __init__(self):
#         # Phrasal verb particles for detection (not translation)
#         self.particles = [
#             "up", "down", "in", "out", "on", "off", "away", "back",
#             "over", "through", "along", "around", "forward", "after", "into"
#         ]
        
#         # German separable prefixes for detection
#         self.german_prefixes = [
#             'auf', 'aus', 'an', 'ab', 'bei', 'ein', 'mit', 'nach',
#             'vor', 'zu', 'zurück', 'weg', 'weiter', 'fort'
#         ]
        
#         # Test sentences with expected phrasal verbs
#         self.test_cases = [
#             # Common phrasal verbs
#             ("I woke up early this morning", ["woke up"]),
#             ("She needs to look up the information", ["look up"]),
#             ("They came up with a great idea", ["came up with"]),
#             ("Please turn off the lights", ["turn off"]),
#             ("He stood up and walked away", ["stood up"]),
            
#             # Less common phrasal verbs (AI will handle these too!)
#             ("She brushed up on her Spanish", ["brushed up on"]),
#             ("He chickened out of the deal", ["chickened out of"]),
#             ("They hammered out an agreement", ["hammered out"]),
#             ("I bumped into my teacher", ["bumped into"]),
#             ("Let's touch base on Monday", ["touch base on"]),
            
#             # German separable verbs
#             ("Ich stehe früh auf", ["stehe auf"]),
#             ("Er ruft mich morgen an", ["ruft an"]),
#             ("Wir gehen heute aus", ["gehen aus"]),
#             ("Sie macht die Tür zu", ["macht zu"]),
#         ]

#     def detect_phrasal_verbs(self, text: str) -> List[str]:
#         """
#         Detect phrasal verbs using pattern matching (no dictionary needed).
#         """
#         found_phrases = []
#         words = text.lower().split()
        
#         i = 0
#         while i < len(words):
#             # Check for 3-word phrasal verbs (verb + particle + preposition)
#             if i + 2 < len(words):
#                 word2 = words[i + 1].rstrip('.,!?;:')
#                 word3 = words[i + 2].rstrip('.,!?;:')
                
#                 # Pattern: verb + particle + preposition
#                 if word2 in self.particles and word3 in ["with", "to", "for", "at", "on", "of"]:
#                     phrase = f"{words[i]} {word2} {word3}"
#                     found_phrases.append(phrase)
#                     i += 3
#                     continue
            
#             # Check for 2-word phrasal verbs (verb + particle)
#             if i + 1 < len(words):
#                 word2 = words[i + 1].rstrip('.,!?;:')
#                 if word2 in self.particles:
#                     phrase = f"{words[i]} {word2}"
#                     found_phrases.append(phrase)
#                     i += 2
#                     continue
            
#             i += 1
        
#         return found_phrases

#     def detect_german_separable(self, text: str) -> List[str]:
#         """
#         Detect German separable verbs in separated form.
#         """
#         found_verbs = []
#         words = text.lower().split()
        
#         for i in range(len(words)):
#             # Look for verb...prefix pattern within 5 words
#             for j in range(i + 1, min(i + 6, len(words))):
#                 prefix = words[j].rstrip('.,!?;:')
#                 if prefix in self.german_prefixes:
#                     verb_phrase = f"{words[i]} {prefix}"
#                     found_verbs.append(verb_phrase)
#                     break
        
#         return found_verbs

#     def simulate_ai_translation(self, phrase: str, is_german: bool = False) -> str:
#         """
#         Simulate what the AI translation would return.
#         In production, this would call Gemini AI.
#         """
#         # This simulates the AI call
#         print(f"      📤 AI Query: Translate '{phrase}' to Spanish")
        
#         # In real implementation, this would be:
#         # response = gemini_model.generate_content(f"Translate '{phrase}' to Spanish")
        
#         # Simulated AI responses (in production, these come from Gemini)
#         simulated_responses = {
#             "woke up": "se despertó",
#             "look up": "buscar",
#             "came up with": "inventó",
#             "turn off": "apagar",
#             "stood up": "se levantó",
#             "brushed up on": "repasó",
#             "chickened out of": "se acobardó de",
#             "hammered out": "negoció",
#             "bumped into": "se encontró con",
#             "touch base on": "ponerse en contacto el",
#             "stehe auf": "me levanto",
#             "ruft an": "llama",
#             "gehen aus": "salimos",
#             "macht zu": "cierra",
#         }
        
#         translation = simulated_responses.get(phrase, f"[AI would translate: {phrase}]")
#         print(f"      📥 AI Response: '{translation}'")
#         return translation

#     def test_ai_based_system(self):
#         """
#         Test the AI-based phrasal verb system.
#         """
#         print("\n" + "="*70)
#         print("🤖 AI-POWERED PHRASAL VERB DETECTION AND TRANSLATION")
#         print("="*70)
#         print("\nThis system uses AI for ALL translations - no dictionaries needed!")
#         print("="*70)
        
#         for sentence, expected in self.test_cases:
#             is_german = any(word in sentence.lower() for word in ["ich", "er", "sie", "wir"])
            
#             # Detect phrases
#             if is_german:
#                 found = self.detect_german_separable(sentence)
#             else:
#                 found = self.detect_phrasal_verbs(sentence)
            
#             # Display results
#             print(f"\n📝 Sentence: '{sentence}'")
#             print(f"   Expected: {expected}")
#             print(f"   Detected: {found}")
            
#             # Simulate AI translation for each detected phrase
#             if found:
#                 print("   🔄 AI Translations:")
#                 for phrase in found:
#                     translation = self.simulate_ai_translation(phrase, is_german)
#                     print(f"      ✅ '{phrase}' -> '{translation}'")
            
#             # Check if detection matches expectation
#             status = "✅ PASS" if set(found) == set(expected) else "⚠️  PARTIAL"
#             print(f"   Status: {status}")

#     def demonstrate_advantages(self):
#         """
#         Show advantages of AI-based approach.
#         """
#         print("\n" + "="*70)
#         print("💡 ADVANTAGES OF AI-BASED APPROACH")
#         print("="*70)
        
#         advantages = [
#             ("No Dictionary Maintenance", 
#              "AI translates ANY phrasal verb, even new or uncommon ones"),
            
#             ("Handles All Tenses", 
#              "wake up, wakes up, woke up, waking up - all handled automatically"),
            
#             ("Context Awareness", 
#              "AI understands context for better translations"),
            
#             ("Language Flexibility", 
#              "Easily extends to any language pair"),
            
#             ("Infinite Coverage", 
#              "Works with slang, idioms, and regional expressions"),
#         ]
        
#         for title, description in advantages:
#             print(f"\n✅ {title}")
#             print(f"   {description}")
        
#         print("\n" + "="*70)
#         print("🎯 EXAMPLES OF AI HANDLING UNCOMMON PHRASES:")
#         print("="*70)
        
#         uncommon_phrases = [
#             "zonked out" ,       # fell asleep suddenly
#             "sussed out",        # figured out
#             "kipped down",       # went to sleep
#             "scarpered off",     # ran away quickly
#             "beavered away at",  # worked hard on
#         ]
        
#         print("\nThese would all be translated correctly by AI without")
#         print("needing to add them to any dictionary:")
        
#         for phrase in uncommon_phrases:
#             print(f"  • '{phrase}' → AI provides correct Spanish translation")

#     def run_all_tests(self):
#         """
#         Run complete test suite.
#         """
#         print("\n" + "🚀"*35)
#         print(" AI-POWERED PHRASAL VERB HANDLING TEST SUITE")
#         print("🚀"*35)
        
#         self.test_ai_based_system()
#         self.demonstrate_advantages()
        
#         print("\n" + "="*70)
#         print("📊 TEST SUMMARY")
#         print("="*70)
#         print("✅ Phrasal verb detection: Pattern-based (no dictionary)")
#         print("✅ Translation: AI-powered (Gemini)")
#         print("✅ Coverage: Unlimited (any phrase works)")
#         print("✅ Maintenance: Zero (no dictionaries to update)")
#         print("\n🎯 Ready for integration with your translation service!")
#         print("="*70)

# if __name__ == "__main__":
#     tester = AIPhrasalVerbTester()
#     tester.run_all_tests()



# api_config.py - Configuration helper for managing API limits and fallback options

import os
from enum import Enum
from typing import Optional
import json
from datetime import datetime, timedelta

class APITier(Enum):
    """API tier levels with their respective limits"""
    FREE = "free"
    PAY_AS_YOU_GO = "pay_as_you_go"
    CUSTOM = "custom"

class APIConfig:
    """
    Configuration manager for API rate limits and fallback strategies
    """
    
    # Default rate limits for different tiers
    TIER_LIMITS = {
        APITier.FREE: {
            "requests_per_minute": 15,
            "requests_per_day": 1500,
            "input_tokens_per_minute": 32000,
            "input_tokens_per_day": 1500000,
            "output_tokens_per_minute": 2000,
            "output_tokens_per_day": 50000,
            "model": "gemini-1.5-flash"  # Use flash for free tier
        },
        APITier.PAY_AS_YOU_GO: {
            "requests_per_minute": 360,
            "requests_per_day": 30000,
            "input_tokens_per_minute": 4000000,
            "input_tokens_per_day": 100000000,
            "output_tokens_per_minute": 100000,
            "output_tokens_per_day": 10000000,
            "model": "gemini-1.5-pro-latest"
        },
        APITier.CUSTOM: {
            # Will be loaded from environment or config file
            "requests_per_minute": 100,
            "requests_per_day": 10000,
            "input_tokens_per_minute": 100000,
            "input_tokens_per_day": 10000000,
            "output_tokens_per_minute": 10000,
            "output_tokens_per_day": 1000000,
            "model": "gemini-1.5-pro-latest"
        }
    }
    
    def __init__(self, tier: APITier = APITier.FREE, config_file: Optional[str] = None):
        """
        Initialize API configuration
        
        Args:
            tier: API tier level
            config_file: Optional path to JSON config file
        """
        self.tier = tier
        self.config_file = config_file or "api_config.json"
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize usage tracking
        self.usage_tracker = UsageTracker(self.config_file)
        
        # Fallback options
        self.enable_caching = True
        self.enable_fallback_translations = True
        self.enable_batch_processing = True
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
    def _load_config(self) -> dict:
        """Load configuration from file or environment"""
        # Try to load from file first
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    custom_config = json.load(f)
                    if 'tier_limits' in custom_config:
                        return custom_config['tier_limits']
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
        
        # Check environment variables for tier override
        env_tier = os.getenv("GEMINI_API_TIER", "").upper()
        if env_tier == "PAID":
            self.tier = APITier.PAY_AS_YOU_GO
        elif env_tier == "CUSTOM":
            self.tier = APITier.CUSTOM
            # Load custom limits from environment
            return {
                "requests_per_minute": int(os.getenv("GEMINI_RPM", 100)),
                "requests_per_day": int(os.getenv("GEMINI_RPD", 10000)),
                "input_tokens_per_minute": int(os.getenv("GEMINI_INPUT_TPM", 100000)),
                "input_tokens_per_day": int(os.getenv("GEMINI_INPUT_TPD", 10000000)),
                "output_tokens_per_minute": int(os.getenv("GEMINI_OUTPUT_TPM", 10000)),
                "output_tokens_per_day": int(os.getenv("GEMINI_OUTPUT_TPD", 1000000)),
                "model": os.getenv("GEMINI_MODEL", "gemini-1.5-pro-latest")
            }
        
        # Return default limits for the tier
        return self.TIER_LIMITS[self.tier]
    
    def save_config(self):
        """Save current configuration to file"""
        config_data = {
            "tier": self.tier.value,
            "tier_limits": self.config,
            "options": {
                "enable_caching": self.enable_caching,
                "enable_fallback_translations": self.enable_fallback_translations,
                "enable_batch_processing": self.enable_batch_processing,
                "max_retries": self.max_retries,
                "retry_delay": self.retry_delay
            },
            "last_updated": datetime.now().isoformat()
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            print(f"Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def get_model_name(self) -> str:
        """Get the appropriate model name based on tier"""
        return self.config.get("model", "gemini-1.5-flash")
    
    def get_rate_limits(self) -> dict:
        """Get current rate limits"""
        return {
            "rpm": self.config["requests_per_minute"],
            "rpd": self.config["requests_per_day"],
            "input_tpm": self.config["input_tokens_per_minute"],
            "input_tpd": self.config["input_tokens_per_day"],
            "output_tpm": self.config["output_tokens_per_minute"],
            "output_tpd": self.config["output_tokens_per_day"]
        }
    
    def should_use_fallback(self) -> bool:
        """Determine if fallback translations should be used"""
        return self.enable_fallback_translations and self.usage_tracker.is_near_limit()

class UsageTracker:
    """Track API usage to prevent hitting limits"""
    
    def __init__(self, storage_file: str = "api_usage.json"):
        self.storage_file = storage_file
        self.usage_data = self._load_usage()
    
    def _load_usage(self) -> dict:
        """Load usage data from file"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "requests_today": 0,
            "requests_this_minute": 0,
            "tokens_today": 0,
            "tokens_this_minute": 0,
            "last_request": None,
            "date": datetime.now().date().isoformat()
        }
    
    def track_request(self, input_tokens: int = 0, output_tokens: int = 0):
        """Track a new API request"""
        now = datetime.now()
        
        # Reset daily counter if new day
        if self.usage_data["date"] != now.date().isoformat():
            self.usage_data["requests_today"] = 0
            self.usage_data["tokens_today"] = 0
            self.usage_data["date"] = now.date().isoformat()
        
        # Reset minute counter if new minute
        if self.usage_data["last_request"]:
            last_request = datetime.fromisoformat(self.usage_data["last_request"])
            if (now - last_request).seconds >= 60:
                self.usage_data["requests_this_minute"] = 0
                self.usage_data["tokens_this_minute"] = 0
        
        # Update counters
        self.usage_data["requests_today"] += 1
        self.usage_data["requests_this_minute"] += 1
        self.usage_data["tokens_today"] += input_tokens + output_tokens
        self.usage_data["tokens_this_minute"] += input_tokens + output_tokens
        self.usage_data["last_request"] = now.isoformat()
        
        self._save_usage()
    
    def _save_usage(self):
        """Save usage data to file"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save usage data: {e}")
    
    def is_near_limit(self, threshold: float = 0.8) -> bool:
        """Check if usage is near limits (80% by default)"""
        # This would check against configured limits
        # Simplified for demonstration
        return self.usage_data["requests_today"] > 1200  # 80% of 1500

    def get_usage_summary(self) -> dict:
        """Get current usage summary"""
        return {
            "requests_today": self.usage_data["requests_today"],
            "requests_this_minute": self.usage_data["requests_this_minute"],
            "tokens_today": self.usage_data["tokens_today"],
            "tokens_this_minute": self.usage_data["tokens_this_minute"],
            "last_request": self.usage_data["last_request"]
        }

# Fallback translation dictionary for common phrases
FALLBACK_TRANSLATIONS = {
    # English to Spanish - Common phrases
    "hello": "hola",
    "goodbye": "adiós",
    "thank you": "gracias",
    "please": "por favor",
    "yes": "sí",
    "no": "no",
    "i am": "yo soy",
    "you are": "tú eres",
    "wake up": "despertar",
    "get up": "levantarse",
    "sit down": "sentarse",
    "stand up": "levantarse",
    "turn on": "encender",
    "turn off": "apagar",
    "look for": "buscar",
    "wait for": "esperar",
    "think about": "pensar en",
    "talk about": "hablar de",
    "listen to": "escuchar",
    "come back": "volver",
    "go away": "irse",
    "put on": "ponerse",
    "take off": "quitarse",
    
    # German to Spanish - Common phrases
    "guten tag": "buenos días",
    "auf wiedersehen": "adiós",
    "danke": "gracias",
    "bitte": "por favor",
    "ja": "sí",
    "nein": "no",
    "ich bin": "yo soy",
    "du bist": "tú eres",
    "aufstehen": "levantarse",
    "anziehen": "vestirse",
    "ausziehen": "desvestirse",
    "aufmachen": "abrir",
    "zumachen": "cerrar",
    "weggehen": "irse",
    "zurückkommen": "volver",
    
    # Common words
    "the": "el/la",
    "a": "un/una",
    "and": "y",
    "or": "o",
    "but": "pero",
    "with": "con",
    "without": "sin",
    "for": "para",
    "from": "de",
    "to": "a",
    "in": "en",
    "on": "en",
    "at": "en",
    "by": "por",
    "about": "sobre",
    "through": "a través de",
    "during": "durante",
    "before": "antes",
    "after": "después",
    "above": "encima",
    "below": "debajo",
}

def get_fallback_translation(phrase: str, source_lang: str = "en") -> str:
    """
    Get a fallback translation when API is unavailable
    
    Args:
        phrase: The phrase to translate
        source_lang: Source language code ("en", "de", "es")
    
    Returns:
        Translated phrase or original with brackets if not found
    """
    phrase_lower = phrase.lower().strip()
    
    # Check if we have a direct translation
    if phrase_lower in FALLBACK_TRANSLATIONS:
        return FALLBACK_TRANSLATIONS[phrase_lower]
    
    # Try to translate word by word
    words = phrase_lower.split()
    translated_words = []
    
    for word in words:
        if word in FALLBACK_TRANSLATIONS:
            translated_words.append(FALLBACK_TRANSLATIONS[word])
        else:
            translated_words.append(f"[{word}]")
    
    return " ".join(translated_words)

def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a text
    Rough estimation: ~4 characters per token
    """
    return len(text) // 4

# Usage example
if __name__ == "__main__":
    # Initialize configuration
    config = APIConfig(tier=APITier.FREE)
    
    print("Current API Configuration:")
    print(f"Tier: {config.tier.value}")
    print(f"Model: {config.get_model_name()}")
    print(f"Rate Limits: {config.get_rate_limits()}")
    
    # Track a request
    config.usage_tracker.track_request(input_tokens=100, output_tokens=50)
    
    print(f"\nUsage Summary: {config.usage_tracker.get_usage_summary()}")
    
    # Check if we should use fallback
    if config.should_use_fallback():
        print("\nWarning: Approaching rate limits, using fallback translations")
        
        # Example fallback translation
        test_phrase = "wake up"
        fallback = get_fallback_translation(test_phrase)
        print(f"Fallback translation for '{test_phrase}': {fallback}")
    
    # Save configuration
    config.save_config()