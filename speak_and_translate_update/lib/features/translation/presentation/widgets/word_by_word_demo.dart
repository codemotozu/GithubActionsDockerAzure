// word_by_word_demo.dart - Demo component showing perfect UI-Audio synchronization

import 'package:flutter/material.dart';
import 'dart:async';

class WordByWordDemo extends StatefulWidget {
  const WordByWordDemo({super.key});

  @override
  State<WordByWordDemo> createState() => _WordByWordDemoState();
}

class _WordByWordDemoState extends State<WordByWordDemo>
    with TickerProviderStateMixin {
  late AnimationController _highlightController;
  late Animation<Color?> _highlightAnimation;
  
  int _currentHighlightIndex = -1;
  bool _isPlaying = false;
  Timer? _audioSimulationTimer;

  // Demo data that shows EXACT synchronization
  final Map<String, Map<String, String>> _demoWordByWordData = {
    // English phrasal verbs - treated as single units
    'english_colloquial_0_wake_up': {
      'source': 'wake up',
      'spanish': 'despertar',
      'language': 'english',
      'style': 'english_colloquial',
      'order': '0',
      'is_phrasal_verb': 'true',
      'display_format': '[wake up] ([despertar])',
    },
    'english_colloquial_1_every': {
      'source': 'every',
      'spanish': 'cada',
      'language': 'english',
      'style': 'english_colloquial',
      'order': '1',
      'is_phrasal_verb': 'false',
      'display_format': '[every] ([cada])',
    },
    'english_colloquial_2_morning': {
      'source': 'morning',
      'spanish': 'mañana',
      'language': 'english',
      'style': 'english_colloquial',
      'order': '2',
      'is_phrasal_verb': 'false',
      'display_format': '[morning] ([mañana])',
    },
    
    // German separable verbs - treated as single units  
    'german_colloquial_0_stehe_auf': {
      'source': 'stehe auf',
      'spanish': 'me levanto',
      'language': 'german',
      'style': 'german_colloquial',
      'order': '0',
      'is_phrasal_verb': 'true',
      'display_format': '[stehe auf] ([me levanto])',
    },
    'german_colloquial_1_jeden': {
      'source': 'jeden',
      'spanish': 'cada',
      'language': 'german',
      'style': 'german_colloquial',
      'order': '1',
      'is_phrasal_verb': 'false',
      'display_format': '[jeden] ([cada])',
    },
    'german_colloquial_2_Tag': {
      'source': 'Tag',
      'spanish': 'día',
      'language': 'german',
      'style': 'german_colloquial',
      'order': '2',
      'is_phrasal_verb': 'false',
      'display_format': '[Tag] ([día])',
    },
  };

  @override
  void initState() {
    super.initState();
    _highlightController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );
    _highlightAnimation = ColorTween(
      begin: Colors.transparent,
      end: Colors.orange.withOpacity(0.3),
    ).animate(CurvedAnimation(
      parent: _highlightController,
      curve: Curves.easeInOut,
    ));
  }

  @override
  void dispose() {
    _highlightController.dispose();
    _audioSimulationTimer?.cancel();
    super.dispose();
  }

  void _simulateAudioPlayback() {
    if (_isPlaying) {
      _stopAudioSimulation();
      return;
    }

    setState(() {
      _isPlaying = true;
      _currentHighlightIndex = -1;
    });

    // Get ordered items for simulation
    final englishItems = _getOrderedItemsForLanguage('english');
    final germanItems = _getOrderedItemsForLanguage('german');
    final allItems = [...englishItems, ...germanItems];

    // Simulate audio playback with highlights
    int currentIndex = 0;
    _audioSimulationTimer = Timer.periodic(const Duration(milliseconds: 1500), (timer) {
      if (currentIndex >= allItems.length) {
        _stopAudioSimulation();
        return;
      }

      setState(() {
        _currentHighlightIndex = currentIndex;
      });

      _highlightController.forward().then((_) {
        _highlightController.reverse();
      });

      currentIndex++;
    });
  }

  void _stopAudioSimulation() {
    _audioSimulationTimer?.cancel();
    setState(() {
      _isPlaying = false;
      _currentHighlightIndex = -1;
    });
    _highlightController.reset();
  }

  List<MapEntry<String, Map<String, String>>> _getOrderedItemsForLanguage(String language) {
    return _demoWordByWordData.entries
        .where((entry) => entry.value['language'] == language)
        .toList()
      ..sort((a, b) {
        final orderA = int.tryParse(a.value['order'] ?? '0') ?? 0;
        final orderB = int.tryParse(b.value['order'] ?? '0') ?? 0;
        return orderA.compareTo(orderB);
      });
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

  Widget _buildWordPairChip(MapEntry<String, Map<String, String>> entry, int globalIndex) {
    final wordData = entry.value;
    final sourceWord = wordData['source'] ?? '';
    final spanishEquiv = wordData['spanish'] ?? '';
    final isPhrasalVerb = wordData['is_phrasal_verb'] == 'true';
    final displayFormat = wordData['display_format'] ?? '';
    final language = wordData['language'] ?? '';

    final isHighlighted = _currentHighlightIndex == globalIndex;

    return AnimatedBuilder(
      animation: _highlightAnimation,
      builder: (context, child) {
        return Container(
          margin: const EdgeInsets.only(right: 8, bottom: 8),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: isHighlighted 
                ? _highlightAnimation.value 
                : Colors.white.withOpacity(0.1),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: isPhrasalVerb 
                  ? Colors.orange 
                  : (isHighlighted ? Colors.orange : Colors.white30),
              width: isHighlighted ? 3 : (isPhrasalVerb ? 2 : 1),
            ),
            boxShadow: isHighlighted ? [
              BoxShadow(
                color: Colors.orange.withOpacity(0.5),
                blurRadius: 8,
                spreadRadius: 2,
              ),
            ] : null,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Audio format display - exactly what user hears
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.4),
                  borderRadius: BorderRadius.circular(12),
                  border: isHighlighted ? Border.all(color: Colors.orange, width: 2) : null,
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (isHighlighted) ...[
                      const Icon(Icons.volume_up, color: Colors.orange, size: 12),
                      const SizedBox(width: 4),
                    ],
                    Text(
                      displayFormat,
                      style: TextStyle(
                        color: isHighlighted ? Colors.orange : Colors.white,
                        fontSize: 11,
                        fontFamily: 'monospace',
                        fontWeight: isHighlighted ? FontWeight.bold : FontWeight.w500,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
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
                      color: _getLanguageColor(language).withOpacity(
                        isHighlighted ? 0.6 : 0.3
                      ),
                      borderRadius: BorderRadius.circular(8),
                      border: isHighlighted ? Border.all(color: _getLanguageColor(language), width: 2) : null,
                    ),
                    child: Text(
                      sourceWord,
                      style: TextStyle(
                        color: _getLanguageColor(language),
                        fontSize: 13,
                        fontWeight: isHighlighted ? FontWeight.w900 : FontWeight.bold,
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
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.green.withOpacity(
                        isHighlighted ? 0.6 : 0.3
                      ),
                      borderRadius: BorderRadius.circular(8),
                      border: isHighlighted ? Border.all(color: Colors.green, width: 2) : null,
                    ),
                    child: Text(
                      spanishEquiv,
                      style: TextStyle(
                        color: Colors.green,
                        fontSize: 13,
                        fontWeight: isHighlighted ? FontWeight.w900 : FontWeight.bold,
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
                    color: Colors.orange.withOpacity(isHighlighted ? 0.6 : 0.3),
                    borderRadius: BorderRadius.circular(10),
                    border: isHighlighted ? Border.all(color: Colors.orange, width: 2) : null,
                  ),
                  child: Text(
                    language == 'german' ? 'Separable Verb' : 'Phrasal Verb',
                    style: TextStyle(
                      color: Colors.orange,
                      fontSize: 9,
                      fontWeight: isHighlighted ? FontWeight.w900 : FontWeight.w600,
                    ),
                  ),
                ),
              ],
              
              // Currently playing indicator
              if (isHighlighted) ...[
                const SizedBox(height: 4),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 6,
                      height: 6,
                      decoration: const BoxDecoration(
                        color: Colors.orange,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 4),
                    const Text(
                      'NOW PLAYING',
                      style: TextStyle(
                        color: Colors.orange,
                        fontSize: 8,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ],
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final englishItems = _getOrderedItemsForLanguage('english');
    final germanItems = _getOrderedItemsForLanguage('german');
    final allItems = [...englishItems, ...germanItems];

    return Scaffold(
      backgroundColor: const Color(0xFF000000),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1C1C1E),
        title: const Text(
          'Word-by-Word Demo',
          style: TextStyle(color: Colors.white),
        ),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header explanation
            Container(
              padding: const EdgeInsets.all(16),
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
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.sync, color: Colors.purple, size: 24),
                      SizedBox(width: 12),
                      Text(
                        'Perfect UI-Audio Synchronization Demo',
                        style: TextStyle(
                          color: Colors.purple,
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'What you see is EXACTLY what you hear!',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'This demo shows how phrasal verbs (like "wake up") and German separable verbs (like "stehe auf") are treated as single units in both the visual display and audio output.',
                    style: TextStyle(
                      color: Colors.white70,
                      fontSize: 14,
                    ),
                  ),
                  const SizedBox(height: 12),
                  ElevatedButton.icon(
                    onPressed: _simulateAudioPlayback,
                    icon: Icon(
                      _isPlaying ? Icons.stop : Icons.play_arrow,
                      color: Colors.white,
                    ),
                    label: Text(
                      _isPlaying ? 'Stop Demo' : 'Start Audio Demo',
                      style: const TextStyle(color: Colors.white),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: _isPlaying ? Colors.red : Colors.orange,
                    ),
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 24),
            
            // English section
            Container(
              margin: const EdgeInsets.only(bottom: 20),
              decoration: BoxDecoration(
                color: Colors.blue.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.blue, width: 1),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      children: [
                        const Text('🇺🇸', style: TextStyle(fontSize: 20)),
                        const SizedBox(width: 8),
                        const Text(
                          'English Word-by-Word',
                          style: TextStyle(
                            color: Colors.blue,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const Spacer(),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: Colors.blue.withOpacity(0.3),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            'Sentence: "I wake up every morning"',
                            style: const TextStyle(
                              color: Colors.blue,
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                    child: Wrap(
                      children: englishItems.asMap().entries.map((mapEntry) {
                        return _buildWordPairChip(mapEntry.value, mapEntry.key);
                      }).toList(),
                    ),
                  ),
                ],
              ),
            ),
            
            // German section
            Container(
              margin: const EdgeInsets.only(bottom: 20),
              decoration: BoxDecoration(
                color: Colors.amber.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.amber, width: 1),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      children: [
                        const Text('🇩🇪', style: TextStyle(fontSize: 20)),
                        const SizedBox(width: 8),
                        const Text(
                          'German Word-by-Word',
                          style: TextStyle(
                            color: Colors.amber,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const Spacer(),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: Colors.amber.withOpacity(0.3),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            'Sentence: "Ich stehe jeden Tag auf"',
                            style: const TextStyle(
                              color: Colors.amber,
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                    child: Wrap(
                      children: germanItems.asMap().entries.map((mapEntry) {
                        return _buildWordPairChip(
                          mapEntry.value, 
                          mapEntry.key + englishItems.length
                        );
                      }).toList(),
                    ),
                  ),
                ],
              ),
            ),
            
            // Format explanation
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.cyan.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.cyan, width: 1),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.info, color: Colors.cyan, size: 20),
                      SizedBox(width: 8),
                      Text(
                        'Key Points',
                        style: TextStyle(
                          color: Colors.cyan,
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  _buildKeyPoint(
                    '🎯 Perfect Synchronization',
                    'The visual display matches the audio EXACTLY - no discrepancies.'
                  ),
                  _buildKeyPoint(
                    '🔗 Phrasal/Separable Verbs',
                    'Complex verbs like "wake up" and "stehe auf" are treated as single units.'
                  ),
                  _buildKeyPoint(
                    '📱 Format Consistency', 
                    'Audio format: [target word] ([Spanish equivalent]) matches UI display.'
                  ),
                  _buildKeyPoint(
                    '🎵 Sequential Order',
                    'Audio plays word pairs in the exact same order as displayed visually.'
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildKeyPoint(String title, String description) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  description,
                  style: const TextStyle(
                    color: Colors.white70,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}