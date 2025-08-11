// prompt_screen.dart - Updated with dynamic mother tongue integration

import 'dart:async';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:speak_and_translate_update/features/translation/presentation/providers/shared_provider.dart' show isContinuousListeningActiveProvider, isListeningProvider, settingsProvider;
import 'package:speech_to_text/speech_recognition_error.dart' as stt;
import 'package:speech_to_text/speech_recognition_result.dart' as stt;
import 'package:speech_to_text/speech_to_text.dart' as stt;
import '../../domain/repositories/translation_repository.dart';
import '../widgets/voice_command_status_inficator.dart';
import 'settings_screen.dart';
import '../widgets/speech_tips_widget.dart';

class PromptScreen extends ConsumerStatefulWidget {
  const PromptScreen({super.key});

  @override
  ConsumerState<PromptScreen> createState() => _PromptScreenState();
}

class _PromptScreenState extends ConsumerState<PromptScreen> {
  late final TextEditingController _textController;
  late stt.SpeechToText _speech;
  bool _isInitialized = false;
  String _accumulatedText = '';
  bool _isProcessingAudio = false;
  bool _shouldProcessAfterStop = false;
  Timer? _speechPauseTimer;
  Timer? _voiceStartTimer;
  Timer? _restartTimer;
  double _soundThreshold = 0.05;
  
  bool _isListeningSession = false;
  int _consecutiveErrors = 0;
  final int _maxConsecutiveErrors = 3;
  bool _hasHadValidInput = false;

  // Dynamic mother tongue support
  String _currentMotherTongue = 'spanish';

  @override
  void initState() {
    super.initState();
    _textController = TextEditingController();
    _speech = stt.SpeechToText();
    _initializeSpeech();
  }

  Future<void> _initializeSpeech() async {
    try {
      _isInitialized = true;
      debugPrint('🎤 Speech service initialized successfully');
    } catch (e) {
      debugPrint('❌ Speech init error: $e');
    }
  }

  // Helper method to get language display name and flag
  String _getLanguageDisplayName(String languageCode) {
    switch (languageCode.toLowerCase()) {
      case 'spanish':
        return 'Spanish (Español)';
      case 'english':
        return 'English';
      case 'german':
        return 'German (Deutsch)';
      case 'french':
        return 'French (Français)';
      case 'italian':
        return 'Italian (Italiano)';
      case 'portuguese':
        return 'Portuguese (Português)';
      default:
        return languageCode.toUpperCase();
    }
  }

  String _getLanguageFlag(String languageCode) {
    switch (languageCode.toLowerCase()) {
      case 'spanish':
        return '🇪🇸';
      case 'english':
        return '🇺🇸';
      case 'german':
        return '🇩🇪';
      case 'french':
        return '🇫🇷';
      case 'italian':
        return '🇮🇹';
      case 'portuguese':
        return '🇵🇹';
      default:
        return '🌐';
    }
  }

  // Get speech recognition locale for mother tongue
  String _getSpeechLocaleForMotherTongue(String motherTongue) {
    switch (motherTongue.toLowerCase()) {
      case 'spanish':
        return 'es-ES';
      case 'english':
        return 'en-US';
      case 'german':
        return 'de-DE';
      case 'french':
        return 'fr-FR';
      case 'italian':
        return 'it-IT';
      case 'portuguese':
        return 'pt-PT';
      default:
        return 'es-ES'; // Default to Spanish
    }
  }

  void _updateMotherTongueFromSettings() {
    final settings = ref.read(settingsProvider);
    final newMotherTongue = settings['motherTongue'] as String? ?? 'spanish';
    
    if (newMotherTongue != _currentMotherTongue) {
      debugPrint('🌐 Mother tongue changed from $_currentMotherTongue to $newMotherTongue');
      _currentMotherTongue = newMotherTongue;
      
      // Restart listening with new language if currently active
      if (ref.read(isContinuousListeningActiveProvider)) {
        _restartWithNewLanguage();
      }
    }
  }

  Future<void> _restartWithNewLanguage() async {
    debugPrint('🔄 Restarting speech recognition with new language: $_currentMotherTongue');
    
    // Stop current session
    await _stopCurrentSession();
    
    // Wait a moment then restart
    await Future.delayed(const Duration(milliseconds: 500));
    
    if (mounted && ref.read(isContinuousListeningActiveProvider)) {
      await _initializeContinuousListening();
    }
  }

  Future<void> _stopCurrentSession() async {
    try {
      _speechPauseTimer?.cancel();
      _voiceStartTimer?.cancel();
      _restartTimer?.cancel();
      
      await _speech.stop();
      await _speech.cancel();
      
      _isProcessingAudio = false;
      _accumulatedText = '';
      _shouldProcessAfterStop = false;
      _textController.clear();
      _isListeningSession = false;
      _consecutiveErrors = 0;
      _hasHadValidInput = false;
      
      ref.read(isListeningProvider.notifier).state = false;
    } catch (e) {
      debugPrint('❌ Error stopping current session: $e');
    }
  }

  Future<void> _initializeContinuousListening() async {
    if (!_isInitialized) return;

    // Update mother tongue from settings
    _updateMotherTongueFromSettings();

    try {
      bool available = await _speech.initialize(
        onStatus: (status) {
          debugPrint('🎯 Speech status: $status');
          _handleStatusChange(status);
        },
        onError: (error) {
          debugPrint('❌ Speech error: $error');
          _handleSpeechError(error);
        },
      );

      if (available) {
        ref.read(isContinuousListeningActiveProvider.notifier).state = true;
        _startContinuousListening();
        debugPrint('✅ Continuous listening initialized for $_currentMotherTongue');
      } else {
        debugPrint('❌ Speech recognition not available');
      }
    } catch (e) {
      debugPrint('❌ Error initializing continuous listening: $e');
    }
  }

  void _handleStatusChange(String status) {
    switch (status) {
      case 'listening':
        ref.read(isListeningProvider.notifier).state = true;
        ref.read(isContinuousListeningActiveProvider.notifier).state = true;
        _isListeningSession = true;
        _consecutiveErrors = 0;
        break;
      case 'done':
        ref.read(isListeningProvider.notifier).state = false;
        _handleSpeechCompletion();
        break;
      case 'notListening':
        ref.read(isListeningProvider.notifier).state = false;
        break;
    }
  }

  void _handleSpeechCompletion() {
    if (_accumulatedText.isNotEmpty && _accumulatedText.trim().length > 3) {
      _processRecognizedText(_accumulatedText);
    } else {
      if (!_isProcessingAudio && ref.read(isContinuousListeningActiveProvider)) {
        _scheduleRestart(delay: 800);
      }
    }
  }

  void _handleSpeechError(stt.SpeechRecognitionError error) {
    _consecutiveErrors++;
    
    if (error.errorMsg == 'error_no_match') {
      debugPrint('🔄 No speech detected (${_consecutiveErrors}/${_maxConsecutiveErrors})');
      if (_consecutiveErrors < _maxConsecutiveErrors) {
        _scheduleRestart(delay: 500);
      } else {
        debugPrint('⚠️ Too many consecutive no-match errors, longer pause');
        _scheduleRestart(delay: 2000);
        _consecutiveErrors = 0;
      }
    } else if (error.errorMsg == 'error_speech_timeout') {
      debugPrint('⏰ Speech timeout, checking for accumulated text...');
      if (_accumulatedText.trim().length > 3) {
        _processRecognizedText(_accumulatedText);
      } else {
        _scheduleRestart(delay: 1000);
      }
    } else {
      debugPrint('⚠️ Speech recognition error: ${error.errorMsg}');
      _scheduleRestart(delay: 1500);
    }
  }

  void _scheduleRestart({required int delay}) {
    if (!ref.read(isContinuousListeningActiveProvider) || _isProcessingAudio) {
      return;
    }
    
    _restartTimer?.cancel();
    
    _restartTimer = Timer(Duration(milliseconds: delay), () {
      if (mounted && !_isProcessingAudio && 
          ref.read(isContinuousListeningActiveProvider)) {
        _startContinuousListening();
      }
    });
  }

  void _startContinuousListening() {
    if (!_speech.isAvailable || _isProcessingAudio || !mounted) return;

    // Get the correct locale for the current mother tongue
    final localeId = _getSpeechLocaleForMotherTongue(_currentMotherTongue);
    
    debugPrint('🎤 Starting continuous listening for $_currentMotherTongue ($localeId)');
    _accumulatedText = '';
    _textController.text = '';
    _shouldProcessAfterStop = false;
    _speechPauseTimer?.cancel();
    _voiceStartTimer?.cancel();
    _isListeningSession = true;

    _speech.listen(
      onResult: (result) {
        _handleSpeechResult(result);
      },
      listenFor: const Duration(minutes: 30),
      pauseFor: const Duration(seconds: 10),
      partialResults: true,
      localeId: localeId,  // Use dynamic locale based on mother tongue
      listenMode: stt.ListenMode.dictation,
      cancelOnError: false,
      onSoundLevelChange: (level) {
        _handleSoundLevel(level);
      },
    );
  }

  void _handleSoundLevel(double level) {
    if (level > _soundThreshold) {
      _speechPauseTimer?.cancel();
      
      if (_accumulatedText.isEmpty && _voiceStartTimer == null) {
        _voiceStartTimer = Timer(const Duration(milliseconds: 300), () {
          if (_accumulatedText.isEmpty && mounted) {
            setState(() {
              _textController.text = "(${_getListeningText()})";
            });
          }
        });
      }
    } else if (_accumulatedText.isNotEmpty) {
      final pauseDuration = _accumulatedText.length > 30 
          ? const Duration(seconds: 10) 
          : const Duration(seconds: 8);
          
      _speechPauseTimer?.cancel();
      _speechPauseTimer = Timer(pauseDuration, () {
        if (!_isProcessingAudio && _accumulatedText.isNotEmpty) {
          _processRecognizedText(_accumulatedText);
        }
      });
    }
  }

  String _getListeningText() {
    switch (_currentMotherTongue.toLowerCase()) {
      case 'spanish':
        return 'Escuchando...';
      case 'english':
        return 'Listening...';
      case 'german':
        return 'Höre zu...';
      case 'french':
        return 'Écoute...';
      case 'italian':
        return 'Ascoltando...';
      case 'portuguese':
        return 'Ouvindo...';
      default:
        return 'Listening...';
    }
  }

  void _handleSpeechResult(stt.SpeechRecognitionResult result) {
    if (result.recognizedWords.isEmpty) return;
    
    _speechPauseTimer?.cancel();
    _voiceStartTimer?.cancel();
    _voiceStartTimer = null;
    _hasHadValidInput = true;
    
    setState(() {
      if (result.finalResult) {
        if (_accumulatedText.isEmpty) {
          _accumulatedText = result.recognizedWords;
        } else {
          if (!_accumulatedText.endsWith(' ') && 
              !result.recognizedWords.startsWith(' ')) {
            _accumulatedText += ' ';
          }
          _accumulatedText += result.recognizedWords;
        }
        _textController.text = _accumulatedText;
        debugPrint('✅ Accumulated text ($_currentMotherTongue): $_accumulatedText');
        
        final pauseTime = _accumulatedText.split(' ').length > 5
            ? const Duration(seconds: 10)
            : const Duration(seconds: 8);
            
        _speechPauseTimer = Timer(pauseTime, () {
          if (!_isProcessingAudio && _accumulatedText.isNotEmpty) {
            _processRecognizedText(_accumulatedText);
          }
        });
      } else {
        String partialText = _accumulatedText.isEmpty 
            ? result.recognizedWords 
            : '$_accumulatedText ${result.recognizedWords}';
        _textController.text = partialText;
        debugPrint('📝 Partial text ($_currentMotherTongue): $partialText');
        
        if (result.recognizedWords.isEmpty) {
          _textController.text += '...';
        }
      }
    });
  }

  Future<void> _processRecognizedText(String text) async {
    if (text.isEmpty || _isProcessingAudio) return;

    final cleanText = text.trim();
    if (cleanText.length < 4) {
      debugPrint('⚠️ Text too short, resetting: $cleanText');
      _resetContinuousListening();
      return;
    }

    _isProcessingAudio = true;
    _speechPauseTimer?.cancel();
    _voiceStartTimer?.cancel();
    _restartTimer?.cancel();
    
    try {
      await _speech.stop();
      await _speech.cancel();
      
      ref.read(isListeningProvider.notifier).state = false;
      
      await Future.delayed(const Duration(milliseconds: 300));
      
      await ref.read(translationRepositoryProvider).playUISound('start_conversation');
      
      debugPrint('🚀 Auto-starting conversation with: $cleanText ($_currentMotherTongue)');
      
      if (mounted) {
        Navigator.pushNamed(
          context,
          '/conversation',
          arguments: cleanText,
        ).then((_) {
          _resetAfterConversation();
        });
      }
    } catch (e) {
      debugPrint('❌ Error processing recognized text: $e');
      _resetContinuousListening();
    } finally {
      _isProcessingAudio = false;
    }
  }

  void _resetAfterConversation() {
    _textController.clear();
    _accumulatedText = '';
    _isProcessingAudio = false;
    _shouldProcessAfterStop = false;
    _speechPauseTimer?.cancel();
    _voiceStartTimer?.cancel();
    _restartTimer?.cancel();
    _isListeningSession = false;
    _consecutiveErrors = 0;
    _hasHadValidInput = false;
    
    debugPrint('🔄 Conversation completed, resetting state');
    
    if (ref.read(isContinuousListeningActiveProvider)) {
      Future.delayed(const Duration(milliseconds: 1500), () {
        if (mounted && !_isProcessingAudio) {
          debugPrint('🔄 Restarting continuous listening after conversation');
          _startContinuousListening();
        }
      });
    }
  }

  void _resetContinuousListening() {
    _accumulatedText = '';
    _isProcessingAudio = false;
    _shouldProcessAfterStop = false;
    _textController.clear();
    _speechPauseTimer?.cancel();
    _voiceStartTimer?.cancel();
    _restartTimer?.cancel();
    _isListeningSession = false;
    _consecutiveErrors = 0;
    
    if (ref.read(isContinuousListeningActiveProvider) && !_isProcessingAudio) {
      _scheduleRestart(delay: 1000);
    }
  }

  Future<void> _startConversation() async {
    if (_textController.text.isNotEmpty) {
      await ref.read(translationRepositoryProvider).playUISound('start_conversation');

      debugPrint('🚀 Manual conversation start: ${_textController.text} ($_currentMotherTongue)');

      if (mounted) {
        Navigator.pushNamed(
          context,
          '/conversation',
          arguments: _textController.text,
        ).then((_) => _textController.clear());
      }
    }
  }

  String _getMicrophoneInstructions() {
    final isActive = ref.watch(isContinuousListeningActiveProvider);
    if (isActive) {
      if (_isListeningSession) {
        switch (_currentMotherTongue.toLowerCase()) {
          case 'spanish':
            return 'Micrófono activo - Habla normalmente, el mensaje se enviará automáticamente después de una pausa';
          case 'english':
            return 'Microphone active - Speak normally, message will be sent automatically after a pause';
          case 'german':
            return 'Mikrofon aktiv - Sprechen Sie normal, die Nachricht wird automatisch nach einer Pause gesendet';
          case 'french':
            return 'Microphone actif - Parlez normalement, le message sera envoyé automatiquement après une pause';
          case 'italian':
            return 'Microfono attivo - Parla normalmente, il messaggio verrà inviato automaticamente dopo una pausa';
          case 'portuguese':
            return 'Microfone ativo - Fale normalmente, a mensagem será enviada automaticamente após uma pausa';
          default:
            return 'Microphone active - Speak normally, message will be sent automatically after a pause';
        }
      } else {
        return 'Reconectando micrófono...';
      }
    } else {
      return 'Modo escucha continua - Toca el micrófono para activar';
    }
  }

  Future<void> _stopContinuousListening() async {
    try {
      await _stopCurrentSession();
      ref.read(isContinuousListeningActiveProvider.notifier).state = false;
      
      debugPrint('🛑 Continuous listening stopped by user');
    } catch (e) {
      debugPrint('❌ Error stopping continuous listening: $e');
    }
  }

  // Build mother tongue indicator widget
  Widget _buildMotherTongueIndicator() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.blue[900]!.withOpacity(0.3), Colors.cyan[900]!.withOpacity(0.3)],
          begin: Alignment.centerLeft,
          end: Alignment.centerRight,
        ),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.cyan, width: 1),
      ),
      child: Row(
        children: [
          Text(
            _getLanguageFlag(_currentMotherTongue),
            style: const TextStyle(fontSize: 24),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.record_voice_over, color: Colors.cyan, size: 16),
                    const SizedBox(width: 4),
                    const Text(
                      'Speaking in:',
                      style: TextStyle(color: Colors.cyan, fontSize: 12, fontWeight: FontWeight.w600),
                    ),
                  ],
                ),
                const SizedBox(height: 2),
                Text(
                  _getLanguageDisplayName(_currentMotherTongue),
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
          if (_isListeningSession)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.green.withOpacity(0.2),
                borderRadius: BorderRadius.circular(4),
                border: Border.all(color: Colors.green, width: 1),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.mic, color: Colors.green, size: 14),
                  const SizedBox(width: 4),
                  Text(
                    'ACTIVE',
                    style: const TextStyle(
                      color: Colors.green,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _speechPauseTimer?.cancel();
    _voiceStartTimer?.cancel();
    _restartTimer?.cancel();
    
    _speech.stop();
    _speech.cancel();
    
    _isProcessingAudio = false;
    _accumulatedText = '';
    
    _textController.dispose();
    
    debugPrint('🧹 PromptScreen disposed cleanly');
    
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final currentSettings = ref.watch(settingsProvider);
    final isListening = ref.watch(isListeningProvider);
    final isContinuousActive = ref.watch(isContinuousListeningActiveProvider);

    // Update mother tongue when settings change
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _updateMotherTongueFromSettings();
    });

    return Scaffold(
      backgroundColor: const Color(0xFF000000),
      appBar: CupertinoNavigationBar(
        backgroundColor: const Color(0xFF1C1C1E),
        border: null,
        middle: const Text('AI Chat Assistant',
            style: TextStyle(
                color: Colors.white,
                fontSize: 17,
                fontWeight: FontWeight.w600)),
        trailing: CupertinoButton(
          padding: EdgeInsets.zero,
          child: const Icon(CupertinoIcons.gear,
              color: CupertinoColors.systemGrey, size: 28),
          onPressed: () async {
            final currentSettings = ref.read(settingsProvider);
            debugPrint('🔧 Opening settings with current: $currentSettings');
            
            final result = await Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => SettingsScreen(initialSettings: currentSettings),
              ),
            );
            
            if (result != null && result is Map<String, dynamic>) {
              await _stopContinuousListening();
              await Future.delayed(const Duration(milliseconds: 500));
              
              ref.read(settingsProvider.notifier).state = result;
              debugPrint('✅ Settings updated: $result');
              
              // Always restart continuous listening since it's the only mode
              await Future.delayed(const Duration(milliseconds: 1000));
              await _initializeContinuousListening();
              debugPrint('🔄 Continuous listening restarted after settings update');
            }
          },
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            // Scrollable content area
            Expanded(
              child: SingleChildScrollView(
                child: Column(
                  children: [
                    // Mother tongue indicator
                    _buildMotherTongueIndicator(),
                    
                    VoiceCommandStatusIndicator(
                      isListening: isListening || isContinuousActive,
                    ),
                    
                    // Always show speech tips without close button
                    SpeechTipsWidget(),
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: _isListeningSession ? const Color(0xFF1B4D3E) : const Color(0xFF2C2C2E),
                        borderRadius: BorderRadius.circular(8),
                        border: _isListeningSession ? Border.all(
                          color: Colors.green,
                          width: 1,
                        ) : null,
                      ),
                      child: Text(
                        _getMicrophoneInstructions(),
                        style: TextStyle(
                          color: _isListeningSession ? Colors.green : Colors.white, 
                          fontSize: 14,
                          fontWeight: _isListeningSession ? FontWeight.w500 : FontWeight.w400,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                    const SizedBox(height: 12),
                    ConstrainedBox(
                      constraints: BoxConstraints(
                        minHeight: 100,
                        maxHeight: MediaQuery.of(context).size.height * 0.4,
                      ),
                      child: CupertinoTextField(
                        controller: _textController,
                        maxLines: null,
                        style: const TextStyle(color: Colors.white, fontSize: 17),
                        placeholder: _getPlaceholderText(),
                        placeholderStyle: const TextStyle(
                            color: CupertinoColors.placeholderText, fontSize: 17),
                        decoration: BoxDecoration(
                          color: const Color(0xFF2C2C2E),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(
                            color: const Color(0xFF3A3A3C),
                            width: 0.5,
                          ),
                        ),
                        padding: const EdgeInsets.all(16),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),
            // Button row
            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    onPressed: _startConversation,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color.fromARGB(255, 61, 62, 63),
                      minimumSize: const Size(double.infinity, 50),
                    ),
                    child: Text(
                      _getStartButtonText(),
                      style: const TextStyle(color: Colors.white),
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                // Continuous listening microphone button
                ElevatedButton(
                  onPressed: () async {
                    if (isContinuousActive) {
                      await _stopContinuousListening();
                      debugPrint('🛑 Continuous listening stopped by user');
                    } else {
                      if (!_isProcessingAudio) {
                        debugPrint('▶️ Starting continuous listening by user');
                        await _initializeContinuousListening();
                      }
                    }
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: isContinuousActive ? Colors.red : Colors.white,
                    shape: const CircleBorder(),
                    padding: const EdgeInsets.all(16),
                  ),
                  child: Icon(
                    isContinuousActive ? Icons.mic_off : Icons.mic,
                    size: 28,
                    color: isContinuousActive ? Colors.white : Colors.black,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  String _getPlaceholderText() {
    switch (_currentMotherTongue.toLowerCase()) {
      case 'spanish':
        return 'escribe tu mensaje aquí';
      case 'english':
        return 'write your prompt here';
      case 'german':
        return 'schreibe deine Nachricht hier';
      case 'french':
        return 'écris ton message ici';
      case 'italian':
        return 'scrivi il tuo messaggio qui';
      case 'portuguese':
        return 'escreve a tua mensagem aqui';
      default:
        return 'write your prompt here';
    }
  }

  String _getStartButtonText() {
    switch (_currentMotherTongue.toLowerCase()) {
      case 'spanish':
        return 'iniciar conversación';
      case 'english':
        return 'start conversation';
      case 'german':
        return 'Gespräch beginnen';
      case 'french':
        return 'démarrer la conversation';
      case 'italian':
        return 'inizia conversazione';
      case 'portuguese':
        return 'iniciar conversa';
      default:
        return 'start conversation';
    }
  }
}