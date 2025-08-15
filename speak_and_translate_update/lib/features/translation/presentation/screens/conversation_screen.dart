// conversation_screen.dart - Complete Multi-Style Support with Perfect Sync..............................
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_markdown_plus/flutter_markdown_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:speak_and_translate_update/features/translation/presentation/providers/shared_provider.dart' show settingsProvider;

import '../../data/models/chat_message_model.dart';
import '../../domain/entities/translation.dart';
import '../../domain/repositories/translation_repository.dart';
import '../providers/speech_provider.dart';
import '../providers/translation_provider.dart';

class ConversationScreen extends ConsumerStatefulWidget {
  final String prompt;

  const ConversationScreen({
    super.key,
    required this.prompt,
  });

  @override
  ConsumerState<ConversationScreen> createState() => _ConversationScreenState();
}

class _ConversationScreenState extends ConsumerState<ConversationScreen> {
  final ScrollController _scrollController = ScrollController();
  bool _isPlayingAudio = false;
  int _currentPlayingStyleIndex = -1;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (widget.prompt.isNotEmpty) {
        ref.read(translationProvider.notifier).startConversation(widget.prompt);
      }
    });
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  void dispose() {
    _scrollController.dispose();
    
    final shouldStopSpeech = mounted;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (shouldStopSpeech && mounted) {
        try {
          ref.read(speechProvider.notifier).stop();
        } catch (e) {
          print('Safe disposal error: $e');
        }
      }
    });
    
    super.dispose();
  }

  // Helper methods for language display
  String _getLanguageDisplayName(String languageCode) {
    switch (languageCode.toLowerCase()) {
      case 'spanish':
      case 'es':
        return 'Spanish (Español)';
      case 'english':
      case 'en':
        return 'English';
      case 'german':
      case 'de':
        return 'German (Deutsch)';
      case 'french':
      case 'fr':
        return 'French (Français)';
      case 'italian':
      case 'it':
        return 'Italian (Italiano)';
      case 'portuguese':
      case 'pt':
        return 'Portuguese (Português)';
      default:
        return languageCode.toUpperCase();
    }
  }

  String _getLanguageFlag(String languageCode) {
    switch (languageCode.toLowerCase()) {
      case 'spanish':
      case 'es':
        return '🇪🇸';
      case 'english':
      case 'en':
        return '🇺🇸';
      case 'german':
      case 'de':
        return '🇩🇪';
      case 'french':
      case 'fr':
        return '🇫🇷';
      case 'italian':
      case 'it':
        return '🇮🇹';
      case 'portuguese':
      case 'pt':
        return '🇵🇹';
      default:
        return '🌐';
    }
  }

  Color _getLanguageColor(String language) {
    switch (language.toLowerCase()) {
      case 'german':
        return Colors.amber;
      case 'english':
        return Colors.blue;
      case 'spanish':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }

  Color _getStyleColor(String styleName) {
    if (styleName.contains('native')) return const Color(0xFF4CAF50);
    if (styleName.contains('colloquial')) return const Color(0xFF2196F3);
    if (styleName.contains('informal')) return const Color(0xFFFF9800);
    if (styleName.contains('formal')) return const Color(0xFF9C27B0);
    return const Color(0xFF9E9E9E);
  }

  String _getStyleDisplayName(String styleName) {
    return styleName.replaceAll('_', ' ').split(' ').map((word) {
      if (word.isEmpty) return word;
      return word[0].toUpperCase() + word.substring(1);
    }).join(' ');
  }

  // Parse multi-style translations from the response
  List<StyleTranslation> _parseMultiStyleTranslations(Translation translation) {
    List<StyleTranslation> styles = [];
    
    // Parse from the translated text
    final lines = translation.translatedText.split('\n');
    String? currentLanguage;
    
    for (int i = 0; i < lines.length; i++) {
      final line = lines[i].trim();
      
      if (line.contains('GERMAN TRANSLATIONS:')) {
        currentLanguage = 'german';
      } else if (line.contains('ENGLISH TRANSLATIONS:')) {
        currentLanguage = 'english';
      } else if (line.contains('SPANISH TRANSLATIONS:')) {
        currentLanguage = 'spanish';
      } else if (line.startsWith('*') && currentLanguage != null) {
        // Parse style line
        final parts = line.substring(1).trim().split(':');
        if (parts.length >= 2) {
          final styleName = parts[0].trim();
          final translationText = parts.sublist(1).join(':').trim();
          
          // Check if we have word-by-word data for this style
          final wordByWordData = _getWordByWordForStyle(
            translation.wordByWord, 
            styleName.toLowerCase().replaceAll(' ', '_')
          );
          
          styles.add(StyleTranslation(
            language: currentLanguage,
            styleName: styleName,
            translation: translationText,
            wordByWordData: wordByWordData,
            hasWordByWord: wordByWordData.isNotEmpty,
          ));
        }
      }
    }
    
    return styles;
  }

  // Get word-by-word data for a specific style
  Map<String, Map<String, String>> _getWordByWordForStyle(
    Map<String, Map<String, String>>? allWordByWord,
    String styleName
  ) {
    if (allWordByWord == null) return {};
    
    final styleData = <String, Map<String, String>>{};
    
    allWordByWord.forEach((key, value) {
      if (value['style'] == styleName) {
        styleData[key] = value;
      }
    });
    
    return styleData;
  }

  // Build multi-style translation display
  Widget _buildMultiStyleTranslationDisplay(
    Translation translation,
    Map<String, dynamic> settings
  ) {
    final styles = _parseMultiStyleTranslations(translation);
    
    if (styles.isEmpty) {
      // Fallback to simple display
      return MarkdownBody(
        data: translation.translatedText,
        styleSheet: MarkdownStyleSheet(
          p: const TextStyle(fontSize: 16, color: Colors.white),
        ),
      );
    }
    
    // Group styles by language
    final Map<String, List<StyleTranslation>> groupedStyles = {};
    for (final style in styles) {
      groupedStyles.putIfAbsent(style.language, () => []);
      groupedStyles[style.language]!.add(style);
    }
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Display each language group
        ...groupedStyles.entries.map((entry) {
          final language = entry.key;
          final languageStyles = entry.value;
          final isWordByWordEnabled = language == 'german' 
              ? settings['germanWordByWord'] == true
              : (language == 'english' ? settings['englishWordByWord'] == true : false);
          
          return _buildLanguageSection(
            language: language,
            styles: languageStyles,
            isWordByWordEnabled: isWordByWordEnabled,
            onPlayStyle: (styleIndex) => _playStyleAudio(styleIndex, languageStyles),
          );
        }),
      ],
    );
  }

  // Build language section with multiple styles
  Widget _buildLanguageSection({
    required String language,
    required List<StyleTranslation> styles,
    required bool isWordByWordEnabled,
    required Function(int) onPlayStyle,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: _getLanguageColor(language).withOpacity(0.05),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: _getLanguageColor(language).withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Language header
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: _getLanguageColor(language).withOpacity(0.1),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
            ),
            child: Row(
              children: [
                Text(
                  _getLanguageFlag(language),
                  style: const TextStyle(fontSize: 20),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    _getLanguageDisplayName(language),
                    style: TextStyle(
                      color: _getLanguageColor(language),
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                if (isWordByWordEnabled)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.orange.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: Colors.orange, width: 1),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.sync, size: 14, color: Colors.orange),
                        SizedBox(width: 4),
                        Text(
                          'WORD-BY-WORD',
                          style: TextStyle(
                            color: Colors.orange,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
          
          // Display each style
          Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              children: styles.asMap().entries.map((entry) {
                final index = entry.key;
                final style = entry.value;
                return _buildStyleCard(
                  style: style,
                  isPlaying: _isPlayingAudio && _currentPlayingStyleIndex == index,
                  onPlay: () => onPlayStyle(index),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }


// Build individual style card - UPDATED: Play icons removed
Widget _buildStyleCard({
  required StyleTranslation style,
  required bool isPlaying,
  required VoidCallback onPlay,
}) {
  return Container(
    margin: const EdgeInsets.only(bottom: 12),
    decoration: BoxDecoration(
      color: Colors.white.withOpacity(0.05),
      borderRadius: BorderRadius.circular(8),
      border: Border.all(
        color: _getStyleColor(style.styleName).withOpacity(0.5),
        width: 1,
      ),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Style header WITHOUT play button
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: _getStyleColor(style.styleName).withOpacity(0.1),
            borderRadius: const BorderRadius.vertical(top: Radius.circular(8)),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: _getStyleColor(style.styleName).withOpacity(0.3),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  _getStyleDisplayName(style.styleName),
                  style: TextStyle(
                    color: _getStyleColor(style.styleName),
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              const Spacer(),
              // REMOVED: Play button IconButton completely removed
            ],
          ),
        ),
        
        // Translation text
        Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                style.translation,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 15,
                  height: 1.4,
                ),
              ),
              
              // Word-by-word visualization if available
              if (style.hasWordByWord && style.wordByWordData.isNotEmpty) ...[
                const SizedBox(height: 12),
                _buildWordByWordVisualization(style.wordByWordData),
              ],
            ],
          ),
        ),
      ],
    ),
  );
}

  // Build word-by-word visualization for a style
  Widget _buildWordByWordVisualization(Map<String, Map<String, String>> wordByWordData) {
    // Sort by order
    final sortedEntries = wordByWordData.entries.toList()
      ..sort((a, b) {
        final orderA = int.tryParse(a.value['order'] ?? '0') ?? 0;
        final orderB = int.tryParse(b.value['order'] ?? '0') ?? 0;
        return orderA.compareTo(orderB);
      });
    
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.3),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.orange.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.hearing, size: 16, color: Colors.orange),
              const SizedBox(width: 8),
              const Text(
                'Word-by-Word Audio Format',
                style: TextStyle(
                  color: Colors.orange,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: sortedEntries.map((entry) {
              final data = entry.value;
              final displayFormat = data['display_format'] ?? '';
              final isPhrasalVerb = data['is_phrasal_verb'] == 'true';
              
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.orange.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: isPhrasalVerb ? Colors.red : Colors.orange,
                    width: isPhrasalVerb ? 2 : 1,
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (isPhrasalVerb)
                      const Icon(Icons.link, size: 14, color: Colors.red),
                    if (isPhrasalVerb)
                      const SizedBox(width: 4),
                    Text(
                      displayFormat,
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontFamily: 'monospace',
                        fontWeight: isPhrasalVerb ? FontWeight.bold : FontWeight.normal,
                      ),
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  // Play audio for a specific style
  Future<void> _playStyleAudio(int styleIndex, List<StyleTranslation> styles) async {
    // Implementation for playing specific style audio
    setState(() {
      _isPlayingAudio = true;
      _currentPlayingStyleIndex = styleIndex;
    });
    
    // Simulate audio playback
    await Future.delayed(const Duration(seconds: 3));
    
    setState(() {
      _isPlayingAudio = false;
      _currentPlayingStyleIndex = -1;
    });
  }

  @override
  Widget build(BuildContext context) {
    final translationState = ref.watch(translationProvider);
    final speechState = ref.watch(speechProvider);
    final settings = ref.watch(settingsProvider);

    return Scaffold(
      backgroundColor: const Color(0xFF000000),
      appBar: AppBar(
        centerTitle: true,
        backgroundColor: const Color(0xFF1C1C1E),
        title: const Text('Multi-Style AI Conversation',
            style: TextStyle(color: Colors.white)),
        actions: [
          IconButton(
            icon: const Icon(Icons.delete, color: Colors.white),
            onPressed: () =>
                ref.read(translationProvider.notifier).clearConversation(),
            tooltip: 'Clear history',
          ),
          IconButton(
            icon: Icon(
              speechState ? Icons.volume_up : Icons.volume_off,
              color: speechState ? Colors.white : Colors.grey,
            ),
            onPressed: () =>
                ref.read(speechProvider.notifier).toggleHandsFreeMode(),
            tooltip: speechState ? 'Disable audio' : 'Enable audio',
          ),
          IconButton(
            icon: const Icon(Icons.settings, color: Colors.white),
            onPressed: () => Navigator.pushNamed(context, '/settings'),
            tooltip: 'Settings',
          ),
        ],
      ),
      body: Column(
        children: [
          // Multi-style info header
          if (settings['appMode'] == 'languageLearning')
            _buildMultiStyleInfoHeader(settings),
          
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: translationState.messages.length,
              itemBuilder: (context, index) {
                final message = translationState.messages[index];
                return _buildMessageWidget(message, speechState, settings);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMultiStyleInfoHeader(Map<String, dynamic> settings) {
    final motherTongue = settings['motherTongue'] as String? ?? 'spanish';
    
    // Count selected styles
    int germanStyleCount = 0;
    if (settings['germanNative'] == true) germanStyleCount++;
    if (settings['germanColloquial'] == true) germanStyleCount++;
    if (settings['germanInformal'] == true) germanStyleCount++;
    if (settings['germanFormal'] == true) germanStyleCount++;
    
    int englishStyleCount = 0;
    if (settings['englishNative'] == true) englishStyleCount++;
    if (settings['englishColloquial'] == true) englishStyleCount++;
    if (settings['englishInformal'] == true) englishStyleCount++;
    if (settings['englishFormal'] == true) englishStyleCount++;
    
    final totalStyles = germanStyleCount + englishStyleCount;
    
    if (totalStyles == 0) return const SizedBox.shrink();
    
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.purple[900]!.withOpacity(0.3), Colors.blue[900]!.withOpacity(0.3)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.purple, width: 1),
      ),
      child: Row(
        children: [
          const Icon(Icons.style, color: Colors.purple, size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Multi-Style Translation Active',
                  style: const TextStyle(
                    color: Colors.purple,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '$totalStyles styles selected (German: $germanStyleCount, English: $englishStyleCount)',
                  style: const TextStyle(
                    color: Colors.white70,
                    fontSize: 12,
                  ),
                ),
                if (settings['germanWordByWord'] == true || settings['englishWordByWord'] == true)
                  const Text(
                    '🎯 Perfect UI-Audio sync enabled',
                    style: TextStyle(
                      color: Colors.orange,
                      fontSize: 11,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageWidget(ChatMessage message, bool speechState, Map<String, dynamic> settings) {
    switch (message.type) {
      case MessageType.user:
        return _buildUserMessage(message, settings);
      case MessageType.ai:
        if (message.isLoading) return _buildLoadingMessage(settings);
        if (message.error != null) return _buildErrorMessage(message.error!);
        return _buildAiMessage(message, speechState, settings);
    }
  }

  Widget _buildUserMessage(ChatMessage message, Map<String, dynamic> settings) {
    final motherTongue = settings['motherTongue'] as String? ?? 'spanish';
    
    return Container(
      padding: const EdgeInsets.all(12),
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.grey[900],
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CircleAvatar(
            backgroundColor: Colors.orange[100],
            child: const Icon(Icons.person, color: Colors.black),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  message.text,
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                    color: Colors.orange[700],
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Speaking in ${_getLanguageDisplayName(motherTongue)}',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.orange[300],
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAiMessage(ChatMessage message, bool speechState, Map<String, dynamic> settings) {
    final translation = message.translation!;

    if (speechState && translation.audioPath != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) async {
        try {
          await ref
              .read(speechProvider.notifier)
              .playAudio(translation.audioPath);
          ref.read(translationProvider.notifier).clearConversation();

          if (mounted) {
            Navigator.pop(context);
            WidgetsBinding.instance.addPostFrameCallback((_) {
              ref.read(translationRepositoryProvider).playCompletionSound();
            });
          }
        } catch (e) {
          print('Error handling audio completion: $e');
        }
      });
    }

    return Container(
      padding: const EdgeInsets.all(12),
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.grey[900],
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CircleAvatar(
            backgroundColor: Colors.blue[100],
            child: const Icon(Icons.smart_toy),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Multi-style translation display
                _buildMultiStyleTranslationDisplay(translation, settings),
                
                // Global audio control if available
                if (translation.audioPath != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 12),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        IconButton(
                          icon: Icon(
                            speechState
                                ? Icons.pause_circle_filled
                                : Icons.play_circle_fill,
                            color: Colors.orange[800],
                            size: 32,
                          ),
                          onPressed: () {
                            if (speechState) {
                              ref.read(speechProvider.notifier).stop();
                            } else {
                              ref
                                  .read(speechProvider.notifier)
                                  .playAudio(translation.audioPath);
                            }
                          },
                        ),
                        Text(
                          speechState ? 'Pause All Styles' : 'Play All Styles',
                          style: TextStyle(
                            color: Colors.orange[800],
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLoadingMessage(Map<String, dynamic> settings) {
    // Count selected styles
    int totalStyles = 0;
    if (settings['germanNative'] == true) totalStyles++;
    if (settings['germanColloquial'] == true) totalStyles++;
    if (settings['germanInformal'] == true) totalStyles++;
    if (settings['germanFormal'] == true) totalStyles++;
    if (settings['englishNative'] == true) totalStyles++;
    if (settings['englishColloquial'] == true) totalStyles++;
    if (settings['englishInformal'] == true) totalStyles++;
    if (settings['englishFormal'] == true) totalStyles++;
    
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16.0),
      child: Center(
        child: Column(
          children: [
            const CircularProgressIndicator(),
            const SizedBox(height: 12),
            Text(
              'Generating $totalStyles style${totalStyles > 1 ? 's' : ''}...',
              style: const TextStyle(color: Colors.white),
            ),
            if (totalStyles > 1)
              const Text(
                'Perfect multi-style synchronization in progress',
                style: TextStyle(
                  color: Colors.orange,
                  fontSize: 12,
                  fontStyle: FontStyle.italic,
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorMessage(String error) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16.0),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.red[900]!.withOpacity(0.3),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            const Icon(Icons.error_outline, color: Colors.red),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                'Error: $error',
                style: const TextStyle(color: Colors.red),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// Model class for style translations
class StyleTranslation {
  final String language;
  final String styleName;
  final String translation;
  final Map<String, Map<String, String>> wordByWordData;
  final bool hasWordByWord;

  StyleTranslation({
    required this.language,
    required this.styleName,
    required this.translation,
    required this.wordByWordData,
    required this.hasWordByWord,
  });
}







































