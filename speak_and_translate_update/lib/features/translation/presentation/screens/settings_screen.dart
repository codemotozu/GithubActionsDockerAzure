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
  fluencyPractice,
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
  beginner,
  intermediate,
  advanced,
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
  
  // Fluency practice settings
  PracticeLanguage _practiceLanguage = PracticeLanguage.english;
  CorrectionLevel _correctionLevel = CorrectionLevel.intermediate;
  bool _pronunciationFeedback = true;
  bool _grammarCorrection = true;
  bool _vocabularyEnhancement = true;
  bool _realTimeCorrection = false;
  
  // Word-by-word audio settings - User has complete freedom
  bool _germanWordByWord = false;
  bool _englishWordByWord = false;
  
  // German styles - User has complete freedom
  bool _germanNative = false;
  bool _germanColloquial = false;
  bool _germanInformal = false;
  bool _germanFormal = false;
  
  // English styles - User has complete freedom
  bool _englishNative = false;
  bool _englishColloquial = false;
  bool _englishInformal = false;
  bool _englishFormal = false;

  // Expansion states
  bool _germanExpanded = false;
  bool _englishExpanded = false;
  bool _fluencyExpanded = false;

  @override
  void initState() {
    super.initState();
    _loadInitialSettings();
    
    // DEBUGGER POINT 1: Log initial settings load
    _debugLog('initState', 'Loading initial settings');
  }

  void _loadInitialSettings() {
    if (widget.initialSettings != null) {
      final settings = widget.initialSettings!;
      
      // DEBUGGER POINT 2: Log settings being loaded
      _debugLog('_loadInitialSettings', 'Settings from parent: $settings');
      
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
      
      // Load fluency practice settings
      final practiceLanguageString = settings['practiceLanguage'] as String?;
      _practiceLanguage = _getPracticeLanguageFromString(practiceLanguageString ?? 'english');
      
      final correctionLevelString = settings['correctionLevel'] as String?;
      _correctionLevel = _getCorrectionLevelFromString(correctionLevelString ?? 'intermediate');
      
      _pronunciationFeedback = settings['pronunciationFeedback'] as bool? ?? true;
      _grammarCorrection = settings['grammarCorrection'] as bool? ?? true;
      _vocabularyEnhancement = settings['vocabularyEnhancement'] as bool? ?? true;
      _realTimeCorrection = settings['realTimeCorrection'] as bool? ?? false;
      
      // Load word-by-word audio settings - NO DEFAULTS FORCED
      _germanWordByWord = settings['germanWordByWord'] as bool? ?? false;
      _englishWordByWord = settings['englishWordByWord'] as bool? ?? false;
      
      // Load translation style preferences - NO DEFAULTS FORCED
      _germanNative = settings['germanNative'] as bool? ?? false;
      _germanColloquial = settings['germanColloquial'] as bool? ?? false;
      _germanInformal = settings['germanInformal'] as bool? ?? false;
      _germanFormal = settings['germanFormal'] as bool? ?? false;
      _englishNative = settings['englishNative'] as bool? ?? false;
      _englishColloquial = settings['englishColloquial'] as bool? ?? false;
      _englishInformal = settings['englishInformal'] as bool? ?? false;
      _englishFormal = settings['englishFormal'] as bool? ?? false;
      
      // DEBUGGER POINT 3: Log loaded state
      _debugLogCurrentState('After loading settings');
    }
  }

  // Debug helper methods
  void _debugLog(String method, String message) {
    debugPrint('\n🔍 [$method] $message');
  }

  void _debugLogCurrentState(String context) {
    debugPrint('\n' + '='*60);
    debugPrint('📋 SETTINGS STATE: $context');
    debugPrint('='*60);
    debugPrint('🇩🇪 German Settings:');
    debugPrint('  Native: $_germanNative');
    debugPrint('  Colloquial: $_germanColloquial');
    debugPrint('  Informal: $_germanInformal');
    debugPrint('  Formal: $_germanFormal');
    debugPrint('  Word-by-Word: $_germanWordByWord');
    debugPrint('🇺🇸 English Settings:');
    debugPrint('  Native: $_englishNative');
    debugPrint('  Colloquial: $_englishColloquial');
    debugPrint('  Informal: $_englishInformal');
    debugPrint('  Formal: $_englishFormal');
    debugPrint('  Word-by-Word: $_englishWordByWord');
    debugPrint('='*60 + '\n');
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

  bool get _isAnyStyleSelected {
    return _isGermanSelected || _isEnglishSelected;
  }

  // Build current selection summary widget
  Widget _buildSelectionSummary() {
    final selectedStyles = <String>[];
    final audioFeatures = <String>[];
    
    // Collect German styles
    if (_germanNative) selectedStyles.add('German Native');
    if (_germanColloquial) selectedStyles.add('German Colloquial');
    if (_germanInformal) selectedStyles.add('German Informal');
    if (_germanFormal) selectedStyles.add('German Formal');
    
    // Collect English styles
    if (_englishNative) selectedStyles.add('English Native');
    if (_englishColloquial) selectedStyles.add('English Colloquial');
    if (_englishInformal) selectedStyles.add('English Informal');
    if (_englishFormal) selectedStyles.add('English Formal');
    
    // Collect audio features
    if (_germanWordByWord) audioFeatures.add('German Word-by-Word');
    if (_englishWordByWord) audioFeatures.add('English Word-by-Word');
    
    return Container(
      padding: const EdgeInsets.all(12),
      margin: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _isAnyStyleSelected 
            ? Colors.green[900]!.withOpacity(0.3)
            : Colors.orange[900]!.withOpacity(0.3),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: _isAnyStyleSelected ? Colors.green : Colors.orange,
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                _isAnyStyleSelected ? Icons.check_circle : Icons.warning,
                color: _isAnyStyleSelected ? Colors.green : Colors.orange,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  _isAnyStyleSelected 
                      ? 'Your Selected Styles:'
                      : 'No styles selected - Please select at least one',
                  style: TextStyle(
                    color: _isAnyStyleSelected ? Colors.green : Colors.orange,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          if (_isAnyStyleSelected) ...[
            const SizedBox(height: 8),
            if (selectedStyles.isNotEmpty)
              Text(
                selectedStyles.join(', '),
                style: const TextStyle(color: Colors.white70),
              ),
            if (audioFeatures.isNotEmpty) ...[
              const SizedBox(height: 4),
              // Row(
              //   children: [
              //     const Icon(Icons.volume_up, size: 16, color: Colors.cyan),
              //     const SizedBox(width: 4),
              //     Text(
              //       audioFeatures.join(', '),
              //       style: const TextStyle(
              //         color: Colors.cyan,
              //         fontStyle: FontStyle.italic,
              //       ),
              //     ),
              //   ],
              // ),
               Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: audioFeatures.map((feature) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Row(
                    children: [
                      const Icon(Icons.volume_up, size: 16, color: Colors.cyan),
                      const SizedBox(width: 4),
                      Text(
                        feature,
                        style: const TextStyle(
                          color: Colors.cyan,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
            ],
          ],
        ],
      ),
    );
  }

  void _handleSave() async {
    // DEBUGGER POINT 4: Log save attempt
    _debugLog('_handleSave', 'User clicked save');
    _debugLogCurrentState('Before validation');
    
    // Check if at least one style is selected
    if (!_isAnyStyleSelected) {
      // DEBUGGER POINT 5: Log validation failure
      _debugLog('_handleSave', 'No styles selected - showing warning');
      
      // Show warning dialog
      final shouldUseDefaults = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('⚠️ No Translation Styles Selected'),
          content: const Text(
            'You haven\'t selected any translation styles.\n\n'
            'Would you like to:\n'
            '• Go back and select styles, or\n'
            '• Use default settings (Colloquial for both languages)?'
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Go Back'),
            ),
            TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Use Defaults'),
            ),
          ],
        ),
      );
      
      if (shouldUseDefaults == true) {
        // Apply minimal defaults
        setState(() {
          _germanColloquial = true;
          _englishColloquial = true;
        });
        
        // DEBUGGER POINT 6: Log default application
        _debugLog('_handleSave', 'User chose to use defaults');
        _debugLogCurrentState('After applying defaults');
      } else {
        return; // User chose to go back
      }
    }
    
    final updatedSettings = {
      'microphoneMode': 'continuousListening',
      'motherTongue': _getMotherTongueString(_motherTongue),
      'appMode': _getAppModeString(_appMode),
      
      // Fluency practice settings
      'practiceLanguage': _getPracticeLanguageString(_practiceLanguage),
      'correctionLevel': _getCorrectionLevelString(_correctionLevel),
      'pronunciationFeedback': _pronunciationFeedback,
      'grammarCorrection': _grammarCorrection,
      'vocabularyEnhancement': _vocabularyEnhancement,
      'realTimeCorrection': _realTimeCorrection,
      
      // Word-by-word audio settings - EXACT user selection
      'germanWordByWord': _germanWordByWord,
      'englishWordByWord': _englishWordByWord,
      
      // Translation style preferences - EXACT user selection
      'germanNative': _germanNative,
      'germanColloquial': _germanColloquial,
      'germanInformal': _germanInformal,
      'germanFormal': _germanFormal,
      'englishNative': _englishNative,
      'englishColloquial': _englishColloquial,
      'englishInformal': _englishInformal,
      'englishFormal': _englishFormal,
    };

    // DEBUGGER POINT 7: Log final settings being saved
    _debugLog('_handleSave', 'Final settings to save:');
    debugPrint(updatedSettings.toString());

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
      
      // DEBUGGER POINT 8: Log successful save
      _debugLog('_handleSave', '✅ Settings saved to Hive successfully');
      
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
      // DEBUGGER POINT 9: Log save error
      _debugLog('_handleSave', '❌ Error saving settings: $e');
      
      // Close loading dialog if it's open
      Navigator.of(context).pop();
      
      // Show error message
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
        actions: [
          // Clear all button
          IconButton(
            icon: const Icon(Icons.clear_all, color: Colors.orange),
            onPressed: () {
              // DEBUGGER POINT 10: Log clear all action
              _debugLog('AppBar', 'User clicked clear all');
              
              setState(() {
                // Clear all selections
                _germanNative = false;
                _germanColloquial = false;
                _germanInformal = false;
                _germanFormal = false;
                _englishNative = false;
                _englishColloquial = false;
                _englishInformal = false;
                _englishFormal = false;
                _germanWordByWord = false;
                _englishWordByWord = false;
              });
              
              _debugLogCurrentState('After clearing all');
            },
            tooltip: 'Clear All Selections',
          ),
        ],
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

              // Translation Styles Section (only show in Language Learning mode)
              if (_appMode == AppMode.languageLearning) ...[
                const Text('Translation Styles', style: TextStyle(color: Colors.cyan, fontSize: 16, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                
                // Selection summary
                _buildSelectionSummary(),
                
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
                              Row(
                                children: [
                                  if (_isGermanSelected)
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                      margin: const EdgeInsets.only(right: 8),
                                      decoration: BoxDecoration(
                                        color: Colors.green,
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                      child: Text(
                                        '${[_germanNative, _germanColloquial, _germanInformal, _germanFormal].where((e) => e).length} selected',
                                        style: const TextStyle(color: Colors.white, fontSize: 12),
                                      ),
                                    ),
                                  Icon(_germanExpanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down, color: Colors.white),
                                ],
                              ),
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
                                      // DEBUGGER POINT 11: Log toggle change
                                      _debugLog('German Word-by-Word', 'Changed to: $value');
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
                              Row(
                                children: [
                                  if (_isEnglishSelected)
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                      margin: const EdgeInsets.only(right: 8),
                                      decoration: BoxDecoration(
                                        color: Colors.green,
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                      child: Text(
                                        '${[_englishNative, _englishColloquial, _englishInformal, _englishFormal].where((e) => e).length} selected',
                                        style: const TextStyle(color: Colors.white, fontSize: 12),
                                      ),
                                    ),
                                  Icon(_englishExpanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down, color: Colors.white),
                                ],
                              ),
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
                                      // DEBUGGER POINT 12: Log toggle change
                                      _debugLog('English Word-by-Word', 'Changed to: $value');
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