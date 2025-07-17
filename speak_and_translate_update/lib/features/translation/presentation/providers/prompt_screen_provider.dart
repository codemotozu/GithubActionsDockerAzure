import 'package:flutter_riverpod/flutter_riverpod.dart';

final promptScreenProvider = StateNotifierProvider<PromptScreenNotifier, PromptScreenState>((ref) {
  return PromptScreenNotifier();
});

class PromptScreenState {
  final bool isListening;
  final String currentText;

  PromptScreenState({this.isListening = false, this.currentText = ''});
}

class PromptScreenNotifier extends StateNotifier<PromptScreenState> {
  PromptScreenNotifier() : super(PromptScreenState());

  void setListening(bool listening) {
    state = PromptScreenState(
      isListening: listening,
      currentText: state.currentText
    );
  }

  void updateText(String text) {
    state = PromptScreenState(
      isListening: state.isListening,
      currentText: text
    );
  }


   // Add the missing submitCommand method
 void submitCommand(String command) {
    // Implement your command submission logic here
    state = PromptScreenState(
      isListening: false,  // Typically stop listening after submission
      currentText: command
    );
 }
}
