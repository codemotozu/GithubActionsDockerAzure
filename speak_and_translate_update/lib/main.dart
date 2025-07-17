// lib/main.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:speak_and_translate_update/features/translation/presentation/providers/shared_provider.dart' show settingsProvider;
import 'features/translation/presentation/screens/prompt_screen.dart';
import 'features/translation/presentation/screens/settings_screen.dart';
import 'features/translation/presentation/screens/conversation_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    const ProviderScope(
      child: MyApp(),
    ),
  );
}
 
class MyApp extends ConsumerWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'AI Chat Assistant ',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      initialRoute: '/',
      routes: {
        '/': (context) => const PromptScreen(),
      },
      onGenerateRoute: (settings) {
        if (settings.name == '/conversation') {
          final prompt = settings.arguments as String;
          return MaterialPageRoute(
            builder: (context) => ConversationScreen(prompt: prompt),
          );
        } else if (settings.name == '/settings') {
          return MaterialPageRoute(
            builder: (context) {
              return Consumer(
                builder: (context, ref, child) {
                  final currentSettings = ref.read(settingsProvider);
                  return SettingsScreen(initialSettings: currentSettings);
                },
              );
            },
          );
        }
        return null;
      },
    );
  }
}