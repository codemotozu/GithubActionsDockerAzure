// Updated translation_model.dart to handle enhanced word-by-word UI data

class Translation {
  final String originalText;
  final String translatedText;
  final String sourceLanguage;
  final String targetLanguage;
  final String? audioPath;
  final Map<String, String>? translations;
  final Map<String, Map<String, String>>? wordByWord; // Enhanced for UI visualization
  final Map<String, Map<String, String>>? grammarExplanations;

  Translation({
    required this.originalText,
    required this.translatedText,
    required this.sourceLanguage,
    required this.targetLanguage,
    this.audioPath,
    this.translations,
    this.wordByWord, // Now contains structured UI data
    this.grammarExplanations,
  });

  factory Translation.fromJson(Map<String, dynamic> json) {
    return Translation(
      originalText: json['original_text'] as String,
      translatedText: json['translated_text'] as String,
      sourceLanguage: json['source_language'] as String,
      targetLanguage: json['target_language'] as String,
      audioPath: json['audio_path'] as String?,
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
          ? Map<String, Map<String, String>>.from(
              (json['grammar_explanations'] as Map).map(
                (key, value) => MapEntry(
                  key as String,
                  Map<String, String>.from(value as Map),
                ),
              ),
            )
          : null,
    );
  }

  // Helper method to check if word-by-word data is available
  bool get hasWordByWordData => wordByWord != null && wordByWord!.isNotEmpty;

  // Helper method to get word pairs for a specific language
  List<MapEntry<String, Map<String, String>>> getWordPairsForLanguage(String language) {
    if (!hasWordByWordData) return [];
    
    return wordByWord!.entries
        .where((entry) => entry.value['language'] == language)
        .toList();
  }

  // Helper method to get all available languages in word-by-word data
  Set<String> getAvailableLanguages() {
    if (!hasWordByWordData) return {};
    
    return wordByWord!.values
        .map((data) => data['language'] ?? 'unknown')
        .toSet();
  }

  // Helper method to check if a specific language has word-by-word data
  bool hasWordByWordForLanguage(String language) {
    return getWordPairsForLanguage(language).isNotEmpty;
  }

  // Helper method to get the display format for debugging
  Map<String, List<String>> getDisplayFormats() {
    if (!hasWordByWordData) return {};
    
    final formats = <String, List<String>>{};
    
    for (final entry in wordByWord!.entries) {
      final language = entry.value['language'] ?? 'unknown';
      final displayFormat = entry.value['display_format'] ?? 'No format';
      
      formats.putIfAbsent(language, () => []);
      formats[language]!.add(displayFormat);
    }
    
    return formats;
  }

  // Helper method to count word pairs by language
  Map<String, int> getWordPairCounts() {
    if (!hasWordByWordData) return {};
    
    final counts = <String, int>{};
    
    for (final entry in wordByWord!.entries) {
      final language = entry.value['language'] ?? 'unknown';
      counts[language] = (counts[language] ?? 0) + 1;
    }
    
    return counts;
  }

  // Debug method to print word-by-word structure
  void debugPrintWordByWordStructure() {
    if (!hasWordByWordData) {
      print('📝 No word-by-word data available');
      return;
    }

    print('\n📝 WORD-BY-WORD DATA STRUCTURE:');
    print('='*50);
    
    final languages = getAvailableLanguages();
    print('Available languages: ${languages.join(', ')}');
    
    final counts = getWordPairCounts();
    print('Word pair counts: $counts');
    
    print('\nDetailed breakdown:');
    for (final entry in wordByWord!.entries) {
      final key = entry.key;
      final data = entry.value;
      
      print('Key: $key');
      print('  Source: ${data['source']}');
      print('  Spanish: ${data['spanish']}');
      print('  Language: ${data['language']}');
      print('  Style: ${data['style']}');
      print('  Order: ${data['order']}');
      print('  Is Phrasal Verb: ${data['is_phrasal_verb']}');
      print('  Display Format: ${data['display_format']}');
      print('');
    }
    
    print('='*50);
  }
}