// lib/features/translation/presentation/widgets/voice_command_status_indicator.dart
import 'package:flutter/material.dart';

const _statusKey = Key('voiceStatusIndicator');

class VoiceCommandStatusIndicator extends StatelessWidget {
  final bool isListening;

  const VoiceCommandStatusIndicator({
    super.key,
    required this.isListening,
  });

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      key: _statusKey,
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
      height: isListening ? 40 : 0,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.7),
        borderRadius: BorderRadius.circular(20),
      ),
      child: AnimatedOpacity(
        opacity: isListening ? 1 : 0,
        duration: const Duration(milliseconds: 200),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.mic, color: Colors.red, size: 20),
            const SizedBox(width: 8),
            Text(
              'Escuchando...',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.w500,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}
