import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../domain/repositories/translation_repository.dart';

final speechProvider = StateNotifierProvider<SpeechNotifier, bool>((ref) {
  final repository = ref.watch(translationRepositoryProvider);
  return SpeechNotifier(repository);
});

class SpeechNotifier extends StateNotifier<bool> {
  final TranslationRepository _repository;
  bool _isPlaying = false;

  SpeechNotifier(this._repository) : super(true); // Default to true for auto-playback

  bool get isPlaying => _isPlaying;
  bool get isHandsFreeMode => state;

  void toggleHandsFreeMode() {
    state = !state;
  }

  Future<void> playAudio(String? audioPath) async {
    if (audioPath == null) return;
    
    try {
      _isPlaying = true;
      await _repository.playAudio(audioPath);
      _isPlaying = false;
    } catch (e) {
      _isPlaying = false;
      print('Error playing audio: $e'); // Debug log
      rethrow;
    }
  }

  Future<void> stop() async {
    try {
      await _repository.stopAudio();
      _isPlaying = false;
    } catch (e) {
      print('Error stopping audio: $e'); // Debug log
    }
  }

  @override
  void dispose() {
    _repository.dispose();
    super.dispose();
  }
}
