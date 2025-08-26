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
        color: const Color(0xFF2D3748),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          _buildTranslationContent(),
        ],
      ),
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
    
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          if (germanStyles.isNotEmpty) _buildLanguageSection('German', '🇩🇪', const Color(0xFFFFB800), germanStyles),
          if (germanStyles.isNotEmpty && englishStyles.isNotEmpty) const SizedBox(height: 20),
          if (englishStyles.isNotEmpty) _buildLanguageSection('English', '🇺🇸', const Color(0xFF3B82F6), englishStyles),
        ],
      ),
    );
  }

  Widget _buildLanguageSection(String language, String flag, Color primaryColor, List<Map<String, dynamic>> styles) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF2D3748),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Language Header
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.black.withOpacity(0.2),
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(12),
                topRight: Radius.circular(12),
              ),
            ),
            child: Row(
              children: [
                Text(
                  flag,
                  style: const TextStyle(fontSize: 24),
                ),
                const SizedBox(width: 12),
                Text(
                  language,
                  style: TextStyle(
                    color: primaryColor,
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFF8C00),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Text(
                    'WORD-BY-WORD',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
          ),
          
          // Style Sections
          for (final style in styles) _buildStyleSection(style, primaryColor),
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
    
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Style Header
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: primaryColor,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              '${language == 'german' ? 'German' : 'English'} $styleType',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 14,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          
          const SizedBox(height: 12),
          
          // Complete Translation Text
          Text(
            translation,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 16,
              height: 1.4,
              fontWeight: FontWeight.w500,
            ),
          ),
          
          const SizedBox(height: 12),
          
          // Word-by-Word Section
          if (wordPairs.isNotEmpty) ...[
            _buildWordByWordGrid(wordPairs, primaryColor, styleName),
          ] else ...[
            // Create fallback word pairs from the translation text
            _buildWordByWordGrid(_createFallbackWordPairs(translation, language), primaryColor, styleName),
          ],
        ],
      ),
    );
  }

  Widget _buildWordByWordGrid(List<dynamic> wordPairs, Color primaryColor, String styleName) {
    return Column(
      children: wordPairs.map((pairData) {
        final pairList = pairData as List<dynamic>;
        if (pairList.length < 2) return const SizedBox.shrink();
        
        final sourceWord = pairList[0].toString();
        final targetWord = pairList[1].toString();
        final confidence = pairList.length > 2 ? double.tryParse(pairList[2].toString()) ?? 0.85 : 0.85;
        final explanation = pairList.length > 3 ? pairList[3].toString() : '';
        final isCurrentWord = _currentPlayingWord == '$styleName:$sourceWord';
        
        return Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: _buildWordChipWithExplanation(sourceWord, targetWord, confidence, explanation, primaryColor, styleName, isCurrentWord),
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
            // Play button
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.2),
                shape: BoxShape.circle,
              ),
              child: Icon(
                isCurrentWord ? Icons.volume_up : Icons.play_arrow,
                color: Colors.white,
                size: 18,
              ),
            ),
            
            const SizedBox(width: 16),
            
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
  
  Widget _buildWordChipWithExplanation(
    String sourceWord, 
    String targetWord, 
    double confidence, 
    String explanation,
    Color primaryColor, 
    String styleName, 
    bool isCurrentWord
  ) {
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
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                // Play button
                Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    isCurrentWord ? Icons.volume_up : Icons.play_arrow,
                    color: Colors.white,
                    size: 18,
                  ),
                ),
                
                const SizedBox(width: 16),
                
                // Word pair text - Format: sourceWord → targetWord
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
            
            // AI Explanation (if available)
            if (explanation.isNotEmpty) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  explanation,
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.9),
                    fontSize: 12,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ),
            ],
          ],
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
    if (confidence >= 0.9) return Colors.green;
    if (confidence >= 0.8) return Colors.lime;
    if (confidence >= 0.7) return Colors.orange;
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