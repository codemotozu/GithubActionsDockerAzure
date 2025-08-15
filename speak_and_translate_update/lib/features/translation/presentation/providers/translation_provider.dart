// lib/features/translation/presentation/providers/translation_provider.dart - Updated with EXACT mother tongue support per requirements
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
    
    // EXACT per requirements: Log raw settings for debugging
    _debugPrintSettings('Raw Settings from Provider', settings);
    
    // CRITICAL: Extract mother tongue for dynamic behavior
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

    // EXACT per requirements: For language learning mode, use user preferences with mother tongue
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
    
    // EXACT per requirements: Log processed preferences with mother tongue
    _debugPrintSettings('Processed User Preferences with Mother Tongue', userPreferences);
    
    return userPreferences;
  }

  bool _hasAnyStyleSelected() {
    final prefs = _getStylePreferences();
    
    // EXACT per requirements: Check if at least one translation style is selected
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
    
    print('🔍 Style Validation: Has any style selected = $hasStyle');
    
    return hasStyle;
  }

  String _getExpectedBehaviorForMotherTongue(String motherTongue) {
    switch (motherTongue.toLowerCase()) {
      case 'spanish':
        return 'Spanish → German and/or English based on your selections';
      case 'english':
        return 'English → Spanish (automatic) + German if selected';
      case 'german':
        return 'German → Spanish (automatic) + English if selected';
      default:
        return '$motherTongue → German and/or English based on your selections';
    }
  }

  Map<String, dynamic> _applyMotherTongueDefaults(Map<String, dynamic> preferences) {
    final motherTongue = preferences['motherTongue'] as String? ?? 'spanish';
    
    print('🌐 Applying EXACT defaults for mother tongue: $motherTongue');
    print('🎯 Expected behavior: ${_getExpectedBehaviorForMotherTongue(motherTongue)}');
    
    // EXACT per requirements: Apply intelligent defaults based on mother tongue
    switch (motherTongue.toLowerCase()) {
      case 'spanish':
        // EXACT: Spanish → German and English colloquial by default
        preferences['germanColloquial'] = true;
        preferences['englishColloquial'] = true;
        print('   ✅ Applied Spanish defaults: German + English colloquial');
        break;
        
      case 'english':
        // EXACT: English → German colloquial by default (Spanish is automatic)
        preferences['germanColloquial'] = true;
        print('   ✅ Applied English defaults: German colloquial (Spanish automatic)');
        break;
        
      case 'german':
        // EXACT: German → English colloquial by default (Spanish is automatic)
        preferences['englishColloquial'] = true;
        print('   ✅ Applied German defaults: English colloquial (Spanish automatic)');
        break;
        
      default:
        // Other languages → German and English colloquial
        preferences['germanColloquial'] = true;
        preferences['englishColloquial'] = true;
        print('   ✅ Applied $motherTongue defaults: German + English colloquial');
        break;
    }
    
    return preferences;
  }

  // Debug helper method
  void _debugPrintSettings(String label, Map<String, dynamic> settings) {
    print('\n${'='*60}');
    print('🎯 $label:');
    print('='*60);
    
    // CRITICAL: Mother tongue (determines entire translation behavior)
    print('🌐 Mother Tongue: ${settings['motherTongue']}');
    print('🎯 Expected Behavior: ${_getExpectedBehaviorForMotherTongue(settings['motherTongue'] ?? 'spanish')}');
    
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
    
    // EXACT per requirements: Show what will happen
    final motherTongue = settings['motherTongue'] as String? ?? 'spanish';
    final hasGerman = [settings['germanNative'], settings['germanColloquial'], settings['germanInformal'], settings['germanFormal']].any((v) => v == true);
    final hasEnglish = [settings['englishNative'], settings['englishColloquial'], settings['englishInformal'], settings['englishFormal']].any((v) => v == true);
    
    print('🎯 Translation Targets:');
    if (motherTongue == 'spanish') {
      if (hasGerman) print('  ✅ German (user selected)');
      if (hasEnglish) print('  ✅ English (user selected)');
      if (!hasGerman && !hasEnglish) print('  ⚠️ No targets selected');
    } else if (motherTongue == 'english') {
      print('  ✅ Spanish (automatic for English speakers)');
      if (hasGerman) print('  ✅ German (user selected)');
    } else if (motherTongue == 'german') {
      print('  ✅ Spanish (automatic for German speakers)');
      if (hasEnglish) print('  ✅ English (user selected)');
    }
    
    // Word-by-word audio status
    print('🎵 Word-by-Word Audio:');
    if (settings['germanWordByWord'] == true) {
      print('  ✅ German: [German word] ([Spanish equivalent])');
    } else {
      print('  ❌ German: Simple translation reading');
    }
    if (settings['englishWordByWord'] == true) {
      print('  ✅ English: [English word] ([Spanish equivalent])');
    } else {
      print('  ❌ English: Simple translation reading');
    }
    
    print('='*60 + '\n');
  }

  Future<void> startConversation(String text) async {
    if (!_mounted || text.isEmpty) return;

    try {
      // EXACT per requirements: Log conversation start with dynamic behavior
      print('\n🚀 STARTING DYNAMIC CONVERSATION (EXACT per requirements)');
      print('Input text: "$text"');
      
      // Get user's EXACT style preferences INCLUDING mother tongue
      var stylePreferences = _getStylePreferences();
      
      // EXACT per requirements: Validate and apply defaults ONLY if nothing is selected
      if (!_hasAnyStyleSelected()) {
        print('⚠️ No styles selected - applying intelligent defaults based on mother tongue');
        stylePreferences = _applyMotherTongueDefaults(stylePreferences);
        
        _debugPrintSettings('After Applying Mother Tongue Defaults', stylePreferences);
      } else {
        print('✅ User has selected specific styles - using exact preferences');
      }

      // EXACT per requirements: Final preferences being sent to backend
      print('\n📤 SENDING TO BACKEND (EXACT per requirements):');
      print('Mother Tongue: ${stylePreferences['motherTongue']}');
      print('🎯 Backend will implement EXACT logic:');
      
      final motherTongue = stylePreferences['motherTongue'] as String;
      switch (motherTongue.toLowerCase()) {
        case 'spanish':
          print('  📋 Spanish Logic: Translate to German and/or English based on selections');
          break;
        case 'english':
          print('  📋 English Logic: Translate to Spanish (automatic) + German if selected');
          break;
        case 'german':
          print('  📋 German Logic: Translate to Spanish (automatic) + English if selected');
          break;
        default:
          print('  📋 $motherTongue Logic: Translate to German and/or English based on selections');
          break;
      }
      
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

      // EXACT per requirements: Send to translation service with mother tongue
      final translation = await _repository.getTranslation(
        text, 
        stylePreferences: stylePreferences,  // Now includes mother tongue for dynamic behavior
      );
      
      if (!_mounted) return;

      // EXACT per requirements: Log response received
      print('\n📥 RESPONSE RECEIVED (EXACT per requirements):');
      print('Translation text length: ${translation.translatedText.length}');
      print('Audio path: ${translation.audioPath ?? "No audio"}');
      print('Source language detected: ${translation.sourceLanguage}');
      
      // Check if word-by-word audio was generated
      if (translation.audioPath != null) {
        final germanWordByWord = stylePreferences['germanWordByWord'] ?? false;
        final englishWordByWord = stylePreferences['englishWordByWord'] ?? false;
        final anyWordByWord = germanWordByWord || englishWordByWord;
        
        print('🎵 Audio Type: ${anyWordByWord ? "Word-by-word breakdown" : "Simple translation reading"}');
        if (anyWordByWord) {
          print('🎯 Format: [target word] ([Spanish equivalent])');
        }
      }
      
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
      // EXACT per requirements: Log errors with context
      print('\n❌ ERROR IN DYNAMIC CONVERSATION:');
      print('Error type: ${e.runtimeType}');
      print('Error message: $e');
      print('This may indicate an issue with the dynamic mother tongue logic');
      
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