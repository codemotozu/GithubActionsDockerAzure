// Updated translation.dart (Domain Entity) with enhanced word-by-word structure

import 'dart:ui';

class Translation {
  final String originalText;
  final String translatedText;
  final String sourceLanguage;
  final String targetLanguage;
  final String? audioPath;
  final Map<String, String>? translations;
  final Map<String, Map<String, String>>? wordByWord; // Enhanced for exact audio-visual matching
  final Map<String, String>? grammarExplanations;

  Translation({
    required this.originalText,
    required this.translatedText,
    required this.sourceLanguage,
    required this.targetLanguage,
    this.audioPath,
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
          ? Map<String, String>.from(json['grammar_explanations'] as Map)
          : null,
    );
  }

  // Convert to JSON for API communication
  Map<String, dynamic> toJson() {
    return {
      'original_text': originalText,
      'translated_text': translatedText,
      'source_language': sourceLanguage,
      'target_language': targetLanguage,
      'audio_path': audioPath,
      'translations': translations,
      'word_by_word': wordByWord,
      'grammar_explanations': grammarExplanations,
    };
  }

  // Helper methods for UI integration

  /// Check if word-by-word data is available
  bool get hasWordByWordData => wordByWord != null && wordByWord!.isNotEmpty;

  /// Get word pairs for a specific language
  List<WordPairData> getWordPairsForLanguage(String language) {
    if (!hasWordByWordData) return [];
    
    return wordByWord!.entries
        .where((entry) => entry.value['language'] == language)
        .map((entry) => WordPairData.fromMap(entry.key, entry.value))
        .toList()
      ..sort((a, b) => a.order.compareTo(b.order));
  }

  /// Get all available languages in word-by-word data
  Set<String> getAvailableLanguages() {
    if (!hasWordByWordData) return {};
    
    return wordByWord!.values
        .map((data) => data['language'] ?? 'unknown')
        .where((lang) => lang != 'unknown')
        .toSet();
  }

  /// Check if a specific language has word-by-word data
  bool hasWordByWordForLanguage(String language) {
    return getWordPairsForLanguage(language).isNotEmpty;
  }

  /// Get word pair counts by language
  Map<String, int> getWordPairCounts() {
    if (!hasWordByWordData) return {};
    
    final counts = <String, int>{};
    
    for (final entry in wordByWord!.entries) {
      final language = entry.value['language'] ?? 'unknown';
      if (language != 'unknown') {
        counts[language] = (counts[language] ?? 0) + 1;
      }
    }
    
    return counts;
  }

  /// Get phrasal verbs for a specific language
  List<WordPairData> getPhrasalVerbsForLanguage(String language) {
    return getWordPairsForLanguage(language)
        .where((pair) => pair.isPhrasalVerb)
        .toList();
  }

  /// Get all phrasal verbs across all languages
  Map<String, List<WordPairData>> getAllPhrasalVerbs() {
    final result = <String, List<WordPairData>>{};
    
    for (final language in getAvailableLanguages()) {
      final phrasalVerbs = getPhrasalVerbsForLanguage(language);
      if (phrasalVerbs.isNotEmpty) {
        result[language] = phrasalVerbs;
      }
    }
    
    return result;
  }

  /// Create a copy with updated word-by-word data
  Translation copyWith({
    String? originalText,
    String? translatedText,
    String? sourceLanguage,
    String? targetLanguage,
    String? audioPath,
    Map<String, String>? translations,
    Map<String, Map<String, String>>? wordByWord,
    Map<String, String>? grammarExplanations,
  }) {
    return Translation(
      originalText: originalText ?? this.originalText,
      translatedText: translatedText ?? this.translatedText,
      sourceLanguage: sourceLanguage ?? this.sourceLanguage,
      targetLanguage: targetLanguage ?? this.targetLanguage,
      audioPath: audioPath ?? this.audioPath,
      translations: translations ?? this.translations,
      wordByWord: wordByWord ?? this.wordByWord,
      grammarExplanations: grammarExplanations ?? this.grammarExplanations,
    );
  }

  @override
  String toString() {
    return 'Translation('
        'originalText: $originalText, '
        'translatedText: ${translatedText.length > 50 ? '${translatedText.substring(0, 50)}...' : translatedText}, '
        'sourceLanguage: $sourceLanguage, '
        'targetLanguage: $targetLanguage, '
        'hasAudio: ${audioPath != null}, '
        'hasWordByWord: $hasWordByWordData, '
        'wordPairCounts: ${getWordPairCounts()}'
        ')';
  }
}

/// Data class for individual word pairs with enhanced structure
class WordPairData {
  final String key;
  final String sourceWord;
  final String spanishEquivalent;
  final String language;
  final String style;
  final int order;
  final bool isPhrasalVerb;
  final String displayFormat;

  WordPairData({
    required this.key,
    required this.sourceWord,
    required this.spanishEquivalent,
    required this.language,
    required this.style,
    required this.order,
    required this.isPhrasalVerb,
    required this.displayFormat,
  });

  factory WordPairData.fromMap(String key, Map<String, String> data) {
    return WordPairData(
      key: key,
      sourceWord: data['source'] ?? '',
      spanishEquivalent: data['spanish'] ?? '',
      language: data['language'] ?? 'unknown',
      style: data['style'] ?? 'unknown',
      order: int.tryParse(data['order'] ?? '0') ?? 0,
      isPhrasalVerb: data['is_phrasal_verb'] == 'true',
      displayFormat: data['display_format'] ?? '[${data['source'] ?? ''}] ([${data['spanish'] ?? ''}])',
    );
  }

  Map<String, String> toMap() {
    return {
      'source': sourceWord,
      'spanish': spanishEquivalent,
      'language': language,
      'style': style,
      'order': order.toString(),
      'is_phrasal_verb': isPhrasalVerb.toString(),
      'display_format': displayFormat,
    };
  }

  /// Get the audio format exactly as it will be spoken
  String get audioFormat => displayFormat;

  /// Check if this is a German separable verb
  bool get isGermanSeparableVerb => language == 'german' && isPhrasalVerb;

  /// Check if this is an English phrasal verb
  bool get isEnglishPhrasalVerb => language == 'english' && isPhrasalVerb;

  /// Get language-specific description
  String get verbTypeDescription {
    if (isGermanSeparableVerb) return 'German Separable Verb';
    if (isEnglishPhrasalVerb) return 'English Phrasal Verb';
    return 'Word/Phrase';
  }

  /// Get color for UI display based on language
  Color get languageColor {
    switch (language.toLowerCase()) {
      case 'german':
        return const Color(0xFFFFB74D); // Amber
      case 'english':
        return const Color(0xFF42A5F5); // Blue
      case 'spanish':
        return const Color(0xFF66BB6A); // Green
      default:
        return const Color(0xFF9E9E9E); // Grey
    }
  }

  @override
  String toString() {
    return 'WordPairData('
        'sourceWord: $sourceWord, '
        'spanishEquivalent: $spanishEquivalent, '
        'language: $language, '
        'style: $style, '
        'order: $order, '
        'isPhrasalVerb: $isPhrasalVerb, '
        'displayFormat: $displayFormat'
        ')';
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is WordPairData &&
          runtimeType == other.runtimeType &&
          key == other.key &&
          sourceWord == other.sourceWord &&
          spanishEquivalent == other.spanishEquivalent &&
          language == other.language &&
          style == other.style &&
          order == other.order;

  @override
  int get hashCode =>
      key.hashCode ^
      sourceWord.hashCode ^
      spanishEquivalent.hashCode ^
      language.hashCode ^
      style.hashCode ^
      order.hashCode;
}

/// Extension methods for easy access to word-by-word data
extension TranslationWordByWordExtensions on Translation {
  /// Get a summary of word-by-word data for debugging
  String get wordByWordSummary {
    if (!hasWordByWordData) return 'No word-by-word data';
    
    final counts = getWordPairCounts();
    final languages = getAvailableLanguages();
    final phrasalVerbs = getAllPhrasalVerbs();
    
    final buffer = StringBuffer();
    buffer.writeln('Word-by-Word Summary:');
    buffer.writeln('Languages: ${languages.join(', ')}');
    buffer.writeln('Counts: $counts');
    
    if (phrasalVerbs.isNotEmpty) {
      buffer.writeln('Phrasal/Separable Verbs:');
      phrasalVerbs.forEach((language, verbs) {
        buffer.writeln('  $language: ${verbs.map((v) => v.sourceWord).join(', ')}');
      });
    }
    
    return buffer.toString();
  }

  /// Validate that the word-by-word data is correctly structured
  List<String> validateWordByWordData() {
    final errors = <String>[];
    
    if (!hasWordByWordData) {
      return ['No word-by-word data available'];
    }
    
    for (final entry in wordByWord!.entries) {
      final key = entry.key;
      final data = entry.value;
      
      // Check required fields
      if (data['source'] == null || data['source']!.isEmpty) {
        errors.add('Key $key: Missing or empty source word');
      }
      
      if (data['spanish'] == null || data['spanish']!.isEmpty) {
        errors.add('Key $key: Missing or empty Spanish equivalent');
      }
      
      if (data['language'] == null || data['language']!.isEmpty) {
        errors.add('Key $key: Missing or empty language');
      }
      
      if (data['display_format'] == null || data['display_format']!.isEmpty) {
        errors.add('Key $key: Missing or empty display format');
      }
      
      // Validate display format
      final displayFormat = data['display_format'] ?? '';
      if (!displayFormat.contains('[') || !displayFormat.contains(']') || 
          !displayFormat.contains('(') || !displayFormat.contains(')')) {
        errors.add('Key $key: Invalid display format: $displayFormat');
      }
    }
    
    return errors;
  }
}