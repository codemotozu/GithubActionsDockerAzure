// lib/main.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:speak_and_translate_update/features/translation/presentation/providers/shared_provider.dart' show settingsProvider, settingsInitializationProvider;
import 'features/translation/presentation/screens/prompt_screen.dart';
import 'features/translation/presentation/screens/settings_screen.dart';
import 'features/translation/presentation/screens/conversation_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  try {
    // Initialize Hive with Flutter support
    await Hive.initFlutter();
    
    // Open the settings box
    await Hive.openBox('settings');
    
    print("✅ Hive initialized successfully");
  } catch (e) {
    // Log and handle initialization errors
    print("❌ Error initializing Hive: $e");
  }
  
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
    // Initialize settings from Hive on app startup
    ref.watch(settingsInitializationProvider);
    
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
