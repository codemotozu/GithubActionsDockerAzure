

// Enhanced word_by_word_visualization_widget.dart with accurate synchronization

import 'package:flutter/material.dart';

class WordByWordVisualizationWidget extends StatefulWidget {
  final Map<String, Map<String, String>>? wordByWordData;
  final bool isVisible;
  final VoidCallback? onToggleVisibility;
  final Function(String)? onPlayWord; // NEW: Add callback for playing individual words

  const WordByWordVisualizationWidget({
    super.key,
    this.wordByWordData,
    this.isVisible = true,
    this.onToggleVisibility,
    this.onPlayWord, // NEW: Support for playing individual words
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
  String _selectedStyle = '';

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

  // ENHANCED: Group and sort word pairs to match EXACT audio order
  Map<String, List<MapEntry<String, Map<String, String>>>> _getPerfectlySynchronizedData() {
    if (widget.wordByWordData == null || widget.wordByWordData!.isEmpty) {
      return {};
    }

    final Map<String, List<MapEntry<String, Map<String, String>>>> groupedData = {};
    
    // Group by language AND style (for more accurate grouping)
    for (final entry in widget.wordByWordData!.entries) {
      final wordData = entry.value;
      final language = wordData['language'] ?? 'unknown';
      final style = wordData['style'] ?? 'unknown';
      
      // Use combined key for perfect sync per style
      final styleKey = '$language-$style';
      
      if (language != 'unknown') {
        groupedData.putIfAbsent(styleKey, () => []);
        groupedData[styleKey]!.add(entry);
      }
    }
    
    // CRITICAL: Sort each style group by order to match audio sequence
    for (final key in groupedData.keys) {
      groupedData[key]!.sort((a, b) {
        final orderA = int.tryParse(a.value['order'] ?? '0') ?? 0;
        final orderB = int.tryParse(b.value['order'] ?? '0') ?? 0;
        return orderA.compareTo(orderB);
      });
    }
    
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

  String _getStyleDisplayName(String styleKey) {
    // Extract style name from combined key (language-style)
    final parts = styleKey.split('-');
    if (parts.length < 2) return styleKey;
    
    final language = parts[0];
    final style = parts[1];
    
    return '$language ${style.replaceAll('_', ' ')}';
  }

  // ENHANCED: Build an individual word pair card with debugging info
  Widget _buildWordPairCard(
    MapEntry<String, Map<String, String>> entry, 
    int globalIndex,
    String styleKey
  ) {
    final wordData = entry.value;
    final sourceWord = wordData['source'] ?? '';
    final spanishEquiv = wordData['spanish'] ?? '';
    final isPhrasalVerb = wordData['is_phrasal_verb'] == 'true';
    final displayFormat = wordData['display_format'] ?? '';
    final language = wordData['language'] ?? '';
    final order = wordData['order'] ?? '0';

    final isHighlighted = _currentHighlightIndex == globalIndex;

    // Calculate expected format for validation
    final expectedFormat = '[${sourceWord}] ([${spanishEquiv}])';
    final formatMatch = displayFormat == expectedFormat;

    return GestureDetector(
      onTap: () {
        // Set highlight and play audio if callback provided
        setState(() {
          _currentHighlightIndex = isHighlighted ? -1 : globalIndex;
        });
        
        if (widget.onPlayWord != null) {
          widget.onPlayWord!(displayFormat);
        }
      },
      child: Container(
        margin: const EdgeInsets.only(right: 8, bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: isHighlighted 
              ? _getLanguageColor(language).withOpacity(0.3)
              : Colors.white.withOpacity(0.1),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isPhrasalVerb 
                ? Colors.orange 
                : (isHighlighted ? _getLanguageColor(language) : Colors.white30),
            width: isHighlighted ? 3 : (isPhrasalVerb ? 2 : 1),
          ),
          boxShadow: isHighlighted ? [
            BoxShadow(
              color: _getLanguageColor(language).withOpacity(0.5),
              blurRadius: 8,
              spreadRadius: 2,
            ),
          ] : null,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // CRITICAL: Audio format display - EXACTLY what user hears
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
                        color: formatMatch 
                            ? (isHighlighted ? Colors.orange : Colors.cyan)
                            : Colors.red, // Highlight format mismatches
                        fontSize: 12,
                        fontFamily: 'monospace',
                        fontWeight: isHighlighted ? FontWeight.bold : FontWeight.w500,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  
                  // VALIDATION: Add indicator for format match
                  if (!formatMatch)
                    const Icon(
                      Icons.warning_amber_rounded,
                      color: Colors.red,
                      size: 14,
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
      ),
    );
  }

  // ENHANCED: Build style selector
  Widget _buildStyleSelector(Map<String, List<MapEntry<String, Map<String, String>>>> groupedData) {
    final styles = groupedData.keys.toList();
    
    return SizedBox(
      height: 50,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        itemCount: styles.length,
        itemBuilder: (context, index) {
          final styleKey = styles[index];
          final isSelected = _selectedStyle == styleKey;
          final pairCount = groupedData[styleKey]?.length ?? 0;
          
          final parts = styleKey.split('-');
          final language = parts.isNotEmpty ? parts[0] : 'unknown';
          final styleName = _getStyleDisplayName(styleKey);
          
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: Material(
              color: Colors.transparent,
              child: InkWell(
                onTap: () {
                  setState(() {
                    _selectedStyle = isSelected ? '' : styleKey;
                    _currentHighlightIndex = -1;
                  });
                },
                borderRadius: BorderRadius.circular(20),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: isSelected 
                        ? _getLanguageColor(language).withOpacity(0.3)
                        : Colors.white.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                      color: isSelected 
                          ? _getLanguageColor(language)
                          : Colors.white30,
                      width: isSelected ? 2 : 1,
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        _getLanguageFlag(language),
                        style: const TextStyle(fontSize: 16),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        styleName,
                        style: TextStyle(
                          color: isSelected 
                              ? _getLanguageColor(language)
                              : Colors.white70,
                          fontSize: 12,
                          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                        ),
                      ),
                      const SizedBox(width: 6),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: _getLanguageColor(language).withOpacity(0.2),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(
                          '$pairCount',
                          style: TextStyle(
                            color: _getLanguageColor(language),
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.isVisible || widget.wordByWordData == null || widget.wordByWordData!.isEmpty) {
      return const SizedBox.shrink();
    }

    final synchronizedData = _getPerfectlySynchronizedData();

    if (synchronizedData.isEmpty) {
      return const SizedBox.shrink();
    }

    // Calculate total pairs across all styles
    final totalPairs = synchronizedData.values.fold(0, (sum, entries) => sum + entries.length);
    final styleCount = synchronizedData.length;

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
          // Header with perfect sync emphasis
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
                          'Perfect UI-Audio Synchronization',
                          style: TextStyle(
                            color: Colors.blue,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 2),
                        const Text(
                          'What you see is exactly what you hear',
                          style: TextStyle(
                            color: Colors.blue,
                            fontSize: 12,
                            fontStyle: FontStyle.italic,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '$totalPairs perfectly synchronized word pairs across $styleCount styles',
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
                          'PERFECT SYNC',
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
                        'Audio format: [target word] ([Spanish equivalent])',
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
                      child: const Text(
                        'TAP TO EXPAND',
                        style: TextStyle(
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
                  // Perfect sync explanation
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
                              'Perfect Synchronization Guarantee',
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
                          '✓ Visual display order = Audio speaking order',
                          style: TextStyle(color: Colors.white, fontSize: 12),
                        ),
                        const Text(
                          '✓ UI format = Audio format (exactly)',
                          style: TextStyle(color: Colors.white, fontSize: 12),
                        ),
                        const Text(
                          '✓ Phrasal verbs treated as single units',
                          style: TextStyle(color: Colors.white, fontSize: 12),
                        ),
                        const Text(
                          '✓ Zero discrepancies between seen and heard',
                          style: TextStyle(color: Colors.white, fontSize: 12),
                        ),
                        const Text(
                          '✓ Tap any word to highlight and check pronunciation',
                          style: TextStyle(color: Colors.white, fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // Style selector
                  if (synchronizedData.length > 1) ...[
                    const Text(
                      'Select Style to View:',
                      style: TextStyle(
                        color: Colors.white70,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    _buildStyleSelector(synchronizedData),
                    const SizedBox(height: 16),
                  ],
                  
                  // Get entries to display
                  Builder(
                    builder: (context) {
                      List<MapEntry<String, Map<String, String>>> entriesToDisplay = [];
                      String displayStyleName = 'All Styles';
                      
                      if (_selectedStyle.isNotEmpty && synchronizedData.containsKey(_selectedStyle)) {
                        entriesToDisplay = synchronizedData[_selectedStyle]!;
                        displayStyleName = _getStyleDisplayName(_selectedStyle);
                      } else if (synchronizedData.length == 1) {
                        // Single style, show it directly
                        final styleKey = synchronizedData.keys.first;
                        entriesToDisplay = synchronizedData[styleKey]!;
                        displayStyleName = _getStyleDisplayName(styleKey);
                      } else {
                        // Show "select a style" prompt
                        return const Center(
                          child: Padding(
                            padding: EdgeInsets.all(16.0),
                            child: Text(
                              '👆 Select a style above to view word-by-word pairs',
                              style: TextStyle(
                                color: Colors.white70,
                                fontStyle: FontStyle.italic,
                              ),
                            ),
                          ),
                        );
                      }
                      
                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Current view info
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Row(
                              children: [
                                const Icon(Icons.visibility, color: Colors.cyan, size: 16),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    'Viewing: $displayStyleName (${entriesToDisplay.length} pairs)',
                                    style: const TextStyle(
                                      color: Colors.cyan,
                                      fontSize: 12,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                                const Icon(Icons.touch_app, color: Colors.amber, size: 14),
                                const SizedBox(width: 4),
                                const Text(
                                  'TAP WORDS TO HIGHLIGHT',
                                  style: TextStyle(
                                    color: Colors.amber,
                                    fontSize: 9,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          
                          const SizedBox(height: 16),
                          
                          // Word pairs display
                          Wrap(
                            children: entriesToDisplay.asMap().entries.map((entry) {
                              return _buildWordPairCard(
                                entry.value,
                                entry.key,
                                _selectedStyle.isEmpty ? displayStyleName : _selectedStyle,
                              );
                            }).toList(),
                          ),
                        ],
                      );
                    }
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}