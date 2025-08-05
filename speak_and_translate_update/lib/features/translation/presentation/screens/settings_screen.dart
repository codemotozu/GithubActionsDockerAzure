import 'package:flutter/material.dart';
import 'package:speak_and_translate_update/features/translation/data/repositories/hive_user_settings_repository.dart';

enum MotherTongue {
  spanish,
  english,
  german,
  french,
  italian,
  portuguese,
  chinese,
  japanese,
  korean,
  arabic,
  russian,
  dutch,
  hindi,
  bengali,
}

enum AppMode {
  languageLearning,
  travelMode,
  fluencyPractice,  // NEW: Fluency practice mode
}

enum PracticeLanguage {
  english,
  german,
  french,
  italian,
  portuguese,
  chinese,
  japanese,
  korean,
}

enum CorrectionLevel {
  beginner,     // Focus on major errors only
  intermediate, // Grammar + pronunciation
  advanced,     // Detailed corrections including style
}

class SettingsScreen extends StatefulWidget {
  final Map<String, dynamic>? initialSettings;
  
  const SettingsScreen({super.key, this.initialSettings});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  MotherTongue _motherTongue = MotherTongue.english;
  AppMode _appMode = AppMode.languageLearning;
  
  // NEW: Fluency practice settings
  PracticeLanguage _practiceLanguage = PracticeLanguage.english;
  CorrectionLevel _correctionLevel = CorrectionLevel.intermediate;
  bool _pronunciationFeedback = true;
  bool _grammarCorrection = true;
  bool _vocabularyEnhancement = true;
  bool _realTimeCorrection = false; // Correct while speaking vs after
  
  // Word-by-word audio settings
  bool _germanWordByWord = true;
  bool _englishWordByWord = false;
  
  // German styles
  bool _germanNative = false;
  bool _germanColloquial = true;
  bool _germanInformal = false;
  bool _germanFormal = false;
  
  // English styles  
  bool _englishNative = false;
  bool _englishColloquial = true;
  bool _englishInformal = false;
  bool _englishFormal = false;

  // Expansion states
  bool _germanExpanded = false;
  bool _englishExpanded = false;
  bool _fluencyExpanded = false; // NEW: Fluency section expansion

  @override
  void initState() {
    super.initState();
    _loadInitialSettings();
  }

  void _loadInitialSettings() {
    if (widget.initialSettings != null) {
      final settings = widget.initialSettings!;
      
      // Load mother tongue
      final motherTongueString = settings['motherTongue'] as String?;
      _motherTongue = _getMotherTongueFromString(motherTongueString ?? 'english');
      
      // Load app mode
      final appModeString = settings['appMode'] as String?;
      if (appModeString == 'travelMode') {
        _appMode = AppMode.travelMode;
      } else if (appModeString == 'fluencyPractice') {
        _appMode = AppMode.fluencyPractice;
      } else {
        _appMode = AppMode.languageLearning;
      }
      
      // NEW: Load fluency practice settings
      final practiceLanguageString = settings['practiceLanguage'] as String?;
      _practiceLanguage = _getPracticeLanguageFromString(practiceLanguageString ?? 'english');
      
      final correctionLevelString = settings['correctionLevel'] as String?;
      _correctionLevel = _getCorrectionLevelFromString(correctionLevelString ?? 'intermediate');
      
      _pronunciationFeedback = settings['pronunciationFeedback'] as bool? ?? true;
      _grammarCorrection = settings['grammarCorrection'] as bool? ?? true;
      _vocabularyEnhancement = settings['vocabularyEnhancement'] as bool? ?? true;
      _realTimeCorrection = settings['realTimeCorrection'] as bool? ?? false;
      
      // Load word-by-word audio settings
      _germanWordByWord = settings['germanWordByWord'] as bool? ?? true;
      _englishWordByWord = settings['englishWordByWord'] as bool? ?? false;
      
      // Load translation style preferences
      _germanNative = settings['germanNative'] as bool? ?? false;
      _germanColloquial = settings['germanColloquial'] as bool? ?? true;
      _germanInformal = settings['germanInformal'] as bool? ?? false;
      _germanFormal = settings['germanFormal'] as bool? ?? false;
      _englishNative = settings['englishNative'] as bool? ?? false;
      _englishColloquial = settings['englishColloquial'] as bool? ?? true;
      _englishInformal = settings['englishInformal'] as bool? ?? false;
      _englishFormal = settings['englishFormal'] as bool? ?? false;
    }
  }

  MotherTongue _getMotherTongueFromString(String value) {
    switch (value) {
      case 'english': return MotherTongue.english;
      case 'german': return MotherTongue.german;
      case 'french': return MotherTongue.french;
      case 'italian': return MotherTongue.italian;
      case 'portuguese': return MotherTongue.portuguese;
      case 'chinese': return MotherTongue.chinese;
      case 'japanese': return MotherTongue.japanese;
      case 'korean': return MotherTongue.korean;
      case 'arabic': return MotherTongue.arabic;
      case 'russian': return MotherTongue.russian;
      case 'dutch': return MotherTongue.dutch;
      case 'hindi': return MotherTongue.hindi;
      case 'bengali': return MotherTongue.bengali;
      default: return MotherTongue.spanish;
    }
  }

  // NEW: Helper methods for fluency practice settings
  PracticeLanguage _getPracticeLanguageFromString(String value) {
    switch (value) {
      case 'english': return PracticeLanguage.english;
      case 'german': return PracticeLanguage.german;
      case 'french': return PracticeLanguage.french;
      case 'italian': return PracticeLanguage.italian;
      case 'portuguese': return PracticeLanguage.portuguese;
      case 'chinese': return PracticeLanguage.chinese;
      case 'japanese': return PracticeLanguage.japanese;
      case 'korean': return PracticeLanguage.korean;
      default: return PracticeLanguage.english;
    }
  }

  CorrectionLevel _getCorrectionLevelFromString(String value) {
    switch (value) {
      case 'beginner': return CorrectionLevel.beginner;
      case 'intermediate': return CorrectionLevel.intermediate;
      case 'advanced': return CorrectionLevel.advanced;
      default: return CorrectionLevel.intermediate;
    }
  }

  String _getLanguageName(MotherTongue language) {
    switch (language) {
      case MotherTongue.spanish: return 'Spanish';
      case MotherTongue.english: return 'English';
      case MotherTongue.german: return 'German';
      case MotherTongue.french: return 'French';
      case MotherTongue.italian: return 'Italian';
      case MotherTongue.portuguese: return 'Portuguese';
      case MotherTongue.chinese: return 'Chinese';
      case MotherTongue.japanese: return 'Japanese';
      case MotherTongue.korean: return 'Korean';
      case MotherTongue.arabic: return 'Arabic';
      case MotherTongue.russian: return 'Russian';
      case MotherTongue.dutch: return 'Dutch';
      case MotherTongue.hindi: return 'Hindi';
      case MotherTongue.bengali: return 'Bengali';
    }
  }

  String _getPracticeLanguageName(PracticeLanguage language) {
    switch (language) {
      case PracticeLanguage.english: return 'English';
      case PracticeLanguage.german: return 'German';
      case PracticeLanguage.french: return 'French';
      case PracticeLanguage.italian: return 'Italian';
      case PracticeLanguage.portuguese: return 'Portuguese';
      case PracticeLanguage.chinese: return 'Chinese';
      case PracticeLanguage.japanese: return 'Japanese';
      case PracticeLanguage.korean: return 'Korean';
    }
  }

  String _getCorrectionLevelName(CorrectionLevel level) {
    switch (level) {
      case CorrectionLevel.beginner: return 'Beginner (Basic Errors)';
      case CorrectionLevel.intermediate: return 'Intermediate (Grammar + Pronunciation)';
      case CorrectionLevel.advanced: return 'Advanced (Detailed + Style)';
    }
  }

  String _getMotherTongueString(MotherTongue tongue) {
    return tongue.toString().split('.').last;
  }

  String _getAppModeString(AppMode mode) {
    switch (mode) {
      case AppMode.languageLearning: return 'languageLearning';
      case AppMode.travelMode: return 'travelMode';
      case AppMode.fluencyPractice: return 'fluencyPractice';
    }
  }

  String _getPracticeLanguageString(PracticeLanguage language) {
    return language.toString().split('.').last;
  }

  String _getCorrectionLevelString(CorrectionLevel level) {
    return level.toString().split('.').last;
  }

  // Helper methods to check if any styles are selected for each language
  bool get _isGermanSelected {
    return _germanNative || _germanColloquial || _germanInformal || _germanFormal;
  }

  bool get _isEnglishSelected {
    return _englishNative || _englishColloquial || _englishInformal || _englishFormal;
  }

  void _handleSave() async {
    final updatedSettings = {
      // Always set to continuous listening since it's the only option now
      'microphoneMode': 'continuousListening',
      'motherTongue': _getMotherTongueString(_motherTongue),
      'appMode': _getAppModeString(_appMode),
      
      // NEW: Fluency practice settings
      'practiceLanguage': _getPracticeLanguageString(_practiceLanguage),
      'correctionLevel': _getCorrectionLevelString(_correctionLevel),
      'pronunciationFeedback': _pronunciationFeedback,
      'grammarCorrection': _grammarCorrection,
      'vocabularyEnhancement': _vocabularyEnhancement,
      'realTimeCorrection': _realTimeCorrection,
      
      // Word-by-word audio settings
      'germanWordByWord': _germanWordByWord,
      'englishWordByWord': _englishWordByWord,
      
      // Translation style preferences
      'germanNative': _germanNative,
      'germanColloquial': _germanColloquial,
      'germanInformal': _germanInformal,
      'germanFormal': _germanFormal,
      'englishNative': _englishNative,
      'englishColloquial': _englishColloquial,
      'englishInformal': _englishInformal,
      'englishFormal': _englishFormal,
    };

    try {
      // Show loading indicator
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (BuildContext context) {
          return const Center(
            child: CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(Colors.cyan),
            ),
          );
        },
      );

      // Save settings to Hive
      final repository = UserSettingsRepository();
      await repository.saveUserSettings(updatedSettings);
      
      // Close loading dialog
      Navigator.of(context).pop();
      
      // Show success message
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("✅ Settings saved successfully!"),
          backgroundColor: Colors.green,
          duration: Duration(seconds: 2),
        ),
      );
      
      // Return to previous screen with updated settings
      Navigator.pop(context, updatedSettings);
      
    } catch (e) {
      // Close loading dialog if it's open
      Navigator.of(context).pop();
      
      // Handle error: show error message
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("❌ Error saving settings: $e"),
          backgroundColor: Colors.red,
          duration: const Duration(seconds: 3),
        ),
      );
      
      // Still return the settings even if saving failed (for immediate UI update)
      Navigator.pop(context, updatedSettings);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        iconTheme: const IconThemeData(color: Colors.white),
        backgroundColor: Colors.black,
        title: const Text('Settings', style: TextStyle(color: Colors.cyan)),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Microphone Mode Information (no longer selectable)
              const Text('Microphone Mode', style: TextStyle(color: Colors.cyan, fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF1B4D3E),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: const Color(0xFF4CAF50), width: 1),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.mic, color: Colors.green, size: 24),
                    const SizedBox(width: 12),
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Continuous Listening', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600)),
                          SizedBox(height: 4),
                          Text('Microphone is always active and automatically sends when you speak', style: TextStyle(color: Colors.grey, fontSize: 14)),
                        ],
                      ),
                    ),
                    const Icon(Icons.check_circle, color: Colors.green, size: 24),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // Mother Tongue Section
              const Text('Mother Tongue', style: TextStyle(color: Colors.cyan, fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFF2C2C2E),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: const Color(0xFF3A3A3C), width: 0.5),
                ),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<MotherTongue>(
                    value: _motherTongue,
                    isExpanded: true,
                    dropdownColor: const Color(0xFF2C2C2E),
                    style: const TextStyle(color: Colors.white, fontSize: 16),
                    onChanged: (MotherTongue? newValue) {
                      if (newValue != null) {
                        setState(() {
                          _motherTongue = newValue;
                        });
                      }
                    },
                    items: MotherTongue.values.map<DropdownMenuItem<MotherTongue>>((MotherTongue value) {
                      return DropdownMenuItem<MotherTongue>(
                        value: value,
                        child: Text(_getLanguageName(value), style: const TextStyle(color: Colors.white)),
                      );
                    }).toList(),
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // App Mode Section
              const Text('App Mode', style: TextStyle(color: Colors.cyan, fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Column(
                children: [
                  ListTile(
                    title: const Text('Language Learning', style: TextStyle(color: Colors.white, fontSize: 16)),
                    subtitle: const Text('Learn German and English with multiple styles', style: TextStyle(color: Colors.grey, fontSize: 14)),
                    trailing: Radio<AppMode>(
                      value: AppMode.languageLearning,
                      groupValue: _appMode,
                      onChanged: (AppMode? value) {
                        if (value != null) {
                          setState(() => _appMode = value);
                        }
                      },
                      fillColor: MaterialStateProperty.resolveWith((states) => states.contains(MaterialState.selected) ? Colors.cyan : Colors.grey),
                    ),
                  ),
                  ListTile(
                    title: const Text('Travel Mode', style: TextStyle(color: Colors.white, fontSize: 16)),
                    subtitle: const Text('Auto-detect foreign languages and translate to your mother tongue', style: TextStyle(color: Colors.grey, fontSize: 14)),
                    trailing: Radio<AppMode>(
                      value: AppMode.travelMode,
                      groupValue: _appMode,
                      onChanged: (AppMode? value) {
                        if (value != null) {
                          setState(() => _appMode = value);
                        }
                      },
                      fillColor: MaterialStateProperty.resolveWith((states) => states.contains(MaterialState.selected) ? Colors.cyan : Colors.grey),
                    ),
                  ),
                  // NEW: Fluency Practice Mode
                  ListTile(
                    title: const Text('Fluency Practice', style: TextStyle(color: Colors.white, fontSize: 16)),
                    subtitle: const Text('Practice speaking and get grammar/pronunciation corrections', style: TextStyle(color: Colors.grey, fontSize: 14)),
                    trailing: Radio<AppMode>(
                      value: AppMode.fluencyPractice,
                      groupValue: _appMode,
                      onChanged: (AppMode? value) {
                        if (value != null) {
                          setState(() => _appMode = value);
                        }
                      },
                      fillColor: MaterialStateProperty.resolveWith((states) => states.contains(MaterialState.selected) ? Colors.cyan : Colors.grey),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // NEW: Fluency Practice Settings
              if (_appMode == AppMode.fluencyPractice) ...[
                const Text('Fluency Practice Settings', style: TextStyle(color: Colors.cyan, fontSize: 16, fontWeight: FontWeight.bold)),
                const SizedBox(height: 16),
                
                Container(
                  decoration: BoxDecoration(
                    color: const Color(0xFF1B3A4D),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.orange, width: 1),
                  ),
                  child: Column(
                    children: [
                      InkWell(
                        onTap: () {
                          setState(() {
                            _fluencyExpanded = !_fluencyExpanded;
                          });
                        },
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              const Text('Practice Configuration', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w500)),
                              Icon(_fluencyExpanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down, color: Colors.white),
                            ],
                          ),
                        ),
                      ),
                      if (_fluencyExpanded) ...[
                        const Divider(color: Color(0xFF3A3A3C), height: 1, thickness: 0.5),
                        Padding(
                          padding: const EdgeInsets.all(16.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              // Practice Language Selection
                              const Text('Target Language', style: TextStyle(color: Colors.orange, fontSize: 15, fontWeight: FontWeight.w600)),
                              const SizedBox(height: 8),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                                decoration: BoxDecoration(
                                  color: const Color(0xFF2C2C2E),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: DropdownButtonHideUnderline(
                                  child: DropdownButton<PracticeLanguage>(
                                    value: _practiceLanguage,
                                    isExpanded: true,
                                    dropdownColor: const Color(0xFF2C2C2E),
                                    style: const TextStyle(color: Colors.white, fontSize: 14),
                                    onChanged: (PracticeLanguage? newValue) {
                                      if (newValue != null) {
                                        setState(() {
                                          _practiceLanguage = newValue;
                                        });
                                      }
                                    },
                                    items: PracticeLanguage.values.map<DropdownMenuItem<PracticeLanguage>>((PracticeLanguage value) {
                                      return DropdownMenuItem<PracticeLanguage>(
                                        value: value,
                                        child: Text(_getPracticeLanguageName(value), style: const TextStyle(color: Colors.white)),
                                      );
                                    }).toList(),
                                  ),
                                ),
                              ),
                              const SizedBox(height: 16),
                              
                              // Correction Level
                              const Text('Correction Level', style: TextStyle(color: Colors.orange, fontSize: 15, fontWeight: FontWeight.w600)),
                              const SizedBox(height: 8),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                                decoration: BoxDecoration(
                                  color: const Color(0xFF2C2C2E),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: DropdownButtonHideUnderline(
                                  child: DropdownButton<CorrectionLevel>(
                                    value: _correctionLevel,
                                    isExpanded: true,
                                    dropdownColor: const Color(0xFF2C2C2E),
                                    style: const TextStyle(color: Colors.white, fontSize: 14),
                                    onChanged: (CorrectionLevel? newValue) {
                                      if (newValue != null) {
                                        setState(() {
                                          _correctionLevel = newValue;
                                        });
                                      }
                                    },
                                    items: CorrectionLevel.values.map<DropdownMenuItem<CorrectionLevel>>((CorrectionLevel value) {
                                      return DropdownMenuItem<CorrectionLevel>(
                                        value: value,
                                        child: Text(_getCorrectionLevelName(value), style: const TextStyle(color: Colors.white)),
                                      );
                                    }).toList(),
                                  ),
                                ),
                              ),
                              const SizedBox(height: 16),
                              
                              // Correction Features
                              const Text('Correction Features', style: TextStyle(color: Colors.orange, fontSize: 15, fontWeight: FontWeight.w600)),
                              const SizedBox(height: 8),
                              
                              // Pronunciation Feedback
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  const Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text('Pronunciation Feedback', style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w500)),
                                        SizedBox(height: 2),
                                        Text('Analyze and correct pronunciation', style: TextStyle(color: Colors.grey, fontSize: 12)),
                                      ],
                                    ),
                                  ),
                                  Switch(
                                    value: _pronunciationFeedback,
                                    onChanged: (value) {
                                      setState(() => _pronunciationFeedback = value);
                                    },
                                    activeColor: Colors.orange,
                                  ),
                                ],
                              ),
                              
                              // Grammar Correction
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  const Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text('Grammar Correction', style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w500)),
                                        SizedBox(height: 2),
                                        Text('Fix grammar mistakes and structure', style: TextStyle(color: Colors.grey, fontSize: 12)),
                                      ],
                                    ),
                                  ),
                                  Switch(
                                    value: _grammarCorrection,
                                    onChanged: (value) {
                                      setState(() => _grammarCorrection = value);
                                    },
                                    activeColor: Colors.orange,
                                  ),
                                ],
                              ),
                              
                              // Vocabulary Enhancement
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  const Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text('Vocabulary Enhancement', style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w500)),
                                        SizedBox(height: 2),
                                        Text('Suggest better word choices', style: TextStyle(color: Colors.grey, fontSize: 12)),
                                      ],
                                    ),
                                  ),
                                  Switch(
                                    value: _vocabularyEnhancement,
                                    onChanged: (value) {
                                      setState(() => _vocabularyEnhancement = value);
                                    },
                                    activeColor: Colors.orange,
                                  ),
                                ],
                              ),
                              
                              // Real-time Correction
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  const Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text('Real-time Correction', style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w500)),
                                        SizedBox(height: 2),
                                        Text('Interrupt for immediate corrections', style: TextStyle(color: Colors.grey, fontSize: 12)),
                                      ],
                                    ),
                                  ),
                                  Switch(
                                    value: _realTimeCorrection,
                                    onChanged: (value) {
                                      setState(() => _realTimeCorrection = value);
                                    },
                                    activeColor: Colors.orange,
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 24),
              ],

              // Translation Styles Section (only show in Language Learning mode)
              if (_appMode == AppMode.languageLearning) ...[
                const Text('Translation Styles', style: TextStyle(color: Colors.cyan, fontSize: 16, fontWeight: FontWeight.bold)),
                const SizedBox(height: 16),
                
                // German Expandable Section
                Container(
                  decoration: BoxDecoration(
                    color: _isGermanSelected ? const Color(0xFF1B4D3E) : const Color(0xFF2C2C2E),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: _isGermanSelected ? const Color(0xFF4CAF50) : const Color(0xFF3A3A3C), width: _isGermanSelected ? 1.0 : 0.5),
                  ),
                  child: Column(
                    children: [
                      InkWell(
                        onTap: () {
                          setState(() {
                            _germanExpanded = !_germanExpanded;
                          });
                        },
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              const Text('German', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w500)),
                              Icon(_germanExpanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down, color: Colors.white),
                            ],
                          ),
                        ),
                      ),
                      if (_germanExpanded) ...[
                        const Divider(color: Color(0xFF3A3A3C), height: 1, thickness: 0.5),
                        Padding(
                          padding: const EdgeInsets.all(8.0),
                          child: Column(
                            children: [
                              // German Word-by-Word Audio Toggle
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  const Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text('Word-by-Word Audio', style: TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w500)),
                                        SizedBox(height: 2),
                                        Text('Play detailed pronunciation breakdown', style: TextStyle(color: Colors.grey, fontSize: 13)),
                                      ],
                                    ),
                                  ),
                                  Switch(
                                    value: _germanWordByWord,
                                    onChanged: (value) {
                                      setState(() => _germanWordByWord = value);
                                    },
                                    activeColor: Colors.cyan,
                                  ),
                                ],
                              ),
                              const SizedBox(height: 12),
                              const Divider(color: Color(0xFF3A3A3C), height: 1, thickness: 0.5),
                              const SizedBox(height: 8),
                              Row(
                                children: [
                                  Expanded(
                                    child: CheckboxListTile(
                                      title: const Text('Native', style: TextStyle(color: Colors.white, fontSize: 14)),
                                      value: _germanNative,
                                      onChanged: (bool? value) {
                                        setState(() {
                                          _germanNative = value ?? false;
                                        });
                                      },
                                      activeColor: Colors.cyan,
                                      contentPadding: EdgeInsets.zero,
                                      dense: true,
                                    ),
                                  ),
                                  Expanded(
                                    child: CheckboxListTile(
                                      title: const Text('Colloquial', style: TextStyle(color: Colors.white, fontSize: 14)),
                                      value: _germanColloquial,
                                      onChanged: (bool? value) {
                                        setState(() {
                                          _germanColloquial = value ?? false;
                                        });
                                      },
                                      activeColor: Colors.cyan,
                                      contentPadding: EdgeInsets.zero,
                                      dense: true,
                                    ),
                                  ),
                                ],
                              ),
                              Row(
                                children: [
                                  Expanded(
                                    child: CheckboxListTile(
                                      title: const Text('Informal', style: TextStyle(color: Colors.white, fontSize: 14)),
                                      value: _germanInformal,
                                      onChanged: (bool? value) {
                                        setState(() {
                                          _germanInformal = value ?? false;
                                        });
                                      },
                                      activeColor: Colors.cyan,
                                      contentPadding: EdgeInsets.zero,
                                      dense: true,
                                    ),
                                  ),
                                  Expanded(
                                    child: CheckboxListTile(
                                      title: const Text('Formal', style: TextStyle(color: Colors.white, fontSize: 14)),
                                      value: _germanFormal,
                                      onChanged: (bool? value) {
                                        setState(() {
                                          _germanFormal = value ?? false;
                                        });
                                      },
                                      activeColor: Colors.cyan,
                                      contentPadding: EdgeInsets.zero,
                                      dense: true,
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                
                const SizedBox(height: 12),
                
                // English Expandable Section
                Container(
                  decoration: BoxDecoration(
                    color: _isEnglishSelected ? const Color(0xFF1B4D3E) : const Color(0xFF2C2C2E),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: _isEnglishSelected ? const Color(0xFF4CAF50) : const Color(0xFF3A3A3C), width: _isEnglishSelected ? 1.0 : 0.5),
                  ),
                  child: Column(
                    children: [
                      InkWell(
                        onTap: () {
                          setState(() {
                            _englishExpanded = !_englishExpanded;
                          });
                        },
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              const Text('English', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w500)),
                              Icon(_englishExpanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down, color: Colors.white),
                            ],
                          ),
                        ),
                      ),
                      if (_englishExpanded) ...[
                        const Divider(color: Color(0xFF3A3A3C), height: 1, thickness: 0.5),
                        Padding(
                          padding: const EdgeInsets.all(8.0),
                          child: Column(
                            children: [
                              // English Word-by-Word Audio Toggle
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  const Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text('Word-by-Word Audio', style: TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w500)),
                                        SizedBox(height: 2),
                                        Text('Play detailed pronunciation breakdown', style: TextStyle(color: Colors.grey, fontSize: 13)),
                                      ],
                                    ),
                                  ),
                                  Switch(
                                    value: _englishWordByWord,
                                    onChanged: (value) {
                                      setState(() => _englishWordByWord = value);
                                    },
                                    activeColor: Colors.cyan,
                                  ),
                                ],
                              ),
                              const SizedBox(height: 12),
                              const Divider(color: Color(0xFF3A3A3C), height: 1, thickness: 0.5),
                              const SizedBox(height: 8),
                              Row(
                                children: [
                                  Expanded(
                                    child: CheckboxListTile(
                                      title: const Text('Native', style: TextStyle(color: Colors.white, fontSize: 14)),
                                      value: _englishNative,
                                      onChanged: (bool? value) {
                                        setState(() {
                                          _englishNative = value ?? false;
                                        });
                                      },
                                      activeColor: Colors.cyan,
                                      contentPadding: EdgeInsets.zero,
                                      dense: true,
                                    ),
                                  ),
                                  Expanded(
                                    child: CheckboxListTile(
                                      title: const Text('Colloquial', style: TextStyle(color: Colors.white, fontSize: 14)),
                                      value: _englishColloquial,
                                      onChanged: (bool? value) {
                                        setState(() {
                                          _englishColloquial = value ?? false;
                                        });
                                      },
                                      activeColor: Colors.cyan,
                                      contentPadding: EdgeInsets.zero,
                                      dense: true,
                                    ),
                                  ),
                                ],
                              ),
                              Row(
                                children: [
                                  Expanded(
                                    child: CheckboxListTile(
                                      title: const Text('Informal', style: TextStyle(color: Colors.white, fontSize: 14)),
                                      value: _englishInformal,
                                      onChanged: (bool? value) {
                                        setState(() {
                                          _englishInformal = value ?? false;
                                        });
                                      },
                                      activeColor: Colors.cyan,
                                      contentPadding: EdgeInsets.zero,
                                      dense: true,
                                    ),
                                  ),
                                  Expanded(
                                    child: CheckboxListTile(
                                      title: const Text('Formal', style: TextStyle(color: Colors.white, fontSize: 14)),
                                      value: _englishFormal,
                                      onChanged: (bool? value) {
                                        setState(() {
                                          _englishFormal = value ?? false;
                                        });
                                      },
                                      activeColor: Colors.cyan,
                                      contentPadding: EdgeInsets.zero,
                                      dense: true,
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 24),
              ],
              
              // Save Button
              const SizedBox(height: 40),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _handleSave,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                  child: const Text('SAVE', style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
                ),
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }
}