// word_by_word_demo_screen.dart - Demo screen to test and showcase word-by-word visualization

import 'package:flutter/material.dart';
import '../widgets/word_by_word_visualization_widget.dart';

class WordByWordDemoScreen extends StatefulWidget {
  const WordByWordDemoScreen({super.key});

  @override
  State<WordByWordDemoScreen> createState() => _WordByWordDemoScreenState();
}

class _WordByWordDemoScreenState extends State<WordByWordDemoScreen> {
  bool _showEnglishExample = true;
  bool _showGermanExample = true;
  bool _showMixedExample = false;

  // Sample data that matches what the backend would send
  final Map<String, Map<String, String>> _sampleEnglishData = {
    'english_colloquial_0_wake_up': {
      'source': 'wake up',
      'spanish': 'despertar',
      'language': 'english',
      'style': 'english_colloquial',
      'order': '0',
      'is_phrasal_verb': 'true',
      'display_format': '[wake up] ([despertar])'
    },
    'english_colloquial_1_early': {
      'source': 'early',
      'spanish': 'temprano',
      'language': 'english',
      'style': 'english_colloquial',
      'order': '1',
      'is_phrasal_verb': 'false',
      'display_format': '[early] ([temprano])'
    },
    'english_colloquial_2_go_out': {
      'source': 'go out',
      'spanish': 'salir',
      'language': 'english',
      'style': 'english_colloquial',
      'order': '2',
      'is_phrasal_verb': 'true',
      'display_format': '[go out] ([salir])'
    },
    'english_colloquial_3_came_up_with': {
      'source': 'came up with',
      'spanish': 'inventó',
      'language': 'english',
      'style': 'english_colloquial',
      'order': '3',
      'is_phrasal_verb': 'true',
      'display_format': '[came up with] ([inventó])'
    },
    'english_formal_0_wake_up': {
      'source': 'wake up',
      'spanish': 'despertar',
      'language': 'english',
      'style': 'english_formal',
      'order': '0',
      'is_phrasal_verb': 'true',
      'display_format': '[wake up] ([despertar])'
    },
    'english_formal_1_arise': {
      'source': 'arise',
      'spanish': 'levantarse',
      'language': 'english',
      'style': 'english_formal',
      'order': '1',
      'is_phrasal_verb': 'false',
      'display_format': '[arise] ([levantarse])'
    },
  };

  final Map<String, Map<String, String>> _sampleGermanData = {
    'german_colloquial_0_stehe_auf': {
      'source': 'stehe auf',
      'spanish': 'me levanto',
      'language': 'german',
      'style': 'german_colloquial',
      'order': '0',
      'is_phrasal_verb': 'true',
      'display_format': '[stehe auf] ([me levanto])'
    },
    'german_colloquial_1_früh': {
      'source': 'früh',
      'spanish': 'temprano',
      'language': 'german',
      'style': 'german_colloquial',
      'order': '1',
      'is_phrasal_verb': 'false',
      'display_format': '[früh] ([temprano])'
    },
    'german_colloquial_2_gehe_aus': {
      'source': 'gehe aus',
      'spanish': 'salgo',
      'language': 'german',
      'style': 'german_colloquial',
      'order': '2',
      'is_phrasal_verb': 'true',
      'display_format': '[gehe aus] ([salgo])'
    },
    'german_native_0_aufstehen': {
      'source': 'aufstehen',
      'spanish': 'levantarse',
      'language': 'german',
      'style': 'german_native',
      'order': '0',
      'is_phrasal_verb': 'false',
      'display_format': '[aufstehen] ([levantarse])'
    },
  };

  Map<String, Map<String, String>> _getCurrentData() {
    final data = <String, Map<String, String>>{};
    
    if (_showEnglishExample) {
      data.addAll(_sampleEnglishData);
    }
    
    if (_showGermanExample) {
      data.addAll(_sampleGermanData);
    }
    
    if (_showMixedExample) {
      // Add some mixed examples
      data.addAll({
        'english_informal_0_chill_out': {
          'source': 'chill out',
          'spanish': 'relajarse',
          'language': 'english',
          'style': 'english_informal',
          'order': '0',
          'is_phrasal_verb': 'true',
          'display_format': '[chill out] ([relajarse])'
        },
        'german_informal_0_abhängen': {
          'source': 'abhängen',
          'spanish': 'relajarse',
          'language': 'german',
          'style': 'german_informal',
          'order': '0',
          'is_phrasal_verb': 'false',
          'display_format': '[abhängen] ([relajarse])'
        },
      });
    }
    
    return data;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF000000),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1C1C1E),
        title: const Text(
          'Word-by-Word Visualization Demo',
          style: TextStyle(color: Colors.white),
        ),
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Demo Info
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [Colors.blue[900]!.withOpacity(0.3), Colors.cyan[900]!.withOpacity(0.3)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.cyan, width: 1),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.info_outline, color: Colors.cyan),
                      SizedBox(width: 8),
                      Text(
                        'Word-by-Word Visualization Demo',
                        style: TextStyle(
                          color: Colors.cyan,
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'This demo shows how the word-by-word visualization works. '
                    'What you see here is exactly what you would hear in the audio.',
                    style: TextStyle(color: Colors.white, fontSize: 14),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.orange.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: const Text(
                      'Key Point: The visual display matches the audio format exactly - [target word] ([Spanish equivalent])',
                      style: TextStyle(
                        color: Colors.orange,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 24),
            
            // Controls
            const Text(
              'Demo Controls',
              style: TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            
            Card(
              color: const Color(0xFF2C2C2E),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    SwitchListTile(
                      title: const Text(
                        'Show English Examples',
                        style: TextStyle(color: Colors.white),
                      ),
                      subtitle: const Text(
                        'Phrasal verbs like "wake up", "go out"',
                        style: TextStyle(color: Colors.grey),
                      ),
                      value: _showEnglishExample,
                      onChanged: (value) {
                        setState(() {
                          _showEnglishExample = value;
                        });
                      },
                      activeColor: Colors.blue,
                    ),
                    SwitchListTile(
                      title: const Text(
                        'Show German Examples',
                        style: TextStyle(color: Colors.white),
                      ),
                      subtitle: const Text(
                        'Separable verbs like "stehe auf", "gehe aus"',
                        style: TextStyle(color: Colors.grey),
                      ),
                      value: _showGermanExample,
                      onChanged: (value) {
                        setState(() {
                          _showGermanExample = value;
                        });
                      },
                      activeColor: Colors.amber,
                    ),
                    SwitchListTile(
                      title: const Text(
                        'Show Mixed Examples',
                        style: TextStyle(color: Colors.white),
                      ),
                      subtitle: const Text(
                        'Informal styles from both languages',
                        style: TextStyle(color: Colors.grey),
                      ),
                      value: _showMixedExample,
                      onChanged: (value) {
                        setState(() {
                          _showMixedExample = value;
                        });
                      },
                      activeColor: Colors.green,
                    ),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 24),
            
            // Examples Section
            const Text(
              'Example Scenarios',
              style: TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            
            // Example 1: English Phrasal Verbs
            if (_showEnglishExample) ...[
              _buildExampleCard(
                title: 'English Phrasal Verbs',
                description: 'When a user says "I want to wake up early and go out"',
                audioDescription: 'Audio says: [wake up] [despertar] [early] [temprano] [go out] [salir]',
                flag: '🇺🇸',
                color: Colors.blue,
              ),
              const SizedBox(height: 16),
            ],
            
            // Example 2: German Separable Verbs
            if (_showGermanExample) ...[
              _buildExampleCard(
                title: 'German Separable Verbs',
                description: 'When a user says "Ich stehe früh auf und gehe aus"',
                audioDescription: 'Audio says: [stehe auf] [me levanto] [früh] [temprano] [gehe aus] [salgo]',
                flag: '🇩🇪',
                color: Colors.amber,
              ),
              const SizedBox(height: 16),
            ],
            
            // Live Demo
            const Text(
              'Live Visualization Demo',
              style: TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            
            // The actual widget demo
            WordByWordVisualizationWidget(
              wordByWordData: _getCurrentData(),
              isVisible: true,
            ),
            
            const SizedBox(height: 24),
            
            // Technical Details
            _buildTechnicalDetails(),
            
            const SizedBox(height: 24),
            
            // Implementation Notes
            _buildImplementationNotes(),
          ],
        ),
      ),
    );
  }

  Widget _buildExampleCard({
    required String title,
    required String description,
    required String audioDescription,
    required String flag,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(flag, style: const TextStyle(fontSize: 24)),
              const SizedBox(width: 8),
              Text(
                title,
                style: TextStyle(
                  color: color,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            description,
            style: const TextStyle(color: Colors.white, fontSize: 14),
          ),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.black.withOpacity(0.3),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Row(
              children: [
                const Icon(Icons.volume_up, color: Colors.orange, size: 16),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    audioDescription,
                    style: const TextStyle(
                      color: Colors.orange,
                      fontSize: 12,
                      fontFamily: 'monospace',
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTechnicalDetails() {
    return ExpansionTile(
      title: const Text(
        'Technical Details',
        style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
      ),
      iconColor: Colors.cyan,
      collapsedIconColor: Colors.cyan,
      children: [
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: const Color(0xFF2C2C2E),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Data Structure',
                style: TextStyle(color: Colors.cyan, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.3),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: const Text(
                  '''Map<String, Map<String, String>> wordByWordData = {
  'english_colloquial_0_wake_up': {
    'source': 'wake up',
    'spanish': 'despertar',
    'language': 'english',
    'style': 'english_colloquial',
    'order': '0',
    'is_phrasal_verb': 'true',
    'display_format': '[wake up] ([despertar])'
  },
  // ... more entries
};''',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                    fontFamily: 'monospace',
                  ),
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                'Key Features',
                style: TextStyle(color: Colors.cyan, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              ...[
                '• Grouped by language and style',
                '• Maintains audio playback order',
                '• Identifies phrasal/separable verbs',
                '• Shows exact audio format',
                '• Supports multiple translation styles',
                '• Expandable/collapsible interface',
              ].map((feature) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text(
                  feature,
                  style: const TextStyle(color: Colors.white, fontSize: 14),
                ),
              )).toList(),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildImplementationNotes() {
    return ExpansionTile(
      title: const Text(
        'Implementation Notes',
        style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
      ),
      iconColor: Colors.orange,
      collapsedIconColor: Colors.orange,
      children: [
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: const Color(0xFF2C2C2E),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Requirements Implementation',
                style: TextStyle(color: Colors.orange, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              ...[
                '✅ Point 4.1: UI shows exactly what audio says',
                '✅ English phrasal verbs: [wake up] ([despertar])',
                '✅ German separable verbs: [stehe auf] ([me levanto])',
                '✅ Visual format matches audio format exactly',
                '✅ Grouped by language and style',
                '✅ Highlights phrasal/separable verbs',
                '✅ Maintains audio playback order',
                '✅ Shows format explanation to users',
              ].map((item) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text(
                  item,
                  style: const TextStyle(color: Colors.white, fontSize: 14),
                ),
              )).toList(),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.green.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: const Text(
                  'SUCCESS: What users see matches exactly what they hear!',
                  style: TextStyle(
                    color: Colors.green,
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}