import 'package:hive/hive.dart';

class UserSettingsRepository {
  final Box _settingsBox = Hive.box('settings');

  // Retrieve the user settings from Hive.
  Future<Map<String, dynamic>> getUserSettings() async {
    try {
      final storedSettings = _settingsBox.get('userSettings');
      if (storedSettings != null && storedSettings is Map) {
        return Map<String, dynamic>.from(storedSettings);
      }
    } catch (e) {
      // Log the error; continue with default settings.
      print("Error retrieving user settings: $e");
    }
    // Return default settings if no data exists.
    return {
      'microphoneMode': 'continuousListening', // Always continuous listening now
      'motherTongue': 'spanish',
      'appMode': 'languageLearning',
      
      // NEW: Fluency practice settings with defaults
      'practiceLanguage': 'english',
      'correctionLevel': 'intermediate',
      'pronunciationFeedback': true,
      'grammarCorrection': true,
      'vocabularyEnhancement': true,
      'realTimeCorrection': false,
      
      // Word-by-word audio settings
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
    };
  }

  // Save the updated user settings to Hive.
  Future<void> saveUserSettings(Map<String, dynamic> settings) async {
    try {
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