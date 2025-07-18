// lib/features/translation/presentation/providers/shared_providers.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';

// Settings state provider - shared across the entire app
final settingsProvider = StateProvider<Map<String, dynamic>>((ref) => {
  // Existing voice/microphone settings - CAMBIADO A CONTINUOUS LISTENING POR DEFECTO
  'microphoneMode': 'continuousListening', // 'voiceCommand' or 'continuousListening'
  // 'motherTongue': 'english',
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

// Existing voice providers (keep unchanged)
final isListeningProvider = StateProvider<bool>((ref) => false);
final isContinuousListeningActiveProvider = StateProvider<bool>((ref) => false);