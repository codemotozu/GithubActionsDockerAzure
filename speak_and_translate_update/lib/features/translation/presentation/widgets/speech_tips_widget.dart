import 'package:flutter/material.dart';

class SpeechTipsWidget extends StatefulWidget {
  final bool isVisible;
  final VoidCallback? onDismiss;
  
  const SpeechTipsWidget({
    super.key,
    this.isVisible = true,
    this.onDismiss,
  });

  @override
  State<SpeechTipsWidget> createState() => _SpeechTipsWidgetState();
}

class _SpeechTipsWidgetState extends State<SpeechTipsWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;
  bool _isExpanded = false;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );
    
    if (widget.isVisible) {
      _animationController.forward();
    }
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.isVisible) return const SizedBox.shrink();

    return FadeTransition(
      opacity: _fadeAnimation,
      child: Container(
        margin: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF1E3A8A), Color(0xFF3B82F6)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.3),
              blurRadius: 8,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          children: [
            // Header
            InkWell(
              onTap: () {
                setState(() {
                  _isExpanded = !_isExpanded;
                });
              },
              borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    const Icon(
                      Icons.lightbulb_outline,
                      color: Colors.amber,
                      size: 24,
                    ),
                    const SizedBox(width: 12),
                    const Expanded(
                      child: Text(
                        'Speech Tips for Better Recognition',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    Icon(
                      _isExpanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                      color: Colors.white,
                    ),
                    const SizedBox(width: 8),
                    if (widget.onDismiss != null)
                      InkWell(
                        onTap: widget.onDismiss,
                        borderRadius: BorderRadius.circular(20),
                        child: const Padding(
                          padding: EdgeInsets.all(4),
                          child: Icon(
                            Icons.close,
                            color: Colors.white70,
                            size: 20,
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
            
            // Expandable Content
            AnimatedContainer(
              duration: const Duration(milliseconds: 300),
              height: _isExpanded ? null : 0,
              child: _isExpanded ? _buildTipsContent() : null,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTipsContent() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Divider(color: Colors.white30, height: 1),
          const SizedBox(height: 16),
          
          // Microphone Tips
          _buildTipSection(
            icon: Icons.mic,
            title: 'For Better Voice Recognition:',
            tips: [
              'Speak clearly and at a moderate pace',
              'Avoid speaking too fast - give the mic time to capture',
              'Don\'t pause mid-sentence - speak continuously',
              'Keep consistent volume throughout',
              'Minimize background noise',
            ],
          ),
          
          const SizedBox(height: 20),
          
          // Shadowing Tips
          _buildTipSection(
            icon: Icons.record_voice_over,
            title: 'Improve Pronunciation with "Shadowing":',
            tips: [
              'Listen to the app\'s pronunciation carefully',
              'Repeat immediately after the app speaks',
              'Try to match the rhythm and intonation',
              'Practice the same phrase multiple times',
              'Focus on difficult sounds and words',
            ],
          ),
          
          const SizedBox(height: 20),
          
          // Practice Mode Button
          Container(
            width: double.infinity,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.white30),
            ),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  const Icon(
                    Icons.school,
                    color: Colors.amber,
                    size: 20,
                  ),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text(
                      'Practice Mode: Enable word-by-word audio in settings for detailed pronunciation practice',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 13,
                        fontStyle: FontStyle.italic,
                      ),
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

  Widget _buildTipSection({
    required IconData icon,
    required String title,
    required List<String> tips,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: Colors.amber, size: 20),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                title,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        ...tips.map((tip) => Padding(
          padding: const EdgeInsets.only(left: 28, bottom: 4),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                '• ',
                style: TextStyle(color: Colors.white70, fontSize: 12),
              ),
              Expanded(
                child: Text(
                  tip,
                  style: const TextStyle(
                    color: Colors.white70,
                    fontSize: 12,
                    height: 1.3,
                  ),
                ),
              ),
            ],
          ),
        )),
      ],
    );
  }
}