// translation.dart - Updated Domain Entity with Multi-Style Support and Perfect Sync

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
  final List<TranslationStyle>? styles; // NEW: Multiple styles support

  Translation({
    required this.originalText,
    required this.translatedText,
    required this.sourceLanguage,
    required this.targetLanguage,
    this.audioPath,
    this.translations,
    this.wordByWord,
    this.grammarExplanations,
    this.styles,
  });

  factory Translation.fromJson(Map<String, dynamic> json) {
    // Parse styles from the response
    List<TranslationStyle>? parsedStyles;
    if (json['styles'] != null && json['styles'] is List) {
      parsedStyles = (json['styles'] as List)
          .map((styleJson) => TranslationStyle.fromJson(styleJson))
          .toList();
    } else {
      // Create styles from translations if styles field not present
      parsedStyles = _createStylesFromTranslations(json);
    }

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
      styles: parsedStyles,
    );
  }

  // Helper method to create styles from translations data
  static List<TranslationStyle>? _createStylesFromTranslations(Map<String, dynamic> json) {
    final translations = json['translations'] as Map<String, dynamic>?;
    final wordByWord = json['word_by_word'] as Map<String, dynamic>?;
    
    if (translations == null || translations.isEmpty) return null;
    
    final styles = <TranslationStyle>[];
    
    // Parse each translation as a potential style
    translations.forEach((key, value) {
      if (value is String && value.isNotEmpty) {
        // Extract word pairs for this style if available
        final stylePairs = <WordPair>[];
        
        if (wordByWord != null) {
          wordByWord.forEach((wbwKey, wbwData) {
            if (wbwData is Map) {
              final style = wbwData['style'] as String?;
              if (style == key || style?.contains(key) == true) {
                final source = wbwData['source'] as String? ?? '';
                final spanish = wbwData['spanish'] as String? ?? '';
                final order = int.tryParse(wbwData['order']?.toString() ?? '0') ?? 0;
                final isPhrasalVerb = wbwData['is_phrasal_verb'] == 'true';
                
                stylePairs.add(WordPair(
                  sourceWord: source,
                  spanishEquivalent: spanish,
                  order: order,
                  isPhrasalVerb: isPhrasalVerb,
                ));
              }
            }
          });
        }
        
        // Sort pairs by order
        stylePairs.sort((a, b) => a.order.compareTo(b.order));
        
        styles.add(TranslationStyle(
          name: key,
          translation: value,
          wordPairs: stylePairs,
        ));
      }
    });
    
    return styles.isNotEmpty ? styles : null;
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
      'styles': styles?.map((s) => s.toJson()).toList(),
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

  /// Get word pairs for a specific style
  List<WordPairData> getWordPairsForStyle(String styleName) {
    if (!hasWordByWordData) return [];
    
    return wordByWord!.entries
        .where((entry) => entry.value['style']?.contains(styleName) == true)
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

  /// Get all available styles in word-by-word data
  Set<String> getAvailableStyles() {
    if (!hasWordByWordData) return {};
    
    final styles = <String>{};
    for (final data in wordByWord!.values) {
      final style = data['style'];
      if (style != null && style != 'unknown') {
        styles.add(style);
      }
    }
    return styles;
  }

  /// Check if a specific language has word-by-word data
  bool hasWordByWordForLanguage(String language) {
    return getWordPairsForLanguage(language).isNotEmpty;
  }

  /// Check if a specific style has word-by-word data
  bool hasWordByWordForStyle(String styleName) {
    return getWordPairsForStyle(styleName).isNotEmpty;
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

  /// Get word pair counts by style
  Map<String, int> getWordPairCountsByStyle() {
    if (!hasWordByWordData) return {};
    
    final counts = <String, int>{};
    
    for (final entry in wordByWord!.entries) {
      final style = entry.value['style'] ?? 'unknown';
      if (style != 'unknown') {
        counts[style] = (counts[style] ?? 0) + 1;
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

  /// Get all styles for a specific language
  List<TranslationStyle> getStylesForLanguage(String language) {
    if (styles == null) return [];
    
    return styles!.where((style) {
      // Determine language from style name
      final styleName = style.name.toLowerCase();
      final languageLower = language.toLowerCase();
      return styleName.contains(languageLower) || 
             (languageLower == 'english' && !styleName.contains('german') && !styleName.contains('spanish')) ||
             (languageLower == 'spanish' && styleName.contains('spanish'));
    }).toList();
  }

  /// Check if any style has word-by-word data
  bool hasAnyWordByWordData() {
    if (styles == null) return hasWordByWordData;
    return styles!.any((style) => style.hasWordByWord) || hasWordByWordData;
  }

  /// Get total number of selected styles
  int getTotalStyleCount() {
    if (styles != null) return styles!.length;
    
    // Count from translations if styles not available
    if (translations != null) {
      return translations!.keys
          .where((key) => !key.contains('error') && !key.contains('main'))
          .length;
    }
    
    return 0;
  }

  /// Check if this is a multi-style translation
  bool get isMultiStyle => getTotalStyleCount() > 1;

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
    List<TranslationStyle>? styles,
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
      styles: styles ?? this.styles,
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
        'wordPairCounts: ${getWordPairCounts()}, '
        'styleCount: ${getTotalStyleCount()}, '
        'isMultiStyle: $isMultiStyle'
        ')';
  }
}

/// Translation style with its specific word pairs
class TranslationStyle {
  final String name;
  final String translation;
  final List<WordPair> wordPairs;
  final bool hasWordByWord;
  
  TranslationStyle({
    required this.name,
    required this.translation,
    this.wordPairs = const [],
  }) : hasWordByWord = wordPairs.isNotEmpty;
  
  factory TranslationStyle.fromJson(Map<String, dynamic> json) {
    final pairs = <WordPair>[];
    
    print('[STYLE_JSON] Parsing TranslationStyle: ${json['name']}');
    print('[STYLE_JSON] Translation: ${json['translation']}');
    print('[STYLE_JSON] Word pairs type: ${json['word_pairs']?.runtimeType}');
    
    if (json['word_pairs'] != null && json['word_pairs'] is List) {
      final wordPairsList = json['word_pairs'] as List;
      print('[STYLE_JSON] Found ${wordPairsList.length} word pairs to parse');
      
      for (int i = 0; i < wordPairsList.length; i++) {
        final pairData = wordPairsList[i];
        print('[STYLE_JSON] Parsing word pair $i: ${pairData.runtimeType} - $pairData');
        
        try {
          if (pairData is Map<String, dynamic>) {
            // New AI format from neural optimizer - direct Map
            print('[AI_DATA] Using AI Map format: source=${pairData['source']}, spanish=${pairData['spanish']}');
            pairs.add(WordPair.fromJson(pairData));
          } else if (pairData is Map) {
            // Convert other Map types to String dynamic Map
            final convertedData = Map<String, dynamic>.from(pairData);
            print('[AI_DATA] Converted Map format: source=${convertedData['source']}, spanish=${convertedData['spanish']}');
            pairs.add(WordPair.fromJson(convertedData));
          } else {
            print('[STYLE_JSON] Unknown word pair format: ${pairData.runtimeType} - $pairData');
          }
        } catch (e) {
          print('[STYLE_JSON] Error parsing word pair $i: $e');
        }
      }
    }
    
    print('[STYLE_JSON] Successfully parsed ${pairs.length} word pairs for ${json['name']}');
    
    return TranslationStyle(
      name: json['name'] as String,
      translation: json['translation'] as String,
      wordPairs: pairs,
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'translation': translation,
      'word_pairs': wordPairs.map((p) => p.toJson()).toList(),
      'has_word_by_word': hasWordByWord,
    };
  }
  
  /// Get the language of this style
  String get language {
    final nameLower = name.toLowerCase();
    if (nameLower.contains('german')) return 'german';
    if (nameLower.contains('english')) return 'english';
    if (nameLower.contains('spanish')) return 'spanish';
    return 'unknown';
  }
  
  /// Get the style type (native, colloquial, informal, formal)
  String get styleType {
    final nameLower = name.toLowerCase();
    if (nameLower.contains('native')) return 'native';
    if (nameLower.contains('colloquial')) return 'colloquial';
    if (nameLower.contains('informal')) return 'informal';
    if (nameLower.contains('formal')) return 'formal';
    return 'unknown';
  }
  
  /// Get display color for this style
  Color get styleColor {
    switch (styleType) {
      case 'native':
        return const Color(0xFF4CAF50); // Green
      case 'colloquial':
        return const Color(0xFF2196F3); // Blue
      case 'informal':
        return const Color(0xFFFF9800); // Orange
      case 'formal':
        return const Color(0xFF9C27B0); // Purple
      default:
        return const Color(0xFF9E9E9E); // Grey
    }
  }
}

/// Word pair for multi-style support
class WordPair {
  final String sourceWord;
  final String spanishEquivalent;
  final int order;
  final bool isPhrasalVerb;
  
  WordPair({
    required this.sourceWord,
    required this.spanishEquivalent,
    this.order = 0,
    this.isPhrasalVerb = false,
  });
  
  factory WordPair.fromJson(Map<String, dynamic> json) {
    // Handle AI neural optimizer format
    final sourceWord = json['source']?.toString() ?? '';
    final spanishWord = json['spanish']?.toString() ?? '';
    final order = int.tryParse(json['order']?.toString() ?? '0') ?? 0;
    final isPhrasalVerb = json['is_phrasal_verb'] == true || json['is_phrasal_verb'] == 'true';
    
    print('[WORD_PAIR] Creating WordPair: "$sourceWord" → "$spanishWord" (order: $order, phrasal: $isPhrasalVerb)');
    
    // Check if we have real AI data or placeholder data
    if (spanishWord.contains('_es') || spanishWord == 'EMERGENCY_FALLBACK') {
      print('[WORD_PAIR_ERROR] Placeholder data detected: $spanishWord - AI sync issue!');
    } else if (spanishWord.isNotEmpty && sourceWord.isNotEmpty) {
      print('[WORD_PAIR_SUCCESS] Real AI data: $sourceWord → $spanishWord');
    }
    
    return WordPair(
      sourceWord: sourceWord,
      spanishEquivalent: spanishWord,
      order: order,
      isPhrasalVerb: isPhrasalVerb,
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'source': sourceWord,
      'spanish': spanishEquivalent,
      'order': order,
      'is_phrasal_verb': isPhrasalVerb,
    };
  }
  
  /// Get the display format for UI
  String get displayFormat => '[$sourceWord] ([$spanishEquivalent])';
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

  /// Get color for UI display based on style
  Color get styleColor {
    if (style.contains('native')) return const Color(0xFF4CAF50);
    if (style.contains('colloquial')) return const Color(0xFF2196F3);
    if (style.contains('informal')) return const Color(0xFFFF9800);
    if (style.contains('formal')) return const Color(0xFF9C27B0);
    return const Color(0xFF9E9E9E);
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
    final styleCounts = getWordPairCountsByStyle();
    final languages = getAvailableLanguages();
    final availableStyles = getAvailableStyles();
    final phrasalVerbs = getAllPhrasalVerbs();
    
    final buffer = StringBuffer();
    buffer.writeln('Word-by-Word Summary:');
    buffer.writeln('Languages: ${languages.join(', ')}');
    buffer.writeln('Styles: ${availableStyles.join(', ')}');
    buffer.writeln('Language Counts: $counts');
    buffer.writeln('Style Counts: $styleCounts');
    
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
  
  /// Get statistics about the translation
  Map<String, dynamic> getStatistics() {
    return {
      'original_length': originalText.length,
      'translated_length': translatedText.length,
      'has_audio': audioPath != null,
      'total_styles': getTotalStyleCount(),
      'is_multi_style': isMultiStyle,
      'languages': getAvailableLanguages().toList(),
      'styles': getAvailableStyles().toList(),
      'word_pair_counts': getWordPairCounts(),
      'style_word_counts': getWordPairCountsByStyle(),
      'phrasal_verb_count': getAllPhrasalVerbs().values.fold(0, (sum, list) => sum + list.length),
    };
  }
}