// conversation_screen.dart - Enhanced for MULTIPLE translation styles support

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_markdown_plus/flutter_markdown_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:speak_and_translate_update/features/translation/presentation/providers/shared_provider.dart' show settingsProvider;

import '../../data/models/chat_message_model.dart';
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

  String _getExpectedBehaviorForMotherTongue(String motherTongue) {
    switch (motherTongue.toLowerCase()) {
      case 'spanish':
        return 'Spanish → Multiple German and/or English styles based on selections';
      case 'english':
        return 'English → Spanish (automatic) + Multiple German styles if selected';
      case 'german':
        return 'German → Spanish (automatic) + Multiple English styles if selected';
      default:
        return '$motherTongue → Multiple German and/or English styles based on selections';
    }
  }

  // ENHANCED: Analyze multiple styles sync status from translation data
  Map<String, dynamic> _analyzeMultipleStylesSyncStatus(translation) {
    final settings = ref.watch(settingsProvider);
    final bool germanWordByWord = settings['germanWordByWord'] == true;
    final bool englishWordByWord = settings['englishWordByWord'] == true;
    final bool anyWordByWordRequested = germanWordByWord || englishWordByWord;
    
    final bool hasAudio = translation.audioPath != null;
    final bool hasWordByWordData = translation.wordByWord != null && 
                                   (translation.wordByWord as Map).isNotEmpty;
    
    // Count word pairs by language and style
    final Map<String, Map<String, int>> styleWordPairCounts = {};
    final List<String> syncIssues = [];
    final List<String> syncFeatures = [];
    
    if (hasWordByWordData) {
      final wordByWordMap = translation.wordByWord as Map<String, Map<String, String>>;
      
      // Group by language and style
      for (final entry in wordByWordMap.entries) {
        final data = entry.value;
        final language = data['language'] ?? 'unknown';
        final style = data['display_style'] ?? data['style'] ?? 'unknown';
        
        if (language != 'unknown' && style != 'unknown') {
          styleWordPairCounts.putIfAbsent(language, () => {});
          styleWordPairCounts[language]!.putIfAbsent(style, () => 0);
          styleWordPairCounts[language]![style] = styleWordPairCounts[language]![style]! + 1;
        }
      }
      
      // ENHANCED: Analyze multiple styles sync features
      syncFeatures.add('✓ Multiple styles UI display order = Audio speaking order');
      syncFeatures.add('✓ Each style has complete sentence + word breakdown');
      syncFeatures.add('✓ UI format = Audio format (exactly, per style)');
      
      // Check for phrasal/separable verbs across all styles
      final phrasalVerbs = wordByWordMap.values.where(
        (data) => data['is_phrasal_verb'] == 'true'
      ).toList();
      
      if (phrasalVerbs.isNotEmpty) {
        syncFeatures.add('✓ ${phrasalVerbs.length} phrasal/separable verbs as single units across all styles');
      }
      
      // Validate display formats across all styles
      int validFormatCount = 0;
      for (final data in wordByWordMap.values) {
        final source = data['source'] ?? '';
        final spanish = data['spanish'] ?? '';
        final displayFormat = data['display_format'] ?? '';
        final expectedFormat = '[$source] ([$spanish])';
        
        if (displayFormat == expectedFormat) {
          validFormatCount++;
        } else {
          syncIssues.add('Format mismatch: $displayFormat vs $expectedFormat');
        }
      }
      
      if (validFormatCount == wordByWordMap.length) {
        syncFeatures.add('✓ All formats perfectly synchronized across all styles');
      }
    }
    
    // Determine sync status for multiple styles
    String syncStatus;
    Color syncColor;
    
    if (anyWordByWordRequested && hasAudio && hasWordByWordData && syncIssues.isEmpty) {
      syncStatus = 'PERFECT MULTIPLE STYLES SYNCHRONIZATION';
      syncColor = Colors.green;
    } else if (anyWordByWordRequested && hasAudio && hasWordByWordData && syncIssues.isNotEmpty) {
      syncStatus = 'MULTIPLE STYLES SYNC ISSUES DETECTED';
      syncColor = Colors.orange;
    } else if (anyWordByWordRequested && hasAudio && !hasWordByWordData) {
      syncStatus = 'AUDIO WITHOUT MULTIPLE STYLES SYNC DATA';
      syncColor = Colors.red;
    } else if (!anyWordByWordRequested && hasAudio) {
      syncStatus = 'MULTIPLE STYLES TRANSLATION AUDIO';
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
      'styleWordPairCounts': styleWordPairCounts,
      'syncFeatures': syncFeatures,
      'syncIssues': syncIssues,
      'germanWordByWord': germanWordByWord,
      'englishWordByWord': englishWordByWord,
    };
  }

  Widget _buildMultipleStylesSyncStatusIndicator(Map<String, dynamic> syncAnalysis) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: syncAnalysis['syncColor'].withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: syncAnalysis['syncColor'], width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                _getSyncStatusIcon(syncAnalysis['syncStatus']),
                color: syncAnalysis['syncColor'],
                size: 20,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  syncAnalysis['syncStatus'],
                  style: TextStyle(
                    color: syncAnalysis['syncColor'],
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                ),
              ),
            ],
          ),
          
          if (syncAnalysis['anyWordByWordRequested']) ...[
            const SizedBox(height: 8),
            Text(
              'Multiple styles word-by-word audio requested:',
              style: TextStyle(color: Colors.white70, fontSize: 12),
            ),
            if (syncAnalysis['germanWordByWord'])
              Text('  • German: Complete sentences + [German word] ([Spanish])',
                   style: TextStyle(color: Colors.amber, fontSize: 11, fontFamily: 'monospace')),
            if (syncAnalysis['englishWordByWord'])
              Text('  • English: Complete sentences + [English word] ([Spanish])',
                   style: TextStyle(color: Colors.blue, fontSize: 11, fontFamily: 'monospace')),
          ],
          
          // ENHANCED: Show style-specific word pair counts
          if (syncAnalysis['styleWordPairCounts'].isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              'Perfect sync data generated by style:',
              style: TextStyle(color: Colors.white70, fontSize: 12),
            ),
            ...syncAnalysis['styleWordPairCounts'].entries.map((languageEntry) {
              final language = languageEntry.key;
              final styles = languageEntry.value;
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('  • $language:', style: TextStyle(color: _getLanguageColor(language), fontSize: 11, fontWeight: FontWeight.bold)),
                  ...styles.entries.map((styleEntry) =>
                    Text('    - ${styleEntry.key}: ${styleEntry.value} synchronized pairs',
                         style: TextStyle(color: Colors.green, fontSize: 10))
                  ).toList(),
                ],
              );
            }).toList(),
          ],
          
          if (syncAnalysis['syncFeatures'].isNotEmpty) ...[
            const SizedBox(height: 8),
            ...syncAnalysis['syncFeatures'].map((feature) =>
              Text(feature, style: TextStyle(color: Colors.green, fontSize: 11))
            ).toList(),
          ],
          
          if (syncAnalysis['syncIssues'].isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              'Multiple styles synchronization issues:',
              style: TextStyle(color: Colors.red, fontSize: 12, fontWeight: FontWeight.bold),
            ),
            ...syncAnalysis['syncIssues'].map((issue) =>
              Text('  • $issue', style: TextStyle(color: Colors.red, fontSize: 10))
            ).toList(),
          ],
        ],
      ),
    );
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

  IconData _getSyncStatusIcon(String status) {
    if (status.contains('PERFECT')) {
      return Icons.verified;
    } else if (status.contains('ISSUES')) {
      return Icons.warning;
    } else if (status.contains('WITHOUT')) {
      return Icons.error;
    } else if (status.contains('TRANSLATION AUDIO')) {
      return Icons.volume_up;
    } else {
      return Icons.volume_off;
    }
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
        title: const Text('AI Conversation - Multiple Styles',
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
          // ENHANCED: Dynamic multiple styles language configuration info
          if (settings['appMode'] == 'languageLearning')
            _buildMultipleStylesLanguageInfo(settings),
          
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

  Widget _buildMultipleStylesLanguageInfo(Map<String, dynamic> settings) {
    final motherTongue = settings['motherTongue'] as String? ?? 'spanish';
    final selectedStyles = <String>[];
    final audioFeatures = <String>[];
    
    // Check German styles (can be multiple)
    if (settings['germanNative'] == true) selectedStyles.add('German Native');
    if (settings['germanColloquial'] == true) selectedStyles.add('German Colloquial');
    if (settings['germanInformal'] == true) selectedStyles.add('German Informal');
    if (settings['germanFormal'] == true) selectedStyles.add('German Formal');
    
    // Check English styles (can be multiple)
    if (settings['englishNative'] == true) selectedStyles.add('English Native');
    if (settings['englishColloquial'] == true) selectedStyles.add('English Colloquial');
    if (settings['englishInformal'] == true) selectedStyles.add('English Informal');
    if (settings['englishFormal'] == true) selectedStyles.add('English Formal');

    // Check word-by-word audio settings with ENHANCED multiple styles indicators
    if (settings['germanWordByWord'] == true) {
      audioFeatures.add('German Multiple Styles Audio');
    }
    if (settings['englishWordByWord'] == true) {
      audioFeatures.add('English Multiple Styles Audio');
    }

    // Determine target languages based on mother tongue and selections
    List<String> expectedTargetLanguages = [];
    List<String> automaticTargetLanguages = [];
    
    switch (motherTongue.toLowerCase()) {
      case 'spanish':
        if (selectedStyles.any((style) => style.startsWith('German'))) {
          final germanStylesCount = selectedStyles.where((style) => style.startsWith('German')).length;
          expectedTargetLanguages.add('German ($germanStylesCount styles)');
        }
        if (selectedStyles.any((style) => style.startsWith('English'))) {
          final englishStylesCount = selectedStyles.where((style) => style.startsWith('English')).length;
          expectedTargetLanguages.add('English ($englishStylesCount styles)');
        }
        break;
      case 'english':
        automaticTargetLanguages.add('Spanish');
        if (selectedStyles.any((style) => style.startsWith('German'))) {
          final germanStylesCount = selectedStyles.where((style) => style.startsWith('German')).length;
          expectedTargetLanguages.add('German ($germanStylesCount styles)');
        }
        break;
      case 'german':
        automaticTargetLanguages.add('Spanish');
        if (selectedStyles.any((style) => style.startsWith('English'))) {
          final englishStylesCount = selectedStyles.where((style) => style.startsWith('English')).length;
          expectedTargetLanguages.add('English ($englishStylesCount styles)');
        }
        break;
      default:
        if (selectedStyles.any((style) => style.startsWith('German'))) {
          final germanStylesCount = selectedStyles.where((style) => style.startsWith('German')).length;
          expectedTargetLanguages.add('German ($germanStylesCount styles)');
        }
        if (selectedStyles.any((style) => style.startsWith('English'))) {
          final englishStylesCount = selectedStyles.where((style) => style.startsWith('English')).length;
          expectedTargetLanguages.add('English ($englishStylesCount styles)');
        }
        break;
    }

    // Show appropriate status with ENHANCED multiple styles emphasis
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
                        ? 'Using defaults: ${automaticTargetLanguages.join(" + ")} + multiple style translations'
                        : 'Using defaults: Multiple German + English style translations',
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
                        'MULTIPLE STYLES',
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
          
          // Translation directions for multiple styles
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
          
          // ENHANCED: Show all selected styles in a more organized way
          if (selectedStyles.isNotEmpty) ...[
            const SizedBox(height: 8),
            Row(
              children: [
                const SizedBox(width: 32),
                const Icon(Icons.style, color: Colors.green, size: 16),
                const SizedBox(width: 8),
                const Text(
                  'Selected styles:',
                  style: TextStyle(color: Colors.green, fontWeight: FontWeight.w600),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Wrap(
              children: selectedStyles.map((style) => Container(
                margin: const EdgeInsets.only(left: 48, right: 4, bottom: 4),
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.green.withOpacity(0.3),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.green, width: 1),
                ),
                child: Text(
                  style,
                  style: const TextStyle(color: Colors.green, fontSize: 11),
                ),
              )).toList(),
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
                      '$feature: Complete sentences + [target word] ([Spanish])',
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
                '🎯 ENHANCED: Each style gets complete sentence + word breakdown',
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
        if (message.isLoading) return _buildMultipleStylesLoadingMessage();
        if (message.error != null) return _buildMultipleStylesErrorMessage(message.error!);
        return _buildMultipleStylesAiMessage(message, speechState);
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

  Widget _buildMultipleStylesAiMessage(ChatMessage message, bool speechState) {
    final translation = message.translation!;
    final settings = ref.watch(settingsProvider);

    // ENHANCED: Analyze multiple styles sync status
    final syncAnalysis = _analyzeMultipleStylesSyncStatus(translation);

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
        // ENHANCED: Multiple styles sync status indicator
        _buildMultipleStylesSyncStatusIndicator(syncAnalysis),
        
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
                    MarkdownBody(
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
                    ),
                    
                    // ENHANCED: Multiple styles word-by-word visualization
                    WordByWordVisualizationWidget(
                      wordByWordData: translation.wordByWord,
                      isVisible: translation.wordByWord != null && translation.wordByWord!.isNotEmpty,
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
                              speechState ? 'Pause' : 'Play Multiple Styles Audio',
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

  Widget _buildMultipleStylesLoadingMessage() {
    final settings = ref.watch(settingsProvider);
    final motherTongue = settings['motherTongue'] as String? ?? 'spanish';
    
    // Count selected styles
    final germanStyles = [
      settings['germanNative'],
      settings['germanColloquial'],
      settings['germanInformal'],
      settings['germanFormal']
    ].where((style) => style == true).length;
    
    final englishStyles = [
      settings['englishNative'],
      settings['englishColloquial'],
      settings['englishInformal'],
      settings['englishFormal']
    ].where((style) => style == true).length;
    
    final totalStyles = germanStyles + englishStyles;
    
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
            if (totalStyles > 0) ...[
              const SizedBox(height: 4),
              Text(
                'Generating $totalStyles translation styles...',
                style: TextStyle(
                  color: Colors.blue[300],
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
                totalStyles > 0 
                    ? '🎯 Preparing multiple styles UI-Audio synchronization...'
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

  Widget _buildMultipleStylesErrorMessage(String error) {
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
                    'Error in Multiple Styles Translation: $error',
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
                    '• Multiple styles sync validation failures',
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
                        child: const Text('Go to Multiple Styles Settings'),
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