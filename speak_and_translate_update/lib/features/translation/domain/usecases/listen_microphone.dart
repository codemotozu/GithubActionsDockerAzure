import '../repositories/translation_repository.dart';


class ListenMicrophone {
  final TranslationRepository repository;

  ListenMicrophone(this.repository);

  Future<String> execute(String audioPath) async { // Changed return type
    // Implementation for processing audio file
    return repository.processAudioInput(audioPath);
  }
}