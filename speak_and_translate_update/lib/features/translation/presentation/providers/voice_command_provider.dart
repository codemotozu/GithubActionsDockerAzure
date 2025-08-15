import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/repositories/translation_repository.dart';
import 'audio_recorder_provider.dart';
import 'prompt_screen_provider.dart';

class VoiceCommandState {
  final bool isListening;
  final String? lastCommand;
  final String? error;
  final bool isProcessing; 

  VoiceCommandState({
    this.isListening = false,
    this.lastCommand,
    this.error,
    this.isProcessing = false,
  });

  
  VoiceCommandState copyWith({
    bool? isListening,
    String? lastCommand,
    String? error,
    bool? isProcessing,
  }) {
    return VoiceCommandState(
      isListening: isListening ?? this.isListening,
      lastCommand: lastCommand ?? this.lastCommand,
      error: error ?? this.error,
      isProcessing: isProcessing ?? this.isProcessing,
    );
  }
}

class VoiceCommandNotifier extends StateNotifier<VoiceCommandState> {
  final AudioRecorder _recorder;
  final TranslationRepository _repository;
  final Ref _ref;

  VoiceCommandNotifier(this._recorder, this._repository, this._ref)
      : super(VoiceCommandState());

  Future<void> processVoiceCommand(String command) async {
    try {
      final commandLower = command.toLowerCase();
      
      if (commandLower == "open") {
        // First update prompt screen state
        _ref.read(promptScreenProvider.notifier).setListening(true);
        
        // Start recording first
        try {
          await _recorder.startListening(command);
          // Only update state after successful start of listening
          state = state.copyWith(
            isListening: true,
            lastCommand: command,
            isProcessing: false
          );
        } catch (e) {
          // If recording fails, update both states accordingly
          _ref.read(promptScreenProvider.notifier).setListening(false);
          state = state.copyWith(
            isListening: false,
            error: e.toString(),
            isProcessing: false
          );
          rethrow; // Re-throw to be caught by outer try-catch
        }
      } else if (commandLower == "stop") {
        if (state.isListening) {
          try {
            final audioPath = await _recorder.stopListening();
            _ref.read(promptScreenProvider.notifier).setListening(false);
            
            if (audioPath != null) {
              state = state.copyWith(isProcessing: true);
              final text = await _repository.processAudioInput(audioPath);
              _ref.read(promptScreenProvider.notifier).updateText(text);
              
              state = state.copyWith(
                isListening: false,
                lastCommand: text,
                isProcessing: false
              );
            } else {
              state = state.copyWith(
                isListening: false,
                error: "Failed to get audio path",
                isProcessing: false
              );
            }
          } catch (e) {
            state = state.copyWith(
              isListening: false,
              error: e.toString(),
              isProcessing: false
            );
          }
        }
      }
    } catch (e) {
      state = state.copyWith(
        isListening: false,
        error: e.toString(),
        isProcessing: false
      );
    }
  }

  Future<void> handleSpeechRecognition(String audioPath) async {
    try {
      final text = await _repository.processAudioInput(audioPath);
      if (text.toLowerCase() == "open") {
        await processVoiceCommand("open");
      } else if (text.toLowerCase() == "stop") {
        await processVoiceCommand("stop");
      }
    } catch (e) {
      state = state.copyWith(
        isListening: false,
        error: e.toString(),
        isProcessing: false
      );
    }
  }
}

final voiceCommandProvider = StateNotifierProvider<VoiceCommandNotifier, VoiceCommandState>((ref) {
  return VoiceCommandNotifier(
    ref.watch(audioRecorderProvider),
    ref.watch(translationRepositoryProvider),
    ref,
  );
});