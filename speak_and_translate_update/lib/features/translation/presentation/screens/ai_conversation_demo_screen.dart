// ai_conversation_demo_screen.dart - Demo screen showcasing the new AI conversation UI

import 'package:flutter/material.dart';
import '../widgets/enhanced_word_by_word_widget.dart';
import '../widgets/ai_conversation_widget.dart';

class AIConversationDemoScreen extends StatefulWidget {
  const AIConversationDemoScreen({super.key});

  @override
  State<AIConversationDemoScreen> createState() => _AIConversationDemoScreenState();
}

class _AIConversationDemoScreenState extends State<AIConversationDemoScreen> {
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F1419),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1F2937),
        elevation: 0,
        title: const Text(
          'AI Translation Assistant',
          style: TextStyle(
            color: Colors.white,
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 16),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF10B981), Color(0xFF059669)],
              ),
              borderRadius: BorderRadius.circular(15),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.psychology_alt, size: 16, color: Colors.white),
                SizedBox(width: 4),
                Text(
                  'AI ACTIVE',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // User message
            _buildUserMessage("Ich esse jetzt viel mehr"),
            
            const SizedBox(height: 20),
            
            // AI Response with Enhanced Word-by-Word UI
            EnhancedWordByWordWidget(
              translationData: _getSampleTranslationData(),
              showConfidenceRatings: true,
              onWordTap: (word) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('Playing audio for: $word'),
                    backgroundColor: const Color(0xFF6366F1),
                    behavior: SnackBarBehavior.floating,
                  ),
                );
              },
            ),
            
            const SizedBox(height: 40),
            
            // Section divider
            Container(
              width: double.infinity,
              height: 1,
              margin: const EdgeInsets.symmetric(vertical: 20),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    Colors.transparent,
                    Colors.grey[700]!,
                    Colors.transparent,
                  ],
                ),
              ),
            ),
            
            // Alternative UI Style
            const Text(
              'Alternative Conversation Style',
              style: TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            
            const SizedBox(height: 16),
            
            // AI Conversation Widget (alternative style)
            AIConversationWidget(
              translationData: _getSampleTranslationData(),
              onWordSelected: (word) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('Word selected: $word'),
                    backgroundColor: const Color(0xFFEF4444),
                    behavior: SnackBarBehavior.floating,
                  ),
                );
              },
              onPlayAll: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Playing all translations...'),
                    backgroundColor: Color(0xFF10B981),
                    behavior: SnackBarBehavior.floating,
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildUserMessage(String message) {
    return Container(
      margin: const EdgeInsets.only(left: 50),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF3B82F6), Color(0xFF1D4ED8)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF3B82F6).withOpacity(0.3),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Text(
                message,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          // User Avatar
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF3B82F6), Color(0xFF1D4ED8)],
              ),
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Icon(
              Icons.person,
              color: Colors.white,
              size: 24,
            ),
          ),
        ],
      ),
    );
  }

  Map<String, dynamic> _getSampleTranslationData() {
    return {
      'style_data': [
        {
          'style': 'german_native',
          'translation': 'Ich esse jetzt viel mehr.',
          'word_pairs': [
            ['Ich', 'Yo', '1.00'],
            ['esse', 'como', '0.95'],
            ['jetzt', 'ahora', '0.98'],
            ['viel', 'mucho', '0.92'],
            ['mehr', 'más', '0.96'],
          ],
        },
        {
          'style': 'german_formal',
          'translation': 'Ich konsumiere nun eine deutlich größere Menge an Nahrung.',
          'word_pairs': [
            ['Ich', 'Yo', '1.00'],
            ['konsumiere', 'consumo', '0.88'],
            ['nun', 'ahora', '0.94'],
            ['eine', 'una', '0.97'],
            ['deutlich', 'claramente', '0.85'],
            ['größere', 'mayor', '0.91'],
            ['Menge', 'cantidad', '0.89'],
            ['an', 'de', '0.93'],
            ['Nahrung', 'comida', '0.87'],
          ],
        },
        {
          'style': 'english_native',
          'translation': "I'm eating a lot more now.",
          'word_pairs': [
            ['I', 'yo', '1.00'],
            ['am', 'estoy', '0.96'],
            ['eating', 'comiendo', '0.98'],
            ['a lot', 'mucho', '0.94'],
            ['more', 'más', '0.97'],
            ['now', 'ahora', '0.99'],
          ],
        },
        {
          'style': 'english_formal',
          'translation': 'I am consuming a significantly larger quantity of food at present.',
          'word_pairs': [
            ['I', 'yo', '1.00'],
            ['am', 'estoy', '0.96'],
            ['consuming', 'consumiendo', '0.87'],
            ['a', 'una', '0.98'],
            ['significantly', 'significativamente', '0.83'],
            ['larger', 'mayor', '0.91'],
            ['quantity', 'cantidad', '0.89'],
            ['of', 'de', '0.95'],
            ['food', 'comida', '0.94'],
            ['at present', 'actualmente', '0.86'],
          ],
        },
      ],
      'original_text': 'Ich esse jetzt viel mehr',
      'audio_filename': 'sample_audio.mp3',
    };
  }
}