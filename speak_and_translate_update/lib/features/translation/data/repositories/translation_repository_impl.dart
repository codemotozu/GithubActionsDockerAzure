// Updated translation_repository_impl.dart with mother tongue support

import 'package:audio_session/audio_session.dart';
import 'package:http/http.dart' as http;
import 'package:http/io_client.dart';
import 'dart:convert';
import 'dart:io';
import 'package:path/path.dart' as path;
import '../../domain/entities/translation.dart';
import '../../domain/repositories/translation_repository.dart';
import 'package:just_audio/just_audio.dart';
import 'package:http_parser/http_parser.dart';

class AudioMetadata {
  final String album;
  final String title;
  final Uri artwork;

  const AudioMetadata({
    required this.album,
    required this.title,
    required this.artwork,
  });
}

class TranslationStylePreferences {
  final bool germanNative;
  final bool germanColloquial;
  final bool germanInformal;
  final bool germanFormal;
  final bool englishNative;
  final bool englishColloquial;
  final bool englishInformal;
  final bool englishFormal;
  final bool germanWordByWord;
  final bool englishWordByWord;
  final String motherTongue; // NEW: Mother tongue support

  TranslationStylePreferences({
    this.germanNative = false,
    this.germanColloquial = false,
    this.germanInformal = false,
    this.germanFormal = false,
    this.englishNative = false,
    this.englishColloquial = false,
    this.englishInformal = false,
    this.englishFormal = false,
    this.germanWordByWord = true,
    this.englishWordByWord = false,
    this.motherTongue = 'spanish', // Default to Spanish
  });

  Map<String, dynamic> toJson() {
    return {
      'german_native': germanNative,
      'german_colloquial': germanColloquial,
      'german_informal': germanInformal,
      'german_formal': germanFormal,
      'english_native': englishNative,
      'english_colloquial': englishColloquial,
      'english_informal': englishInformal,
      'english_formal': englishFormal,
      'german_word_by_word': germanWordByWord,
      'english_word_by_word': englishWordByWord,
      'mother_tongue': motherTongue, // NEW: Include mother tongue in API payload
    };
  }

  factory TranslationStylePreferences.fromSettings(Map<String, dynamic> settings) {
    return TranslationStylePreferences(
      germanNative: settings['germanNative'] as bool? ?? false,
      germanColloquial: settings['germanColloquial'] as bool? ?? false,
      germanInformal: settings['germanInformal'] as bool? ?? false,
      germanFormal: settings['germanFormal'] as bool? ?? false,
      englishNative: settings['englishNative'] as bool? ?? false,
      englishColloquial: settings['englishColloquial'] as bool? ?? false,
      englishInformal: settings['englishInformal'] as bool? ?? false,
      englishFormal: settings['englishFormal'] as bool? ?? false,
      germanWordByWord: settings['germanWordByWord'] as bool? ?? true,
      englishWordByWord: settings['englishWordByWord'] as bool? ?? false,
      motherTongue: settings['motherTongue'] as String? ?? 'spanish', // NEW: Extract mother tongue
    );
  }
}

class TranslationRepositoryImpl implements TranslationRepository {
  // final String baseUrl = 'http://10.0.2.2:8000'; // here you can hear the translaion in my local machine dont forget to update main.py
  // final String baseUrl = 'http://192.168.0.2:8000'; // android cellphone ...
  final String baseUrl = 'https://speak-translate-docker-and-azure.thankfulisland-32dcba80.francecentral.azurecontainerapps.io';
  static const timeoutDuration = Duration(seconds: 240);
  late AudioPlayer _audioPlayer = AudioPlayer();
  final AudioPlayer _soundPlayer = AudioPlayer(); // For completion sound
  final HttpClient _httpClient = HttpClient()
    ..badCertificateCallback = (cert, host, port) => true;
  late final http.Client _client;
  final AudioPlayer _uiSoundPlayer = AudioPlayer();

  TranslationRepositoryImpl() {
    _client = IOClient(_httpClient);
  }

  String _getAudioUrl(String audioPath) {
    final filename = path.basename(audioPath);
    final encodedFilename = Uri.encodeComponent(filename);
    return '$baseUrl/api/audio/$encodedFilename';
  }

  @override
  Future<void> playUISound(String soundType) async {
    try {
      String soundPath;
      switch (soundType) {
        case 'mic_on':
          soundPath = 'assets/sounds/open.wav';
          break;
        case 'mic_off':
          soundPath = 'assets/sounds/close.wav';
          break;
        case 'start_conversation':
          soundPath = 'assets/sounds/send.wav';
          break;
        default:
          return;
      }
      
      await _uiSoundPlayer.setAsset(soundPath);
      await _uiSoundPlayer.play();
    } catch (e) {
      print('Error playing UI sound: $e');
    }
  }

  @override
  Future<void> playAudio(String audioPath) async {
    final session = await AudioSession.instance;
    await session.configure(const AudioSessionConfiguration.speech());

    try {
      // Release previous resources
      await _audioPlayer.stop();
      await _audioPlayer.dispose(); // Add this line

      // Reinitialize player
      _audioPlayer = AudioPlayer(); // Recreate the instance
      
      final audioUrl = _getAudioUrl(audioPath);
      print('Playing audio from URL: $audioUrl');

      // Set source with proper headers
      await _audioPlayer.setAudioSource(
        AudioSource.uri(
          Uri.parse(audioUrl),
          headers: {"Content-Type": "audio/mpeg"},
        ),
      );

      // Handle playback completion
      _audioPlayer.playbackEventStream.listen(
        (event) {},
        onError: (e, st) => print('Player error: $e'),
      );

      await _audioPlayer.play();
      await _audioPlayer.playerStateStream.firstWhere(
        (state) => state.processingState == ProcessingState.completed
      );
    } catch (e) {
      print('Audio playback error: $e');
      await _audioPlayer.stop();
    }
  }

  @override
  Future<void> playCompletionSound() async {
    try {
      await _soundPlayer.setAsset('assets/sounds/Blink.wav');
      await _soundPlayer.play();
    } catch (e) {
      print('Error playing completion sound: $e');
    }
  }

  // Updated getTranslation method with mother tongue support
  @override
  Future<Translation> getTranslation(String text, {Map<String, dynamic>? stylePreferences}) async {
    try {
      // Create style preferences object with mother tongue support
      TranslationStylePreferences? preferences;
      if (stylePreferences != null) {
        preferences = TranslationStylePreferences.fromSettings(stylePreferences);
      }

      // Log the mother tongue being used
      print('\n🌐 REPOSITORY: Making API call with:');
      print('   Text: "$text"');
      print('   Mother Tongue: ${preferences?.motherTongue ?? "not specified"}');
      print('   German word-by-word: ${preferences?.germanWordByWord ?? false}');
      print('   English word-by-word: ${preferences?.englishWordByWord ?? false}');
      print('   German styles: Native=${preferences?.germanNative}, Colloquial=${preferences?.germanColloquial}, Informal=${preferences?.germanInformal}, Formal=${preferences?.germanFormal}');
      print('   English styles: Native=${preferences?.englishNative}, Colloquial=${preferences?.englishColloquial}, Informal=${preferences?.englishInformal}, Formal=${preferences?.englishFormal}');

      // Prepare request body with mother tongue support
      final Map<String, dynamic> requestBody = {
        'text': text,
        'source_lang': preferences?.motherTongue ?? 'spanish',  // Use mother tongue as source
        'target_lang': 'multi',  // Multiple target languages based on mother tongue
      };

      // Add style preferences if provided (includes mother tongue)
      if (preferences != null) {
        requestBody['style_preferences'] = preferences.toJson();
        print('   📤 Style preferences JSON: ${jsonEncode(preferences.toJson())}');
      }

      print('📤 Full request body: ${jsonEncode(requestBody)}');

      final response = await _client.post(
        Uri.parse('$baseUrl/api/conversation'),
        headers: {
          'Content-Type': 'application/json; charset=UTF-8',
          'Accept': 'application/json; charset=UTF-8',
        },
        body: utf8.encode(json.encode(requestBody)),
      ).timeout(timeoutDuration);

      print('📥 API Response status: ${response.statusCode}');

      if (response.statusCode == 200) {
        final String decodedBody = utf8.decode(response.bodyBytes);
        print('📥 Response body preview: ${decodedBody.substring(0, min(200, decodedBody.length))}...');
        
        final Map<String, dynamic> data = json.decode(decodedBody);
        final translation = Translation.fromJson(data);
        
        if (translation.audioPath != null) {
          final audioUrl = _getAudioUrl(translation.audioPath!);
          print('🎵 Audio URL generated: $audioUrl');
        } else {
          print('🔇 No audio path in response');
          
          // Additional debugging for audio generation
          if (preferences?.germanWordByWord == true || preferences?.englishWordByWord == true) {
            print('⚠️ WARNING: Word-by-word audio was requested but no audio path returned');
            print('   German word-by-word requested: ${preferences?.germanWordByWord}');
            print('   English word-by-word requested: ${preferences?.englishWordByWord}');
          }
        }
        
        print('✅ Translation completed successfully');
        return translation;
      } else {
        final errorBody = utf8.decode(response.bodyBytes);
        print('❌ Server error ${response.statusCode}: $errorBody');
        throw Exception('Server error: ${response.statusCode}\n$errorBody');
      }
    } catch (e) {
      print('❌ Error in getTranslation: $e');
      if (e.toString().contains('Connection refused')) {
        throw Exception('Cannot connect to server. Please make sure the server is running at $baseUrl');
      }
      rethrow;
    }
  }

  @override
  Future<void> stopAudio() async {
    await _audioPlayer.stop();
  }

  @override
  void dispose() {
    _client.close();
    _audioPlayer.dispose();
    _soundPlayer.dispose(); // Dispose the sound player
    _uiSoundPlayer.dispose();
  }

  // Update processAudioInput to support different mother tongue languages
  @override
  Future<String> processAudioInput(String audioPath) async {
    try {
      final file = File(audioPath);
      final mimeType = _getMimeType(audioPath);
      
      final request = http.MultipartRequest('POST', Uri.parse('$baseUrl/api/speech-to-text'))
        ..files.add(await http.MultipartFile.fromPath(
          'file',
          audioPath,
          contentType: MediaType.parse(mimeType),
        ));

      final response = await request.send().timeout(timeoutDuration);
      
      if (response.statusCode == 200) {
        final responseText = await response.stream.bytesToString();
        final responseData = json.decode(responseText);
        return responseData['text'];
      } else {
        final errorBody = await response.stream.bytesToString();
        throw Exception('ASR Error ${response.statusCode}: $errorBody');
      }
    } catch (e) {
      print('Audio processing error: $e');
      rethrow;
    }
  }

  String _getMimeType(String filePath) {
    final ext = path.extension(filePath).toLowerCase();
    switch (ext) {
      case '.wav':
        return 'audio/wav; codecs=1';
      case '.mp3':
        return 'audio/mpeg; codecs=mp3';
      case '.aac':
        return 'audio/aac; codecs=mp4a.40.2';
      case '.ogg':
        return 'audio/ogg; codecs=vorbis';
      default:
        throw FormatException('Unsupported audio format: $ext');
    }
  }

  // Helper function for min operation
  int min(int a, int b) => a < b ? a : b;
}