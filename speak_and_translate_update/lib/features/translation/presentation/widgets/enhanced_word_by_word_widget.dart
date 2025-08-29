// enhanced_word_by_word_widget.dart - Enhanced Word-by-Word with AI Conversation Style

import 'package:flutter/material.dart';
import 'package:audioplayers/audioplayers.dart';

class EnhancedWordByWordWidget extends StatefulWidget {
  final Map<String, dynamic> translationData;
  final String? audioFilename;
  final Function(String)? onWordTap;
  final bool showConfidenceRatings;
  final bool germanWordByWordAudio;
  final bool englishWordByWordAudio;
  final Function(String)? onPlaySentenceAudio;

  const EnhancedWordByWordWidget({
    super.key,
    required this.translationData,
    this.audioFilename,
    this.onWordTap,
    this.showConfidenceRatings = true,
    this.germanWordByWordAudio = false,
    this.englishWordByWordAudio = false,
    this.onPlaySentenceAudio,
  });

  @override
  State<EnhancedWordByWordWidget> createState() => _EnhancedWordByWordWidgetState();
}

class _EnhancedWordByWordWidgetState extends State<EnhancedWordByWordWidget>
    with TickerProviderStateMixin {
  
  final AudioPlayer _audioPlayer = AudioPlayer();
  String _currentPlayingStyle = '';
  String _currentPlayingWord = '';
  
  // Track which style sections are expanded
  final Map<String, bool> _expandedStyles = <String, bool>{};
  
  // Animation controllers for smooth expand/collapse
  final Map<String, AnimationController> _expansionControllers = <String, AnimationController>{};
  final Map<String, Animation<double>> _expansionAnimations = <String, Animation<double>>{};
  
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
    
    // Dispose expansion controllers
    for (final controller in _expansionControllers.values) {
      controller.dispose();
    }
    
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: _buildTranslationContent(),
    );
  }


  Widget _buildTranslationContent() {
    final styleData = widget.translationData['style_data'] as List<dynamic>? ?? [];
    
    // CRITICAL DEBUG: Print EVERYTHING we're receiving to find sync issue
    print('🔍 [ENHANCED_WIDGET] ======== RECEIVING DATA ========');
    print('🔍 [ENHANCED_WIDGET] Total styles received: ${styleData.length}');
    print('🔍 [ENHANCED_WIDGET] Full translationData keys: ${widget.translationData.keys.toList()}');
    
    for (int i = 0; i < styleData.length; i++) {
      final style = styleData[i] as Map<String, dynamic>;
      final styleName = style['style'] ?? 'unknown';
      final translation = style['translation'] ?? 'no translation';
      final wordPairs = style['word_pairs'] as List<dynamic>? ?? [];
      
      print('🎯 [ENHANCED_WIDGET] Style $i: "$styleName"');
      print('🎯 [ENHANCED_WIDGET] Translation: "$translation"');
      print('🎯 [ENHANCED_WIDGET] Word pairs count: ${wordPairs.length}');
      
      // Check EACH word pair for real AI data vs placeholders
      for (int j = 0; j < wordPairs.length; j++) {
        final wordPair = wordPairs[j];
        if (wordPair is List && wordPair.length >= 2) {
          final sourceWord = wordPair[0].toString();
          final targetWord = wordPair[1].toString();
          final confidence = wordPair.length > 2 ? wordPair[2].toString() : 'unknown';
          final explanation = wordPair.length > 3 ? wordPair[3].toString() : '';
          
          print('   📝 [WORD_PAIR] $j: "$sourceWord" → "$targetWord" (${confidence})');
          if (explanation.isNotEmpty) {
            print('   💡 [EXPLANATION] $explanation');
          }
          
          // Check if this looks like placeholder data
          if (targetWord.contains('_es') || targetWord == 'EMERGENCY_FALLBACK') {
            print('   ⚠️ [PLACEHOLDER_DETECTED] This is NOT real AI translation!');
          } else if (targetWord.length > 2 && !targetWord.contains('_')) {
            print('   ✅ [REAL_AI_DATA] This looks like real AI translation');
          }
        }
      }
    }
    print('🔍 [ENHANCED_WIDGET] ======== END DATA DEBUG ========');
    
    if (styleData.isEmpty) {
      print('❌ [ENHANCED_WIDGET] NO STYLE DATA - This will show empty UI');
      return Container(
        padding: const EdgeInsets.all(16),
        child: const Text(
          'No translation styles available',
          style: TextStyle(color: Colors.white),
        ),
      );
    }
    
    // Group styles by language
    final germanStyles = <Map<String, dynamic>>[];
    final englishStyles = <Map<String, dynamic>>[];
    
    for (final style in styleData) {
      final styleMap = style as Map<String, dynamic>;
      final styleName = styleMap['style'] as String? ?? '';
      
      if (styleName.contains('german')) {
        germanStyles.add(styleMap);
      } else if (styleName.contains('english')) {
        englishStyles.add(styleMap);
      }
    }
    
    return Column(
      children: [
        if (germanStyles.isNotEmpty) 
          _buildLanguageSection('German', '🇩🇪', const Color(0xFFDC2626), germanStyles),
        if (englishStyles.isNotEmpty) 
          _buildLanguageSection('English', '🇺🇸', const Color(0xFF2563EB), englishStyles),
      ],
    );
  }

  Widget _buildLanguageSection(String language, String flag, Color primaryColor, List<Map<String, dynamic>> styles) {
    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            const Color(0xFF2D3748),
            const Color(0xFF1A202C),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Language Header
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [primaryColor.withOpacity(0.1), Colors.transparent],
              ),
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(16),
                topRight: Radius.circular(16),
              ),
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: primaryColor.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    flag,
                    style: const TextStyle(fontSize: 24),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        language,
                        style: TextStyle(
                          color: primaryColor,
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 0.5,
                        ),
                      ),
                      Text(
                        '${styles.length} translation styles',
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.7),
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          
          // Style Sections
          ...styles.map((style) => _buildStyleSection(style, primaryColor)).toList(),
          
          const SizedBox(height: 8),
        ],
      ),
    );
  }
  
  Widget _buildStyleSection(Map<String, dynamic> styleData, Color primaryColor) {
    final styleName = styleData['style'] as String? ?? '';
    final translation = styleData['translation'] as String? ?? '';
    final wordPairs = styleData['word_pairs'] as List<dynamic>? ?? [];
    
    // Determine style type for display
    String styleType = 'Native';
    if (styleName.contains('colloquial')) styleType = 'Colloquial';
    else if (styleName.contains('informal')) styleType = 'Informal'; 
    else if (styleName.contains('formal')) styleType = 'Formal';
    
    final language = styleName.contains('german') ? 'german' : 'english';
    final isExpanded = _expandedStyles[styleName] ?? false;
    
    // Initialize animation controller if not exists
    if (!_expansionControllers.containsKey(styleName)) {
      final controller = AnimationController(
        duration: const Duration(milliseconds: 300),
        vsync: this,
      );
      _expansionControllers[styleName] = controller;
      _expansionAnimations[styleName] = CurvedAnimation(
        parent: controller,
        curve: Curves.easeInOut,
      );
    }
    
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            const Color(0xFF374151),
            const Color(0xFF1F2937),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: primaryColor.withOpacity(0.2),
          width: 1,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.2),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Style Header with Translation
          Container(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Style Badge
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [primaryColor, primaryColor.withOpacity(0.8)],
                    ),
                    borderRadius: BorderRadius.circular(20),
                    boxShadow: [
                      BoxShadow(
                        color: primaryColor.withOpacity(0.3),
                        blurRadius: 4,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Text(
                    '${language == 'german' ? 'German' : 'English'} $styleType',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
                
                const SizedBox(height: 16),
                
                // Complete Translation Text
                Text(
                  translation,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 17,
                    height: 1.5,
                    fontWeight: FontWeight.w500,
                    letterSpacing: 0.3,
                  ),
                ),
                
                const SizedBox(height: 16),
                
                // Word-by-Word Toggle Button
                Material(
                  color: Colors.transparent,
                  child: InkWell(
                    onTap: () => _toggleWordByWordSection(styleName),
                    borderRadius: BorderRadius.circular(25),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 200),
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20),
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFFFF8C00), Color(0xFFFF7700)],
                        ),
                        borderRadius: BorderRadius.circular(25),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFFFF8C00).withOpacity(0.4),
                            blurRadius: 8,
                            offset: const Offset(0, 3),
                          ),
                        ],
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(
                            Icons.translate,
                            color: Colors.white,
                            size: 18,
                          ),
                          const SizedBox(width: 10),
                          const Text(
                            'WORD-BY-WORD',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 1,
                            ),
                          ),
                          const SizedBox(width: 10),
                          AnimatedRotation(
                            turns: isExpanded ? 0.5 : 0.0,
                            duration: const Duration(milliseconds: 300),
                            child: const Icon(
                              Icons.keyboard_arrow_down,
                              color: Colors.white,
                              size: 20,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          
          // Animated Expandable Word-by-Word Section
          AnimatedBuilder(
            animation: _expansionAnimations[styleName]!,
            builder: (context, child) {
              return ClipRRect(
                borderRadius: const BorderRadius.only(
                  bottomLeft: Radius.circular(16),
                  bottomRight: Radius.circular(16),
                ),
                child: SizeTransition(
                  sizeFactor: _expansionAnimations[styleName]!,
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [
                          Colors.black.withOpacity(0.1),
                          Colors.black.withOpacity(0.2),
                        ],
                      ),
                    ),
                    child: Column(
                      children: [
                        Container(
                          height: 1,
                          width: double.infinity,
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              colors: [
                                Colors.transparent,
                                primaryColor.withOpacity(0.5),
                                Colors.transparent,
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),
                        if (wordPairs.isNotEmpty)
                          _buildWordByWordGrid(wordPairs, primaryColor, styleName)
                        else
                          _buildWordByWordGrid(_createFallbackWordPairs(translation, language), primaryColor, styleName),
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildWordByWordGrid(List<dynamic> wordPairs, Color primaryColor, String styleName) {
    return Column(
      children: wordPairs.asMap().entries.map((entry) {
        final index = entry.key;
        final pairData = entry.value;
        final pairList = pairData as List<dynamic>;
        if (pairList.length < 2) return const SizedBox.shrink();
        
        final sourceWord = pairList[0].toString();
        final targetWord = pairList[1].toString();
        final confidence = pairList.length > 2 ? double.tryParse(pairList[2].toString()) ?? 0.85 : 0.85;
        final explanation = pairList.length > 3 ? pairList[3].toString() : '';
        final isCurrentWord = _currentPlayingWord == '$styleName:$sourceWord';
        
        return AnimatedContainer(
          duration: Duration(milliseconds: 100 + (index * 50)),
          curve: Curves.easeOutBack,
          margin: const EdgeInsets.only(bottom: 10),
          child: _buildEnhancedWordChip(
            sourceWord, 
            targetWord, 
            confidence, 
            explanation, 
            primaryColor, 
            styleName, 
            isCurrentWord,
            index
          ),
        );
      }).toList(),
    );
  }
  
  Widget _buildWordChip(String sourceWord, String targetWord, double confidence, Color primaryColor, String styleName, bool isCurrentWord) {
    return GestureDetector(
      onTap: () => _playWordPair(sourceWord, targetWord, styleName),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: isCurrentWord ? primaryColor : primaryColor.withOpacity(0.3),
          borderRadius: BorderRadius.circular(25),
          border: Border.all(
            color: primaryColor.withOpacity(0.8),
            width: 2,
          ),
        ),
        child: Row(
          children: [
            // Word pair text
            Expanded(
              child: RichText(
                text: TextSpan(
                  children: [
                    TextSpan(
                      text: sourceWord,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const TextSpan(
                      text: ' → ',
                      style: TextStyle(
                        color: Colors.white70,
                        fontSize: 14,
                      ),
                    ),
                    TextSpan(
                      text: targetWord,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            
            // Confidence percentage
            Text(
              '${(confidence * 100).toInt()}%',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 14,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildEnhancedWordChip(
    String sourceWord, 
    String targetWord, 
    double confidence, 
    String explanation,
    Color primaryColor, 
    String styleName, 
    bool isCurrentWord,
    int index
  ) {
    final confidenceColor = _getConfidenceColor(confidence);
    
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () => _playWordPair(sourceWord, targetWord, styleName),
        borderRadius: BorderRadius.circular(20),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          width: double.infinity,
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            gradient: isCurrentWord
                ? LinearGradient(
                    colors: [
                      primaryColor,
                      primaryColor.withOpacity(0.8),
                    ],
                  )
                : LinearGradient(
                    colors: [
                      const Color(0xFF4B5563),
                      const Color(0xFF374151),
                    ],
                  ),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: isCurrentWord 
                  ? Colors.white.withOpacity(0.3)
                  : primaryColor.withOpacity(0.3),
              width: 1.5,
            ),
            boxShadow: [
              BoxShadow(
                color: isCurrentWord 
                    ? primaryColor.withOpacity(0.3)
                    : Colors.black.withOpacity(0.2),
                blurRadius: isCurrentWord ? 8 : 4,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  // Word pair text with better typography
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        RichText(
                          text: TextSpan(
                            children: [
                              TextSpan(
                                text: sourceWord,
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                  letterSpacing: 0.3,
                                ),
                              ),
                              TextSpan(
                                text: ' → ',
                                style: TextStyle(
                                  color: Colors.white.withOpacity(0.7),
                                  fontSize: 14,
                                  fontWeight: FontWeight.w300,
                                ),
                              ),
                              TextSpan(
                                text: targetWord,
                                style: TextStyle(
                                  color: Colors.white.withOpacity(0.9),
                                  fontSize: 16,
                                  fontWeight: FontWeight.w500,
                                  letterSpacing: 0.2,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  
                  // Confidence badge with color coding
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: confidenceColor.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: confidenceColor.withOpacity(0.5),
                        width: 1,
                      ),
                    ),
                    child: Text(
                      '${(confidence * 100).toInt()}%',
                      style: TextStyle(
                        color: confidenceColor,
                        fontSize: 13,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 0.3,
                      ),
                    ),
                  ),
                ],
              ),
              
              // AI Explanation with better styling
              if (explanation.isNotEmpty && !explanation.contains('EMERGENCY_FALLBACK')) ...[
                const SizedBox(height: 12),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        Colors.black.withOpacity(0.3),
                        Colors.black.withOpacity(0.2),
                      ],
                    ),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: Colors.white.withOpacity(0.1),
                      width: 1,
                    ),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        Icons.psychology_outlined,
                        color: const Color(0xFFFF8C00),
                        size: 16,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          explanation,
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.85),
                            fontSize: 12,
                            height: 1.4,
                            fontStyle: FontStyle.italic,
                            letterSpacing: 0.2,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
  
  // CRITICAL FIX: This method should only be used if no AI word pairs are available
  List<dynamic> _createFallbackWordPairs(String translation, String language) {
    final words = translation.split(' ');
    final fallbackPairs = <List<dynamic>>[];
    
    print('[CRITICAL_WARNING] Using fallback word pairs instead of AI translations');
    print('[CRITICAL_WARNING] This means backend AI data is not reaching the frontend properly');
    print('[AI_FALLBACK] Creating emergency fallback for $language: $translation');
    
    // Emergency fallback with basic word pairs - this should NOT be used if AI data is available
    for (final word in words) {
      String cleanWord = word.trim().replaceAll(RegExp(r'[.,!?;:]'), '');
      if (cleanWord.isNotEmpty) {
        final confidence = (0.85 + (fallbackPairs.length * 0.01)).clamp(0.80, 0.98);
        fallbackPairs.add([
          cleanWord, 
          'EMERGENCY_FALLBACK', // Clear indicator that this is NOT real AI translation
          confidence.toStringAsFixed(2),
          'AI data missing - backend sync issue' // Clear error message
        ]);
      }
    }
    
    print('[EMERGENCY_FALLBACK] Generated ${fallbackPairs.length} emergency word pairs');
    print('[EMERGENCY_FALLBACK] If you see "EMERGENCY_FALLBACK" in UI, AI sync is broken');
    return fallbackPairs;
  }
  
  // Essential methods for word-by-word functionality

  Color _getConfidenceColor(double confidence) {
    if (confidence >= 0.9) return const Color(0xFF10B981); // Emerald
    if (confidence >= 0.8) return const Color(0xFF84CC16); // Lime
    if (confidence >= 0.7) return const Color(0xFFF59E0B); // Amber
    if (confidence >= 0.6) return const Color(0xFFEF4444); // Red
    return const Color(0xFF8B5CF6); // Purple for very low confidence
  }

  // Play sentence audio for the complete translation
  void _playSentenceAudio(String language) {
    if (widget.audioFilename != null && widget.onPlaySentenceAudio != null) {
      print('🎵 Playing complete sentence audio for $language');
      widget.onPlaySentenceAudio!(widget.audioFilename!);
    } else {
      print('⚠️ No sentence audio available for $language');
    }
  }

  void _playWordPair(String sourceWord, String targetWord, String styleName) {
    // Determine language and user preferences
    final isGerman = styleName.contains('german');
    final isEnglish = styleName.contains('english');
    
    final shouldPlayWordAudio = (isGerman && widget.germanWordByWordAudio) || 
                               (isEnglish && widget.englishWordByWordAudio);
    
    // Animate word selection
    setState(() {
      _currentPlayingWord = '$styleName:$sourceWord';
    });
    
    // Trigger haptic feedback
    // HapticFeedback.lightImpact();
    
    widget.onWordTap?.call('$sourceWord → $targetWord');
    
    print('👁️ Word-by-word visual feedback: $sourceWord → $targetWord');
    
    // Always play sentence audio first
    _playSentenceAudio(isGerman ? 'german' : 'english');
    
    // Play individual word audio only if enabled
    if (shouldPlayWordAudio) {
      print('🎵 Playing word-by-word audio');
      Future.delayed(const Duration(milliseconds: 1500), () {
        _playIndividualWordAudio(sourceWord, targetWord, isGerman ? 'german' : 'english');
      });
    } else {
      print('🔇 Sentence audio only (word-by-word audio disabled)');
    }
    
    // Reset visual feedback
    Future.delayed(const Duration(milliseconds: 2500), () {
      if (mounted) {
        setState(() {
          _currentPlayingWord = '';
        });
      }
    });
  }

  // Play individual word audio (when word-by-word audio is enabled)
  void _playIndividualWordAudio(String sourceWord, String targetWord, String language) {
    // This would integrate with TTS to speak: "[sourceWord] ([Spanish equivalent])"
    // For example: "Krankenhaus (hospital)" or "hospital (hospital)"
    
    final audioText = language == 'german' 
        ? '$sourceWord ($targetWord)'  // German word (Spanish equivalent)
        : '$sourceWord ($targetWord)'; // English word (Spanish equivalent)
        
    print('🎵 TTS would say: "$audioText"');
    // TODO: Integrate with actual TTS service for individual words
  }

  void _toggleWordByWordSection(String styleName) {
    setState(() {
      final isCurrentlyExpanded = _expandedStyles[styleName] ?? false;
      _expandedStyles[styleName] = !isCurrentlyExpanded;
      
      if (_expandedStyles[styleName]!) {
        _expansionControllers[styleName]?.forward();
      } else {
        _expansionControllers[styleName]?.reverse();
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