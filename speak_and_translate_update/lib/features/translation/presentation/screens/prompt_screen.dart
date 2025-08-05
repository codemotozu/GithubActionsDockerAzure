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

  Future<void> _initializeContinuousListening() async {
    if (!_isInitialized) return;

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
        debugPrint('✅ Continuous listening initialized and started');
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

    debugPrint('🎤 Starting enhanced continuous listening...');
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
      localeId: 'es-ES',
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
              _textController.text = "(Escuchando...)";
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
        debugPrint('✅ Accumulated text: $_accumulatedText');
        
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
        debugPrint('📝 Partial text: $partialText');
        
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
      
      debugPrint('🚀 Auto-starting conversation with: $cleanText');
      
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

      debugPrint('🚀 Manual conversation start: ${_textController.text}');

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
        return 'Micrófono activo - Habla normalmente, el mensaje se enviará automáticamente después de una pausa';
      } else {
        return 'Reconectando micrófono...';
      }
    } else {
      return 'Modo escucha continua - Toca el micrófono para activar';
    }
  }

  Future<void> _stopContinuousListening() async {
    try {
      _speechPauseTimer?.cancel();
      _voiceStartTimer?.cancel();
      _restartTimer?.cancel();
      
      await _speech.stop();
      await _speech.cancel();
      
      ref.read(isContinuousListeningActiveProvider.notifier).state = false;
      ref.read(isListeningProvider.notifier).state = false;
      
      _isProcessingAudio = false;
      _accumulatedText = '';
      _shouldProcessAfterStop = false;
      _textController.clear();
      _isListeningSession = false;
      _consecutiveErrors = 0;
      _hasHadValidInput = false;
      
      debugPrint('🛑 Continuous listening stopped by user');
    } catch (e) {
      debugPrint('❌ Error stopping continuous listening: $e');
    }
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
                        placeholder: 'write your prompt here',
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
                    child: const Text('start conversation',
                        style: TextStyle(color: Colors.white)),
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
}