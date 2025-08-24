// neural_audio_player_widget.dart - Word-by-Word Audio Learning Widget

import 'package:flutter/material.dart';
import 'package:audioplayers/audioplayers.dart';
import 'dart:async';

class NeuralAudioPlayerWidget extends StatefulWidget {
  final Map<String, Map<String, String>>? wordByWordData;
  final String? mainAudioPath;
  final bool showWordByWordAudio;
  final Function(String)? onWordSelected;

  const NeuralAudioPlayerWidget({
    super.key,
    this.wordByWordData,
    this.mainAudioPath,
    this.showWordByWordAudio = true,
    this.onWordSelected,
  });

  @override
  State<NeuralAudioPlayerWidget> createState() => _NeuralAudioPlayerWidgetState();
}

class _NeuralAudioPlayerWidgetState extends State<NeuralAudioPlayerWidget>
    with TickerProviderStateMixin {
  
  final AudioPlayer _audioPlayer = AudioPlayer();
  final AudioPlayer _wordPlayer = AudioPlayer();
  
  late AnimationController _playingController;
  late AnimationController _waveController;
  
  late Animation<double> _playingAnimation;
  late Animation<double> _waveAnimation;
  
  bool _isPlaying = false;
  bool _isPlayingWord = false;
  String _currentPlayingWord = '';
  Duration _currentPosition = Duration.zero;
  Duration _totalDuration = Duration.zero;
  
  List<String> _wordSequence = [];
  int _currentWordIndex = -1;
  Timer? _wordPlayTimer;
  
  @override
  void initState() {
    super.initState();
    
    _playingController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );
    
    _waveController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    )..repeat(reverse: true);
    
    _playingAnimation = Tween<double>(begin: 1.0, end: 1.2).animate(
      CurvedAnimation(parent: _playingController, curve: Curves.easeInOut)
    );
    
    _waveAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _waveController, curve: Curves.easeInOut)
    );
    
    _setupAudioPlayer();
    _prepareWordSequence();
  }
  
  @override
  void dispose() {
    _playingController.dispose();
    _waveController.dispose();
    _audioPlayer.dispose();
    _wordPlayer.dispose();
    _wordPlayTimer?.cancel();
    super.dispose();
  }
  
  void _setupAudioPlayer() {
    _audioPlayer.onPlayerStateChanged.listen((PlayerState state) {
      setState(() {
        _isPlaying = state == PlayerState.playing;
      });
      
      if (_isPlaying) {
        _playingController.forward();
      } else {
        _playingController.reverse();
      }
    });
    
    _audioPlayer.onPositionChanged.listen((Duration position) {
      setState(() {
        _currentPosition = position;
      });
    });
    
    _audioPlayer.onDurationChanged.listen((Duration duration) {
      setState(() {
        _totalDuration = duration;
      });
    });
    
    // Word player setup
    _wordPlayer.onPlayerStateChanged.listen((PlayerState state) {
      setState(() {
        _isPlayingWord = state == PlayerState.playing;
      });
    });
  }
  
  void _prepareWordSequence() {
    if (widget.wordByWordData == null) return;
    
    _wordSequence.clear();
    
    // Sort by order if available, otherwise use insertion order
    var sortedEntries = widget.wordByWordData!.entries.toList();
    sortedEntries.sort((a, b) {
      int orderA = int.tryParse(a.value['order'] ?? '0') ?? 0;
      int orderB = int.tryParse(b.value['order'] ?? '0') ?? 0;
      return orderA.compareTo(orderB);
    });
    
    for (var entry in sortedEntries) {
      String source = entry.value['source'] ?? '';
      String target = entry.value['spanish'] ?? '';
      if (source.isNotEmpty && target.isNotEmpty) {
        _wordSequence.add('$source → $target');
      }
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            Colors.orange[900]!.withOpacity(0.2),
            Colors.amber[900]!.withOpacity(0.2),
            Colors.yellow[900]!.withOpacity(0.2),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.orange, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildHeader(),
          const SizedBox(height: 16),
          
          if (widget.mainAudioPath != null) ...[
            _buildMainAudioControls(),
            const SizedBox(height: 16),
          ],
          
          if (widget.showWordByWordAudio && _wordSequence.isNotEmpty) ...[
            _buildWordByWordControls(),
            const SizedBox(height: 16),
            _buildWordSequenceDisplay(),
          ],
        ],
      ),
    );
  }
  
  Widget _buildHeader() {
    return Row(
      children: [
        AnimatedBuilder(
          animation: _waveAnimation,
          builder: (context, child) {
            return Transform.scale(
              scale: 1.0 + (_waveAnimation.value * 0.2),
              child: Icon(
                Icons.graphic_eq,
                color: Colors.orange.withOpacity(0.7 + (_waveAnimation.value * 0.3)),
                size: 28,
              ),
            );
          },
        ),
        const SizedBox(width: 12),
        const Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Neural Audio Learning',
                style: TextStyle(
                  color: Colors.orange,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                'Word-by-Word Audio Translation',
                style: TextStyle(
                  color: Colors.white70,
                  fontSize: 14,
                ),
              ),
            ],
          ),
        ),
        _buildPlaybackSpeedControl(),
      ],
    );
  }
  
  Widget _buildPlaybackSpeedControl() {
    return PopupMenuButton<double>(
      icon: const Icon(Icons.speed, color: Colors.orange),
      onSelected: (double speed) {
        _audioPlayer.setPlaybackRate(speed);
        _wordPlayer.setPlaybackRate(speed);
      },
      itemBuilder: (BuildContext context) => <PopupMenuEntry<double>>[
        const PopupMenuItem<double>(
          value: 0.5,
          child: Text('0.5x Speed'),
        ),
        const PopupMenuItem<double>(
          value: 0.75,
          child: Text('0.75x Speed'),
        ),
        const PopupMenuItem<double>(
          value: 1.0,
          child: Text('Normal Speed'),
        ),
        const PopupMenuItem<double>(
          value: 1.25,
          child: Text('1.25x Speed'),
        ),
        const PopupMenuItem<double>(
          value: 1.5,
          child: Text('1.5x Speed'),
        ),
      ],
    );
  }
  
  Widget _buildMainAudioControls() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.3),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Row(
            children: [
              const Icon(Icons.music_note, color: Colors.orange, size: 20),
              const SizedBox(width: 8),
              const Text(
                'Full Translation Audio',
                style: TextStyle(
                  color: Colors.orange,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          
          Row(
            children: [
              AnimatedBuilder(
                animation: _playingAnimation,
                builder: (context, child) {
                  return Transform.scale(
                    scale: _playingAnimation.value,
                    child: IconButton(
                      onPressed: _toggleMainAudio,
                      icon: Icon(
                        _isPlaying ? Icons.pause_circle : Icons.play_circle,
                        size: 48,
                        color: Colors.orange,
                      ),
                    ),
                  );
                },
              ),
              
              Expanded(
                child: Column(
                  children: [
                    Slider(
                      value: _currentPosition.inMilliseconds.toDouble(),
                      max: _totalDuration.inMilliseconds.toDouble(),
                      onChanged: (value) {
                        _audioPlayer.seek(Duration(milliseconds: value.round()));
                      },
                      activeColor: Colors.orange,
                      inactiveColor: Colors.orange.withOpacity(0.3),
                    ),
                    
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            _formatDuration(_currentPosition),
                            style: const TextStyle(color: Colors.white70, fontSize: 12),
                          ),
                          Text(
                            _formatDuration(_totalDuration),
                            style: const TextStyle(color: Colors.white70, fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
  
  Widget _buildWordByWordControls() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.amber[900]!.withOpacity(0.2),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.amber, width: 1),
      ),
      child: Column(
        children: [
          Row(
            children: [
              const Icon(Icons.hearing, color: Colors.amber, size: 20),
              const SizedBox(width: 8),
              const Text(
                'Word-by-Word Learning',
                style: TextStyle(
                  color: Colors.amber,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              ElevatedButton.icon(
                onPressed: _startWordByWordPlayback,
                icon: const Icon(Icons.play_arrow),
                label: const Text('Play All'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.amber,
                  foregroundColor: Colors.black,
                ),
              ),
              
              ElevatedButton.icon(
                onPressed: _isPlayingWord ? null : _playCurrentWord,
                icon: const Icon(Icons.volume_up),
                label: const Text('Current'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.orange,
                  foregroundColor: Colors.white,
                ),
              ),
              
              ElevatedButton.icon(
                onPressed: _stopWordPlayback,
                icon: const Icon(Icons.stop),
                label: const Text('Stop'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red[700],
                  foregroundColor: Colors.white,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
  
  Widget _buildWordSequenceDisplay() {
    return Container(
      height: 200,
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.3),
        borderRadius: BorderRadius.circular(12),
      ),
      child: ListView.builder(
        itemCount: _wordSequence.length,
        itemBuilder: (context, index) {
          bool isCurrentWord = index == _currentWordIndex;
          bool hasPlayed = index < _currentWordIndex;
          
          return AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: isCurrentWord 
                  ? Colors.amber.withOpacity(0.3)
                  : hasPlayed 
                    ? Colors.green.withOpacity(0.2)
                    : Colors.transparent,
              borderRadius: BorderRadius.circular(8),
              border: isCurrentWord 
                  ? Border.all(color: Colors.amber, width: 2)
                  : hasPlayed
                    ? Border.all(color: Colors.green, width: 1)
                    : Border.all(color: Colors.grey.withOpacity(0.3), width: 1),
            ),
            child: Row(
              children: [
                Container(
                  width: 24,
                  height: 24,
                  decoration: BoxDecoration(
                    color: isCurrentWord 
                        ? Colors.amber
                        : hasPlayed 
                          ? Colors.green
                          : Colors.grey,
                    shape: BoxShape.circle,
                  ),
                  child: Center(
                    child: Text(
                      '${index + 1}',
                      style: TextStyle(
                        color: isCurrentWord || hasPlayed ? Colors.black : Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
                
                const SizedBox(width: 12),
                
                Expanded(
                  child: Text(
                    _wordSequence[index],
                    style: TextStyle(
                      color: isCurrentWord 
                          ? Colors.amber
                          : hasPlayed 
                            ? Colors.green
                            : Colors.white70,
                      fontSize: 14,
                      fontWeight: isCurrentWord ? FontWeight.bold : FontWeight.normal,
                    ),
                  ),
                ),
                
                IconButton(
                  onPressed: () => _playSpecificWord(index),
                  icon: Icon(
                    Icons.play_circle_outline,
                    color: isCurrentWord ? Colors.amber : Colors.white54,
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
  
  void _toggleMainAudio() async {
    if (_isPlaying) {
      await _audioPlayer.pause();
    } else {
      if (widget.mainAudioPath != null) {
        await _audioPlayer.play(DeviceFileSource(widget.mainAudioPath!));
      }
    }
  }
  
  void _startWordByWordPlayback() {
    _currentWordIndex = 0;
    _playCurrentWord();
  }
  
  void _playCurrentWord() async {
    if (_currentWordIndex >= 0 && _currentWordIndex < _wordSequence.length) {
      setState(() {
        _currentPlayingWord = _wordSequence[_currentWordIndex];
      });
      
      // Highlight the current word
      widget.onWordSelected?.call(_currentPlayingWord);
      
      // Generate TTS for the current word (this would integrate with your TTS service)
      await _generateAndPlayWordAudio(_currentPlayingWord);
      
      // Move to next word after playing
      _wordPlayTimer = Timer(const Duration(milliseconds: 2000), () {
        setState(() {
          _currentWordIndex++;
        });
        
        if (_currentWordIndex < _wordSequence.length) {
          _playCurrentWord();
        } else {
          // Finished playing all words
          _currentWordIndex = -1;
          _currentPlayingWord = '';
        }
      });
    }
  }
  
  void _playSpecificWord(int index) {
    setState(() {
      _currentWordIndex = index;
    });
    _playCurrentWord();
  }
  
  void _stopWordPlayback() {
    _wordPlayTimer?.cancel();
    _wordPlayer.stop();
    setState(() {
      _currentWordIndex = -1;
      _currentPlayingWord = '';
      _isPlayingWord = false;
    });
  }
  
  Future<void> _generateAndPlayWordAudio(String wordPair) async {
    // This would integrate with your TTS service
    // For now, simulate audio playback
    
    setState(() {
      _isPlayingWord = true;
    });
    
    // Simulate TTS generation and playback
    await Future.delayed(const Duration(milliseconds: 1500));
    
    setState(() {
      _isPlayingWord = false;
    });
  }
  
  String _formatDuration(Duration duration) {
    String twoDigits(int n) => n.toString().padLeft(2, '0');
    String twoDigitMinutes = twoDigits(duration.inMinutes.remainder(60));
    String twoDigitSeconds = twoDigits(duration.inSeconds.remainder(60));
    return '$twoDigitMinutes:$twoDigitSeconds';
  }
}