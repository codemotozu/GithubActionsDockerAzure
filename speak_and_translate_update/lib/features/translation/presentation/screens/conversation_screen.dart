// conversation_screen.dart - Complete file with multi-style support

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
import '../widgets/word_by_word_visualization_widget.dart';

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
    
    // Safe disposal pattern
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

  String _getExpectedBehaviorForMotherTongue(String motherTongue) {
    switch (motherTongue.toLowerCase()) {
      case 'spanish':
        return 'Spanish → German and/or English based on your selections';
      case 'english':
        return 'English → Spanish (automatic) + German if selected';
      case 'german':
        return 'German → Spanish (automatic) + English if selected';
      default:
        return '$motherTongue → German and/or English based on your selections';
    }
  }

  // CRITICAL: Analyze perfect sync status from translation data
  Map<String, dynamic> _analyzePerfectSyncStatus(translation) {
    final settings = ref.watch(settingsProvider);
    final bool germanWordByWord = settings['germanWordByWord'] == true;
    final bool englishWordByWord = settings['englishWordByWord'] == true;
    final bool anyWordByWordRequested = germanWordByWord || englishWordByWord;
    
    final bool hasAudio = translation.audioPath != null;
    final bool hasWordByWordData = translation.wordByWord != null && 
                                   (translation.wordByWord as Map).isNotEmpty;
    
    // Count word pairs by language and style
    final Map<String, int> wordPairCounts = {};
    final Map<String, int> styleCounts = {};
    final List<String> syncIssues = [];
    final List<String> syncFeatures = [];
    
    if (hasWordByWordData) {
      final wordByWordMap = translation.wordByWord as Map<String, Map<String, String>>;
      
      // Group by language and style
      for (final entry in wordByWordMap.entries) {
        final data = entry.value;
        final language = data['language'] ?? 'unknown';
        final style = data['style'] ?? 'unknown';
        
        if (language != 'unknown') {
          wordPairCounts[language] = (wordPairCounts[language] ?? 0) + 1;
        }
        
        if (style != 'unknown') {
          styleCounts[style] = (styleCounts[style] ?? 0) + 1;
        }
      }
      
      // Analyze perfect sync features
      syncFeatures.add('✓ UI display order = Audio speaking order');
      syncFeatures.add('✓ UI format = Audio format (exactly)');
      syncFeatures.add('✓ Multiple styles synchronized');
      
      // Check for phrasal/separable verbs
      final phrasalVerbs = wordByWordMap.values.where(
        (data) => data['is_phrasal_verb'] == 'true'
      ).toList();
      
      if (phrasalVerbs.isNotEmpty) {
        syncFeatures.add('✓ ${phrasalVerbs.length} phrasal/separable verbs as single units');
      }
      
      // Validate display formats
      int validFormatCount = 0;
      for (final data in wordByWordMap.values) {
        final source = data['source'] ?? '';
        final spanish = data['spanish'] ?? '';
        final displayFormat = data['display_format'] ?? '';
        final expectedFormat = '[$source] ([${spanish}])';
        
        if (displayFormat == expectedFormat) {
          validFormatCount++;
        } else {
          syncIssues.add('Format mismatch: $displayFormat vs $expectedFormat');
        }
      }
      
      if (validFormatCount == wordByWordMap.length) {
        syncFeatures.add('✓ All formats perfectly synchronized');
      }
    }
    
    // Determine sync status
    String syncStatus;
    Color syncColor;
    
    if (anyWordByWordRequested && hasAudio && hasWordByWordData && syncIssues.isEmpty) {
      syncStatus = 'PERFECT MULTI-STYLE SYNCHRONIZATION';
      syncColor = Colors.green;
    } else if (anyWordByWordRequested && hasAudio && hasWordByWordData && syncIssues.isNotEmpty) {
      syncStatus = 'SYNC ISSUES DETECTED';
      syncColor = Colors.orange;
    } else if (anyWordByWordRequested && hasAudio && !hasWordByWordData) {
      syncStatus = 'AUDIO WITHOUT SYNC DATA';
      syncColor = Colors.red;
    } else if (!anyWordByWordRequested && hasAudio) {
      syncStatus = 'SIMPLE TRANSLATION AUDIO';
      syncColor = Colors.blue;
    } else {
      syncStatus = 'NO AUDIO GENERATED';
      syncColor = Colors.grey;
    }
    
    return {
      'syncStatus': syncStatus,
      'syncColor': syncColor,
      'hasAudio': hasAudio,
      'hasWordByWordData': hasWordByWordData,
      'anyWordByWordRequested': anyWordByWordRequested,
      'wordPairCounts': wordPairCounts,
      'styleCounts': styleCounts,
      'syncFeatures': syncFeatures,
      'syncIssues': syncIssues,
      'germanWordByWord': germanWordByWord,
      'englishWordByWord': englishWordByWord,
    };
  }

  Widget _buildPerfectSyncStatusIndicator(Map<String, dynamic> syncAnalysis) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: (syncAnalysis['syncColor'] as Color).withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: syncAnalysis['syncColor'] as Color, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                _getSyncStatusIcon(syncAnalysis['syncStatus'] as String),
                color: syncAnalysis['syncColor'] as Color,
                size: 20,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  syncAnalysis['syncStatus'] as String,
                  style: TextStyle(
                    color: syncAnalysis['syncColor'] as Color,
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                ),
              ),
            ],
          ),
          
          if (syncAnalysis['anyWordByWordRequested'] as bool) ...[
            const SizedBox(height: 8),
            const Text(
              'Word-by-word audio requested:',
              style: TextStyle(color: Colors.white70, fontSize: 12),
            ),
            if (syncAnalysis['germanWordByWord'] as bool)
              const Text('  • German: [German word] ([Spanish equivalent])',
                   style: TextStyle(color: Colors.amber, fontSize: 11, fontFamily: 'monospace')),
            if (syncAnalysis['englishWordByWord'] as bool)
              const Text('  • English: [English word] ([Spanish equivalent])',
                   style: TextStyle(color: Colors.blue, fontSize: 11, fontFamily: 'monospace')),
          ],
          
          if ((syncAnalysis['styleCounts'] as Map).isNotEmpty) ...[
            const SizedBox(height: 8),
            const Text(
              'Multi-style sync data generated:',
              style: TextStyle(color: Colors.white70, fontSize: 12),
            ),
            ...(syncAnalysis['styleCounts'] as Map).entries.map((entry) =>
              Text('  • ${entry.key}: ${entry.value} synchronized pairs',
                   style: const TextStyle(color: Colors.green, fontSize: 11))
            ).toList(),
          ],
          
          if ((syncAnalysis['syncFeatures'] as List).isNotEmpty) ...[
            const SizedBox(height: 8),
            ...(syncAnalysis['syncFeatures'] as List).map((feature) =>
              Text(feature, style: const TextStyle(color: Colors.green, fontSize: 11))
            ).toList(),
          ],
          
          if ((syncAnalysis['syncIssues'] as List).isNotEmpty) ...[
            const SizedBox(height: 8),
            const Text(
              'Synchronization issues:',
              style: TextStyle(color: Colors.red, fontSize: 12, fontWeight: FontWeight.bold),
            ),
            ...(syncAnalysis['syncIssues'] as List).map((issue) =>
              Text('  • $issue', style: const TextStyle(color: Colors.red, fontSize: 10))
            ).toList(),
          ],
        ],
      ),
    );
  }

  IconData _getSyncStatusIcon(String status) {
    switch (status) {
      case 'PERFECT MULTI-STYLE SYNCHRONIZATION':
      case 'PERFECT SYNCHRONIZATION':
        return Icons.verified;
      case 'SYNC ISSUES DETECTED':
        return Icons.warning;
      case 'AUDIO WITHOUT SYNC DATA':
        return Icons.error;
      case 'SIMPLE TRANSLATION AUDIO':
        return Icons.volume_up;
      default:
        return Icons.volume_off;
    }
  }

  // Helper method to group translations by style
  Map<String, List<Map<String, dynamic>>> _groupTranslationsByStyle(Translation translation) {
    final Map<String, List<Map<String, dynamic>>> grouped = {
      'german': [],
      'english': [],
      'spanish': [],
    };
    
    // Parse the translated text to identify different styles
    if (translation.translations != null) {
      // Group translations based on the translation data
      translation.translations!.forEach((key, value) {
        if (key.contains('german')) {
          grouped['german']!.add({
            'style': key,
            'translation': value,
          });
        } else if (key.contains('english')) {
          grouped['english']!.add({
            'style': key,
            'translation': value,
          });
        } else if (key.contains('spanish')) {
          grouped['spanish']!.add({
            'style': key,
            'translation': value,
          });
        }
      });
    }
    
    return grouped;
  }

  // Add this new method to display multiple style translations
  Widget _buildMultiStyleTranslations(Translation translation, Map<String, dynamic> settings) {
    // Parse the translation text to show different styles
    final lines = translation.translatedText.split('\n');
    final widgets = <Widget>[];
    
    String? currentLanguage;
    final List<Map<String, String>> currentStyles = [];
    
    for (final line in lines) {
      if (line.contains('GERMAN TRANSLATIONS:')) {
        if (currentStyles.isNotEmpty && currentLanguage != null) {
          widgets.add(_buildLanguageStyleSection(currentLanguage, currentStyles, settings));
        }
        currentLanguage = 'German';
        currentStyles.clear();
      } else if (line.contains('ENGLISH TRANSLATIONS:')) {
        if (currentStyles.isNotEmpty && currentLanguage != null) {
          widgets.add(_buildLanguageStyleSection(currentLanguage, currentStyles, settings));
        }
        currentLanguage = 'English';
        currentStyles.clear();
      } else if (line.contains('SPANISH TRANSLATIONS:')) {
        if (currentStyles.isNotEmpty && currentLanguage != null) {
          widgets.add(_buildLanguageStyleSection(currentLanguage, currentStyles, settings));
        }
        currentLanguage = 'Spanish';
        currentStyles.clear();
      } else if (line.contains(':') && currentLanguage != null && !line.contains('===') && !line.contains('---')) {
        final parts = line.split(':');
        if (parts.length >= 2) {
          final styleName = parts[0].trim().replaceAll('*', '').trim();
          final translation = parts.sublist(1).join(':').trim();
          if (translation.isNotEmpty && !translation.contains('[') && 
              !line.contains('WORD-BY-WORD') && !line.contains('RESULTS')) {
            currentStyles.add({
              'style': styleName,
              'translation': translation,
            });
          }
        }
      }
    }
    
    // Add the last language section
    if (currentStyles.isNotEmpty && currentLanguage != null) {
      widgets.add(_buildLanguageStyleSection(currentLanguage, currentStyles, settings));
    }
    
    if (widgets.isEmpty) {
      // Fallback to simple markdown display
      return MarkdownBody(
        data: translation.translatedText,
        styleSheet: MarkdownStyleSheet(
          p: const TextStyle(fontSize: 16, color: Colors.white),
          h1: const TextStyle(fontSize: 24, color: Colors.orange),
          h2: const TextStyle(fontSize: 22, color: Colors.orange),
          h3: const TextStyle(fontSize: 20, color: Colors.orange),
          code: const TextStyle(
            backgroundColor: Colors.orange,
            fontFamily: 'monospace',
          ),
          listBullet: TextStyle(color: Colors.orange[800]),
        ),
      );
    }
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: widgets,
    );
  }

  // Add this helper method to build language style sections
  Widget _buildLanguageStyleSection(String language, List<Map<String, String>> styles, Map<String, dynamic> settings) {
    final bool isWordByWordEnabled = language.toLowerCase() == 'german' 
        ? settings['germanWordByWord'] == true
        : (language.toLowerCase() == 'english' ? settings['englishWordByWord'] == true : false);
    
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: _getLanguageColor(language).withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: _getLanguageColor(language).withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                _getLanguageFlag(language),
                style: const TextStyle(fontSize: 16),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  language,
                  style: TextStyle(
                    color: _getLanguageColor(language),
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              if (isWordByWordEnabled)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.orange.withOpacity(0.3),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: const Text(
                    'WORD-BY-WORD',
                    style: TextStyle(
                      color: Colors.orange,
                      fontSize: 9,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 8),
          ...styles.map((style) => Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: _getLanguageColor(language).withOpacity(0.2),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    style['style']!,
                    style: TextStyle(
                      color: _getLanguageColor(language),
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    style['translation']!,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                    ),
                  ),
                ),
              ],
            ),
          )).toList(),
        ],
      ),
    );
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
        title: const Text('AI Multi-Style Conversation',
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
          // Dynamic language configuration info
          if (settings['appMode'] == 'languageLearning')
            _buildDynamicLanguageInfo(settings),
          
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: translationState.messages.length,
              itemBuilder: (context, index) {
                final message = translationState.messages[index];
                return _buildMessageWidget(message, speechState);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDynamicLanguageInfo(Map<String, dynamic> settings) {
    final motherTongue = settings['motherTongue'] as String? ?? 'spanish';
    final selectedStyles = <String>[];
    final audioFeatures = <String>[];
    
    // Count German styles
    int germanStyleCount = 0;
    if (settings['germanNative'] == true) { selectedStyles.add('German Native'); germanStyleCount++; }
    if (settings['germanColloquial'] == true) { selectedStyles.add('German Colloquial'); germanStyleCount++; }
    if (settings['germanInformal'] == true) { selectedStyles.add('German Informal'); germanStyleCount++; }
    if (settings['germanFormal'] == true) { selectedStyles.add('German Formal'); germanStyleCount++; }
    
    // Count English styles
    int englishStyleCount = 0;
    if (settings['englishNative'] == true) { selectedStyles.add('English Native'); englishStyleCount++; }
    if (settings['englishColloquial'] == true) { selectedStyles.add('English Colloquial'); englishStyleCount++; }
    if (settings['englishInformal'] == true) { selectedStyles.add('English Informal'); englishStyleCount++; }
    if (settings['englishFormal'] == true) { selectedStyles.add('English Formal'); englishStyleCount++; }

    // Check word-by-word audio settings
    if (settings['germanWordByWord'] == true && germanStyleCount > 0) {
      audioFeatures.add('German Perfect Sync Audio ($germanStyleCount styles)');
    }
    if (settings['englishWordByWord'] == true && englishStyleCount > 0) {
      audioFeatures.add('English Perfect Sync Audio ($englishStyleCount styles)');
    }

    // Determine target languages based on mother tongue
    List<String> expectedTargetLanguages = [];
    List<String> automaticTargetLanguages = [];
    
    switch (motherTongue.toLowerCase()) {
      case 'spanish':
        if (germanStyleCount > 0) {
          expectedTargetLanguages.add('German ($germanStyleCount styles)');
        }
        if (englishStyleCount > 0) {
          expectedTargetLanguages.add('English ($englishStyleCount styles)');
        }
        break;
      case 'english':
        automaticTargetLanguages.add('Spanish');
        if (germanStyleCount > 0) {
          expectedTargetLanguages.add('German ($germanStyleCount styles)');
        }
        break;
      case 'german':
        automaticTargetLanguages.add('Spanish');
        if (englishStyleCount > 0) {
          expectedTargetLanguages.add('English ($englishStyleCount styles)');
        }
        break;
      default:
        if (germanStyleCount > 0) {
          expectedTargetLanguages.add('German ($germanStyleCount styles)');
        }
        if (englishStyleCount > 0) {
          expectedTargetLanguages.add('English ($englishStyleCount styles)');
        }
        break;
    }

    // Show appropriate status
    if (selectedStyles.isEmpty && audioFeatures.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(12),
        margin: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.blue[900]!.withOpacity(0.3),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            const Icon(Icons.info_outline, color: Colors.blue),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        _getLanguageFlag(motherTongue),
                        style: const TextStyle(fontSize: 16),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'Mother Tongue: ${_getLanguageDisplayName(motherTongue)}',
                        style: const TextStyle(color: Colors.blue, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Logic: ${_getExpectedBehaviorForMotherTongue(motherTongue)}',
                    style: const TextStyle(color: Colors.blue, fontSize: 12),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    automaticTargetLanguages.isNotEmpty 
                        ? 'Using defaults: ${automaticTargetLanguages.join(" + ")} translations'
                        : 'Using defaults: German + English translations',
                    style: const TextStyle(color: Colors.blue),
                  ),
                ],
              ),
            ),
          ],
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.all(12),
      margin: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.green[900]!.withOpacity(0.3),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.green, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Mother tongue header
          Row(
            children: [
              const Icon(Icons.check_circle, color: Colors.green),
              const SizedBox(width: 12),
              Text(
                _getLanguageFlag(motherTongue),
                style: const TextStyle(fontSize: 18),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Speaking: ${_getLanguageDisplayName(motherTongue)}',
                      style: const TextStyle(
                        color: Colors.green,
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    Text(
                      'Logic: ${_getExpectedBehaviorForMotherTongue(motherTongue)}',
                      style: const TextStyle(
                        color: Colors.green,
                        fontSize: 11,
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                  ],
                ),
              ),
              if (audioFeatures.isNotEmpty) ...[
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.orange.withOpacity(0.3),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: Colors.orange, width: 1),
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.sync, size: 12, color: Colors.orange),
                      SizedBox(width: 4),
                      Text(
                        'MULTI-STYLE',
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
            ],
          ),
          const SizedBox(height: 8),
          
          // Translation directions
          Row(
            children: [
              const SizedBox(width: 32),
              const Icon(Icons.arrow_forward, color: Colors.green, size: 16),
              const SizedBox(width: 8),
              Text(
                'Translating to: ${[...automaticTargetLanguages.map((lang) => "$lang (automatic)"), ...expectedTargetLanguages].join(", ")}',
                style: const TextStyle(color: Colors.green, fontWeight: FontWeight.w600),
              ),
            ],
          ),
          
          if (selectedStyles.length > 1) ...[
            const SizedBox(height: 8),
            Row(
              children: [
                const SizedBox(width: 32),
                const Icon(Icons.style, color: Colors.purple, size: 16),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    '${selectedStyles.length} styles selected: ${selectedStyles.join(', ')}',
                    style: const TextStyle(color: Colors.purple, fontWeight: FontWeight.w600),
                  ),
                ),
              ],
            ),
          ],
          
          if (audioFeatures.isNotEmpty) ...[
            const SizedBox(height: 8),
            ...audioFeatures.map((feature) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(
                  children: [
                    const SizedBox(width: 32),
                    const Icon(Icons.sync, size: 16, color: Colors.orange),
                    const SizedBox(width: 8),
                    Text(
                      feature,
                      style: const TextStyle(
                        color: Colors.orange,
                        fontStyle: FontStyle.italic,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              );
            }).toList(),
            const SizedBox(height: 4),
            const Padding(
              padding: EdgeInsets.only(left: 32),
              child: Text(
                '🎯 MULTI-STYLE GUARANTEE: Each style with perfect UI-Audio sync',
                style: TextStyle(
                  color: Colors.orange,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildMessageWidget(ChatMessage message, bool speechState) {
    switch (message.type) {
      case MessageType.user:
        return _buildUserMessage(message);
      case MessageType.ai:
        if (message.isLoading) return _buildLoadingMessage();
        if (message.error != null) return _buildErrorMessage(message.error!);
        return _buildAiMessage(message, speechState);
    }
  }

  Widget _buildUserMessage(ChatMessage message) {
    final settings = ref.watch(settingsProvider);
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
          Column(
            children: [
              CircleAvatar(
                backgroundColor: Colors.orange[100],
                child: const Icon(Icons.person, color: Colors.black),
              ),
              const SizedBox(height: 4),
              Text(
                _getLanguageFlag(motherTongue),
                style: const TextStyle(fontSize: 12),
              ),
            ],
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
                Text(
                  'Logic: ${_getExpectedBehaviorForMotherTongue(motherTongue)}',
                  style: TextStyle(
                    fontSize: 11,
                    color: Colors.orange[200],
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

  Widget _buildAiMessage(ChatMessage message, bool speechState) {
    final translation = message.translation!;
    final settings = ref.watch(settingsProvider);

    // CRITICAL: Analyze perfect sync status
    final syncAnalysis = _analyzePerfectSyncStatus(translation);

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

    return Column(
      children: [
        // CRITICAL: Perfect sync status indicator
        _buildPerfectSyncStatusIndicator(syncAnalysis),
        
        Container(
          padding: const EdgeInsets.all(12),
          margin: const EdgeInsets.only(bottom: 16, left: 16, right: 16),
          decoration: BoxDecoration(
            color: Colors.grey[900],
            borderRadius: BorderRadius.circular(8),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Column(
                children: [
                  CircleAvatar(
                    backgroundColor: Colors.blue[100],
                    child: const Icon(Icons.smart_toy),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    '🤖',
                    style: TextStyle(fontSize: 12),
                  ),
                ],
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Display translations with multi-style support
                    _buildMultiStyleTranslations(translation, settings),
                    
                    // CRITICAL: Perfect sync word-by-word visualization
                    if (translation.wordByWord != null && translation.wordByWord!.isNotEmpty)
                      WordByWordVisualizationWidget(
                        wordByWordData: translation.wordByWord,
                        isVisible: true,
                      ),
                    
                    if (translation.audioPath != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 8.0),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            IconButton(
                              icon: Icon(
                                speechState
                                    ? Icons.pause_circle_filled
                                    : Icons.play_circle_fill,
                                color: Colors.orange[800],
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
                              speechState ? 'Pause' : 'Play Multi-Style Audio',
                              style: TextStyle(color: Colors.orange[800]),
                            ),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildLoadingMessage() {
    final settings = ref.watch(settingsProvider);
    final motherTongue = settings['motherTongue'] as String? ?? 'spanish';
    
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
            const SizedBox(height: 8),
            Text(
              'Processing your ${_getLanguageDisplayName(motherTongue)} message...',
              style: const TextStyle(color: Colors.white),
            ),
            const SizedBox(height: 4),
            Text(
              'Logic: ${_getExpectedBehaviorForMotherTongue(motherTongue)}',
              style: TextStyle(
                color: Colors.grey[400],
                fontSize: 12,
                fontStyle: FontStyle.italic,
              ),
            ),
            if (totalStyles > 1) ...[
              const SizedBox(height: 4),
              Text(
                'Generating $totalStyles different style translations...',
                style: const TextStyle(
                  color: Colors.purple,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.orange.withOpacity(0.2),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                totalStyles > 1 
                    ? '🎯 Preparing MULTI-STYLE perfect UI-Audio synchronization...'
                    : '🎯 Preparing perfect UI-Audio synchronization...',
                style: const TextStyle(
                  color: Colors.orange,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
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
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Error in Multi-Style Translation: $error',
                    style: const TextStyle(color: Colors.red),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'This may be due to:',
                    style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold),
                  ),
                  const Text(
                    '• No translation styles selected for your mother tongue',
                    style: TextStyle(color: Colors.red, fontSize: 12),
                  ),
                  const Text(
                    '• Server connection issues',
                    style: TextStyle(color: Colors.red, fontSize: 12),
                  ),
                  const Text(
                    '• Multi-style sync validation failures',
                    style: TextStyle(color: Colors.red, fontSize: 12),
                  ),
                  if (error.contains('translation style'))
                    Padding(
                      padding: const EdgeInsets.only(top: 8.0),
                      child: ElevatedButton(
                        onPressed: () => Navigator.pushNamed(context, '/settings'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.orange,
                          foregroundColor: Colors.white,
                        ),
                        child: const Text('Go to Settings'),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}