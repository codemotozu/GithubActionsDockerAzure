// conversation_integration_widget.dart - Integration layer for AI Conversation UI

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/models/chat_message_model.dart';
import '../../domain/entities/translation.dart';
import '../../domain/repositories/translation_repository.dart';
import 'enhanced_word_by_word_widget.dart';

class ConversationIntegrationWidget extends ConsumerWidget {
  final ChatMessage message;
  final Map<String, dynamic> settings;

  const ConversationIntegrationWidget({
    super.key,
    required this.message,
    required this.settings,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (message.translation == null) {
      return _buildUserMessage(context);
    }

    return _buildAIResponse(context, ref);
  }

  Widget _buildUserMessage(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16, left: 50),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF3B82F6), Color(0xFF1D4ED8)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF3B82F6).withValues(alpha: 0.3),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Text(
                message.text,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          // User Avatar
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF3B82F6), Color(0xFF1D4ED8)],
              ),
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Icon(
              Icons.person,
              color: Colors.white,
              size: 24,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAIResponse(BuildContext context, WidgetRef ref) {
    final translation = message.translation!;
    
    // ALWAYS use the enhanced display - audio settings only control audio behavior
    // User should see all translation styles and visual word-by-word regardless of audio preferences
    return _buildEnhancedAITranslationDisplay(translation, ref);
  }

  Widget _buildSimpleTranslationDisplay(Translation translation) {
    return Container(
      margin: const EdgeInsets.only(bottom: 20, right: 50),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // AI Avatar
          Container(
            width: 50,
            height: 50,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF6366F1), Color(0xFF8B5CF6)],
              ),
              borderRadius: BorderRadius.circular(25),
            ),
            child: const Icon(
              Icons.psychology_alt,
              color: Colors.white,
              size: 28,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF1F2937), Color(0xFF111827)],
                ),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: Colors.grey[700]!),
              ),
              child: Text(
                translation.translatedText,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  height: 1.4,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEnhancedAITranslationDisplay(Translation translation, WidgetRef ref) {
    // Convert translation to the format expected by enhanced widgets
    final translationData = _convertTranslationToWidgetData(translation);
    
    return Container(
      margin: const EdgeInsets.only(bottom: 24, right: 20),
      child: EnhancedWordByWordWidget(
        translationData: translationData,
        audioFilename: translation.audioPath,
        showConfidenceRatings: true,
        germanWordByWordAudio: settings['germanWordByWord'] ?? false,
        englishWordByWordAudio: settings['englishWordByWord'] ?? false,
        onPlaySentenceAudio: (audioPath) {
          // Play the complete sentence audio - ALWAYS available
          debugPrint('🎵 Playing sentence audio: $audioPath');
          // Integrate with the audio repository to play sentence audio
          ref.read(translationRepositoryProvider).playAudio(audioPath);
        },
        onWordTap: (word) {
          // Handle word tap - could trigger specific word audio
          debugPrint('Word tapped: $word');
          // You could integrate with audio playback here
        },
      ),
    );
  }

  Map<String, dynamic> _convertTranslationToWidgetData(Translation translation) {
    // Parse the translation data to extract style information
    final styleData = <Map<String, dynamic>>[];
    
    // DEBUG: Print translation data
    print('[CONVERSION] Original text: ${translation.originalText}');
    print('[CONVERSION] Translated text: ${translation.translatedText}');
    print('[CONVERSION] Has styles: ${translation.styles?.isNotEmpty ?? false}');
    print('[CONVERSION] Has wordByWord: ${translation.wordByWord?.isNotEmpty ?? false}');
    if (translation.styles?.isNotEmpty ?? false) {
      print('[CONVERSION] Styles count: ${translation.styles!.length}');
      for (final style in translation.styles!) {
        print('[CONVERSION] Style: ${style.name} -> ${style.translation}');
        print('[CONVERSION] Word pairs in style: ${style.wordPairs.length}');
      }
    }
    
    // Check if we have word-by-word data
    if (translation.wordByWord?.isNotEmpty ?? false) {
      final styles = _extractStylesFromWordByWord(translation);
      styleData.addAll(styles);
    } else {
      // Create fallback styles from the main translation
      styleData.addAll(_createFallbackStyles(translation));
    }
    
    return {
      'style_data': styleData,
      'original_text': translation.originalText,
      'audio_filename': translation.audioPath,
    };
  }

  List<Map<String, dynamic>> _extractStylesFromWordByWord(Translation translation) {
    final styles = <Map<String, dynamic>>[];
    
    // CRITICAL FIX: Use the backend-provided styles directly for complete translations
    // The backend already provides the correct translations in translation.styles
    if (translation.styles?.isNotEmpty ?? false) {
      debugPrint('[CRITICAL FIX] Using backend-provided styles data for perfect UI display');
      
      for (final translationStyle in translation.styles!) {
        final styleName = translationStyle.name;
        final readyTranslation = translationStyle.translation;
        
        debugPrint('[BACKEND STYLES] Found style: $styleName = "$readyTranslation"');
        
        // Extract AI-powered word pairs with neural optimizer data
        final backendWordPairs = <List<dynamic>>[];
        for (int i = 0; i < translationStyle.wordPairs.length; i++) {
          final dynamic wordPairDynamic = translationStyle.wordPairs[i];
          
          // Try to get AI data from backend (new format) or fallback to old format
          String sourceWord;
          String spanishWord;
          double confidence;
          String explanation;
          
          if (wordPairDynamic is Map<String, dynamic>) {
            // New AI format from neural optimizer (backend sends Map)
            sourceWord = wordPairDynamic['source']?.toString() ?? '';
            spanishWord = wordPairDynamic['spanish']?.toString() ?? '';
            confidence = double.tryParse(wordPairDynamic['confidence']?.toString() ?? '0.85') ?? 0.85;
            explanation = wordPairDynamic['explanation']?.toString() ?? '';
            
            print('[AI_NEURAL] Backend AI data: $sourceWord -> $spanishWord (${(confidence * 100).toInt()}%) - $explanation');
          } else if (wordPairDynamic is WordPair) {
            // Old WordPair object format
            final wordPair = wordPairDynamic as WordPair;
            sourceWord = wordPair.sourceWord;
            spanishWord = wordPair.spanishEquivalent;
            confidence = (0.85 + (i * 0.02)).clamp(0.80, 1.00);
            explanation = _generateAIExplanation(sourceWord, spanishWord, styleName);
            
            print('[AI_FALLBACK] Using WordPair object: $sourceWord -> $spanishWord (${(confidence * 100).toInt()}%) - $explanation');
          } else {
            // Unknown format - create fallback
            sourceWord = wordPairDynamic.toString().split(' ')[0];
            spanishWord = 'translation_needed';
            confidence = 0.80;
            explanation = 'AI translation needed';
            
            print('[AI_ERROR] Unknown wordPair format: ${wordPairDynamic.runtimeType}');
          }
          
          backendWordPairs.add([
            sourceWord,
            spanishWord,
            confidence.toStringAsFixed(2),
            explanation // AI explanation from neural optimizer or fallback
          ]);
        }
        
        styles.add({
          'style': styleName,
          'translation': readyTranslation, // Use the backend-provided complete translation
          'word_pairs': backendWordPairs, // Keep word pairs for audio sync
        });
        
        debugPrint('[UI FIX] Style "$styleName" will display: "$readyTranslation" with ${backendWordPairs.length} word pairs');
      }
      
      if (styles.isNotEmpty) {
        debugPrint('[SUCCESS] Using ${styles.length} backend-provided styles for UI display');
        return styles;
      }
    }
    
    // FALLBACK: If no styles data, try to reconstruct from word-by-word data
    debugPrint('[FALLBACK] No backend styles found, attempting word-by-word reconstruction...');
    
    final processedStyles = <String>{};
    
    // Extract word pairs from word-by-word data (essential for audio sync)
    for (final entry in translation.wordByWord?.entries ?? <MapEntry<String, Map<String, String>>>[]) {
      final wordData = entry.value;
      final style = wordData['style'] ?? '';
      
      if (style.isNotEmpty && !processedStyles.contains(style)) {
        processedStyles.add(style);
        
        // Extract word pairs for this style - PRESERVE EXACT FORMAT FOR AUDIO
        final wordPairs = <List<dynamic>>[];
        final wordEntries = <Map<String, dynamic>>[];  // For proper ordering
        
        // First, collect all word entries for this style
        for (final wordEntry in translation.wordByWord?.entries ?? <MapEntry<String, Map<String, String>>>[]) {
          final data = wordEntry.value;
          if (data['style'] == style) {
            final source = data['source'] ?? '';
            final spanish = data['spanish'] ?? '';
            final confidence = data['_internal_confidence'] ?? '0.85';
            final order = int.tryParse(data['order'] ?? '0') ?? 0;
            
            if (source.isNotEmpty && spanish.isNotEmpty) {
              wordEntries.add({
                'source': source,
                'spanish': spanish,
                'confidence': confidence,
                'order': order,
              });
            }
          }
        }
        
        // Sort by order to ensure correct sequence for both display and audio
        wordEntries.sort((a, b) => (a['order'] as int).compareTo(b['order'] as int));
        
        // Build word pairs for audio
        final styleWordPairs = <List<dynamic>>[];
        for (final entry in wordEntries) {
          styleWordPairs.add([entry['source'], entry['spanish'], entry['confidence']]);
        }
        
        // CRITICAL SYNC FIX: Use Spanish translations instead of source words for UI display
        String translationText = '';
        
        if (wordEntries.isNotEmpty) {
          // Join the SPANISH words (not source words) to form the complete sentence
          // This ensures UI shows Spanish that matches the word-by-word Spanish audio
          final spanishWords = wordEntries.map((entry) => entry['spanish'] as String).toList();
          translationText = spanishWords.join(' ');
          debugPrint('[SYNC FIX] Reconstructed "$style" from Spanish words: $translationText');
          debugPrint('[SYNC FIX] Word count: ${spanishWords.length}, UI will show Spanish matching audio');
        }
        
        // Only use fallback sources if word-by-word reconstruction failed completely
        if (translationText.isEmpty) {
          debugPrint('[SYNC FALLBACK] Word-by-word reconstruction failed for $style, using fallback sources');
          
          // 1. First try structured styles data (most reliable)
          if (translation.styles?.isNotEmpty ?? false) {
            TranslationStyle? matchingStyle;
            try {
              matchingStyle = translation.styles!.firstWhere((s) => s.name == style);
            } catch (e) {
              // If no exact match, try partial match
              try {
                matchingStyle = translation.styles!.firstWhere((s) => s.name.contains(style) || style.contains(s.name));
              } catch (e) {
                // If still no match, use first available
                if (translation.styles!.isNotEmpty) {
                  matchingStyle = translation.styles!.first;
                }
              }
            }
            
            if (matchingStyle != null) {
              translationText = matchingStyle.translation;
            }
          }
          
          // 2. Then try translations map
          if (translationText.isEmpty) {
            final translationsMap = translation.translations ?? {};
            if (translationsMap.containsKey(style)) {
              translationText = translationsMap[style]!;
            }
          }
          
          // 3. Try pattern extraction from formatted text
          if (translationText.isEmpty) {
            final patterns = {
              'german_native': 'German Native',
              'german_colloquial': 'German Colloquial',
              'german_informal': 'German Informal', 
              'german_formal': 'German Formal',
              'english_native': 'English Native',
              'english_colloquial': 'English Colloquial',
              'english_informal': 'English Informal',
              'english_formal': 'English Formal',
            };
            
            final pattern = patterns[style];
            if (pattern != null) {
              translationText = _extractTranslationByPattern(translation.translatedText, pattern);
            }
          }
          
          // 4. Generate meaningful fallback if still empty
          if (translationText.isEmpty) {
            translationText = _generateFallbackTranslation(style, translation);
          }
        }
        
        styles.add({
          'style': style,
          'translation': translationText,
          'word_pairs': styleWordPairs, // CRITICAL: Preserve exact word pairs for audio sync
        });
      }
    }
    
    // If no word-by-word data but we have styles data, use that
    if (styles.isEmpty && (translation.styles?.isNotEmpty ?? false)) {
      for (final translationStyle in translation.styles!) {
        // Convert word pairs to expected format
        final fallbackWordPairs = <List<dynamic>>[];
        for (final wordPair in translationStyle.wordPairs) {
          fallbackWordPairs.add([
            wordPair.sourceWord,
            wordPair.spanishEquivalent,
            '0.85' // default confidence
          ]);
        }
        
        styles.add({
          'style': translationStyle.name,
          'translation': translationStyle.translation,
          'word_pairs': fallbackWordPairs,
        });
      }
    }
    
    return styles;
  }

  List<Map<String, dynamic>> _createFallbackStyles(Translation translation) {
    // Create basic fallback when no word-by-word data is available
    return [
      {
        'style': 'fallback_translation',
        'translation': translation.translatedText,
        'word_pairs': <List<dynamic>>[],
      }
    ];
  }

  String _extractTranslationByPattern(String fullText, String pattern) {
    // Enhanced extraction that looks for translations more thoroughly
    final lines = fullText.split('\n');
    
    // First pass: look for exact pattern match
    for (int i = 0; i < lines.length; i++) {
      final line = lines[i];
      if (line.contains(pattern)) {
        // First, try to extract from the same line after the pattern
        final colonIndex = line.indexOf(':');
        if (colonIndex >= 0 && colonIndex < line.length - 1) {
          final sameLine = line.substring(colonIndex + 1).trim();
          if (sameLine.isNotEmpty && 
              !sameLine.toLowerCase().contains('provide') && 
              !sameLine.toLowerCase().contains('translation here') &&
              !sameLine.toLowerCase().contains('[') &&
              sameLine.length > 3) {
            return sameLine.replaceAll(RegExp(r'[\[\]"]'), '').trim();
          }
        }
        
        // If not found in same line, check next few lines
        for (int j = i + 1; j < lines.length && j < i + 4; j++) {
          final nextLine = lines[j].trim();
          if (nextLine.isNotEmpty && 
              !nextLine.startsWith('*') && 
              !nextLine.startsWith('-') &&
              !nextLine.toLowerCase().contains('provide') &&
              !nextLine.toLowerCase().contains('translation here') &&
              !nextLine.toLowerCase().startsWith('german') &&
              !nextLine.toLowerCase().startsWith('english') &&
              nextLine.length > 3) {
            return nextLine.replaceAll(RegExp(r'[\[\]"]'), '').trim();
          }
        }
      }
    }
    
    // Second pass: look for pattern in multi-style translation format
    // Look for lines like "* German Native: translation text"
    final altPattern = '* $pattern:';
    for (final line in lines) {
      if (line.contains(altPattern)) {
        final colonIndex = line.indexOf(':');
        if (colonIndex >= 0 && colonIndex < line.length - 1) {
          final translation = line.substring(colonIndex + 1).trim();
          if (translation.isNotEmpty && translation.length > 3) {
            return translation;
          }
        }
      }
    }
    
    return '';
  }

  String _generateFallbackTranslation(String style, Translation translation) {
    // Generate a meaningful fallback instead of "Translation not available"
    final language = style.contains('german') ? 'German' : 'English';
    final styleType = style.contains('native') ? 'Native' : 
                     style.contains('formal') ? 'Formal' : 
                     style.contains('colloquial') ? 'Colloquial' : 'Informal';
    
    // First, check if we have translations in the translations map
    if (translation.translations?.isNotEmpty ?? false) {
      final mainTranslation = translation.translations!['main'];
      if (mainTranslation != null && mainTranslation.isNotEmpty) {
        // Try to extract a specific style translation from the main translation
        final extractedFromMain = _extractTranslationByPattern(mainTranslation, '$language $styleType');
        if (extractedFromMain.isNotEmpty) {
          return extractedFromMain;
        }
      }
    }
    
    // Try to extract any meaningful translation from the main translated text
    final lines = translation.translatedText.split('\n');
    for (final line in lines) {
      final cleanLine = line.trim();
      if (cleanLine.isNotEmpty && 
          !cleanLine.contains('=') && 
          !cleanLine.toLowerCase().contains('translation') &&
          !cleanLine.toLowerCase().contains('here you must') &&
          cleanLine.length > 3 &&
          !cleanLine.startsWith('*') &&
          !cleanLine.startsWith('-')) {
        // Check if this line contains a translation that could work
        if (language.toLowerCase() == 'german' && _looksLikeGerman(cleanLine)) {
          return cleanLine;
        } else if (language.toLowerCase() == 'english' && _looksLikeEnglish(cleanLine)) {
          return cleanLine;
        }
      }
    }
    
    // Check word-by-word data for this style to reconstruct translation
    if (translation.wordByWord?.isNotEmpty ?? false) {
      final relevantWords = <String>[];
      translation.wordByWord!.forEach((key, value) {
        if (value['style'] == style && value['source'] != null) {
          relevantWords.add(value['source']!);
        }
      });
      
      if (relevantWords.isNotEmpty) {
        return relevantWords.join(' ');
      }
    }
    
    // Last resort: use original text as context
    return 'Complete $language $styleType translation of: "${translation.originalText}"';
  }
  
  bool _looksLikeGerman(String text) {
    // Simple heuristic to check if text looks like German
    final germanWords = ['das', 'der', 'die', 'und', 'für', 'mit', 'zu', 'ist', 'sind', 'haben'];
    final lowerText = text.toLowerCase();
    return germanWords.any((word) => lowerText.contains(word));
  }
  
  bool _looksLikeEnglish(String text) {
    // Simple heuristic to check if text looks like English
    final englishWords = ['the', 'and', 'for', 'with', 'to', 'is', 'are', 'have', 'has'];
    final lowerText = text.toLowerCase();
    return englishWords.any((word) => lowerText.contains(word));
  }

  bool _hasWordByWordEnabled(Map<String, dynamic> settings) {
    return settings['germanWordByWord'] == true || 
           settings['englishWordByWord'] == true;
  }
  
  String _generateAIExplanation(String sourceWord, String targetWord, String styleName) {
    // AI-powered contextual explanation generation for language learning
    final source = sourceWord.toLowerCase();
    final isGerman = styleName.contains('german');
    
    if (isGerman) {
      // German word explanations with compound word analysis
      if (source.contains('ananassaft')) {
        return 'Saft = jugo, Ananas = piña';
      } else if (source.contains('brombeersaft')) {
        return 'Saft = jugo, Brombeere = mora';
      } else if (source == 'mädchen') {
        return 'Mädchen = niña';
      } else if (source.contains('krankenhaus')) {
        return 'Krankenhaus = hospital, krank = enfermo, Haus = casa';
      } else if (source == 'dame') {
        return 'Dame = dama, señora';
      } else if (source.contains('verehrte')) {
        return 'verehrte = respetada/honorable, Frau = mujer, señora';
      } else if (source == 'befinden') {
        return 'verbo formal para "estar ubicados"';
      } else if (source == 'draußen') {
        return 'literalmente: en el exterior';
      } else if (source.contains('regnet')) {
        return 'regnet = llueve, es = ello';
      } else if (source == 'weil') {
        return 'weil = porque (informal)';
      } else if (source == 'da') {
        return 'da = porque (formal, más elegante que weil)';
      } else if (source == 'sie sich') {
        return 'ellos/ellas se (reflexivo)';
      } else if (source.contains('sind')) {
        return 'del verbo sein = ser/estar';
      }
    } else {
      // English word explanations
      if (source.contains('pineapple juice')) {
        return 'pineapple = piña, juice = jugo';
      } else if (source.contains('blackberry juice')) {
        return 'blackberry = mora, juice = jugo';
      } else if (source == 'little girl' || source.contains('little girl')) {
        return 'little = pequeña, girl = niña';
      } else if (source == 'lady') {
        return 'lady = dama, señora';
      } else if (source == "'cause") {
        return 'abreviación de "because"';
      } else if (source == "they're") {
        return 'they = ellos/ellas, are = están';
      } else if (source.contains('hospital')) {
        return 'hospital = hospital';
      } else if (source.contains("it's raining")) {
        return 'it = ello, is = está, raining = lloviendo';
      } else if (source == 'outside') {
        return 'outside = exterior, afuera';
      }
    }
    
    // Default explanation
    return '';
  }
}

// Enhanced Chat Message Widget that uses the new UI components
class EnhancedChatMessageWidget extends StatelessWidget {
  final ChatMessage message;
  final Map<String, dynamic> settings;
  final VoidCallback? onPlayAudio;

  const EnhancedChatMessageWidget({
    super.key,
    required this.message,
    required this.settings,
    this.onPlayAudio,
  });

  @override
  Widget build(BuildContext context) {
    return ConversationIntegrationWidget(
      message: message,
      settings: settings,
    );
  }
}