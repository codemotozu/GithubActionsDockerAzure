// chat_message_model.dart
import '../../domain/entities/translation.dart';

enum MessageType { user, ai }

class ChatMessage {
  final MessageType type;
  final String text;
  final Translation? translation;
  final bool isLoading;
  final String? error;

  ChatMessage.user(this.text)
      : type = MessageType.user,
        translation = null,
        isLoading = false,
        error = null;

  ChatMessage.ai({required Translation translation})
      : type = MessageType.ai,
        text = translation.translatedText,  // translation is guaranteed here
        translation = translation,
        isLoading = false,
        error = null;

  ChatMessage.aiLoading()
      : type = MessageType.ai,
        text = '',
        translation = null,
        isLoading = true,
        error = null;

  ChatMessage.aiError(this.error)
      : type = MessageType.ai,
        text = error ?? 'An error occurred',
        translation = null,
        isLoading = false;
}