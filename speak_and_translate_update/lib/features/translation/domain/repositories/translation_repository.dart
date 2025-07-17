import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/repositories/translation_repository_impl.dart';
import '../entities/translation.dart';

final translationRepositoryProvider = Provider<TranslationRepository>((ref) {
  return TranslationRepositoryImpl();
});

// Updated translation repository interface
abstract class TranslationRepository {
  Future<Translation> getTranslation(String text, {Map<String, dynamic>? stylePreferences});
  Future<String> processAudioInput(String audioPath);
  Future<void> playAudio(String audioPath);
  Future<void> stopAudio();
  Future<void> playCompletionSound(); 
  Future<void> playUISound(String soundType);
  void dispose();
}