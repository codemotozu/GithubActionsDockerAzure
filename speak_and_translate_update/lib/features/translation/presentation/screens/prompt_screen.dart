

// // ESTE CODIGO NO TIENE PAUSAS NATURALES DEL HABLA 
// // ESTE CODIGO NO TIENE PAUSAS NATURALES DEL HABLA 
// // ESTE CODIGO NO TIENE PAUSAS NATURALES DEL HABLA 
// // ESTE CODIGO NO TIENE PAUSAS NATURALES DEL HABLA 9898
// // ESTE CODIGO NO TIENE PAUSAS NATURALES DEL HABLA 
// // ESTE CODIGO NO TIENE PAUSAS NATURALES DEL HABLA 




import 'dart:async';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:porcupine_flutter/porcupine.dart';
import 'package:porcupine_flutter/porcupine_error.dart';
import 'package:porcupine_flutter/porcupine_manager.dart';
import 'package:speak_and_translate_update/features/translation/presentation/providers/shared_provider.dart' show isContinuousListeningActiveProvider, isListeningProvider, settingsProvider;
import 'package:speech_to_text/speech_recognition_error.dart' as stt;
import 'package:speech_to_text/speech_recognition_result.dart' as stt;
import 'package:speech_to_text/speech_to_text.dart' as stt;
import '../../domain/repositories/translation_repository.dart';
import '../providers/audio_recorder_provider.dart';
import '../providers/voice_command_provider.dart';
import '../widgets/voice_command_status_inficator.dart';
import 'settings_screen.dart';

class PromptScreen extends ConsumerStatefulWidget {
  const PromptScreen({super.key});

  @override
  ConsumerState<PromptScreen> createState() => _PromptScreenState();
}

class _PromptScreenState extends ConsumerState<PromptScreen> {
  late final TextEditingController _textController;
  late final AudioRecorder _recorder;
  late PorcupineManager _porcupineManager;
  late stt.SpeechToText _speech;
  bool _isWakeWordMode = true;
  bool _isInitialized = false;
  String _accumulatedText = '';
  bool _isProcessingAudio = false;
  bool _shouldProcessAfterStop = false;
  Timer? _speechPauseTimer; // Timer for pause detection
  Timer? _voiceStartTimer; // Timer for voice start detection
  double _soundThreshold = 0.05; // Lowered threshold for better start detection

  @override
  void initState() {
    super.initState();
    _textController = TextEditingController();
    _recorder = ref.read(audioRecorderProvider);
    _speech = stt.SpeechToText();

    _initializeRecorder();
    _initPorcupine();
  }

  Future<void> _initializeRecorder() async {
    try {
      await _recorder.init();
      _isInitialized = true;
      debugPrint('🎤 Audio recorder initialized successfully');
    } catch (e) {
      debugPrint('❌ Recorder init error: $e');
    }
  }

  void _initPorcupine() async {
    try {
      _porcupineManager = await PorcupineManager.fromBuiltInKeywords(
        'JpbyAC2iGGx74uGLBhyBcELUU830BM3ZcdOA9CT8EQDeozX3n9INBA==',
        [BuiltInKeyword.JARVIS, BuiltInKeyword.ALEXA],
        _wakeWordCallback,
      );
      await _porcupineManager.start();
      debugPrint("🤖 Porcupine wake word detection initialized successfully");
    } on PorcupineException catch (err) {
      debugPrint("❌ Failed to initialize Porcupine: ${err.message}");
    }
  }

  Future<void> _initializeContinuousListening() async {
    if (!_isInitialized) return;

    try {
      bool available = await _speech.initialize(
        onStatus: (status) {
          debugPrint('🎯 Speech status: $status');
          if (status == 'listening') {
            ref.read(isListeningProvider.notifier).state = true;
            ref.read(isContinuousListeningActiveProvider.notifier).state = true;
          } else if (status == 'done') {
            ref.read(isListeningProvider.notifier).state = false;
            _handleSpeechCompletion();
          } else if (status == 'notListening') {
            ref.read(isListeningProvider.notifier).state = false;
          }
        },
        onError: (error) {
          debugPrint('❌ Speech error: $error');
          ref.read(isListeningProvider.notifier).state = false;
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

  void _handleSpeechCompletion() {
    // Process accumulated text if we have meaningful content
    if (_accumulatedText.isNotEmpty && _accumulatedText.trim().length > 3) {
      _processRecognizedText(_accumulatedText);
    } else {
      _restartContinuousListeningIfNeeded();
    }
  }

  void _handleSpeechError(stt.SpeechRecognitionError error) {
    if (error.errorMsg == 'error_no_match') {
      debugPrint('🔄 No speech detected, restarting listening...');
      _restartContinuousListeningIfNeeded(isNoMatch: true);
    } else if (error.errorMsg == 'error_speech_timeout') {
      debugPrint('⏰ Speech timeout, auto-processing accumulated text...');
      if (_accumulatedText.trim().length > 3) {
        _processRecognizedText(_accumulatedText);
      } else {
        _restartContinuousListeningIfNeeded();
      }
    } else {
      debugPrint('⚠️ Speech recognition error: ${error.errorMsg}');
      _restartContinuousListeningIfNeeded(isError: true);
    }
  }

  void _restartContinuousListeningIfNeeded({bool isError = false, bool isNoMatch = false}) {
    final currentSettings = ref.read(settingsProvider);
    if (currentSettings['microphoneMode'] == 'continuousListening' && 
        ref.read(isContinuousListeningActiveProvider) && 
        !_isProcessingAudio) {
      
      int delay;
      if (isNoMatch) {
        delay = 1000; // Shorter delay for no match (1 second)
      } else if (isError) {
        delay = 3000; // Longer delay for actual errors (3 seconds)
      } else {
        delay = 1500; // Normal delay (1.5 seconds)
      }
      
      debugPrint('🔄 Restarting continuous listening in ${delay}ms');
      Future.delayed(Duration(milliseconds: delay), () {
        if (mounted && !_isProcessingAudio && 
            currentSettings['microphoneMode'] == 'continuousListening' &&
            ref.read(isContinuousListeningActiveProvider)) {
          _startContinuousListening();
        }
      });
    }
  }

  void _startContinuousListening() {
    if (!_speech.isAvailable || _isProcessingAudio) return;

    debugPrint('🎤 Starting enhanced continuous listening...');
    _accumulatedText = '';
    _textController.text = '';
    _shouldProcessAfterStop = false;
    _speechPauseTimer?.cancel();
    _voiceStartTimer?.cancel();

    _speech.listen(
      onResult: (result) {
        _handleSpeechResult(result);
      },
      listenFor: const Duration(minutes: 5),
      pauseFor: const Duration(seconds: 7), // Increased from 5 to 7 seconds
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
    // Improved voice start detection logic
    if (level > _soundThreshold) {
      _speechPauseTimer?.cancel();
      
      // Add buffer for speech start
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
      // Adaptive pause time: longer phrases need longer silence
      final pauseDuration = _accumulatedText.length > 30 
          ? const Duration(seconds: 8) 
          : const Duration(seconds: 7);
          
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
    
    setState(() {
      if (result.finalResult) {
        if (_accumulatedText.isEmpty) {
          _accumulatedText = result.recognizedWords;
        } else {
          // Handle mid-sentence pauses better
          if (!_accumulatedText.endsWith(' ') && 
              !result.recognizedWords.startsWith(' ')) {
            _accumulatedText += ' ';
          }
          _accumulatedText += result.recognizedWords;
        }
        _textController.text = _accumulatedText;
        debugPrint('✅ Accumulated text: $_accumulatedText');
        
        // Adaptive pause timing based on phrase complexity
        final pauseTime = _accumulatedText.split(' ').length > 5
            ? const Duration(seconds: 8)
            : const Duration(seconds: 7);
            
        _speechPauseTimer = Timer(pauseTime, () {
          if (!_isProcessingAudio && _accumulatedText.isNotEmpty) {
            _processRecognizedText(_accumulatedText);
          }
        });
      } else {
        // Show partial results in real-time
        String partialText = _accumulatedText.isEmpty 
            ? result.recognizedWords 
            : '$_accumulatedText ${result.recognizedWords}';
        _textController.text = partialText;
        debugPrint('📝 Partial text: $partialText');
        
        // Add temporary hint text during pauses
        if (result.recognizedWords.isEmpty) {
          _textController.text += '...';
        }
      }
    });
  }

  Future<void> _processRecognizedText(String text) async {
    if (text.isEmpty || _isProcessingAudio) return;

    // Clean the text
    final cleanText = text.replaceAll(RegExp(r'\b(?:jarvis|alexa)\b', caseSensitive: false), '').trim();
    if (cleanText.length < 4) {
      debugPrint('⚠️ Text too short, resetting: $cleanText');
      _resetContinuousListening();
      return;
    }

    _isProcessingAudio = true;
    _speechPauseTimer?.cancel();
    _voiceStartTimer?.cancel();
    
    try {
      // Stop continuous listening before processing
      await _speech.stop();
      await _speech.cancel();
      
      ref.read(isListeningProvider.notifier).state = false;
      
      // Brief pause for audio resources to be released
      await Future.delayed(const Duration(milliseconds: 300));
      
      // Play sound to indicate processing
      await ref.read(translationRepositoryProvider).playUISound('start_conversation');
      
      debugPrint('🚀 Auto-starting conversation with: $cleanText');
      
      // Start conversation automatically
      if (mounted) {
        Navigator.pushNamed(
          context,
          '/conversation',
          arguments: cleanText,
        ).then((_) {
          // Reset everything after conversation
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
    
    debugPrint('🔄 Conversation completed, resetting state');
    
    // Wait before restarting to let audio system settle
    final currentSettings = ref.read(settingsProvider);
    if (currentSettings['microphoneMode'] == 'continuousListening' && 
        ref.read(isContinuousListeningActiveProvider)) {
      Future.delayed(const Duration(milliseconds: 2000), () {
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
    _restartContinuousListeningIfNeeded();
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

  void _wakeWordCallback(int keywordIndex) async {
    if (!mounted) return;

    final currentSettings = ref.read(settingsProvider);
    
    if (currentSettings['microphoneMode'] == 'voiceCommand') {
      if (keywordIndex == 0 && _isWakeWordMode) {
        debugPrint('🤖 JARVIS wake word detected');
        await _startVoiceRecording();
        _isWakeWordMode = false;
      } else if (keywordIndex == 1 && !_isWakeWordMode) {
        debugPrint('🤖 ALEXA wake word detected');
        await _stopVoiceRecording();
        _isWakeWordMode = true;
        
        if (_textController.text.isNotEmpty) {
          await _startConversation();
        }
      }
    }
  }

  void _handleVoiceCommand(VoiceCommandState state) {
    if (!mounted) return;
    setState(() {});

    if (state.error != null) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(state.error!)));
    }
  }

  Future<void> _startVoiceRecording() async {
    try {
      await ref.read(translationRepositoryProvider).playUISound('mic_on');
      await _recorder.startListening("open");
      ref.read(isListeningProvider.notifier).state = true;
      final currentState = ref.read(voiceCommandProvider);
      ref.read(voiceCommandProvider.notifier).state =
          currentState.copyWith(isListening: true);
      debugPrint('🎤 Voice recording started');
    } catch (e) {
      debugPrint('❌ Recording start error: $e');
    }
  }

  Future<void> _stopVoiceRecording() async {
    try {
      await ref.read(translationRepositoryProvider).playUISound('mic_off');
      final path = await _recorder.stopListening();
      if (path != null) {
        var text = await ref
            .read(translationRepositoryProvider)
            .processAudioInput(path);

        text = text.replaceAll(RegExp(r'\b(?:jarvis|alexa)\b', caseSensitive: false), '').trim();

        if (text.isNotEmpty) {
          _textController.text = text;
          debugPrint('✅ Voice recording processed: $text');
        }
      }
    } catch (e) {
      debugPrint('❌ Recording stop error: $e');
    } finally {
      ref.read(isListeningProvider.notifier).state = false;
      final currentState = ref.read(voiceCommandProvider);
      ref.read(voiceCommandProvider.notifier).state =
          currentState.copyWith(isListening: false);
    }
  }

  String _getMicrophoneInstructions() {
    final currentSettings = ref.read(settingsProvider);
    final micMode = currentSettings['microphoneMode'];
    
    if (micMode == 'continuousListening') {
      final isActive = ref.watch(isContinuousListeningActiveProvider);
      if (isActive) {
        return 'Escuchando continuamente - Habla cuando quieras, tu mensaje se enviará automáticamente después de 5 segundos de silencio';
      } else {
        return 'Modo escucha continua - Toca el micrófono para activar';
      }
    } else {
      return _isWakeWordMode 
        ? 'Di "Jarvis" para comenzar a escuchar'
        : 'Di "Alexa" para parar de escuchar e iniciar conversación';
    }
  }

  Future<void> _stopContinuousListening() async {
    try {
      _speechPauseTimer?.cancel();
      _voiceStartTimer?.cancel();
      await _speech.stop();
      await _speech.cancel();
      ref.read(isContinuousListeningActiveProvider.notifier).state = false;
      ref.read(isListeningProvider.notifier).state = false;
      _isProcessingAudio = false;
      _accumulatedText = '';
      _shouldProcessAfterStop = false;
      _textController.clear();
      debugPrint('🛑 Continuous listening stopped by user');
    } catch (e) {
      debugPrint('❌ Error stopping continuous listening: $e');
    }
  }

  @override
  void dispose() {
    _speechPauseTimer?.cancel();
    _voiceStartTimer?.cancel();
    _speech.stop();
    _speech.cancel();
    
    _isProcessingAudio = false;
    _accumulatedText = '';
    
    _porcupineManager.delete();
    _recorder.dispose();
    _textController.dispose();
    
    debugPrint('🧹 PromptScreen disposed cleanly');
    
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final voiceState = ref.watch(voiceCommandProvider);
    final currentSettings = ref.watch(settingsProvider);
    final isListening = ref.watch(isListeningProvider);
    final isContinuousActive = ref.watch(isContinuousListeningActiveProvider);

    ref.listen<VoiceCommandState>(voiceCommandProvider, (_, state) {
      if (!mounted) return;
      _handleVoiceCommand(state);
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
              
              if (result['microphoneMode'] == 'continuousListening') {
                await Future.delayed(const Duration(milliseconds: 1000));
                await _initializeContinuousListening();
                debugPrint('🔄 Continuous listening activated from settings');
              } else {
                ref.read(isContinuousListeningActiveProvider.notifier).state = false;
                ref.read(isListeningProvider.notifier).state = false;
                debugPrint('🔄 Switched to voice command mode');
              }
            }
          },
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            VoiceCommandStatusIndicator(
              isListening: isListening || isContinuousActive,
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFF2C2C2E),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                _getMicrophoneInstructions(),
                style: const TextStyle(
                  color: Colors.white, 
                  fontSize: 14,
                  fontWeight: FontWeight.w400,
                ),
                textAlign: TextAlign.center,
              ),
            ),
            const SizedBox(height: 12),
            Expanded(
              child: Align(
                alignment: Alignment.topLeft,
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
            ),
            const SizedBox(height: 20),
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
                Consumer(
                  builder: (context, ref, child) {
                    final currentSettings = ref.watch(settingsProvider);
                    final micMode = currentSettings['microphoneMode'];
                    
                    if (micMode == 'continuousListening') {
                      return ElevatedButton(
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
                      );
                    } else {
                      return ElevatedButton(
                        onPressed: () => _toggleRecording(isListening),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: isListening ? Colors.red : Colors.white,
                          shape: const CircleBorder(),
                          padding: const EdgeInsets.all(16),
                        ),
                        child: const Icon(Icons.mic, size: 28, color: Colors.black),
                      );
                    }
                  },
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _toggleRecording(bool isCurrentlyListening) async {
    final currentSettings = ref.read(settingsProvider);
    
    if (currentSettings['microphoneMode'] == 'voiceCommand') {
      if (isCurrentlyListening) {
        await _stopVoiceRecording();
        _isWakeWordMode = true;
      } else {
        await _startVoiceRecording();
        _isWakeWordMode = false;
      }
    }
  }
}






























// // // // ESTE CODIGO DA PAUSAS NATURALES DEL HABLA CON CUENTA REGRESIVA 7 SEGUNDOS CUANDO HAY SILENCIO PARA DESPUES ENVIAR EL MENSAJE
// // // // ESTE CODIGO DA PAUSAS NATURALES DEL HABLA CON CUENTA REGRESIVA 7 SEGUNDOS CUANDO HAY SILENCIO PARA DESPUES ENVIAR EL MENSAJE
// // // // ESTE CODIGO DA PAUSAS NATURALES DEL HABLA CON CUENTA REGRESIVA 7 SEGUNDOS CUANDO HAY SILENCIO PARA DESPUES ENVIAR EL MENSAJE
// // // // ESTE CODIGO DA PAUSAS NATURALES DEL HABLA CON CUENTA REGRESIVA 7 SEGUNDOS CUANDO HAY SILENCIO PARA DESPUES ENVIAR EL MENSAJE







// import 'dart:async';
// import 'dart:math';
// import 'package:flutter/cupertino.dart';
// import 'package:flutter/material.dart';
// import 'package:flutter_riverpod/flutter_riverpod.dart';
// import 'package:porcupine_flutter/porcupine.dart';
// import 'package:porcupine_flutter/porcupine_error.dart';
// import 'package:porcupine_flutter/porcupine_manager.dart';
// import 'package:speak_and_translate_update/features/translation/presentation/providers/shared_provider.dart' show isContinuousListeningActiveProvider, isListeningProvider, settingsProvider;
// import 'package:speech_to_text/speech_recognition_error.dart' as stt;
// import 'package:speech_to_text/speech_recognition_result.dart' as stt;
// import 'package:speech_to_text/speech_to_text.dart' as stt;
// import '../../domain/repositories/translation_repository.dart';
// import '../providers/audio_recorder_provider.dart';
// import '../providers/voice_command_provider.dart';
// import '../widgets/voice_command_status_inficator.dart';
// import 'settings_screen.dart';

// class PromptScreen extends ConsumerStatefulWidget {
//   const PromptScreen({super.key});

//   @override
//   ConsumerState<PromptScreen> createState() => _PromptScreenState();
// }

// class _PromptScreenState extends ConsumerState<PromptScreen> with TickerProviderStateMixin {
//   late final TextEditingController _textController;
//   late final AudioRecorder _recorder;
//   late PorcupineManager _porcupineManager;
//   late stt.SpeechToText _speech;
//   bool _isWakeWordMode = true;
//   bool _isInitialized = false;
//   String _accumulatedText = ''; // Texto acumulado de todos los segmentos
//   String _currentSpeechSegment = ''; // Segmento actual de voz
//   bool _isProcessingAudio = false;
//   Timer? _voiceStartTimer;
  
//   // Variables para control de silencio
//   Timer? _silenceTimer;
//   Timer? _countdownDisplayTimer;
//   int _silenceCountdown = 0;
//   bool _isSilenceCountdownActive = false;
//   bool _showCountdown = false;
//   String _countdownStatus = '';
  
//   // Animation controllers
//   late AnimationController _pulseController;
//   late Animation<double> _pulseAnimation;
  
//   // UI State management
//   bool _showListeningIndicator = false;
//   String _listeningStatus = '';

//   // Variables para detección de voz
//   List<double> _recentSoundLevels = [];
//   Timer? _soundLevelAnalysisTimer;
//   bool _isHumanSpeechDetected = false;
//   int _consecutiveVoiceDetections = 0;
//   double _speechThreshold = 0.3;
//   Timer? _voiceActivityTimer;
  
//   // Lista de palabras comunes para filtrar ruido
//   final Set<String> _commonWords = {
//     'el', 'la', 'los', 'las', 'un', 'una', 'y', 'o', 'pero', 'que', 'de', 'del', 'en', 'con', 'por', 'para',
//     'se', 'te', 'me', 'le', 'nos', 'les', 'es', 'son', 'está', 'están', 'ser', 'estar', 'tener', 'hacer',
//     'decir', 'ir', 'ver', 'dar', 'saber', 'querer', 'poder', 'venir', 'llevar', 'traer', 'poner', 'salir',
//     'hola', 'buenos', 'días', 'tardes', 'noches', 'gracias', 'por', 'favor', 'perdón', 'disculpa', 'sí', 'no'
//   };

//   // Variables para manejo de habla con pausas
//   Timer? _pauseDetectionTimer;
//   Timer? _speechResumeTimer;
//   bool _isInSpeechPause = false;
//   final int _pauseThreshold = 1800; // 1.8 segundos para detección de pausa
//   final int _resumeThreshold = 400;  // 0.4 segundos para reanudación de voz
//   double _dynamicSpeechThreshold = 0.3; // Umbral dinámico inicial
//   final List<String> _speechSegments = []; // Almacena todos los segmentos de voz

//   @override
//   void initState() {
//     super.initState();
//     _textController = TextEditingController();
//     _recorder = ref.read(audioRecorderProvider);
//     _speech = stt.SpeechToText();

//     // Initialize animation controllers
//     _pulseController = AnimationController(
//       duration: const Duration(seconds: 1),
//       vsync: this,
//     );
//     _pulseAnimation = Tween<double>(begin: 0.8, end: 1.2).animate(
//       CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
//     );

//     _initializeRecorder();
//     _initPorcupine();
//     _startSoundLevelAnalysis();
//   }

//   void _startSoundLevelAnalysis() {
//     _soundLevelAnalysisTimer = Timer.periodic(const Duration(milliseconds: 100), (timer) {
//       if (_recentSoundLevels.isNotEmpty) {
//         // Calcular nivel promedio reciente
//         double avgLevel = _recentSoundLevels.reduce((a, b) => a + b) / _recentSoundLevels.length;
        
//         // Ajuste dinámico del umbral
//         if (_recentSoundLevels.length > 10) {
//           _dynamicSpeechThreshold = max(0.2, min(0.4, avgLevel * 1.3));
//         }
        
//         // Mantener solo los últimos 10 valores
//         if (_recentSoundLevels.length > 10) {
//           _recentSoundLevels.removeAt(0);
//         }
//       }
//     });
//   }

//   double _calculateVariance(List<double> values) {
//     if (values.isEmpty) return 0.0;
    
//     double mean = values.reduce((a, b) => a + b) / values.length;
//     double variance = 0.0;
    
//     for (double value in values) {
//       variance += pow(value - mean, 2);
//     }
    
//     return variance / values.length;
//   }

//   bool _isRealSpeech(String text) {
//     if (text.trim().length < 2) return false;
    
//     List<String> words = text.toLowerCase()
//         .replaceAll(RegExp(r'[^\w\s]'), '')
//         .split(RegExp(r'\s+'))
//         .where((word) => word.isNotEmpty)
//         .toList();
    
//     if (words.isEmpty) return false;
    
//     int knownWords = words.where((word) => 
//         _commonWords.contains(word) || word.length >= 3).length;
    
//     double ratio = knownWords / words.length;
//     return ratio >= 0.3 && words.length >= 1;
//   }

//   Future<void> _initializeRecorder() async {
//     try {
//       await _recorder.init();
//       _isInitialized = true;
//     } catch (e) {
//       debugPrint('Recorder init error: $e');
//     }
//   }

//   void _initPorcupine() async {
//     try {
//       _porcupineManager = await PorcupineManager.fromBuiltInKeywords(
//         'JpbyAC2iGGx74uGLBhyBcELUU830BM3ZcdOA9CT8EQDeozX3n9INBA==',
//         [BuiltInKeyword.JARVIS, BuiltInKeyword.ALEXA],
//         _wakeWordCallback,
//       );
//       await _porcupineManager.start();
//     } on PorcupineException catch (err) {
//       debugPrint("Failed to initialize Porcupine: ${err.message}");
//     }
//   }

//   Future<void> _initializeContinuousListening() async {
//     if (!_isInitialized) return;

//     try {
//       bool available = await _speech.initialize(
//         onStatus: (status) {
//           _updateListeningStatus(status);
//         },
//         onError: (error) {
//           _handleSpeechError(error);
//         },
//       );

//       if (available) {
//         ref.read(isContinuousListeningActiveProvider.notifier).state = true;
//         _startContinuousListening();
//       }
//     } catch (e) {
//       debugPrint('Error initializing continuous listening: $e');
//     }
//   }

//   void _updateListeningStatus(String status) {
//     setState(() {
//       switch (status) {
//         case 'listening':
//           ref.read(isListeningProvider.notifier).state = true;
//           ref.read(isContinuousListeningActiveProvider.notifier).state = true;
//           _showListeningIndicator = true;
//           if (!_isSilenceCountdownActive) {
//             _listeningStatus = 'Escuchando...';
//           }
//           _pulseController.repeat(reverse: true);
//           break;
//         case 'done':
//           ref.read(isListeningProvider.notifier).state = false;
//           _showListeningIndicator = false;
//           _pulseController.stop();
//           _handleSpeechCompletion();
//           break;
//         case 'notListening':
//           ref.read(isListeningProvider.notifier).state = false;
//           _showListeningIndicator = false;
//           _pulseController.stop();
//           break;
//       }
//     });
//   }

//   void _handleSpeechCompletion() {
//     _restartContinuousListeningIfNeeded();
//   }

//   void _handleSpeechError(stt.SpeechRecognitionError error) {
//     setState(() {
//       _showListeningIndicator = false;
//       _pulseController.stop();
//     });

//     if (error.errorMsg == 'error_no_match') {
//       _restartContinuousListeningIfNeeded(isNoMatch: true);
//     } else if (error.errorMsg == 'error_speech_timeout') {
//       _restartContinuousListeningIfNeeded();
//     } else {
//       _restartContinuousListeningIfNeeded(isError: true);
//     }
//   }

//   void _restartContinuousListeningIfNeeded({bool isError = false, bool isNoMatch = false}) {
//     final currentSettings = ref.read(settingsProvider);
//     if (currentSettings['microphoneMode'] == 'continuousListening' && 
//         ref.read(isContinuousListeningActiveProvider) && 
//         !_isProcessingAudio) {
      
//       int delay = isNoMatch ? 800 : (isError ? 2000 : 1200);
      
//       Future.delayed(Duration(milliseconds: delay), () {
//         if (mounted && !_isProcessingAudio && 
//             currentSettings['microphoneMode'] == 'continuousListening' &&
//             ref.read(isContinuousListeningActiveProvider)) {
//           _startContinuousListening();
//         }
//       });
//     }
//   }

//   void _startContinuousListening() {
//     if (!_speech.isAvailable || _isProcessingAudio) return;

//     setState(() {
//       _showListeningIndicator = true;
//       if (!_isSilenceCountdownActive) {
//         _listeningStatus = 'Escuchando...';
//       }
//       _currentSpeechSegment = ''; // Reiniciar segmento actual
//     });
    
//     _voiceStartTimer?.cancel();
//     _resetVoiceDetectionState();
//     _cancelPauseDetection(); // Cancelar cualquier detección de pausa previa

//     _speech.listen(
//       onResult: (result) {
//         _handleSpeechResult(result);
//       },
//       listenFor: const Duration(minutes: 10),
//       pauseFor: const Duration(seconds: 30),
//       partialResults: true,
//       localeId: 'es-ES',
//       listenMode: stt.ListenMode.dictation,
//       cancelOnError: false,
//       onSoundLevelChange: (level) {
//         _handleSoundLevel(level);
//       },
//     );
//   }

//   void _handleSoundLevel(double level) {
//     _recentSoundLevels.add(level);
    
//     if (level > _dynamicSpeechThreshold) {
//       _consecutiveVoiceDetections++;
      
//       _voiceActivityTimer?.cancel();
      
//       if (_consecutiveVoiceDetections >= 3 && !_isHumanSpeechDetected) {
//         _isHumanSpeechDetected = true;
        
//         setState(() {
//           _listeningStatus = 'Voz detectada...';
//         });
//       }
      
//       // Detección de reanudación de voz después de pausa
//       if (_isInSpeechPause) {
//         _speechResumeTimer?.cancel();
//         _speechResumeTimer = Timer( Duration(milliseconds: _resumeThreshold), () {
//           if (mounted) {
//             setState(() {
//               _isInSpeechPause = false;
//               _listeningStatus = 'Escuchando...';
//             });
//             _cancelSilenceCountdown();
//           }
//         });
//       }
      
//       // Cancelar temporizador de pausa si se detecta voz
//       _pauseDetectionTimer?.cancel();
      
//     } else {
//       if (_consecutiveVoiceDetections > 0) {
//         _consecutiveVoiceDetections = max(0, _consecutiveVoiceDetections - 1);
//       }
      
//       _voiceActivityTimer?.cancel();
//       _voiceActivityTimer = Timer( Duration(milliseconds: 1000), () {
//         if (_consecutiveVoiceDetections == 0 && _isHumanSpeechDetected) {
//           _isHumanSpeechDetected = false;
//         }
//       });
      
//       // Detección de pausas en el habla
//       if (!_isInSpeechPause && _consecutiveVoiceDetections == 0) {
//         _pauseDetectionTimer?.cancel();
//         _pauseDetectionTimer = Timer( Duration(milliseconds: _pauseThreshold), () {
//           if (mounted && _consecutiveVoiceDetections == 0) {
//             setState(() {
//               _isInSpeechPause = true;
//               _listeningStatus = 'Pausa detectada...';
//             });
//             _startSilenceCountdown();
//           }
//         });
//       }
//     }
//   }

//   void _cancelPauseDetection() {
//     _pauseDetectionTimer?.cancel();
//     _speechResumeTimer?.cancel();
//     _isInSpeechPause = false;
//   }

//   void _resetVoiceDetectionState() {
//     _consecutiveVoiceDetections = 0;
//     _isHumanSpeechDetected = false;
//     _recentSoundLevels.clear();
//     _voiceActivityTimer?.cancel();
//     _cancelPauseDetection();
//   }

//   void _handleSpeechResult(stt.SpeechRecognitionResult result) {
//     if (result.recognizedWords.isEmpty) return;
    
//     bool isRealVoice = _isRealSpeech(result.recognizedWords) && 
//                       (_isHumanSpeechDetected || _consecutiveVoiceDetections >= 2);
    
//     if (isRealVoice) {
//       _cancelSilenceCountdown();
//     }
    
//     _voiceStartTimer?.cancel();
//     _voiceStartTimer = null;
    
//     setState(() {
//       if (result.finalResult) {
//         if (isRealVoice) {
//           // Acumular segmento de voz
//           _speechSegments.add(result.recognizedWords);
          
//           // Actualizar texto acumulado
//           _accumulatedText = _speechSegments.join(' ');
          
//           // Actualizar segmento actual
//           _currentSpeechSegment = result.recognizedWords;
          
//           _textController.text = _accumulatedText;
//           _listeningStatus = 'Texto capturado...';
          
//           _startSilenceCountdown();
//         }
//       } else {
//         if (isRealVoice && result.recognizedWords.trim().length > 0) {
//           // Actualizar segmento actual
//           _currentSpeechSegment = result.recognizedWords;
          
//           // Mostrar texto acumulado + segmento actual
//           String displayText = _accumulatedText.isNotEmpty 
//               ? '$_accumulatedText $_currentSpeechSegment' 
//               : _currentSpeechSegment;
              
//           _textController.text = displayText;
//           _listeningStatus = 'Procesando voz...';
//         }
//       }
//     });
//   }

//   void _startSilenceCountdown() {
//     if (_isSilenceCountdownActive) return;
    
//     if (_accumulatedText.trim().isEmpty || _isProcessingAudio) return;
    
//     _isSilenceCountdownActive = true;
//     _silenceCountdown = 7;
    
//     setState(() {
//       _showCountdown = true;
//       _countdownStatus = 'silencio detectado (7)';
//       _listeningStatus = _countdownStatus;
//     });

//     _countdownDisplayTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
//       if (!mounted || _isProcessingAudio) {
//         timer.cancel();
//         return;
//       }
      
//       setState(() {
//         _silenceCountdown--;
//         if (_silenceCountdown > 0) {
//           _countdownStatus = 'silencio detectado ($_silenceCountdown)';
//           _listeningStatus = _countdownStatus;
//         } else {
//           _countdownStatus = 'procesando mensaje...';
//           _listeningStatus = _countdownStatus;
//         }
//       });
      
//       if (_silenceCountdown <= 0) {
//         timer.cancel();
//       }
//     });

//     _silenceTimer = Timer(const Duration(seconds: 7), () {
//       if (_isSilenceCountdownActive && !_isProcessingAudio) {
//         _processSilenceCompleted();
//       }
//     });
//   }

//   void _cancelSilenceCountdown() {
//     if (_isSilenceCountdownActive) {
//       _silenceTimer?.cancel();
//       _countdownDisplayTimer?.cancel();
      
//       _isSilenceCountdownActive = false;
//       _silenceCountdown = 0;
      
//       setState(() {
//         _showCountdown = false;
//         _countdownStatus = '';
//         if (!_isProcessingAudio && ref.read(isContinuousListeningActiveProvider)) {
//           _listeningStatus = 'Escuchando...';
//         }
//       });
//     }
//   }

//   void _processSilenceCompleted() {
//     if (_isProcessingAudio || _accumulatedText.trim().isEmpty) return;
    
//     // Combinar todos los segmentos de voz
//     final fullText = _speechSegments.join(' ');
//     final cleanText = fullText
//         .replaceAll(RegExp(r'\b(?:jarvis|alexa)\b', caseSensitive: false), '')
//         .replaceAll(RegExp(r'\s+'), ' ')
//         .trim();
        
//     if (cleanText.length >= 2) {
//       _processRecognizedText(cleanText);
//     } else {
//       _resetContinuousListening();
//     }
//   }

//   Future<void> _processRecognizedText(String text) async {
//     if (text.isEmpty || _isProcessingAudio) return;
    
//     _cancelSilenceCountdown();
    
//     setState(() {
//       _isProcessingAudio = true;
//       _showListeningIndicator = false;
//       _listeningStatus = 'Iniciando conversación...';
//       _pulseController.stop();
//     });
    
//     try {
//       await _speech.stop();
//       await _speech.cancel();
      
//       ref.read(isListeningProvider.notifier).state = false;
      
//       await Future.delayed(const Duration(milliseconds: 300));
      
//       await ref.read(translationRepositoryProvider).playUISound('start_conversation');
      
//       if (mounted) {
//         Navigator.pushNamed(
//           context,
//           '/conversation',
//           arguments: text,
//         ).then((_) {
//           _resetAfterConversation();
//         });
//       }
//     } catch (e) {
//       _resetContinuousListening();
//     } finally {
//       if (mounted) {
//         setState(() {
//           _isProcessingAudio = false;
//         });
//       }
//     }
//   }

//   void _resetAfterConversation() {
//     if (!mounted) return;
    
//     setState(() {
//       _textController.clear();
//       _accumulatedText = '';
//       _currentSpeechSegment = '';
//       _speechSegments.clear(); // Limpiar todos los segmentos
//       _isProcessingAudio = false;
//       _showListeningIndicator = false;
//       _listeningStatus = '';
//       _isWakeWordMode = true;
//       _isInSpeechPause = false;
//     });
    
//     _cancelSilenceCountdown();
//     _resetVoiceDetectionState();
//     _voiceStartTimer?.cancel();
//     _pulseController.stop();
    
//     final currentSettings = ref.read(settingsProvider);
//     if (currentSettings['microphoneMode'] == 'continuousListening' && 
//         ref.read(isContinuousListeningActiveProvider)) {
//       Future.delayed(const Duration(milliseconds: 1500), () {
//         if (mounted && !_isProcessingAudio) {
//           _startContinuousListening();
//         }
//       });
//     }
//   }

//   void _resetContinuousListening() {
//     setState(() {
//       _accumulatedText = '';
//       _currentSpeechSegment = '';
//       _speechSegments.clear();
//       _isProcessingAudio = false;
//       _showListeningIndicator = false;
//       _listeningStatus = '';
//       _isInSpeechPause = false;
//     });
    
//     _textController.clear();
//     _cancelSilenceCountdown();
//     _resetVoiceDetectionState();
//     _voiceStartTimer?.cancel();
//     _pulseController.stop();
//     _restartContinuousListeningIfNeeded();
//   }

//   Future<void> _startConversation() async {
//     if (_textController.text.isNotEmpty) {
//       await ref.read(translationRepositoryProvider).playUISound('start_conversation');

//       if (mounted) {
//         Navigator.pushNamed(
//           context,
//           '/conversation',
//           arguments: _textController.text,
//         ).then((_) => _textController.clear());
//       }
//     }
//   }

//   void _wakeWordCallback(int keywordIndex) async {
//     if (!mounted) return;

//     final currentSettings = ref.read(settingsProvider);
    
//     if (currentSettings['microphoneMode'] == 'voiceCommand') {
//       if (keywordIndex == 0 && _isWakeWordMode) {
//         await _startVoiceRecording();
//         _isWakeWordMode = false;
//       } else if (keywordIndex == 1 && !_isWakeWordMode) {
//         await _stopVoiceRecording();
//         _isWakeWordMode = true;
        
//         if (_textController.text.isNotEmpty) {
//           await _startConversation();
//         }
//       }
//     }
//   }

//   void _handleVoiceCommand(VoiceCommandState state) {
//     if (!mounted) return;
//     setState(() {});

//     if (state.error != null) {
//       ScaffoldMessenger.of(context)
//           .showSnackBar(SnackBar(content: Text(state.error!)));
//     }
//   }

//   Future<void> _startVoiceRecording() async {
//     try {
//       await ref.read(translationRepositoryProvider).playUISound('mic_on');
//       await _recorder.startListening("open");
//       ref.read(isListeningProvider.notifier).state = true;
//       final currentState = ref.read(voiceCommandProvider);
//       ref.read(voiceCommandProvider.notifier).state =
//           currentState.copyWith(isListening: true);
//     } catch (e) {
//       debugPrint('Recording start error: $e');
//     }
//   }

//   Future<void> _stopVoiceRecording() async {
//     try {
//       await ref.read(translationRepositoryProvider).playUISound('mic_off');
//       final path = await _recorder.stopListening();
//       if (path != null) {
//         var text = await ref
//             .read(translationRepositoryProvider)
//             .processAudioInput(path);

//         text = text.replaceAll(RegExp(r'\b(?:jarvis|alexa)\b', caseSensitive: false), '').trim();

//         if (text.isNotEmpty) {
//           _textController.text = text;
//         }
//       }
//     } catch (e) {
//       debugPrint('Recording stop error: $e');
//     } finally {
//       ref.read(isListeningProvider.notifier).state = false;
//       final currentState = ref.read(voiceCommandProvider);
//       ref.read(voiceCommandProvider.notifier).state =
//           currentState.copyWith(isListening: false);
//     }
//   }

//   String _getMicrophoneInstructions() {
//     final currentSettings = ref.read(settingsProvider);
//     final micMode = currentSettings['microphoneMode'];
    
//     if (micMode == 'continuousListening') {
//       final isActive = ref.watch(isContinuousListeningActiveProvider);
//       if (isActive) {
//         return _listeningStatus.isNotEmpty 
//             ? _listeningStatus 
//             : 'Escucha continua activa';
//       } else {
//         return 'Modo escucha continua';
//       }
//     } else {
//       final isListening = ref.watch(isListeningProvider);
//       if (isListening) {
//         return 'Grabando... Di "Alexa" para parar';
//       } else {
//         return _isWakeWordMode 
//           ? 'Modo comando de voz - Di "Jarvis" para empezar'
//           : 'Di "Alexa" para parar e iniciar conversación';
//       }
//     }
//   }

//   Future<void> _stopContinuousListening() async {
//     try {
//       _cancelSilenceCountdown();
//       _resetVoiceDetectionState();
//       _voiceStartTimer?.cancel();
//       await _speech.stop();
//       await _speech.cancel();
//       ref.read(isContinuousListeningActiveProvider.notifier).state = false;
//       ref.read(isListeningProvider.notifier).state = false;
      
//       setState(() {
//         _isProcessingAudio = false;
//         _accumulatedText = '';
//         _currentSpeechSegment = '';
//         _speechSegments.clear();
//         _showListeningIndicator = false;
//         _listeningStatus = '';
//         _isWakeWordMode = true;
//         _isInSpeechPause = false;
//       });
      
//       _textController.clear();
//       _pulseController.stop();
//     } catch (e) {
//       debugPrint('Error stopping listening: $e');
//     }
//   }

//   @override
//   void dispose() {
//     _cancelSilenceCountdown();
//     _resetVoiceDetectionState();
//     _soundLevelAnalysisTimer?.cancel();
//     _voiceActivityTimer?.cancel();
//     _voiceStartTimer?.cancel();
//     _pauseDetectionTimer?.cancel();
//     _speechResumeTimer?.cancel();
    
//     _speech.stop();
//     _speech.cancel();
    
//     _pulseController.dispose();
    
//     _porcupineManager.delete();
//     _recorder.dispose();
//     _textController.dispose();
    
//     super.dispose();
//   }

//   @override
//   Widget build(BuildContext context) {
//     final voiceState = ref.watch(voiceCommandProvider);
//     final currentSettings = ref.watch(settingsProvider);
//     final isListening = ref.watch(isListeningProvider);
//     final isContinuousActive = ref.watch(isContinuousListeningActiveProvider);

//     ref.listen<VoiceCommandState>(voiceCommandProvider, (_, state) {
//       if (!mounted) return;
//       _handleVoiceCommand(state);
//     });

//     return Scaffold(
//       backgroundColor: const Color(0xFF000000),
//       appBar: CupertinoNavigationBar(
//         backgroundColor: const Color(0xFF1C1C1E),
//         border: null,
//         middle: const Text('AI Chat Assistant',
//             style: TextStyle(
//                 color: Colors.white,
//                 fontSize: 17,
//                 fontWeight: FontWeight.w600)),
//         trailing: CupertinoButton(
//           padding: EdgeInsets.zero,
//           child: const Icon(CupertinoIcons.gear,
//               color: CupertinoColors.systemGrey, size: 28),
//           onPressed: () async {
//             final currentSettings = ref.read(settingsProvider);
            
//             final result = await Navigator.push(
//               context,
//               MaterialPageRoute(
//                 builder: (context) => SettingsScreen(initialSettings: currentSettings),
//               ),
//             );
            
//             if (result != null && result is Map<String, dynamic>) {
//               await _stopContinuousListening();
//               await Future.delayed(const Duration(milliseconds: 500));
              
//               ref.read(settingsProvider.notifier).state = result;
              
//               if (result['microphoneMode'] == 'continuousListening') {
//                 await Future.delayed(const Duration(milliseconds: 1000));
//                 await _initializeContinuousListening();
//               } else {
//                 ref.read(isContinuousListeningActiveProvider.notifier).state = false;
//                 ref.read(isListeningProvider.notifier).state = false;
//               }
//             }
//           },
//         ),
//       ),
//       body: Padding(
//         padding: const EdgeInsets.all(16.0),
//         child: Column(
//           children: [
//             VoiceCommandStatusIndicator(
//               isListening: isListening || isContinuousActive,
//             ),
//             const SizedBox(height: 8),
//             Container(
//               padding: const EdgeInsets.all(12),
//               decoration: BoxDecoration(
//                 color: _showCountdown ? const Color(0xFF4A4A4C) : const Color(0xFF2C2C2E),
//                 borderRadius: BorderRadius.circular(8),
//                 border: _showCountdown ? Border.all(
//                   color: _silenceCountdown <= 3 ? Colors.red : Colors.orange,
//                   width: 2,
//                 ) : (_isHumanSpeechDetected ? Border.all(
//                   color: Colors.green,
//                   width: 1,
//                 ) : null),
//               ),
//               child: Row(
//                 mainAxisAlignment: MainAxisAlignment.center,
//                 children: [
//                   if (_isHumanSpeechDetected && !_showCountdown) ...[
//                     AnimatedBuilder(
//                       animation: _pulseAnimation,
//                       builder: (context, child) {
//                         return Transform.scale(
//                           scale: _pulseAnimation.value,
//                           child: Container(
//                             width: 30,
//                             height: 30,
//                             decoration: BoxDecoration(
//                               shape: BoxShape.circle,
//                               color: Colors.green,
//                               boxShadow: [
//                                 BoxShadow(
//                                   color: Colors.green.withOpacity(0.5),
//                                   blurRadius: 6,
//                                   spreadRadius: 1,
//                                 ),
//                               ],
//                             ),
//                             child: const Icon(
//                               Icons.mic,
//                               color: Colors.white,
//                               size: 16,
//                             ),
//                           ),
//                         );
//                       },
//                     ),
//                     const SizedBox(width: 12),
//                   ],
                  
//                   if (_showCountdown) ...[
//                     AnimatedBuilder(
//                       animation: _pulseAnimation,
//                       builder: (context, child) {
//                         return Transform.scale(
//                           scale: _pulseAnimation.value,
//                           child: Container(
//                             width: 35,
//                             height: 35,
//                             decoration: BoxDecoration(
//                               shape: BoxShape.circle,
//                               color: _silenceCountdown <= 3 ? Colors.red : Colors.orange,
//                               boxShadow: [
//                                 BoxShadow(
//                                   color: (_silenceCountdown <= 3 ? Colors.red : Colors.orange).withOpacity(0.5),
//                                   blurRadius: 8,
//                                   spreadRadius: 2,
//                                 ),
//                               ],
//                             ),
//                             child: Center(
//                               child: Text(
//                                 '$_silenceCountdown',
//                                 style: const TextStyle(
//                                   color: Colors.white,
//                                   fontSize: 18,
//                                   fontWeight: FontWeight.bold,
//                                 ),
//                               ),
//                             ),
//                           ),
//                         );
//                       },
//                     ),
//                     const SizedBox(width: 12),
//                   ],
                  
//                   Expanded(
//                     child: Text(
//                       _getMicrophoneInstructions(),
//                       style: TextStyle(
//                         color: Colors.white,
//                         fontSize: 14,
//                         fontWeight: _showCountdown || _isHumanSpeechDetected ? FontWeight.w600 : FontWeight.w400,
//                       ),
//                       textAlign: TextAlign.center,
//                     ),
//                   ),
//                 ],
//               ),
//             ),
            
//             const SizedBox(height: 12),
//             Expanded(
//               child: Align(
//                 alignment: Alignment.topLeft,
//                 child: CupertinoTextField(
//                   controller: _textController,
//                   maxLines: null,
//                   style: const TextStyle(color: Colors.white, fontSize: 17),
//                   placeholder: 'Escribe tu mensaje aquí',
//                   placeholderStyle: const TextStyle(
//                       color: CupertinoColors.placeholderText, fontSize: 17),
//                   decoration: BoxDecoration(
//                     color: const Color(0xFF2C2C2E),
//                     borderRadius: BorderRadius.circular(12),
//                     border: Border.all(
//                       color: const Color(0xFF3A3A3C),
//                       width: 0.5,
//                     ),
//                   ),
//                   padding: const EdgeInsets.all(16),
//                 ),
//               ),
//             ),
//             const SizedBox(height: 20),
//             Row(
//               children: [
//                 Expanded(
//                   child: ElevatedButton(
//                     onPressed: _startConversation,
//                     style: ElevatedButton.styleFrom(
//                       backgroundColor: const Color.fromARGB(255, 61, 62, 63),
//                       minimumSize: const Size(double.infinity, 50),
//                     ),
//                     child: const Text('Iniciar conversación',
//                         style: TextStyle(color: Colors.white)),
//                   ),
//                 ),
//                 const SizedBox(width: 16),
//                 Consumer(
//                   builder: (context, ref, child) {
//                     final currentSettings = ref.watch(settingsProvider);
//                     final micMode = currentSettings['microphoneMode'];
                    
//                     if (micMode == 'continuousListening') {
//                       return ElevatedButton(
//                         onPressed: () async {
//                           if (isContinuousActive) {
//                             await _stopContinuousListening();
//                           } else {
//                             if (!_isProcessingAudio) {
//                               await _initializeContinuousListening();
//                             }
//                           }
//                         },
//                         style: ElevatedButton.styleFrom(
//                           backgroundColor: isContinuousActive ? Colors.red : Colors.white,
//                           shape: const CircleBorder(),
//                           padding: const EdgeInsets.all(16),
//                         ),
//                         child: Icon(
//                           isContinuousActive ? Icons.mic_off : Icons.mic,
//                           size: 28,
//                           color: isContinuousActive ? Colors.white : Colors.black,
//                         ),
//                       );
//                     } else {
//                       return ElevatedButton(
//                         onPressed: () => _toggleRecording(isListening),
//                         style: ElevatedButton.styleFrom(
//                           backgroundColor: isListening ? Colors.red : Colors.white,
//                           shape: const CircleBorder(),
//                           padding: const EdgeInsets.all(16),
//                         ),
//                         child: Icon(
//                           isListening ? Icons.mic_off : Icons.mic,
//                           size: 28,
//                           color: isListening ? Colors.white : Colors.black,
//                         ),
//                       );
//                     }
//                   },
//                 ),
//               ],
//             ),
//           ],
//         ),
//       ),
//     );
//   }

//   Future<void> _toggleRecording(bool isCurrentlyListening) async {
//     final currentSettings = ref.read(settingsProvider);
    
//     if (currentSettings['microphoneMode'] == 'voiceCommand') {
//       if (isCurrentlyListening) {
//         await _stopVoiceRecording();
//         _isWakeWordMode = true;
//       } else {
//         await _startVoiceRecording();
//         _isWakeWordMode = false;
//       }
//     }
//   }
// }
