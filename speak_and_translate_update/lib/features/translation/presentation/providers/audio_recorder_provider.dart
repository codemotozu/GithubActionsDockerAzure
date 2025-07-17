import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_sound/flutter_sound.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:speak_and_translate_update/features/translation/presentation/providers/shared_provider.dart' show isListeningProvider;

final audioRecorderProvider = Provider<AudioRecorder>((ref) => AudioRecorder(ref));

class AudioRecorder {
  final FlutterSoundRecorder _recorder = FlutterSoundRecorder();
  bool _isInitialized = false;
  String? _path;
  final Ref _ref;

  AudioRecorder(this._ref);

  bool get isListening => _ref.read(isListeningProvider);

  Future<void> init() async {
    if (!_isInitialized) {
      final status = await Permission.microphone.request();
      if (status != PermissionStatus.granted) {
        throw RecordingPermissionException('Microphone permission not granted');
      }
      await _recorder.openRecorder();
      _isInitialized = true;
    }
  }

  Future<void> startListening(String command) async {
    if (!_isInitialized) await init();
    
    if (command.toLowerCase() == "open") {
      try {
        final dir = await getTemporaryDirectory();
        _path = '${dir.path}/audio_${DateTime.now().millisecondsSinceEpoch}.aac';
        await _recorder.startRecorder(
          toFile: _path,
          codec: Codec.aacADTS,
        );
        _ref.read(isListeningProvider.notifier).state = true;
      } catch (e) {
        debugPrint('Error starting recording: $e');
      }
    }
  }

  Future<String?> stopListening() async {
    try {
      if (_recorder.isRecording) {
        await _recorder.stopRecorder();
        _ref.read(isListeningProvider.notifier).state = false;
        return _path;
      }
      return null;
    } catch (e) {
      debugPrint('Error stopping recording: $e');
      return null;
    }
  }

  Future<void> start() async {
    if (!_isInitialized) await init();
    try {
      final dir = await getTemporaryDirectory();
      _path = '${dir.path}/audio_${DateTime.now().millisecondsSinceEpoch}.aac';
      await _recorder.startRecorder(
        toFile: _path,
        codec: Codec.aacADTS,
      );
      _ref.read(isListeningProvider.notifier).state = true;
    } catch (e) {
      debugPrint('Error recording audio: $e');
    }
  }

  Future<String?> stop() async {
    try {
      if (_recorder.isRecording) {
        await _recorder.stopRecorder();
        _ref.read(isListeningProvider.notifier).state = false;
        return _path;
      }
      return null;
    } catch (e) {
      debugPrint('Error stopping recording: $e');
      return null;
    }
  }

  Future<bool> isRecording() async {
    return _recorder.isRecording;
  }

  Future<void> dispose() async {
    if (_isInitialized) {
      await _recorder.closeRecorder();
      _isInitialized = false;
    }
  }
}