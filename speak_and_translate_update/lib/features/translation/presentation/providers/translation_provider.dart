// lib/features/translation/presentation/providers/translation_provider.dart - Updated with mother tongue support
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:speak_and_translate_update/features/translation/presentation/providers/shared_provider.dart' show settingsProvider;

import '../../data/models/chat_message_model.dart';
import '../../domain/repositories/translation_repository.dart';
import 'speech_provider.dart';

// History management constants
const _maxMessages = 50; // Maximum messages to keep in history
const _messagesToKeepWhenPruning = 40; // Number to keep when pruning
const _initialMessagesToPreserve = 2; // Keep first N messages of conversation

class TranslationState {
  final bool isLoading;
  final List<ChatMessage> messages;
  final String? error;

  TranslationState({
    required this.isLoading,
    required this.messages,
    this.error,
  });

  factory TranslationState.initial() => TranslationState(
        isLoading: false,
        messages: [],
        error: null,
      );

  TranslationState copyWith({
    bool? isLoading,
    List<ChatMessage>? messages,
    String? error,
  }) {
    return TranslationState(
      isLoading: isLoading ?? this.isLoading,
      messages: messages ?? this.messages,
      error: error ?? this.error,
    );
  }
}

class TranslationNotifier extends StateNotifier<TranslationState> {
  final TranslationRepository _repository;
  final Ref _ref;
  bool _mounted = true;

  TranslationNotifier(this._repository, this._ref)
      : super(TranslationState.initial());

  Map<String, dynamic> _getStylePreferences() {
    final settings = _ref.read(settingsProvider);
    
    // DEBUGGER POINT 1: Log raw settings
    _debugPrintSettings('Raw Settings from Provider', settings);
    
    // Extract mother tongue - CRITICAL FOR DYNAMIC TRANSLATION
    final motherTongue = settings['motherTongue'] as String? ?? 'spanish';
    
    // Check if we're in language learning mode
    if (settings['appMode'] != 'languageLearning') {
      // For travel mode or other modes, return minimal preferences
      final minimalPrefs = <String, dynamic>{
        'motherTongue': motherTongue,  // ALWAYS include mother tongue
        'germanNative': false,
        'germanColloquial': true,  // Default to colloquial
        'germanInformal': false,
        'germanFormal': false,
        'englishNative': false,
        'englishColloquial': true,  // Default to colloquial
        'englishInformal': false,
        'englishFormal': false,
        'germanWordByWord': false,
        'englishWordByWord': false,
      };
      
      _debugPrintSettings('Travel Mode Preferences', minimalPrefs);
      return minimalPrefs;
    }

    // For language learning mode, use EXACT user preferences with mother tongue
    final userPreferences = <String, dynamic>{
      'motherTongue': motherTongue,  // CRITICAL: Include mother tongue for dynamic translation
      'germanNative': settings['germanNative'] ?? false,
      'germanColloquial': settings['germanColloquial'] ?? false,
      'germanInformal': settings['germanInformal'] ?? false,
      'germanFormal': settings['germanFormal'] ?? false,
      'englishNative': settings['englishNative'] ?? false,
      'englishColloquial': settings['englishColloquial'] ?? false,
      'englishInformal': settings['englishInformal'] ?? false,
      'englishFormal': settings['englishFormal'] ?? false,
      'germanWordByWord': settings['germanWordByWord'] ?? false,
      'englishWordByWord': settings['englishWordByWord'] ?? false,
    };
    
    // DEBUGGER POINT 2: Log processed preferences with mother tongue
    _debugPrintSettings('Processed User Preferences with Mother Tongue', userPreferences);
    
    return userPreferences;
  }

  bool _hasAnyStyleSelected() {
    final prefs = _getStylePreferences();
    
    // Check if at least one translation style is selected (excluding word-by-word)
    final hasStyle = [
      prefs['germanNative'],
      prefs['germanColloquial'], 
      prefs['germanInformal'],
      prefs['germanFormal'],
      prefs['englishNative'],
      prefs['englishColloquial'],
      prefs['englishInformal'],
      prefs['englishFormal']
    ].any((value) => value == true);
    
    // DEBUGGER POINT 3: Log validation result
    print('🔍 Style Validation: Has any style selected = $hasStyle');
    
    return hasStyle;
  }

  Map<String, dynamic> _applyMotherTongueDefaults(Map<String, dynamic> preferences) {
    final motherTongue = preferences['motherTongue'] as String? ?? 'spanish';
    
    print('🌐 Applying defaults for mother tongue: $motherTongue');
    
    // Apply intelligent defaults based on mother tongue
    switch (motherTongue) {
      case 'spanish':
        // Spanish speakers typically want German and English translations
        preferences['germanColloquial'] = true;
        preferences['englishColloquial'] = true;
        break;
      case 'english':
        // English speakers typically want German translations, Spanish is automatic
        preferences['germanColloquial'] = true;
        // Note: Spanish translation is automatic for English speakers
        break;
      case 'german':
        // German speakers typically want English translations, Spanish is automatic  
        preferences['englishColloquial'] = true;
        // Note: Spanish translation is automatic for German speakers
        break;
      default:
        // Fallback to Spanish->German+English
        preferences['germanColloquial'] = true;
        preferences['englishColloquial'] = true;
        break;
    }
    
    return preferences;
  }

  // Debug helper method
  void _debugPrintSettings(String label, Map<String, dynamic> settings) {
    print('\n' + '='*60);
    print('🎯 $label:');
    print('='*60);
    
    // Mother tongue (CRITICAL)
    print('🌐 Mother Tongue: ${settings['motherTongue']}');
    
    // German settings
    print('🇩🇪 German Settings:');
    print('  Native: ${settings['germanNative']}');
    print('  Colloquial: ${settings['germanColloquial']}');
    print('  Informal: ${settings['germanInformal']}');
    print('  Formal: ${settings['germanFormal']}');
    print('  Word-by-Word: ${settings['germanWordByWord']}');
    
    // English settings
    print('🇺🇸 English Settings:');
    print('  Native: ${settings['englishNative']}');
    print('  Colloquial: ${settings['englishColloquial']}');
    print('  Informal: ${settings['englishInformal']}');
    print('  Formal: ${settings['englishFormal']}');
    print('  Word-by-Word: ${settings['englishWordByWord']}');
    
    print('='*60 + '\n');
  }

  Future<void> startConversation(String text) async {
    if (!_mounted || text.isEmpty) return;

    try {
      // DEBUGGER POINT 4: Log conversation start
      print('\n🚀 STARTING DYNAMIC CONVERSATION');
      print('Input text: "$text"');
      
      // Get user's exact style preferences INCLUDING mother tongue
      var stylePreferences = _getStylePreferences();
      
      // Validate and apply defaults ONLY if nothing is selected
      if (!_hasAnyStyleSelected()) {
        print('⚠️ No styles selected - applying intelligent defaults based on mother tongue');
        stylePreferences = _applyMotherTongueDefaults(stylePreferences);
        
        // DEBUGGER POINT 5: Log default application
        _debugPrintSettings('After Applying Mother Tongue Defaults', stylePreferences);
      }

      // DEBUGGER POINT 6: Final preferences being sent to backend
      print('\n📤 SENDING TO BACKEND:');
      print('Mother Tongue: ${stylePreferences['motherTongue']}');
      print('Style Preferences:');
      stylePreferences.forEach((key, value) {
        if (key != 'motherTongue') {  // Don't repeat mother tongue
          if (value == true) {
            print('  ✅ $key: $value');
          } else {
            print('  ❌ $key: $value');
          }
        }
      });

      // Prune history before adding new messages
      var updatedMessages = _pruneMessageHistory([
        ...state.messages,
        ChatMessage.user(text),
        ChatMessage.aiLoading(),
      ]);

      state = state.copyWith(messages: updatedMessages, isLoading: true);
      await _repository.stopAudio();

      // Send to translation service with exact preferences INCLUDING mother tongue
      final translation = await _repository.getTranslation(
        text, 
        stylePreferences: stylePreferences,  // Now includes mother tongue
      );
      
      if (!_mounted) return;

      // DEBUGGER POINT 7: Log response received
      print('\n📥 RESPONSE RECEIVED:');
      print('Translation text length: ${translation.translatedText.length}');
      print('Audio path: ${translation.audioPath ?? "No audio"}');
      print('Source language detected: ${translation.sourceLanguage}');
      
      // Prune again after receiving response
      final newMessages = _pruneMessageHistory(
        List<ChatMessage>.from(state.messages)
          ..removeLast()
          ..add(ChatMessage.ai(translation: translation)),
      );

      state = state.copyWith(
        isLoading: false,
        messages: newMessages,
        error: null,
      );

      // Handle hands-free audio playback
      final isHandsFree = _ref.read(speechProvider);
      if (isHandsFree && translation.audioPath != null) {
        print('🔊 Playing audio in hands-free mode');
        await _repository.playAudio(translation.audioPath!);
      }
      
    } catch (e) {
      // DEBUGGER POINT 8: Log errors
      print('\n❌ ERROR IN CONVERSATION:');
      print('Error type: ${e.runtimeType}');
      print('Error message: $e');
      print('Stack trace: ${StackTrace.current}');
      
      if (!_mounted) return;
      
      final newMessages = _pruneMessageHistory(
        List<ChatMessage>.from(state.messages)
          ..removeLast()
          ..add(ChatMessage.aiError(e.toString())),
      );

      state = state.copyWith(
        isLoading: false,
        messages: newMessages,
        error: e.toString(),
      );
    }
  }

  List<ChatMessage> _pruneMessageHistory(List<ChatMessage> messages) {
    if (messages.length <= _maxMessages) return messages;

    // DEBUGGER POINT 9: Log pruning action
    print('📦 Pruning message history: ${messages.length} -> $_messagesToKeepWhenPruning messages');

    return [
      // Preserve initial conversation context
      ...messages.take(_initialMessagesToPreserve),
      // Keep most recent messages
      ...messages.sublist(
        messages.length - (_messagesToKeepWhenPruning - _initialMessagesToPreserve),
      ),
    ];
  }

  Future<void> playAudio(String audioPath) async {
    try {
      print('🎵 Playing audio: $audioPath');
      await _repository.playAudio(audioPath);
    } catch (e) {
      print('❌ Audio playback error: $e');
      if (_mounted) {
        state = state.copyWith(error: 'Audio playback failed: ${e.toString()}');
      }
    }
  }

  Future<void> stopAudio() async {
    try {
      print('⏹️ Stopping audio');
      await _repository.stopAudio();
    } catch (e) {
      print('❌ Error stopping audio: $e');
      if (_mounted) {
        state = state.copyWith(error: 'Error stopping audio: ${e.toString()}');
      }
    }
  }

  void clearConversation() {
    if (_mounted) {
      print('🗑️ Clearing conversation history');
      state = TranslationState.initial();
    }
  }

  @override
  void dispose() {
    _mounted = false;
    _repository.dispose();
    super.dispose();
  }
}

final translationProvider =
    StateNotifierProvider<TranslationNotifier, TranslationState>((ref) {
  return TranslationNotifier(
    ref.watch(translationRepositoryProvider),
    ref,
  );
});