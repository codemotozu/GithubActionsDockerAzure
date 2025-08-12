// word_by_word_visualization_widget.dart - Widget to display word-by-word breakdown that matches audio

import 'package:flutter/material.dart';

class WordByWordVisualizationWidget extends StatefulWidget {
  final Map<String, Map<String, String>>? wordByWordData;
  final bool isVisible;
  final VoidCallback? onToggleVisibility;

  const WordByWordVisualizationWidget({
    super.key,
    this.wordByWordData,
    this.isVisible = true,
    this.onToggleVisibility,
  });

  @override
  State<WordByWordVisualizationWidget> createState() => _WordByWordVisualizationWidgetState();
}

class _WordByWordVisualizationWidgetState extends State<WordByWordVisualizationWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _expandAnimation;
  bool _isExpanded = false;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _expandAnimation = CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    );
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  void _toggleExpansion() {
    setState(() {
      _isExpanded = !_isExpanded;
      if (_isExpanded) {
        _animationController.forward();
      } else {
        _animationController.reverse();
      }
    });
  }

  // Group word pairs by language and style
  Map<String, Map<String, List<MapEntry<String, Map<String, String>>>>> _groupWordPairs() {
    if (widget.wordByWordData == null || widget.wordByWordData!.isEmpty) {
      return {};
    }

    final grouped = <String, Map<String, List<MapEntry<String, Map<String, String>>>>>{};

    for (final entry in widget.wordByWordData!.entries) {
      final wordData = entry.value;
      final language = wordData['language'] ?? 'unknown';
      final style = wordData['style'] ?? 'unknown';

      grouped.putIfAbsent(language, () => {});
      grouped[language]!.putIfAbsent(style, () => []);
      grouped[language]![style]!.add(entry);
    }

    // Sort by order within each style
    for (final language in grouped.keys) {
      for (final style in grouped[language]!.keys) {
        grouped[language]![style]!.sort((a, b) {
          final orderA = int.tryParse(a.value['order'] ?? '0') ?? 0;
          final orderB = int.tryParse(b.value['order'] ?? '0') ?? 0;
          return orderA.compareTo(orderB);
        });
      }
    }

    return grouped;
  }

  String _getLanguageFlag(String language) {
    switch (language.toLowerCase()) {
      case 'german':
        return '🇩🇪';
      case 'english':
        return '🇺🇸';
      case 'spanish':
        return '🇪🇸';
      default:
        return '🌐';
    }
  }

  String _getLanguageName(String language) {
    switch (language.toLowerCase()) {
      case 'german':
        return 'German';
      case 'english':
        return 'English';
      case 'spanish':
        return 'Spanish';
      default:
        return language;
    }
  }

  String _getStyleDisplayName(String style) {
    final parts = style.split('_');
    if (parts.length >= 2) {
      final styleName = parts[1];
      return styleName[0].toUpperCase() + styleName.substring(1);
    }
    return style;
  }

  Color _getLanguageColor(String language) {
    switch (language.toLowerCase()) {
      case 'german':
        return Colors.amber;
      case 'english':
        return Colors.blue;
      case 'spanish':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }

  Widget _buildWordPairChip(Map<String, String> wordData) {
    final sourceWord = wordData['source'] ?? '';
    final spanishEquiv = wordData['spanish'] ?? '';
    final isPhrasalVerb = wordData['is_phrasal_verb'] == 'true';
    final displayFormat = wordData['display_format'] ?? '[$sourceWord] ([$spanishEquiv])';

    return Container(
      margin: const EdgeInsets.only(right: 8, bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isPhrasalVerb ? Colors.orange : Colors.white30,
          width: isPhrasalVerb ? 2 : 1,
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Audio format display - exactly what user hears
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: Colors.black.withOpacity(0.3),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              displayFormat,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 11,
                fontFamily: 'monospace',
                fontWeight: FontWeight.w500,
              ),
              textAlign: TextAlign.center,
            ),
          ),
          
          const SizedBox(height: 6),
          
          // Visual breakdown
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Source word
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: _getLanguageColor(wordData['language'] ?? 'unknown').withOpacity(0.3),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  sourceWord,
                  style: TextStyle(
                    color: _getLanguageColor(wordData['language'] ?? 'unknown'),
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              
              const SizedBox(width: 8),
              
              // Arrow
              Icon(
                Icons.arrow_forward,
                color: Colors.white70,
                size: 16,
              ),
              
              const SizedBox(width: 8),
              
              // Spanish equivalent
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.green.withOpacity(0.3),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  spanishEquiv,
                  style: const TextStyle(
                    color: Colors.green,
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          
          // Phrasal verb indicator
          if (isPhrasalVerb) ...[
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: Colors.orange.withOpacity(0.3),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                wordData['language'] == 'german' ? 'Separable Verb' : 'Phrasal Verb',
                style: const TextStyle(
                  color: Colors.orange,
                  fontSize: 9,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildLanguageSection(String language, Map<String, List<MapEntry<String, Map<String, String>>>> styles) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: _getLanguageColor(language).withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: _getLanguageColor(language), width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Language header
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Text(
                  _getLanguageFlag(language),
                  style: const TextStyle(fontSize: 20),
                ),
                const SizedBox(width: 8),
                Text(
                  '${_getLanguageName(language)} Word-by-Word',
                  style: TextStyle(
                    color: _getLanguageColor(language),
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: _getLanguageColor(language).withOpacity(0.3),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${styles.values.fold(0, (sum, styleList) => sum + styleList.length)} pairs',
                    style: TextStyle(
                      color: _getLanguageColor(language),
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
          ),
          
          // Style sections
          ...styles.entries.map((styleEntry) {
            final styleName = styleEntry.key;
            final wordPairs = styleEntry.value;
            
            return Container(
              margin: const EdgeInsets.fromLTRB(12, 0, 12, 12),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.05),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.white),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Style header
                  Row(
                    children: [
                      Icon(
                        Icons.style,
                        color: _getLanguageColor(language),
                        size: 16,
                      ),
                      const SizedBox(width: 6),
                      Text(
                        _getStyleDisplayName(styleName),
                        style: TextStyle(
                          color: _getLanguageColor(language),
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const Spacer(),
                      Text(
                        '${wordPairs.length} pairs',
                        style: const TextStyle(
                          color: Colors.white70,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 8),
                  
                  // Word pairs chips
                  Wrap(
                    children: wordPairs.map((pair) => _buildWordPairChip(pair.value)).toList(),
                  ),
                ],
              ),
            );
          }).toList(),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.isVisible || widget.wordByWordData == null || widget.wordByWordData!.isEmpty) {
      return const SizedBox.shrink();
    }

    final groupedPairs = _groupWordPairs();

    if (groupedPairs.isEmpty) {
      return const SizedBox.shrink();
    }

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            Colors.purple[900]!.withOpacity(0.3),
            Colors.blue[900]!.withOpacity(0.3),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.purple, width: 1),
      ),
      child: Column(
        children: [
          // Header
          InkWell(
            onTap: _toggleExpansion,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  const Icon(
                    Icons.hearing,
                    color: Colors.purple,
                    size: 24,
                  ),
                  const SizedBox(width: 12),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Word-by-Word Audio Breakdown',
                          style: TextStyle(
                            color: Colors.purple,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        SizedBox(height: 2),
                        Text(
                          'What you see is what you hear',
                          style: TextStyle(
                            color: Colors.purple,
                            fontSize: 12,
                            fontStyle: FontStyle.italic,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.orange.withOpacity(0.3),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.orange, width: 1),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.volume_up, size: 12, color: Colors.orange),
                        const SizedBox(width: 4),
                        Text(
                          'AUDIO FORMAT',
                          style: const TextStyle(
                            color: Colors.orange,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  Icon(
                    _isExpanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                    color: Colors.purple,
                  ),
                ],
              ),
            ),
          ),
          
          // Format explanation when collapsed
          if (!_isExpanded) ...[
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.white30),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.info_outline, color: Colors.cyan, size: 16),
                    const SizedBox(width: 8),
                    const Expanded(
                      child: Text(
                        'Format: [target word] ([Spanish equivalent])',
                        style: TextStyle(
                          color: Colors.cyan,
                          fontSize: 12,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ),
                    Text(
                      'Tap to view breakdown',
                      style: TextStyle(
                        color: Colors.purple[300],
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
          
          // Expandable content
          SizeTransition(
            sizeFactor: _expandAnimation,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Format explanation
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.cyan.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.cyan, width: 1),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Row(
                          children: [
                            Icon(Icons.format_quote, color: Colors.cyan, size: 16),
                            SizedBox(width: 6),
                            Text(
                              'Audio Format Explanation',
                              style: TextStyle(
                                color: Colors.cyan,
                                fontSize: 14,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'When you play the audio, you\'ll hear:',
                          style: TextStyle(color: Colors.white, fontSize: 12),
                        ),
                        const SizedBox(height: 4),
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: Colors.black.withOpacity(0.3),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: const Text(
                            '[German/English word] followed by [Spanish equivalent]',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 11,
                              fontFamily: 'monospace',
                              fontStyle: FontStyle.italic,
                            ),
                          ),
                        ),
                        const SizedBox(height: 6),
                        const Text(
                          'Example: "wake up" → "despertar" or "stehe auf" → "me levanto"',
                          style: TextStyle(
                            color: Colors.cyan,
                            fontSize: 11,
                            fontStyle: FontStyle.italic,
                          ),
                        ),
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // Language sections
                  ...groupedPairs.entries.map((languageEntry) {
                    return _buildLanguageSection(languageEntry.key, languageEntry.value);
                  }).toList(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}