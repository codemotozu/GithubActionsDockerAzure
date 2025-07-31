import 'package:flutter/material.dart';

class ShadowingPracticeWidget extends StatefulWidget {
  final String originalText;
  final String translatedText;
  final String targetLanguage;
  final VoidCallback? onPlayOriginal;
  final VoidCallback? onPlayTranslation;
  final VoidCallback? onStartRecording;
  final VoidCallback? onStopRecording;
  final bool isRecording;
  final bool isPlaying;
  
  const ShadowingPracticeWidget({
    super.key,
    required this.originalText,
    required this.translatedText,
    required this.targetLanguage,
    this.onPlayOriginal,
    this.onPlayTranslation,
    this.onStartRecording,
    this.onStopRecording,
    this.isRecording = false,
    this.isPlaying = false,
  });

  @override
  State<ShadowingPracticeWidget> createState() => _ShadowingPracticeWidgetState();
}

class _ShadowingPracticeWidgetState extends State<ShadowingPracticeWidget>
    with TickerProviderStateMixin {
  late AnimationController _pulseController;
  late AnimationController _waveController;
  late Animation<double> _pulseAnimation;
  late Animation<double> _waveAnimation;
  
  int _currentStep = 0;
  bool _showInstructions = true;

  final List<Map<String, dynamic>> _practiceSteps = [
    {
      'title': '1. Listen Carefully',
      'instruction': 'Play the audio and listen to the pronunciation',
      'icon': Icons.hearing,
      'color': Colors.blue,
    },
    {
      'title': '2. Shadow Speaking',
      'instruction': 'Repeat immediately after the audio, matching rhythm',
      'icon': Icons.record_voice_over,
      'color': Colors.green,
    },
    {
      'title': '3. Practice Recording',
      'instruction': 'Record yourself and compare with the original',
      'icon': Icons.mic,
      'color': Colors.orange,
    },
    {
      'title': '4. Perfect Your Accent',
      'instruction': 'Focus on difficult sounds and intonation patterns',
      'icon': Icons.tune,
      'color': Colors.purple,
    },
  ];

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );
    _waveController = AnimationController(
      duration: const Duration(milliseconds: 2000),
      vsync: this,
    );
    
    _pulseAnimation = Tween<double>(begin: 0.8, end: 1.2).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
    _waveAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _waveController, curve: Curves.easeInOut),
    );
    
    _pulseController.repeat(reverse: true);
    _waveController.repeat();
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _waveController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF2D1B69), Color(0xFF11998E)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 12,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        children: [
          // Header
          _buildHeader(),
          
          // Instructions Toggle
          if (_showInstructions) _buildInstructions(),
          
          // Text Display
          _buildTextDisplay(),
          
          // Control Buttons
          _buildControlButtons(),
          
          // Practice Steps
          _buildPracticeSteps(),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(
              Icons.school,
              color: Colors.white,
              size: 24,
            ),
          ),
          const SizedBox(width: 12),
          const Expanded(
            child: Text(
              'Shadowing Practice',
              style: TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          IconButton(
            onPressed: () {
              setState(() {
                _showInstructions = !_showInstructions;
              });
            },
            icon: Icon(
              _showInstructions ? Icons.visibility_off : Icons.help_outline,
              color: Colors.white70,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInstructions() {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 0, 16, 16),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.white30),
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'How to Practice Shadowing:',
            style: TextStyle(
              color: Colors.white,
              fontSize: 14,
              fontWeight: FontWeight.w600,
            ),
          ),
          SizedBox(height: 8),
          Text(
            '• Listen to the audio first\n'
            '• Start speaking immediately after you hear it\n'
            '• Try to match the speed and rhythm\n'
            '• Don\'t worry about understanding - focus on sounds\n'
            '• Repeat multiple times for better results',
            style: TextStyle(
              color: Colors.white70,
              fontSize: 12,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTextDisplay() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        children: [
          // Original Text
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.white30),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.text_fields, color: Colors.cyan, size: 16),
                    const SizedBox(width: 8),
                    Text(
                      'Original Text',
                      style: TextStyle(
                        color: Colors.cyan,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  widget.originalText,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
          
          const SizedBox(height: 12),
          
          // Translation
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.white30),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.translate, color: Colors.amber, size: 16),
                    const SizedBox(width: 8),
                    Text(
                      '${widget.targetLanguage} Translation',
                      style: const TextStyle(
                        color: Colors.amber,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  widget.translatedText,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildControlButtons() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          // Play Original
          Expanded(
            child: _buildControlButton(
              onPressed: widget.onPlayOriginal,
              icon: widget.isPlaying ? Icons.volume_up : Icons.play_arrow,
              label: 'Play Original',
              color: Colors.blue,
              isActive: widget.isPlaying,
            ),
          ),
          
          const SizedBox(width: 12),
          
          // Play Translation
          Expanded(
            child: _buildControlButton(
              onPressed: widget.onPlayTranslation,
              icon: Icons.translate,
              label: 'Play Translation',
              color: Colors.green,
            ),
          ),
          
          const SizedBox(width: 12),
          
          // Record Practice
          Expanded(
            child: _buildControlButton(
              onPressed: widget.isRecording ? widget.onStopRecording : widget.onStartRecording,
              icon: widget.isRecording ? Icons.stop : Icons.mic,
              label: widget.isRecording ? 'Stop' : 'Record',
              color: Colors.red,
              isActive: widget.isRecording,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildControlButton({
    required VoidCallback? onPressed,
    required IconData icon,
    required String label,
    required Color color,
    bool isActive = false,
  }) {
    return AnimatedBuilder(
      animation: isActive ? _pulseAnimation : const AlwaysStoppedAnimation(1.0),
      builder: (context, child) {
        return Transform.scale(
          scale: isActive ? _pulseAnimation.value : 1.0,
          child: ElevatedButton(
            onPressed: onPressed,
            style: ElevatedButton.styleFrom(
              backgroundColor: isActive ? color : color.withOpacity(0.3),
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 12),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
                side: BorderSide(
                  color: color,
                  width: isActive ? 2 : 1,
                ),
              ),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(icon, size: 20),
                const SizedBox(height: 4),
                Text(
                  label,
                  style: const TextStyle(fontSize: 10),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildPracticeSteps() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Practice Steps:',
            style: TextStyle(
              color: Colors.white,
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          ...List.generate(_practiceSteps.length, (index) {
            final step = _practiceSteps[index];
            final isActive = index == _currentStep;
            
            return GestureDetector(
              onTap: () {
                setState(() {
                  _currentStep = index;
                });
              },
              child: Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: isActive 
                      ? step['color'].withOpacity(0.2)
                      : Colors.white.withOpacity(0.05),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: isActive 
                        ? step['color']
                        : Colors.white30,
                    width: isActive ? 2 : 1,
                  ),
                ),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: step['color'].withOpacity(0.3),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Icon(
                        step['icon'],
                        color: step['color'],
                        size: 16,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            step['title'],
                            style: TextStyle(
                              color: isActive ? Colors.white : Colors.white70,
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            step['instruction'],
                            style: TextStyle(
                              color: isActive ? Colors.white70 : Colors.white54,
                              fontSize: 11,
                              height: 1.3,
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (isActive)
                      Icon(
                        Icons.play_arrow,
                        color: step['color'],
                        size: 20,
                      ),
                  ],
                ),
              ),
            );
          }),
        ],
      ),
    );
  }
}
