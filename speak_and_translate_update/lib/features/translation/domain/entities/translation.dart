class Translation {
  final String originalText;
  final String translatedText;
  final String sourceLanguage;
  final String targetLanguage;
  final String? audioPath;  // Add this line
  final Map<String, String>? translations;
  final Map<String, Map<String, String>>? wordByWord;
  final Map<String, String>? grammarExplanations;

  Translation({
    required this.originalText,
    required this.translatedText,
    required this.sourceLanguage,
    required this.targetLanguage,
    this.audioPath,  // Add this line
    this.translations,
    this.wordByWord,
    this.grammarExplanations,
  });

factory Translation.fromJson(Map<String, dynamic> json) {
  return Translation(
    originalText: json['original_text'] as String,
    translatedText: json['translated_text'] as String,
    sourceLanguage: json['source_language'] as String,
    targetLanguage: json['target_language'] as String,
    audioPath: json['audio_path'] as String?,  // Add this line
    translations: json['translations'] != null 
        ? Map<String, String>.from(json['translations'] as Map)
        : null,
    wordByWord: json['word_by_word'] != null
        ? Map<String, Map<String, String>>.from(
            (json['word_by_word'] as Map).map(
              (key, value) => MapEntry(
                key as String,
                Map<String, String>.from(value as Map),
              ),
            ),
          )
        : null,
    grammarExplanations: json['grammar_explanations'] != null
        ? Map<String, String>.from(json['grammar_explanations'] as Map)
        : null,
  );
}
}