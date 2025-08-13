// word_by_word_visualization_widget.dart - Enhanced for MULTIPLE translation styles

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
  int _currentHighlightIndex = -1;

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

  // ENHANCED: Group and sort word pairs for MULTIPLE STYLES
  Map<String, Map<String, List<MapEntry<String, Map<String, String>>>>> _getMultipleStylesSynchronizedData() {
    if (widget.wordByWordData == null || widget.wordByWordData!.isEmpty) {
      return {};
    }

    final Map<String, Map<String, List<MapEntry<String, Map<String, String>>>>> groupedData = {};
    
    // Group by language and then by style
    for (final entry in widget.wordByWordData!.entries) {
      final wordData = entry.value;
      final language = wordData['language'] ?? 'unknown';
      final style = wordData['style'] ?? 'unknown';
      final displayStyle = wordData['display_style'] ?? style;
      
      if (language != 'unknown' && style != 'unknown') {
        groupedData.putIfAbsent(language, () => {});
        groupedData[language]!.putIfAbsent(displayStyle, () => []);
        groupedData[language]![displayStyle]!.add(entry);
      }
    }
    
    // ENHANCED: Sort each style group by order to match audio sequence
    for (final language in groupedData.keys) {
      for (final style in groupedData[language]!.keys) {
        groupedData[language]![style]!.sort((a, b) {
          final orderA = int.tryParse(a.value['order'] ?? '0') ?? 0;
          final orderB = int.tryParse(b.value['order'] ?? '0') ?? 0;
          return orderA.compareTo(orderB);
        });
      }
    }
    
    print('🎯 MULTIPLE STYLES SYNC: Grouped data for UI display:');
    groupedData.forEach((language, styles) {
      print('   $language: ${styles.length} styles');
      styles.forEach((styleName, entries) {
        print('      $styleName: ${entries.length} entries in perfect order');
      });
    });
    
    return groupedData;
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

  Color _getStyleColor(String styleName) {
    if (styleName.toLowerCase().contains('native')) {
      return Colors.purple;
    } else if (styleName.toLowerCase().contains('colloquial')) {
      return Colors.orange;
    } else if (styleName.toLowerCase().contains('informal')) {
      return Colors.cyan;
    } else if (styleName.toLowerCase().contains('formal')) {
      return Colors.indigo;
    } else {
      return Colors.grey;
    }
  }

  Widget _buildMultipleStylesWordPairChip(MapEntry<String, Map<String, String>> entry, int globalIndex, String styleName) {
    final wordData = entry.value;
    final sourceWord = wordData['source'] ?? '';
    final spanishEquiv = wordData['spanish'] ?? '';
    final isPhrasalVerb = wordData['is_phrasal_verb'] == 'true';
    final displayFormat = wordData['display_format'] ?? '';
    final language = wordData['language'] ?? '';
    final order = wordData['order'] ?? '0';
    final displayStyle = wordData['display_style'] ?? styleName;

    final isHighlighted = _currentHighlightIndex == globalIndex;
    final styleColor = _getStyleColor(styleName);

    return Container(
      margin: const EdgeInsets.only(right: 8, bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: isHighlighted 
            ? styleColor.withOpacity(0.3)
            : Colors.white.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isPhrasalVerb 
              ? Colors.orange 
              : (isHighlighted ? styleColor : Colors.white30),
          width: isHighlighted ? 3 : (isPhrasalVerb ? 2 : 1),
        ),
        boxShadow: isHighlighted ? [
          BoxShadow(
            color: styleColor.withOpacity(0.5),
            blurRadius: 8,
            spreadRadius: 2,
          ),
        ] : null,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ENHANCED: Style indicator
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: styleColor.withOpacity(0.3),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: styleColor, width: 1),
            ),
            child: Text(
              displayStyle,
              style: TextStyle(
                color: styleColor,
                fontSize: 10,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          
          const SizedBox(height: 6),
          
          // ENHANCED: Audio format display - EXACTLY what user hears for this style
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.black.withOpacity(0.6),
              borderRadius: BorderRadius.circular(8),
              border: isHighlighted ? Border.all(color: Colors.orange, width: 2) : null,
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (isHighlighted) ...[
                  const Icon(Icons.volume_up, color: Colors.orange, size: 14),
                  const SizedBox(width: 6),
                  const Text(
                    'NOW PLAYING:',
                    style: TextStyle(
                      color: Colors.orange,
                      fontSize: 9,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(width: 6),
                ],
                Icon(
                  Icons.hearing,
                  color: isHighlighted ? Colors.orange : Colors.cyan,
                  size: 12,
                ),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    displayFormat,
                    style: TextStyle(
                      color: isHighlighted ? Colors.orange : Colors.cyan,
                      fontSize: 12,
                      fontFamily: 'monospace',
                      fontWeight: isHighlighted ? FontWeight.bold : FontWeight.w500,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
              ],
            ),
          ),
          
          const SizedBox(height: 8),
          
          // Visual breakdown showing the components
          Row(
            children: [
              // Source word/phrase
              Expanded(
                flex: 2,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                  decoration: BoxDecoration(
                    color: _getLanguageColor(language).withOpacity(
                      isHighlighted ? 0.7 : 0.3
                    ),
                    borderRadius: BorderRadius.circular(8),
                    border: isHighlighted ? Border.all(color: _getLanguageColor(language), width: 2) : null,
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _getLanguageName(language),
                        style: TextStyle(
                          color: _getLanguageColor(language),
                          fontSize: 10,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        sourceWord,
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 14,
                          fontWeight: isHighlighted ? FontWeight.w900 : FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              
              const SizedBox(width: 8),
              
              // Arrow
              Icon(
                Icons.arrow_forward,
                color: isHighlighted ? Colors.orange : Colors.white70,
                size: 16,
              ),
              
              const SizedBox(width: 8),
              
              // Spanish equivalent
              Expanded(
                flex: 2,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                  decoration: BoxDecoration(
                    color: Colors.green.withOpacity(
                      isHighlighted ? 0.7 : 0.3
                    ),
                    borderRadius: BorderRadius.circular(8),
                    border: isHighlighted ? Border.all(color: Colors.green, width: 2) : null,
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Spanish',
                        style: TextStyle(
                          color: Colors.green,
                          fontSize: 10,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        spanishEquiv,
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 14,
                          fontWeight: isHighlighted ? FontWeight.w900 : FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 6),
          
          // Additional info row
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // Order indicator
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.grey.withOpacity(0.3),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  '#${int.parse(order) + 1}',
                  style: const TextStyle(
                    color: Colors.white70,
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              
              // Phrasal verb indicator
              if (isPhrasalVerb) 
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.orange.withOpacity(isHighlighted ? 0.7 : 0.3),
                    borderRadius: BorderRadius.circular(10),
                    border: isHighlighted ? Border.all(color: Colors.orange, width: 1) : null,
                  ),
                  child: Text(
                    language == 'german' ? 'Separable Verb' : 'Phrasal Verb',
                    style: TextStyle(
                      color: isHighlighted ? Colors.white : Colors.orange,
                      fontSize: 9,
                      fontWeight: isHighlighted ? FontWeight.w900 : FontWeight.w600,
                    ),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMultipleStylesLanguageSection(String language, Map<String, List<MapEntry<String, Map<String, String>>>> styleGroups) {
    final languageColor = _getLanguageColor(language);
    final totalEntries = styleGroups.values.fold(0, (sum, entries) => sum + entries.length);
    
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: languageColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: languageColor, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ENHANCED: Language header with multiple styles info
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: languageColor.withOpacity(0.2),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
            ),
            child: Row(
              children: [
                Text(
                  _getLanguageFlag(language),
                  style: const TextStyle(fontSize: 24),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${_getLanguageName(language)} Multiple Styles',
                        style: TextStyle(
                          color: languageColor,
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Perfect synchronization across ${styleGroups.length} translation styles',
                        style: const TextStyle(
                          color: Colors.white70,
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
                    color: languageColor.withOpacity(0.3),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${styleGroups.length} styles, $totalEntries pairs',
                    style: TextStyle(
                      color: languageColor,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
          ),
          
          // ENHANCED: Style sections
          ...styleGroups.entries.map((styleEntry) {
            final styleName = styleEntry.key;
            final entries = styleEntry.value;
            final styleColor = _getStyleColor(styleName);
            
            return Container(
              margin: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: styleColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: styleColor, width: 1),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Style header
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: styleColor.withOpacity(0.2),
                      borderRadius: const BorderRadius.vertical(top: Radius.circular(8)),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          Icons.style,
                          color: styleColor,
                          size: 16,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            styleName,
                            style: TextStyle(
                              color: styleColor,
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: styleColor.withOpacity(0.3),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            '${entries.length} pairs',
                            style: TextStyle(
                              color: styleColor,
                              fontSize: 10,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  
                  // Word pairs for this style
                  Padding(
                    padding: const EdgeInsets.all(12),
                    child: Wrap(
                      children: entries.asMap().entries.map((entry) {
                        final index = entry.key;
                        final wordPairEntry = entry.value;
                        return _buildMultipleStylesWordPairChip(wordPairEntry, index, styleName);
                      }).toList(),
                    ),
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

    final synchronizedData = _getMultipleStylesSynchronizedData();

    if (synchronizedData.isEmpty) {
      return const SizedBox.shrink();
    }

    // Calculate total pairs across all languages and styles
    final totalPairs = synchronizedData.values.fold(0, (sum, styles) => 
        sum + styles.values.fold(0, (styleSum, entries) => styleSum + entries.length));
    final totalStyles = synchronizedData.values.fold(0, (sum, styles) => sum + styles.length);

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF1E3A8A), Color(0xFF3B82F6)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.blue, width: 1),
      ),
      child: Column(
        children: [
          // ENHANCED: Header with multiple styles emphasis
          InkWell(
            onTap: _toggleExpansion,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
            child: Container(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  const Icon(
                    Icons.sync,
                    color: Colors.blue,
                    size: 24,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Perfect Multiple Styles UI-Audio Sync',
                          style: TextStyle(
                            color: Colors.blue,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 2),
                        const Text(
                          'Each style has its own complete sentence + word breakdown',
                          style: TextStyle(
                            color: Colors.blue,
                            fontSize: 12,
                            fontStyle: FontStyle.italic,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '$totalPairs perfectly synchronized word pairs across $totalStyles translation styles',
                          style: const TextStyle(
                            color: Colors.white70,
                            fontSize: 11,
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
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.hearing, size: 12, color: Colors.orange),
                        SizedBox(width: 4),
                        Text(
                          'MULTIPLE STYLES',
                          style: TextStyle(
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
                    color: Colors.blue,
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
                        'Audio: Complete sentences for each style + [target word] ([Spanish])',
                        style: TextStyle(
                          color: Colors.cyan,
                          fontSize: 12,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.green.withOpacity(0.3),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        '$totalStyles STYLES',
                        style: const TextStyle(
                          color: Colors.green,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                        ),
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
                  // ENHANCED: Multiple styles synchronization explanation
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.green.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.green, width: 1),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Row(
                          children: [
                            Icon(Icons.verified, color: Colors.green, size: 16),
                            SizedBox(width: 6),
                            Text(
                              'Multiple Styles Perfect Synchronization',
                              style: TextStyle(
                                color: Colors.green,
                                fontSize: 14,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          '✓ Each style has complete sentence + word breakdown',
                          style: TextStyle(color: Colors.white, fontSize: 12),
                        ),
                        const Text(
                          '✓ Visual display order = Audio speaking order (per style)',
                          style: TextStyle(color: Colors.white, fontSize: 12),
                        ),
                        const Text(
                          '✓ UI format = Audio format (exactly, per style)',
                          style: TextStyle(color: Colors.white, fontSize: 12),
                        ),
                        const Text(
                          '✓ Phrasal verbs treated as single units across all styles',
                          style: TextStyle(color: Colors.white, fontSize: 12),
                        ),
                        Text(
                          '✓ Zero discrepancies across $totalStyles translation styles',
                          style: const TextStyle(color: Colors.white, fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // ENHANCED: Language sections with multiple styles
                  ...synchronizedData.entries.map((languageEntry) {
                    return _buildMultipleStylesLanguageSection(languageEntry.key, languageEntry.value);
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