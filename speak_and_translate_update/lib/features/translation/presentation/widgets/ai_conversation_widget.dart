// ai_conversation_widget.dart - AI Conversation-Style Translation Display

import 'package:flutter/material.dart';
import 'package:audioplayers/audioplayers.dart';

class AIConversationWidget extends StatefulWidget {
  final Map<String, dynamic> translationData;
  final String? audioPath;
  final Function(String)? onWordSelected;
  final Function()? onPlayAll;

  const AIConversationWidget({
    super.key,
    required this.translationData,
    this.audioPath,
    this.onWordSelected,
    this.onPlayAll,
  });

  @override
  State<AIConversationWidget> createState() => _AIConversationWidgetState();
}

class _AIConversationWidgetState extends State<AIConversationWidget>
    with TickerProviderStateMixin {
  
  final AudioPlayer _audioPlayer = AudioPlayer();
  String _currentPlayingWord = '';
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    )..repeat(reverse: true);
    
    _pulseAnimation = Tween<double>(begin: 0.8, end: 1.0).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut)
    );
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _audioPlayer.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A1A), // Dark background
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.grey[800]!, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildAIHeader(),
          const SizedBox(height: 20),
          _buildConversationContent(),
        ],
      ),
    );
  }

  Widget _buildAIHeader() {
    return Row(
      children: [
        // AI Avatar
        Container(
          width: 50,
          height: 50,
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF6366F1), Color(0xFF8B5CF6)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(25),
          ),
          child: const Icon(
            Icons.psychology_alt,
            color: Colors.white,
            size: 28,
          ),
        ),
        const SizedBox(width: 12),
        
        // AI Info
        const Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'AI Translation Assistant',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                'Neural machine translation with word-by-word audio',
                style: TextStyle(
                  color: Colors.grey,
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
        
        // Play All Button
        AnimatedBuilder(
          animation: _pulseAnimation,
          builder: (context, child) {
            return Transform.scale(
              scale: _pulseAnimation.value,
              child: IconButton(
                onPressed: widget.onPlayAll,
                icon: Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFFEF4444), Color(0xFFF97316)],
                    ),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Icon(
                    Icons.play_arrow,
                    color: Colors.white,
                    size: 24,
                  ),
                ),
              ),
            );
          },
        ),
      ],
    );
  }

  Widget _buildConversationContent() {
    final styleData = widget.translationData['style_data'] as List<dynamic>? ?? [];
    
    return Column(
      children: [
        for (var style in styleData)
          _buildLanguageSection(style as Map<String, dynamic>),
      ],
    );
  }

  Widget _buildLanguageSection(Map<String, dynamic> styleData) {
    final styleName = styleData['style'] as String? ?? '';
    final translation = styleData['translation'] as String? ?? '';
    final wordPairs = styleData['word_pairs'] as List<dynamic>? ?? [];
    
    // Determine language and style info
    final isGerman = styleName.contains('german');
    final isNative = styleName.contains('native');
    final isFormal = styleName.contains('formal');
    
    final languageName = isGerman ? 'German' : 'English';
    final styleLabel = isNative ? 'Native' : 'Formal';
    final flagIcon = isGerman ? '🇩🇪' : '🇺🇸';
    
    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Language Header
          _buildLanguageHeader(languageName, styleLabel, flagIcon, isGerman),
          const SizedBox(height: 12),
          
          // Translation Text
          _buildTranslationBubble(translation, isGerman),
          const SizedBox(height: 12),
          
          // Word-by-Word Section
          if (wordPairs.isNotEmpty) _buildWordByWordSection(wordPairs, isGerman),
        ],
      ),
    );
  }

  Widget _buildLanguageHeader(String language, String style, String flag, bool isGerman) {
    final primaryColor = isGerman ? const Color(0xFFFFB800) : const Color(0xFF3B82F6);
    
    return Row(
      children: [
        // Flag
        Container(
          width: 32,
          height: 24,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(4),
            border: Border.all(color: Colors.grey[700]!),
          ),
          child: Center(
            child: Text(
              flag,
              style: const TextStyle(fontSize: 16),
            ),
          ),
        ),
        const SizedBox(width: 8),
        
        // Language Name
        Text(
          language,
          style: TextStyle(
            color: primaryColor,
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        
        const SizedBox(width: 12),
        
        // WORD-BY-WORD Badge
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: const Color(0xFFFF6B35),
            borderRadius: BorderRadius.circular(12),
          ),
          child: const Text(
            'WORD-BY-WORD',
            style: TextStyle(
              color: Colors.white,
              fontSize: 10,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildTranslationBubble(String translation, bool isGerman) {
    final primaryColor = isGerman ? const Color(0xFFFFB800) : const Color(0xFF3B82F6);
    
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: primaryColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: primaryColor.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Style Label
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: primaryColor,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              isGerman ? 'German Native' : 'English Native',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 12,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          const SizedBox(height: 12),
          
          // Translation Text
          Text(
            translation,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 16,
              height: 1.4,
            ),
          ),
          
          const SizedBox(height: 8),
          
          // Subtitle
          Text(
            '(here you must the word by word translation for ${isGerman ? 'german native' : 'english native'})',
            style: TextStyle(
              color: Colors.grey[500],
              fontSize: 12,
              fontStyle: FontStyle.italic,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWordByWordSection(List<dynamic> wordPairs, bool isGerman) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF2A2A2A),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[700]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Section Header
          Row(
            children: [
              Icon(
                Icons.hearing,
                color: Colors.orange,
                size: 20,
              ),
              const SizedBox(width: 8),
              const Text(
                'Interactive Word-by-Word Audio',
                style: TextStyle(
                  color: Colors.orange,
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          
          // Word Pairs
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (var i = 0; i < wordPairs.length; i++)
                _buildWordPairButton(wordPairs[i] as List<dynamic>, i, isGerman),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildWordPairButton(List<dynamic> wordPair, int index, bool isGerman) {
    if (wordPair.length < 2) return const SizedBox.shrink();
    
    final sourceWord = wordPair[0].toString();
    final targetWord = wordPair[1].toString();
    final isPlaying = _currentPlayingWord == '$sourceWord→$targetWord';
    
    return GestureDetector(
      onTap: () => _playWordPair(sourceWord, targetWord),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          gradient: isPlaying
              ? const LinearGradient(
                  colors: [Color(0xFFEF4444), Color(0xFFF97316)],
                )
              : LinearGradient(
                  colors: [
                    const Color(0xFF374151).withOpacity(0.8),
                    const Color(0xFF4B5563).withOpacity(0.8),
                  ],
                ),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isPlaying ? Colors.orange : Colors.grey[600]!,
            width: 1,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Play Icon
            Icon(
              isPlaying ? Icons.volume_up : Icons.play_circle_outline,
              color: isPlaying ? Colors.white : Colors.grey[300],
              size: 16,
            ),
            const SizedBox(width: 6),
            
            // Word Pair Text
            RichText(
              text: TextSpan(
                children: [
                  TextSpan(
                    text: sourceWord,
                    style: TextStyle(
                      color: isPlaying ? Colors.white : (isGerman ? const Color(0xFFFFB800) : const Color(0xFF3B82F6)),
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  TextSpan(
                    text: ' → ',
                    style: TextStyle(
                      color: isPlaying ? Colors.white70 : Colors.grey[400],
                      fontSize: 12,
                    ),
                  ),
                  TextSpan(
                    text: targetWord,
                    style: TextStyle(
                      color: isPlaying ? Colors.white : Colors.grey[300],
                      fontSize: 14,
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

  void _playWordPair(String sourceWord, String targetWord) {
    setState(() {
      _currentPlayingWord = '$sourceWord→$targetWord';
    });
    
    widget.onWordSelected?.call('$sourceWord → $targetWord');
    
    // Simulate audio playback
    Future.delayed(const Duration(milliseconds: 1500), () {
      if (mounted) {
        setState(() {
          _currentPlayingWord = '';
        });
      }
    });
  }
}