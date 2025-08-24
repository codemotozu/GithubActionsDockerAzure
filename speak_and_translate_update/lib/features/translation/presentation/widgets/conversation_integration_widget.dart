// conversation_integration_widget.dart - Integration layer for AI Conversation UI

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/models/chat_message_model.dart';
import '../../domain/entities/translation.dart';
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
    
    // Check if user has word-by-word enabled
    final hasWordByWordEnabled = _hasWordByWordEnabled(settings);
    
    if (!hasWordByWordEnabled) {
      return _buildSimpleTranslationDisplay(translation);
    }

    // Use the new AI conversation interface for word-by-word
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
    final processedStyles = <String>{};
    
    for (final entry in translation.wordByWord?.entries ?? <MapEntry<String, Map<String, String>>>[]) {
      final wordData = entry.value;
      final style = wordData['style'] ?? '';
      
      if (style.isNotEmpty && !processedStyles.contains(style)) {
        processedStyles.add(style);
        
        // Extract word pairs for this style
        final wordPairs = <List<dynamic>>[];
        for (final wordEntry in translation.wordByWord?.entries ?? <MapEntry<String, Map<String, String>>>[]) {
          final data = wordEntry.value;
          if (data['style'] == style) {
            final source = data['source'] ?? '';
            final spanish = data['spanish'] ?? '';
            final confidence = data['_internal_confidence'] ?? '0.85';
            
            if (source.isNotEmpty && spanish.isNotEmpty) {
              wordPairs.add([source, spanish, confidence]);
            }
          }
        }
        
        // Get translation text for this style
        String translationText = '';
        if (style.contains('german_native')) {
          translationText = _extractTranslationByPattern(translation.translatedText, 'German Native');
        } else if (style.contains('german_formal')) {
          translationText = _extractTranslationByPattern(translation.translatedText, 'German Formal');
        } else if (style.contains('english_native')) {
          translationText = _extractTranslationByPattern(translation.translatedText, 'English Native');
        } else if (style.contains('english_formal')) {
          translationText = _extractTranslationByPattern(translation.translatedText, 'English Formal');
        }
        
        styles.add({
          'style': style,
          'translation': translationText.isNotEmpty ? translationText : 'Translation not available',
          'word_pairs': wordPairs,
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
    // Simple extraction - in a real implementation, you'd parse the structured response
    final lines = fullText.split('\n');
    for (int i = 0; i < lines.length; i++) {
      if (lines[i].contains(pattern) && i + 1 < lines.length) {
        // Return the next non-empty line after the pattern
        for (int j = i + 1; j < lines.length; j++) {
          final line = lines[j].trim();
          if (line.isNotEmpty && !line.startsWith('*') && !line.startsWith('-')) {
            return line.replaceAll(RegExp(r'^\*\s*'), '').trim();
          }
        }
      }
    }
    return '';
  }

  bool _hasWordByWordEnabled(Map<String, dynamic> settings) {
    return settings['germanWordByWord'] == true || 
           settings['englishWordByWord'] == true;
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