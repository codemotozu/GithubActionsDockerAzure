// hive_user_settings_repository.dart - FIXED with proper word-by-word defaults

import 'package:hive/hive.dart';

class UserSettingsRepository {
  final Box _settingsBox = Hive.box('settings');

  // Retrieve the user settings from Hive.
  Future<Map<String, dynamic>> getUserSettings() async {
    try {
      final storedSettings = _settingsBox.get('userSettings');
      if (storedSettings != null && storedSettings is Map) {
        final settings = Map<String, dynamic>.from(storedSettings);
        
        // CRITICAL FIX: Ensure proper defaults and boolean conversion
        print("🔍 RAW HIVE DATA:");
        print("   Raw germanWordByWord: ${settings['germanWordByWord']} (${settings['germanWordByWord'].runtimeType})");
        print("   Raw englishWordByWord: ${settings['englishWordByWord']} (${settings['englishWordByWord'].runtimeType})");
        
        // Apply proper defaults and ensure boolean types
        final processedSettings = _applyDefaultsAndValidate(settings);
        
        print("🔧 PROCESSED HIVE DATA:");
        print("   Processed germanWordByWord: ${processedSettings['germanWordByWord']} (${processedSettings['germanWordByWord'].runtimeType})");
        print("   Processed englishWordByWord: ${processedSettings['englishWordByWord']} (${processedSettings['englishWordByWord'].runtimeType})");
        
        return processedSettings;
      }
    } catch (e) {
      // Log the error; continue with default settings.
      print("Error retrieving user settings: $e");
    }
    
    // Return default settings if no data exists.
    print("📦 RETURNING DEFAULT SETTINGS");
    return _getDefaultSettings();
  }

  Map<String, dynamic> _getDefaultSettings() {
    final defaults = {
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
      
      // FIXED: Word-by-word audio settings with intelligent defaults
      'germanWordByWord': true,   // CRITICAL: Default to true for Spanish speakers learning German
      'englishWordByWord': false, // Default to false for English
      
      // FIXED: Translation style preferences with intelligent defaults for Spanish speakers
      'germanNative': false,
      'germanColloquial': true,   // CRITICAL: Default to true for Spanish speakers
      'germanInformal': false,
      'germanFormal': false,
      'englishNative': false,
      'englishColloquial': true,  // CRITICAL: Default to true for Spanish speakers  
      'englishInformal': false,
      'englishFormal': false,
    };
    
    print("✅ DEFAULT SETTINGS:");
    print("   germanWordByWord: ${defaults['germanWordByWord']} (${defaults['germanWordByWord'].runtimeType})");
    print("   englishWordByWord: ${defaults['englishWordByWord']} (${defaults['englishWordByWord'].runtimeType})");
    print("   germanColloquial: ${defaults['germanColloquial']} (${defaults['germanColloquial'].runtimeType})");
    print("   englishColloquial: ${defaults['englishColloquial']} (${defaults['englishColloquial'].runtimeType})");
    
    return defaults;
  }

  Map<String, dynamic> _applyDefaultsAndValidate(Map<String, dynamic> settings) {
    final defaults = _getDefaultSettings();
    final result = <String, dynamic>{};
    
    // Apply defaults for any missing keys and ensure proper types
    for (final key in defaults.keys) {
      if (settings.containsKey(key)) {
        // Convert to proper type if needed
        result[key] = _convertToProperType(settings[key], defaults[key]);
      } else {
        // Use default value
        result[key] = defaults[key];
      }
    }
    
    // Ensure any extra keys from stored settings are preserved
    for (final key in settings.keys) {
      if (!result.containsKey(key)) {
        result[key] = settings[key];
      }
    }
    
    return result;
  }

  dynamic _convertToProperType(dynamic value, dynamic defaultValue) {
    if (defaultValue is bool) {
      return _ensureBoolean(value, defaultValue);
    } else if (defaultValue is String) {
      return value?.toString() ?? defaultValue;
    } else if (defaultValue is int) {
      if (value is int) return value;
      if (value is String) return int.tryParse(value) ?? defaultValue;
      return defaultValue;
    }
    return value ?? defaultValue;
  }

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

  // Save the updated user settings to Hive.
  Future<void> saveUserSettings(Map<String, dynamic> settings) async {
    try {
      // CRITICAL: Log what we're saving
      print("💾 SAVING SETTINGS TO HIVE:");
      print("   germanWordByWord: ${settings['germanWordByWord']} (${settings['germanWordByWord'].runtimeType})");
      print("   englishWordByWord: ${settings['englishWordByWord']} (${settings['englishWordByWord'].runtimeType})");
      print("   germanColloquial: ${settings['germanColloquial']} (${settings['germanColloquial'].runtimeType})");
      print("   englishColloquial: ${settings['englishColloquial']} (${settings['englishColloquial'].runtimeType})");
      
      await _settingsBox.put('userSettings', settings);
      print("✅ Settings saved successfully to Hive");
    } catch (e) {
      // Log the error; optionally, rethrow or handle it.
      print("❌ Error saving user settings: $e");
      rethrow; // Re-throw to allow UI to handle the error
    }
  }

  // Clear all user settings (useful for reset functionality)
  Future<void> clearUserSettings() async {
    try {
      await _settingsBox.delete('userSettings');
      print("✅ Settings cleared successfully from Hive");
    } catch (e) {
      print("❌ Error clearing user settings: $e");
      rethrow;
    }
  }

  // Check if settings exist in Hive
  bool hasStoredSettings() {
    try {
      return _settingsBox.containsKey('userSettings');
    } catch (e) {
      print("❌ Error checking stored settings: $e");
      return false;
    }
  }
}