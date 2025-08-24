// enhanced_word_by_word_widget.dart - Enhanced Word-by-Word with AI Conversation Style

import 'package:flutter/material.dart';
import 'package:audioplayers/audioplayers.dart';

class EnhancedWordByWordWidget extends StatefulWidget {
  final Map<String, dynamic> translationData;
  final String? audioFilename;
  final Function(String)? onWordTap;
  final bool showConfidenceRatings;

  const EnhancedWordByWordWidget({
    super.key,
    required this.translationData,
    this.audioFilename,
    this.onWordTap,
    this.showConfidenceRatings = true,
  });

  @override
  State<EnhancedWordByWordWidget> createState() => _EnhancedWordByWordWidgetState();
}

class _EnhancedWordByWordWidgetState extends State<EnhancedWordByWordWidget>
    with TickerProviderStateMixin {
  
  final AudioPlayer _audioPlayer = AudioPlayer();
  String _currentPlayingStyle = '';
  String _currentPlayingWord = '';
  
  late AnimationController _aiPulseController;
  late AnimationController _wordAnimationController;
  late Animation<double> _aiPulseAnimation;
  late Animation<double> _wordScaleAnimation;

  @override
  void initState() {
    super.initState();
    
    _aiPulseController = AnimationController(
      duration: const Duration(milliseconds: 2000),
      vsync: this,
    )..repeat();
    
    _wordAnimationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    
    _aiPulseAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _aiPulseController, curve: Curves.easeInOut)
    );
    
    _wordScaleAnimation = Tween<double>(begin: 1.0, end: 1.1).animate(
      CurvedAnimation(parent: _wordAnimationController, curve: Curves.elasticOut)
    );
  }

  @override
  void dispose() {
    _aiPulseController.dispose();
    _wordAnimationController.dispose();
    _audioPlayer.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF1F2937), Color(0xFF111827)],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        children: [
          _buildAIAssistantHeader(),
          _buildTranslationContent(),
        ],
      ),
    );
  }

  Widget _buildAIAssistantHeader() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: const BoxDecoration(
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(24),
          topRight: Radius.circular(24),
        ),
      ),
      child: Row(
        children: [
          // AI Avatar with pulse animation
          AnimatedBuilder(
            animation: _aiPulseAnimation,
            builder: (context, child) {
              return Container(
                width: 60,
                height: 60,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      Color.lerp(const Color(0xFF6366F1), const Color(0xFF8B5CF6), _aiPulseAnimation.value)!,
                      Color.lerp(const Color(0xFF8B5CF6), const Color(0xFF6366F1), _aiPulseAnimation.value)!,
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(30),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF6366F1).withOpacity(0.3),
                      blurRadius: 15,
                      spreadRadius: _aiPulseAnimation.value * 3,
                    ),
                  ],
                ),
                child: const Icon(
                  Icons.psychology_alt,
                  color: Colors.white,
                  size: 32,
                ),
              );
            },
          ),
          
          const SizedBox(width: 16),
          
          // AI Info
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'AI Neural Translation',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  'Word-by-word analysis with confidence ratings',
                  style: TextStyle(
                    color: Colors.grey[400],
                    fontSize: 14,
                  ),
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.green.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.green.withOpacity(0.3)),
                      ),
                      child: const Text(
                        'AI POWERED',
                        style: TextStyle(
                          color: Colors.green,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.orange.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.orange.withOpacity(0.3)),
                      ),
                      child: const Text(
                        'REAL-TIME',
                        style: TextStyle(
                          color: Colors.orange,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          
          // Master Play Button
          GestureDetector(
            onTap: _playAllStyles,
            child: Container(
              width: 50,
              height: 50,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFFEF4444), Color(0xFFF97316)],
                ),
                borderRadius: BorderRadius.circular(25),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFFEF4444).withOpacity(0.3),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: const Icon(
                Icons.play_arrow,
                color: Colors.white,
                size: 28,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTranslationContent() {
    final styleData = widget.translationData['style_data'] as List<dynamic>? ?? [];
    
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      child: Column(
        children: [
          for (var i = 0; i < styleData.length; i++)
            _buildLanguageStyleSection(styleData[i] as Map<String, dynamic>, i),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _buildLanguageStyleSection(Map<String, dynamic> styleData, int index) {
    final styleName = styleData['style'] as String? ?? '';
    final translation = styleData['translation'] as String? ?? '';
    final wordPairs = styleData['word_pairs'] as List<dynamic>? ?? [];
    
    final isGerman = styleName.contains('german');
    final isNative = styleName.contains('native');
    final isFormal = styleName.contains('formal');
    
    final languageInfo = _getLanguageInfo(isGerman, isNative);
    final isCurrentlyPlaying = _currentPlayingStyle == styleName;
    
    return Container(
      margin: const EdgeInsets.only(bottom: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Language Header with Flag
          _buildLanguageHeader(languageInfo, isCurrentlyPlaying),
          const SizedBox(height: 16),
          
          // Translation Bubble
          _buildTranslationBubble(
            translation, 
            languageInfo, 
            isNative ? 'Native' : 'Formal',
            isCurrentlyPlaying
          ),
          const SizedBox(height: 16),
          
          // Word-by-Word Interactive Section
          if (wordPairs.isNotEmpty)
            _buildInteractiveWordSection(wordPairs, languageInfo, styleName),
        ],
      ),
    );
  }

  Map<String, dynamic> _getLanguageInfo(bool isGerman, bool isNative) {
    if (isGerman) {
      return {
        'name': 'German',
        'flag': '🇩🇪',
        'primaryColor': const Color(0xFFFFB800),
        'secondaryColor': const Color(0xFFFFC107),
      };
    } else {
      return {
        'name': 'English',
        'flag': '🇺🇸',
        'primaryColor': const Color(0xFF3B82F6),
        'secondaryColor': const Color(0xFF60A5FA),
      };
    }
  }

  Widget _buildLanguageHeader(Map<String, dynamic> languageInfo, bool isPlaying) {
    return Row(
      children: [
        // Flag Container
        Container(
          width: 36,
          height: 26,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(6),
            border: Border.all(color: Colors.grey[600]!),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.2),
                blurRadius: 4,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Center(
            child: Text(
              languageInfo['flag'],
              style: const TextStyle(fontSize: 18),
            ),
          ),
        ),
        
        const SizedBox(width: 12),
        
        // Language Name
        Text(
          languageInfo['name'],
          style: TextStyle(
            color: languageInfo['primaryColor'],
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        
        const SizedBox(width: 16),
        
        // WORD-BY-WORD Badge
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFFFF6B35), Color(0xFFFF8E53)],
            ),
            borderRadius: BorderRadius.circular(15),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFFFF6B35).withOpacity(0.3),
                blurRadius: 8,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(
                Icons.hearing,
                color: Colors.white,
                size: 14,
              ),
              const SizedBox(width: 4),
              const Text(
                'WORD-BY-WORD',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ),
        
        const Spacer(),
        
        // Playing Indicator
        if (isPlaying)
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.red.withOpacity(0.2),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 8,
                  height: 8,
                  decoration: const BoxDecoration(
                    color: Colors.red,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 6),
                const Text(
                  'PLAYING',
                  style: TextStyle(
                    color: Colors.red,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _buildTranslationBubble(
    String translation, 
    Map<String, dynamic> languageInfo, 
    String styleLabel,
    bool isPlaying
  ) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: isPlaying
              ? [
                  languageInfo['primaryColor'].withOpacity(0.3),
                  languageInfo['secondaryColor'].withOpacity(0.2),
                ]
              : [
                  languageInfo['primaryColor'].withOpacity(0.15),
                  languageInfo['primaryColor'].withOpacity(0.05),
                ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isPlaying 
              ? languageInfo['primaryColor'].withOpacity(0.6)
              : languageInfo['primaryColor'].withOpacity(0.3),
          width: 1.5,
        ),
        boxShadow: isPlaying
            ? [
                BoxShadow(
                  color: languageInfo['primaryColor'].withOpacity(0.3),
                  blurRadius: 15,
                  spreadRadius: 2,
                ),
              ]
            : null,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Style Badge
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: languageInfo['primaryColor'],
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              '${languageInfo['name']} $styleLabel',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 13,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          
          const SizedBox(height: 16),
          
          // Translation Text
          Text(
            translation,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 17,
              height: 1.5,
              fontWeight: FontWeight.w500,
            ),
          ),
          
          const SizedBox(height: 12),
          
          // Subtitle
          Text(
            '(here you must the word by word translation for ${languageInfo['name'].toLowerCase()} ${styleLabel.toLowerCase()})',
            style: TextStyle(
              color: Colors.grey[400],
              fontSize: 12,
              fontStyle: FontStyle.italic,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInteractiveWordSection(
    List<dynamic> wordPairs, 
    Map<String, dynamic> languageInfo,
    String styleName
  ) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF2D3748).withOpacity(0.8),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey[700]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Section Header
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      languageInfo['primaryColor'].withOpacity(0.2),
                      languageInfo['primaryColor'].withOpacity(0.1),
                    ],
                  ),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  Icons.touch_app,
                  color: languageInfo['primaryColor'],
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              const Text(
                'Interactive Word Learning',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const Spacer(),
              Text(
                '${wordPairs.length} words',
                style: TextStyle(
                  color: Colors.grey[400],
                  fontSize: 12,
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 20),
          
          // Word Buttons Grid
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              for (var i = 0; i < wordPairs.length; i++)
                _buildAnimatedWordButton(wordPairs[i], i, languageInfo, styleName),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildAnimatedWordButton(
    dynamic wordPair, 
    int index, 
    Map<String, dynamic> languageInfo,
    String styleName
  ) {
    final pairList = wordPair as List<dynamic>? ?? [];
    if (pairList.length < 2) return const SizedBox.shrink();
    
    final sourceWord = pairList[0].toString();
    final targetWord = pairList[1].toString();
    final isCurrentWord = _currentPlayingWord == '$styleName:$sourceWord';
    
    // Get confidence if available
    double confidence = 0.85; // Default
    if (widget.showConfidenceRatings && pairList.length > 2) {
      confidence = double.tryParse(pairList[2].toString()) ?? 0.85;
    }
    
    return GestureDetector(
      onTap: () => _playWordPair(sourceWord, targetWord, styleName),
      child: AnimatedScale(
        scale: isCurrentWord ? 1.05 : 1.0,
        duration: const Duration(milliseconds: 200),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          decoration: BoxDecoration(
            gradient: isCurrentWord
                ? LinearGradient(
                    colors: [
                      const Color(0xFFEF4444),
                      const Color(0xFFF97316),
                    ],
                  )
                : LinearGradient(
                    colors: [
                      languageInfo['primaryColor'].withOpacity(0.3),
                      languageInfo['primaryColor'].withOpacity(0.1),
                    ],
                  ),
            borderRadius: BorderRadius.circular(25),
            border: Border.all(
              color: isCurrentWord 
                  ? Colors.orange 
                  : languageInfo['primaryColor'].withOpacity(0.5),
              width: 1.5,
            ),
            boxShadow: isCurrentWord
                ? [
                    BoxShadow(
                      color: Colors.orange.withOpacity(0.4),
                      blurRadius: 10,
                      offset: const Offset(0, 4),
                    ),
                  ]
                : null,
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Play Icon
              Icon(
                isCurrentWord ? Icons.volume_up : Icons.play_circle_outline,
                color: isCurrentWord ? Colors.white : languageInfo['primaryColor'],
                size: 18,
              ),
              const SizedBox(width: 8),
              
              // Word Pair
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  RichText(
                    text: TextSpan(
                      children: [
                        TextSpan(
                          text: sourceWord,
                          style: TextStyle(
                            color: isCurrentWord ? Colors.white : languageInfo['primaryColor'],
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        TextSpan(
                          text: ' → ',
                          style: TextStyle(
                            color: isCurrentWord ? Colors.white70 : Colors.grey[400],
                            fontSize: 12,
                          ),
                        ),
                        TextSpan(
                          text: targetWord,
                          style: TextStyle(
                            color: isCurrentWord ? Colors.white : Colors.grey[300],
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                  ),
                  
                  // Confidence Bar
                  if (widget.showConfidenceRatings)
                    Container(
                      margin: const EdgeInsets.only(top: 4),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Container(
                            width: 40,
                            height: 3,
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(2),
                            ),
                            child: LinearProgressIndicator(
                              value: confidence,
                              backgroundColor: Colors.grey[600],
                              valueColor: AlwaysStoppedAnimation<Color>(
                                _getConfidenceColor(confidence),
                              ),
                            ),
                          ),
                          const SizedBox(width: 4),
                          Text(
                            '${(confidence * 100).toInt()}%',
                            style: TextStyle(
                              color: isCurrentWord ? Colors.white70 : Colors.grey[400],
                              fontSize: 10,
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Color _getConfidenceColor(double confidence) {
    if (confidence >= 0.9) return Colors.green;
    if (confidence >= 0.8) return Colors.orange;
    if (confidence >= 0.7) return Colors.yellow;
    return Colors.red;
  }

  void _playWordPair(String sourceWord, String targetWord, String styleName) {
    setState(() {
      _currentPlayingWord = '$styleName:$sourceWord';
    });
    
    widget.onWordTap?.call('$sourceWord → $targetWord');
    
    // Simulate word audio playback
    Future.delayed(const Duration(milliseconds: 2000), () {
      if (mounted) {
        setState(() {
          _currentPlayingWord = '';
        });
      }
    });
  }

  void _playAllStyles() {
    // Simulate playing all styles
    setState(() {
      _currentPlayingStyle = 'all';
    });
    
    Future.delayed(const Duration(seconds: 3), () {
      if (mounted) {
        setState(() {
          _currentPlayingStyle = '';
        });
      }
    });
  }
}