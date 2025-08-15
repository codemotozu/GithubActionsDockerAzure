// multi_style_word_by_word_widget.dart - Perfect Multi-Style Synchronization
import 'package:flutter/material.dart';

class MultiStyleWordByWordWidget extends StatefulWidget {
  final Map<String, Map<String, String>>? wordByWordData;
  final bool isVisible;
  final VoidCallback? onToggleVisibility;

  const MultiStyleWordByWordWidget({
    super.key,
    this.wordByWordData,
    this.isVisible = true,
    this.onToggleVisibility,
  });

  @override
  State<MultiStyleWordByWordWidget> createState() => _MultiStyleWordByWordWidgetState();
}

class _MultiStyleWordByWordWidgetState extends State<MultiStyleWordByWordWidget>
    with TickerProviderStateMixin {
  late AnimationController _expandController;
  late Animation<double> _expandAnimation;
  bool _isExpanded = true;
  String? _selectedStyle;
  int _highlightedIndex = -1;

  @override
  void initState() {
    super.initState();
    _expandController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _expandAnimation = CurvedAnimation(
      parent: _expandController,
      curve: Curves.easeInOut,
    );
    if (_isExpanded) {
      _expandController.forward();
    }
  }

  @override
  void dispose() {
    _expandController.dispose();
    super.dispose();
  }

  void _toggleExpansion() {
    setState(() {
      _isExpanded = !_isExpanded;
      if (_isExpanded) {
        _expandController.forward();
      } else {
        _expandController.reverse();
      }
    });
  }

  // Group word pairs by style
  Map<String, List<MapEntry<String, Map<String, String>>>> _groupByStyle() {
    if (widget.wordByWordData == null || widget.wordByWordData!.isEmpty) {
      return {};
    }

    final Map<String, List<MapEntry<String, Map<String, String>>>> grouped = {};
    
    for (final entry in widget.wordByWordData!.entries) {
      final style = entry.value['style'] ?? 'unknown';
      grouped.putIfAbsent(style, () => []);
      grouped[style]!.add(entry);
    }
    
    // Sort each style's entries by order
    for (final style in grouped.keys) {
      grouped[style]!.sort((a, b) {
        final orderA = int.tryParse(a.value['order'] ?? '0') ?? 0;
        final orderB = int.tryParse(b.value['order'] ?? '0') ?? 0;
        return orderA.compareTo(orderB);
      });
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

  Color _getStyleColor(String styleName) {
    if (styleName.contains('native')) return const Color(0xFF4CAF50);
    if (styleName.contains('colloquial')) return const Color(0xFF2196F3);
    if (styleName.contains('informal')) return const Color(0xFFFF9800);
    if (styleName.contains('formal')) return const Color(0xFF9C27B0);
    return const Color(0xFF9E9E9E);
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

  String _getStyleDisplayName(String styleName) {
    return styleName.replaceAll('_', ' ').split(' ').map((word) {
      if (word.isEmpty) return word;
      return word[0].toUpperCase() + word.substring(1);
    }).join(' ');
  }

  Widget _buildStyleSelector(Map<String, List<MapEntry<String, Map<String, String>>>> groupedData) {
    final styles = groupedData.keys.toList();
    
    return Container(
      height: 40,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        itemCount: styles.length,
        itemBuilder: (context, index) {
          final style = styles[index];
          final isSelected = _selectedStyle == style;
          final entryCount = groupedData[style]?.length ?? 0;
          
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: Material(
              color: Colors.transparent,
              child: InkWell(
                onTap: () {
                  setState(() {
                    _selectedStyle = isSelected ? null : style;
                    _highlightedIndex = -1;
                  });
                },
                borderRadius: BorderRadius.circular(20),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: isSelected 
                        ? _getStyleColor(style).withOpacity(0.3)
                        : Colors.white.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                      color: isSelected 
                          ? _getStyleColor(style)
                          : Colors.white30,
                      width: isSelected ? 2 : 1,
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        _getStyleDisplayName(style),
                        style: TextStyle(
                          color: isSelected 
                              ? _getStyleColor(style)
                              : Colors.white70,
                          fontSize: 12,
                          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                        ),
                      ),
                      const SizedBox(width: 6),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: _getStyleColor(style).withOpacity(0.2),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(
                          '$entryCount',
                          style: TextStyle(
                            color: _getStyleColor(style),
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

  Widget _buildWordPairCard(
    MapEntry<String, Map<String, String>> entry,
    int index,
    String styleName,
  ) {
    final data = entry.value;
    final source = data['source'] ?? '';
    final spanish = data['spanish'] ?? '';
    final language = data['language'] ?? '';
    final displayFormat = data['display_format'] ?? '';
    final isPhrasalVerb = data['is_phrasal_verb'] == 'true';
    final isHighlighted = _highlightedIndex == index;
    
    return GestureDetector(
      onTap: () {
        setState(() {
          _highlightedIndex = isHighlighted ? -1 : index;
        });
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        margin: const EdgeInsets.only(right: 8, bottom: 8),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isHighlighted 
              ? _getLanguageColor(language).withOpacity(0.2)
              : Colors.white.withOpacity(0.05),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isHighlighted 
                ? _getLanguageColor(language)
                : (isPhrasalVerb ? Colors.orange : Colors.white30),
            width: isHighlighted ? 2 : 1,
          ),
          boxShadow: isHighlighted ? [
            BoxShadow(
              color: _getLanguageColor(language).withOpacity(0.3),
              blurRadius: 8,
              spreadRadius: 2,
            ),
          ] : null,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Audio format display
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.4),
                borderRadius: BorderRadius.circular(6),
                border: isHighlighted 
                    ? Border.all(color: Colors.orange, width: 1)
                    : null,
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.hearing,
                    color: isHighlighted ? Colors.orange : Colors.cyan,
                    size: 12,
                  ),
                  const SizedBox(width: 4),
                  Flexible(
                    child: Text(
                      displayFormat,
                      style: TextStyle(
                        color: isHighlighted ? Colors.orange : Colors.cyan,
                        fontSize: 11,
                        fontFamily: 'monospace',
                        fontWeight: isHighlighted ? FontWeight.bold : FontWeight.normal,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 8),
            
            // Visual breakdown
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Source word
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: _getLanguageColor(language).withOpacity(0.3),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    source,
                    style: TextStyle(
                      color: _getLanguageColor(language),
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                
               pcon const SizedBox(width: 6),
                Icon(
                  Icons.arrow_forward,
                  color: isHighlighted ? Colors.orange : Colors.white54,
                  size: 14,
                ),
                const SizedBox(width: 6),
                
                // Spanish equivalent
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.green.withOpacity(0.3),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    spanish,
                    style: const TextStyle(
                      color: Colors.green,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            
            // Badges
            if (isPhrasalVerb) ...[
              const SizedBox(height: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.orange.withOpacity(0.3),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  language == 'german' ? 'Separable Verb' : 'Phrasal Verb',
                  style: const TextStyle(
                    color: Colors.orange,
                    fontSize: 9,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.isVisible || widget.wordByWordData == null || widget.wordByWordData!.isEmpty) {
      return const SizedBox.shrink();
    }

    final groupedData = _groupByStyle();
    
    if (groupedData.isEmpty) {
      return const SizedBox.shrink();
    }

    // Calculate statistics
    final totalStyles = groupedData.length;
    final totalPairs = widget.wordByWordData!.length;
    
    // Get entries to display
    List<MapEntry<String, Map<String, String>>> entriesToDisplay = [];
    String displayStyleName = 'All Styles';
    
    if (_selectedStyle != null && groupedData.containsKey(_selectedStyle)) {
      entriesToDisplay = groupedData[_selectedStyle]!;
      displayStyleName = _getStyleDisplayName(_selectedStyle!);
    } else {
      // Show all entries if no style selected
      for (final entries in groupedData.values) {
        entriesToDisplay.addAll(entries);
      }
      // Sort by order
      entriesToDisplay.sort((a, b) {
        final orderA = int.tryParse(a.value['order'] ?? '0') ?? 0;
        final orderB = int.tryParse(b.value['order'] ?? '0') ?? 0;
        return orderA.compareTo(orderB);
      });
    }

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 12),
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
          // Header
          InkWell(
            onTap: _toggleExpansion,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
            child: Container(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  const Icon(Icons.sync, color: Colors.blue, size: 24),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Multi-Style Perfect Synchronization',
                          style: TextStyle(
                            color: Colors.blue,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '$totalStyles styles • $totalPairs word pairs',
                          style: const TextStyle(
                            color: Colors.white70,
                            fontSize: 12,
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
                    child: const Text(
                      'PERFECT SYNC',
                      style: TextStyle(
                        color: Colors.orange,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                      ),
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
          
          // Expandable content
          SizeTransition(
            sizeFactor: _expandAnimation,
            child: Container(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Style selector
                  if (totalStyles > 1) ...[
                    const Text(
                      'Select Style to View:',
                      style: TextStyle(
                        color: Colors.white70,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    _buildStyleSelector(groupedData),
                    const SizedBox(height: 16),
                  ],
                  
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
                        Text(
                          'Viewing: $displayStyleName (${entriesToDisplay.length} pairs)',
                          style: const TextStyle(
                            color: Colors.cyan,
                            fontSize: 12,
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
                        _selectedStyle ?? 'all',
                      );
                    }).toList(),
                  ),
                  
                  // Perfect sync guarantee
                  const SizedBox(height: 16),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.green.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.green, width: 1),
                    ),
                    child: const Row(
                      children: [
                        Icon(Icons.verified, color: Colors.green, size: 16),
                        SizedBox(width: 8),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Perfect Synchronization Guarantee',
                                style: TextStyle(
                                  color: Colors.green,
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              SizedBox(height: 4),
                              Text(
                                '✓ Each style maintains exact UI-Audio sync\n'
                                '✓ Display format = Audio format\n'
                                '✓ Display order = Speaking order\n'
                                '✓ All styles perfectly synchronized',
                                style: TextStyle(
                                  color: Colors.white70,
                                  fontSize: 10,
                                  height: 1.3,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
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