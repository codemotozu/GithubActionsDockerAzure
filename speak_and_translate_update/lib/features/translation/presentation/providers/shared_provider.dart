// lib/features/translation/presentation/providers/shared_providers.dart
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
  'microphoneMode': 'continuousListening', // 'voiceCommand' or 'continuousListening'
  'motherTongue': 'spanish',
  'appMode': 'languageLearning',
  
  // Existing word-by-word settings (keep for backward compatibility)
  'germanWordByWord': true,
  'englishWordByWord': false,
  
  // Translation style preferences
  'germanNative': false,
  'germanColloquial': true,
  'germanInformal': false,
  'germanFormal': false,
  'englishNative': false,
  'englishColloquial': true,
  'englishInformal': false,
  'englishFormal': false,
});

// Settings initialization provider - loads Hive settings into the main provider
final settingsInitializationProvider = FutureProvider<void>((ref) async {
  try {
    final repository = UserSettingsRepository();
    final hiveSettings = await repository.getUserSettings();
    
    // Update the main settings provider with Hive data
    ref.read(settingsProvider.notifier).state = hiveSettings;
    
    print("✅ Settings loaded from Hive and applied to provider");
  } catch (e) {
    print("❌ Error loading settings from Hive: $e");
    // Keep default settings if Hive loading fails
  }
});

// Existing voice providers (keep unchanged)
final isListeningProvider = StateProvider<bool>((ref) => false);
final isContinuousListeningActiveProvider = StateProvider<bool>((ref) => false);
