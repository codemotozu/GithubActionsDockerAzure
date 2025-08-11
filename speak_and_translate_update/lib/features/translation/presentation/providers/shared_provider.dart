// lib/features/translation/presentation/providers/shared_provider.dart - FIXED
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:speak_and_translate_update/features/translation/data/repositories/hive_user_settings_repository.dart';

// Hive user settings provider - loads settings from Hive database
final hiveUserSettingsProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final repository = UserSettingsRepository();
  final settings = await repository.getUserSettings();
  return settings;
});

// Settings state provider - shared across the entire app
final settingsProvider = StateProvider<Map<String, dynamic>>((ref) => {
  // Default settings (will be overridden by Hive data when available)
  'microphoneMode': 'continuousListening', // Always continuous listening now
  'motherTongue': 'spanish',  // CRITICAL: Default mother tongue
  'appMode': 'languageLearning',
  
  // NEW: Fluency practice settings with defaults
  'practiceLanguage': 'english',
  'correctionLevel': 'intermediate',
  'pronunciationFeedback': true,
  'grammarCorrection': true,
  'vocabularyEnhancement': true,
  'realTimeCorrection': false,
  
  // FIXED: Word-by-word settings with proper defaults for Spanish speakers
  'germanWordByWord': true,   // CHANGED: Default to true for Spanish speakers
  'englishWordByWord': false, // English word-by-word off by default
  
  // Translation style preferences - Smart defaults for Spanish speakers
  'germanNative': false,
  'germanColloquial': true,   // CHANGED: Default to true for Spanish speakers
  'germanInformal': false,
  'germanFormal': false,
  'englishNative': false,
  'englishColloquial': true,  // CHANGED: Default to true for Spanish speakers
  'englishInformal': false,
  'englishFormal': false,
});

// Settings initialization provider - loads Hive settings into the main provider
final settingsInitializationProvider = FutureProvider<void>((ref) async {
  try {
    final repository = UserSettingsRepository();
    final hiveSettings = await repository.getUserSettings();
    
    // CRITICAL FIX: Ensure word-by-word settings are properly loaded
    print("🔍 LOADING SETTINGS FROM HIVE:");
    print("   Raw germanWordByWord: ${hiveSettings['germanWordByWord']} (${hiveSettings['germanWordByWord'].runtimeType})");
    print("   Raw englishWordByWord: ${hiveSettings['englishWordByWord']} (${hiveSettings['englishWordByWord'].runtimeType})");
    
    // Validate and convert boolean values properly
    final processedSettings = Map<String, dynamic>.from(hiveSettings);
    
    // Ensure boolean conversion for word-by-word settings
    processedSettings['germanWordByWord'] = _ensureBoolean(hiveSettings['germanWordByWord'], true);  // Default true for Spanish speakers
    processedSettings['englishWordByWord'] = _ensureBoolean(hiveSettings['englishWordByWord'], false);
    
    // Ensure boolean conversion for style settings
    processedSettings['germanNative'] = _ensureBoolean(hiveSettings['germanNative'], false);
    processedSettings['germanColloquial'] = _ensureBoolean(hiveSettings['germanColloquial'], true);  // Default true
    processedSettings['germanInformal'] = _ensureBoolean(hiveSettings['germanInformal'], false);
    processedSettings['germanFormal'] = _ensureBoolean(hiveSettings['germanFormal'], false);
    processedSettings['englishNative'] = _ensureBoolean(hiveSettings['englishNative'], false);
    processedSettings['englishColloquial'] = _ensureBoolean(hiveSettings['englishColloquial'], true);  // Default true
    processedSettings['englishInformal'] = _ensureBoolean(hiveSettings['englishInformal'], false);
    processedSettings['englishFormal'] = _ensureBoolean(hiveSettings['englishFormal'], false);
    
    print("🔧 PROCESSED SETTINGS:");
    print("   Processed germanWordByWord: ${processedSettings['germanWordByWord']} (${processedSettings['germanWordByWord'].runtimeType})");
    print("   Processed englishWordByWord: ${processedSettings['englishWordByWord']} (${processedSettings['englishWordByWord'].runtimeType})");
    
    // Update the main settings provider with processed data
    ref.read(settingsProvider.notifier).state = processedSettings;
    
    print("✅ Settings loaded from Hive and applied to provider with proper boolean conversion");
  } catch (e) {
    print("❌ Error loading settings from Hive: $e");
    // Keep default settings if Hive loading fails
  }
});

// Helper function to ensure proper boolean conversion
bool _ensureBoolean(dynamic value, bool defaultValue) {
  if (value == null) return defaultValue;
  if (value is bool) return value;
  if (value is String) {
    return value.toLowerCase() == 'true';
  }
  if (value is int) {
    return value != 0;
  }
  return defaultValue;
}

// Existing voice providers (keep unchanged)
final isListeningProvider = StateProvider<bool>((ref) => false);
final isContinuousListeningActiveProvider = StateProvider<bool>((ref) => false);