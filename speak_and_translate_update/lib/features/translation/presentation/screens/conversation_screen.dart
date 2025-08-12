// Updated conversation_screen.dart with word-by-word visualization matching audio

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
    
    // Use this pattern for safe ref access
    final shouldStopSpeech = mounted;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (shouldStopSpeech && mounted) { // Double-check mounted status
        try {
          ref.read(speechProvider.notifier).stop();
        } catch (e) {
          print('Safe disposal error: $e');
        }
      }
    });
    
    super.dispose();
  }

  // Helper method to get language display name
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

  // Helper method to get language flag emoji
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

  // EXACT per requirements: Get expected behavior for mother tongue
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
        title: const Text('AI Conversation',
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
          // EXACT per requirements: Show dynamic language configuration info
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
    
    // Check German styles
    if (settings['germanNative'] == true) selectedStyles.add('German Native');
    if (settings['germanColloquial'] == true) selectedStyles.add('German Colloquial');
    if (settings['germanInformal'] == true) selectedStyles.add('German Informal');
    if (settings['germanFormal'] == true) selectedStyles.add('German Formal');
    
    // Check English styles
    if (settings['englishNative'] == true) selectedStyles.add('English Native');
    if (settings['englishColloquial'] == true) selectedStyles.add('English Colloquial');
    if (settings['englishInformal'] == true) selectedStyles.add('English Informal');
    if (settings['englishFormal'] == true) selectedStyles.add('English Formal');

    // Check word-by-word audio settings
    if (settings['germanWordByWord'] == true) {
      audioFeatures.add('German Word-by-Word Audio');
    }
    if (settings['englishWordByWord'] == true) {
      audioFeatures.add('English Word-by-Word Audio');
    }

    // EXACT per requirements: Determine target languages based on mother tongue
    List<String> expectedTargetLanguages = [];
    List<String> automaticTargetLanguages = [];
    
    switch (motherTongue.toLowerCase()) {
      case 'spanish':
        // EXACT: Spanish → German and/or English based on selections
        if (selectedStyles.any((style) => style.startsWith('German'))) {
          expectedTargetLanguages.add('German');
        }
        if (selectedStyles.any((style) => style.startsWith('English'))) {
          expectedTargetLanguages.add('English');
        }
        break;
      case 'english':
        // EXACT: English → Spanish (automatic) + German if selected
        automaticTargetLanguages.add('Spanish');
        if (selectedStyles.any((style) => style.startsWith('German'))) {
          expectedTargetLanguages.add('German');
        }
        break;
      case 'german':
        // EXACT: German → Spanish (automatic) + English if selected
        automaticTargetLanguages.add('Spanish');
        if (selectedStyles.any((style) => style.startsWith('English'))) {
          expectedTargetLanguages.add('English');
        }
        break;
      default:
        // Other languages → German and/or English based on selections
        if (selectedStyles.any((style) => style.startsWith('German'))) {
          expectedTargetLanguages.add('German');
        }
        if (selectedStyles.any((style) => style.startsWith('English'))) {
          expectedTargetLanguages.add('English');
        }
        break;
    }

    // EXACT per requirements: Show appropriate status
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
                    'EXACT Logic: ${_getExpectedBehaviorForMotherTongue(motherTongue)}',
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
          // Mother tongue header with EXACT logic
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
                      'EXACT Logic: ${_getExpectedBehaviorForMotherTongue(motherTongue)}',
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
                      Icon(Icons.record_voice_over, size: 12, color: Colors.orange),
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
            ],
          ),
          const SizedBox(height: 8),
          
          // Translation directions
          Row(
            children: [
              const SizedBox(width: 32), // Align with header text
              const Icon(Icons.arrow_forward, color: Colors.green, size: 16),
              const SizedBox(width: 8),
              Text(
                'Translating to: ${[...automaticTargetLanguages.map((lang) => "$lang (automatic)"), ...expectedTargetLanguages].join(", ")}',
                style: const TextStyle(color: Colors.green, fontWeight: FontWeight.w600),
              ),
            ],
          ),
          
          if (selectedStyles.isNotEmpty) ...[
            const SizedBox(height: 8),
            Row(
              children: [
                const SizedBox(width: 32),
                const Icon(Icons.style, color: Colors.green, size: 16),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    selectedStyles.join(', '),
                    style: const TextStyle(color: Colors.green),
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
                    const Icon(Icons.volume_up, size: 16, color: Colors.cyan),
                    const SizedBox(width: 8),
                    Text(
                      '$feature: [target word] ([Spanish equivalent])',
                      style: const TextStyle(
                        color: Colors.cyan,
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                  ],
                ),
              );
            }).toList(),
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
                  'EXACT Logic: ${_getExpectedBehaviorForMotherTongue(motherTongue)}',
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

    if (speechState && translation.audioPath != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) async {
        try {
          await ref
              .read(speechProvider.notifier)
              .playAudio(translation.audioPath);
          ref.read(translationProvider.notifier).clearConversation();

          if (mounted) {
            Navigator.pop(context);
            // Add this to ensure sound plays after navigation animation completes
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
                
                // CRITICAL: Word-by-Word Visualization Widget
                // This shows exactly what the user hears in the audio
                WordByWordVisualizationWidget(
                  wordByWordData: translation.wordByWord,
                  isVisible: translation.wordByWord != null && translation.wordByWord!.isNotEmpty,
                ),
                
                // EXACT per requirements: Show audio format information
                if (translation.audioPath != null) ...[
                  const SizedBox(height: 8),
                  
                  // Check if word-by-word audio was generated
                  Builder(
                    builder: (context) {
                      final germanWordByWord = settings['germanWordByWord'] == true;
                      final englishWordByWord = settings['englishWordByWord'] == true;
                      final anyWordByWord = germanWordByWord || englishWordByWord;
                      
                      return Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.cyan.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: Colors.cyan, width: 1),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                const Icon(Icons.volume_up, color: Colors.cyan, size: 16),
                                const SizedBox(width: 4),
                                Text(
                                  anyWordByWord ? 'Word-by-Word Audio Generated' : 'Translation Audio Generated',
                                  style: const TextStyle(
                                    color: Colors.cyan,
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ],
                            ),
                            if (anyWordByWord) ...[
                              const SizedBox(height: 4),
                              const Text(
                                'Format: [target word] ([Spanish equivalent])',
                                style: TextStyle(
                                  color: Colors.cyan,
                                  fontSize: 11,
                                  fontStyle: FontStyle.italic,
                                ),
                              ),
                              if (germanWordByWord) 
                                const Text(
                                  '• German word-by-word breakdown included',
                                  style: TextStyle(color: Colors.cyan, fontSize: 10),
                                ),
                              if (englishWordByWord)
                                const Text(
                                  '• English word-by-word breakdown included',
                                  style: TextStyle(color: Colors.cyan, fontSize: 10),
                                ),
                              const SizedBox(height: 6),
                              Container(
                                padding: const EdgeInsets.all(6),
                                decoration: BoxDecoration(
                                  color: Colors.purple.withOpacity(0.2),
                                  borderRadius: BorderRadius.circular(4),
                                  border: Border.all(color: Colors.purple, width: 1),
                                ),
                                child: const Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(Icons.visibility, color: Colors.purple, size: 12),
                                    SizedBox(width: 4),
                                    Text(
                                      'Visual breakdown above matches audio exactly',
                                      style: TextStyle(
                                        color: Colors.purple,
                                        fontSize: 10,
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ] else ...[
                              const SizedBox(height: 4),
                              const Text(
                                'Simple translation reading (word-by-word not selected)',
                                style: TextStyle(
                                  color: Colors.cyan,
                                  fontSize: 11,
                                  fontStyle: FontStyle.italic,
                                ),
                              ),
                            ],
                          ],
                        ),
                      );
                    },
                  ),
                ],
                
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
                          speechState ? 'Pause' : 'Play Audio',
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
    );
  }

  Widget _buildLoadingMessage() {
    final settings = ref.watch(settingsProvider);
    final motherTongue = settings['motherTongue'] as String? ?? 'spanish';
    
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
              'EXACT Logic: ${_getExpectedBehaviorForMotherTongue(motherTongue)}',
              style: TextStyle(
                color: Colors.grey[400],
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
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Error in Dynamic Translation: $error',
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
                    '• Invalid dynamic translation configuration',
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