// lib/features/translation/presentation/providers/translation_provider.dart
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
    
    // Check if we're in language learning mode
    if (settings['appMode'] != 'languageLearning') {
      // For travel mode or other modes, return default preferences
      return <String, dynamic>{
        'germanNative': false,
        'germanColloquial': true,
        'germanInformal': false,
        'germanFormal': false,
        'englishNative': false,
        'englishColloquial': true,
        'englishInformal': false,
        'englishFormal': false,
        'germanWordByWord': true,    // Add word-by-word audio preferences
        'englishWordByWord': false,
      };
    }

    // For language learning mode, use the user's style preferences (make it mutable)
    return <String, dynamic>{
      'germanNative': settings['germanNative'] ?? false,
      'germanColloquial': settings['germanColloquial'] ?? false,
      'germanInformal': settings['germanInformal'] ?? false,
      'germanFormal': settings['germanFormal'] ?? false,
      'englishNative': settings['englishNative'] ?? false,
      'englishColloquial': settings['englishColloquial'] ?? false,
      'englishInformal': settings['englishInformal'] ?? false,
      'englishFormal': settings['englishFormal'] ?? false,
      'germanWordByWord': settings['germanWordByWord'] ?? true,     // Include from settings
      'englishWordByWord': settings['englishWordByWord'] ?? false,
    };
  }

  bool _hasAnyStyleSelected() {
    final prefs = _getStylePreferences();
    // Check only translation style preferences, not word-by-word audio preferences
    return [
      prefs['germanNative'],
      prefs['germanColloquial'], 
      prefs['germanInformal'],
      prefs['germanFormal'],
      prefs['englishNative'],
      prefs['englishColloquial'],
      prefs['englishInformal'],
      prefs['englishFormal']
    ].any((value) => value == true);
  }

  Future<void> startConversation(String text) async {
    if (!_mounted || text.isEmpty) return;

    try {


         // Get style preferences - default to colloquial if none selected
    final stylePreferences = {
      'germanNative': false,
      'germanColloquial': true,  // Default
      'germanInformal': false,
      'germanFormal': false,
      'englishNative': false,
      'englishColloquial': true,  // Default
      'englishInformal': false,
      'englishFormal': false,
      'germanWordByWord': true,   // Enable word-by-word for German
      'englishWordByWord': false,
    };

       // Debug logging
    print('🎯 Translation Provider - Style Preferences:');
    print('   German word-by-word: ${stylePreferences['germanWordByWord']}');
    print('   English word-by-word: ${stylePreferences['englishWordByWord']}');

      
      // If no styles are selected, use default colloquial styles
      if (!_hasAnyStyleSelected()) {
        // Use default styles silently - don't block the conversation
        stylePreferences['germanColloquial'] = true;
        stylePreferences['englishColloquial'] = true;
      }

      // Debug logging for word-by-word preferences
      print('🎯 Translation Provider - Style Preferences:');
      print('   German word-by-word: ${stylePreferences['germanWordByWord']}');
      print('   English word-by-word: ${stylePreferences['englishWordByWord']}');
      print('   German styles: Native=${stylePreferences['germanNative']}, Colloquial=${stylePreferences['germanColloquial']}, Informal=${stylePreferences['germanInformal']}, Formal=${stylePreferences['germanFormal']}');
      print('   English styles: Native=${stylePreferences['englishNative']}, Colloquial=${stylePreferences['englishColloquial']}, Informal=${stylePreferences['englishInformal']}, Formal=${stylePreferences['englishFormal']}');

      // Prune history before adding new messages
      var updatedMessages = _pruneMessageHistory([
        ...state.messages,
        ChatMessage.user(text),
        ChatMessage.aiLoading(),
      ]);

      state = state.copyWith(messages: updatedMessages, isLoading: true);
      await _repository.stopAudio();

      final translation = await _repository.getTranslation(
        text, 
        stylePreferences: stylePreferences,
      );
      
      if (!_mounted) return;

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

      final isHandsFree = _ref.read(speechProvider);
      if (isHandsFree && translation.audioPath != null) {
        await _repository.playAudio(translation.audioPath!);
      }
    } catch (e) {
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
      await _repository.playAudio(audioPath);
    } catch (e) {
      if (_mounted) {
        state = state.copyWith(error: 'Audio playback failed: ${e.toString()}');
      }
    }
  }

  Future<void> stopAudio() async {
    try {
      await _repository.stopAudio();
    } catch (e) {
      if (_mounted) {
        state = state.copyWith(error: 'Error stopping audio: ${e.toString()}');
      }
    }
  }

  void clearConversation() {
    if (_mounted) {
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








