// Updated settings_screen.dart with EXACT dynamic translation explanation per requirements

import 'package:flutter/material.dart';
import 'package:speak_and_translate_update/features/translation/data/repositories/hive_user_settings_repository.dart';

enum MotherTongue {
  spanish,
  english,
  german,
  french,
  italian,
  portuguese,
}

enum AppMode {
  languageLearning,
  travelMode,
  fluencyPractice,
}

class SettingsScreen extends StatefulWidget {
  final Map<String, dynamic>? initialSettings;
  
  const SettingsScreen({super.key, this.initialSettings});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  MotherTongue _motherTongue = MotherTongue.spanish;
  AppMode _appMode = AppMode.languageLearning;
  
  // Fluency practice settings
  bool _pronunciationFeedback = true;
  bool _grammarCorrection = true;
  bool _vocabularyEnhancement = true;
  bool _realTimeCorrection = false;
  
  // EXACT per requirements: Word-by-word audio settings - User has complete freedom
  bool _germanWordByWord = false;
  bool _englishWordByWord = false;
  
  // EXACT per requirements: German styles - User has complete freedom
  // Default to Native and Formal for good user experience
  bool _germanNative = true;
  bool _germanColloquial = false;
  bool _germanInformal = false;
  bool _germanFormal = true;
  
  // EXACT per requirements: English styles - User has complete freedom
  // Default to Native and Formal for good user experience
  bool _englishNative = true;
  bool _englishColloquial = false;
  bool _englishInformal = false;
  bool _englishFormal = true;

  // Expansion states
  bool _germanExpanded = false;
  bool _englishExpanded = false;

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
      _motherTongue = _getMotherTongueFromString(motherTongueString ?? 'spanish');
      
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
      _pronunciationFeedback = settings['pronunciationFeedback'] as bool? ?? true;
      _grammarCorrection = settings['grammarCorrection'] as bool? ?? true;
      _vocabularyEnhancement = settings['vocabularyEnhancement'] as bool? ?? true;
      _realTimeCorrection = settings['realTimeCorrection'] as bool? ?? false;
      
      // EXACT per requirements: Load word-by-word audio settings
      _germanWordByWord = settings['germanWordByWord'] as bool? ?? false;
      _englishWordByWord = settings['englishWordByWord'] as bool? ?? false;
      
      // EXACT per requirements: Load translation style preferences
      _germanNative = settings['germanNative'] as bool? ?? false;
      _germanColloquial = settings['germanColloquial'] as bool? ?? false;
      _germanInformal = settings['germanInformal'] as bool? ?? false;
      _germanFormal = settings['germanFormal'] as bool? ?? false;
      _englishNative = settings['englishNative'] as bool? ?? false;
      _englishColloquial = settings['englishColloquial'] as bool? ?? false;
      _englishInformal = settings['englishInformal'] as bool? ?? false;
      _englishFormal = settings['englishFormal'] as bool? ?? false;
    }
  }

  // Helper methods
  MotherTongue _getMotherTongueFromString(String value) {
    switch (value) {
      case 'english': return MotherTongue.english;
      case 'german': return MotherTongue.german;
      case 'french': return MotherTongue.french;
      case 'italian': return MotherTongue.italian;
      case 'portuguese': return MotherTongue.portuguese;
      default: return MotherTongue.spanish;
    }
  }

  String _getLanguageName(MotherTongue language) {
    switch (language) {
      case MotherTongue.spanish: return 'Spanish (Español)';
      case MotherTongue.english: return 'English';
      case MotherTongue.german: return 'German (Deutsch)';
      case MotherTongue.french: return 'French (Français)';
      case MotherTongue.italian: return 'Italian (Italiano)';
      case MotherTongue.portuguese: return 'Portuguese (Português)';
    }
  }

  String _getLanguageFlag(MotherTongue language) {
    switch (language) {
      case MotherTongue.spanish: return '🇪🇸';
      case MotherTongue.english: return '🇺🇸';
      case MotherTongue.german: return '🇩🇪';
      case MotherTongue.french: return '🇫🇷';
      case MotherTongue.italian: return '🇮🇹';
      case MotherTongue.portuguese: return '🇵🇹';
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

  // EXACT per requirements: Check if any styles are selected for each language
  bool get _isGermanSelected {
    return _germanNative || _germanColloquial || _germanInformal || _germanFormal;
  }

  bool get _isEnglishSelected {
    return _englishNative || _englishColloquial || _englishInformal || _englishFormal;
  }

  bool get _isAnyStyleSelected {
    return _isGermanSelected || _isEnglishSelected;
  }

  // EXACT per requirements: Get expected target languages based on mother tongue
  List<String> _getExpectedTargetLanguages() {
    switch (_motherTongue) {
      case MotherTongue.spanish:
        // EXACT: Spanish → German and/or English based on selections
        List<String> targets = [];
        if (_isGermanSelected) targets.add('German');
        if (_isEnglishSelected) targets.add('English');
        return targets;
        
      case MotherTongue.english:
        // EXACT: English → Spanish (automatic) + German if selected
        List<String> targets = ['Spanish (automatic)'];
        if (_isGermanSelected) targets.add('German');
        return targets;
        
      case MotherTongue.german:
        // EXACT: German → Spanish (automatic) + English if selected
        List<String> targets = ['Spanish (automatic)'];
        if (_isEnglishSelected) targets.add('English');
        return targets;
        
      default:
        // Other languages → German and/or English based on selections
        List<String> targets = [];
        if (_isGermanSelected) targets.add('German');
        if (_isEnglishSelected) targets.add('English');
        return targets;
    }
  }

  // EXACT per requirements: Build dynamic translation explanation widget
  Widget _buildDynamicTranslationInfo() {
    final expectedTargets = _getExpectedTargetLanguages();
    final audioFeatures = <String>[];
    
    if (_germanWordByWord) audioFeatures.add('German Word-by-Word');
    if (_englishWordByWord) audioFeatures.add('English Word-by-Word');

    return Container(
      padding: const EdgeInsets.all(16),
      margin: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.blue[900]!.withOpacity(0.3), Colors.purple[900]!.withOpacity(0.3)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.blue, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.translate, color: Colors.lightBlue, size: 24),
              const SizedBox(width: 12),
              const Text(
                'Dynamic Translation Setup',
                style: TextStyle(
                  color: Colors.lightBlue,
                  fontWeight: FontWeight.bold,
                  fontSize: 18,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          
          // EXACT per requirements: Show the dynamic logic
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      _getLanguageFlag(_motherTongue),
                      style: const TextStyle(fontSize: 24),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Your input language:',
                            style: TextStyle(color: Colors.white70, fontSize: 12),
                          ),
                          Text(
                            _getLanguageName(_motherTongue),
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                
                const SizedBox(height: 12),
                
                // EXACT per requirements: Show the dynamic behavior
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.green.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: Colors.green, width: 1),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _getDynamicBehaviorText(),
                        style: const TextStyle(
                          color: Colors.green,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          
          const SizedBox(height: 12),
          
          // Translation directions
          Row(
            children: [
              const Icon(Icons.arrow_forward, color: Colors.lightBlue),
              const SizedBox(width: 8),
              const Text(
                'Will translate to:',
                style: TextStyle(color: Colors.lightBlue, fontWeight: FontWeight.w600),
              ),
            ],
          ),
          
          const SizedBox(height: 8),
          
          // Target languages
          if (expectedTargets.isNotEmpty) ...[
            ...expectedTargets.map((target) => Padding(
              padding: const EdgeInsets.only(left: 32, bottom: 4),
              child: Row(
                children: [
                  Text(
                    _getTargetLanguageFlag(target),
                    style: const TextStyle(fontSize: 16),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    target,
                    style: const TextStyle(color: Colors.white, fontSize: 14),
                  ),
                  if (target.contains('German') && _germanWordByWord)
                    Container(
                      margin: const EdgeInsets.only(left: 8),
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.orange.withOpacity(0.3),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: const Text(
                        'WORD-BY-WORD AUDIO',
                        style: TextStyle(color: Colors.orange, fontSize: 10),
                      ),
                    ),
                  if (target.contains('English') && _englishWordByWord)
                    Container(
                      margin: const EdgeInsets.only(left: 8),
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.orange.withOpacity(0.3),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: const Text(
                        'WORD-BY-WORD AUDIO',
                        style: TextStyle(color: Colors.orange, fontSize: 10),
                      ),
                    ),
                ],
              ),
            )),
          ] else ...[
            Padding(
              padding: const EdgeInsets.only(left: 32),
              child: Text(
                'Select translation styles below to enable translations',
                style: TextStyle(color: Colors.yellow[300], fontStyle: FontStyle.italic),
              ),
            ),
          ],
          
          // EXACT per requirements: Word-by-word audio explanation
          if (audioFeatures.isNotEmpty) ...[
            const SizedBox(height: 12),
            const Divider(color: Colors.white30),
            const SizedBox(height: 8),
            Row(
              children: [
                const Icon(Icons.volume_up, color: Colors.orange, size: 20),
                const SizedBox(width: 8),
                const Text(
                  'Word-by-Word Audio Format:',
                  style: TextStyle(color: Colors.orange, fontWeight: FontWeight.w600),
                ),
              ],
            ),
            const SizedBox(height: 4),
            const Padding(
              padding: EdgeInsets.only(left: 28),
              child: Text(
                '[target word] ([Spanish equivalent])',
                style: TextStyle(color: Colors.orange, fontSize: 12, fontStyle: FontStyle.italic),
              ),
            ),
          ],
        ],
      ),
    );
  }

  String _getDynamicBehaviorText() {
    switch (_motherTongue) {
      case MotherTongue.spanish:
        return 'EXACT Logic: Spanish → German and/or English based on your selections below';
      case MotherTongue.english:
        return 'EXACT Logic: English → Spanish (automatic) + German if you select it below';
      case MotherTongue.german:
        return 'EXACT Logic: German → Spanish (automatic) + English if you select it below';
      default:
        return 'Logic: ${_getLanguageName(_motherTongue)} → German and/or English based on your selections below';
    }
  }

  String _getTargetLanguageFlag(String target) {
    if (target.contains('German')) return '🇩🇪';
    if (target.contains('English')) return '🇺🇸';
    if (target.contains('Spanish')) return '🇪🇸';
    return '🌐';
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
                      : 'No styles selected - Please select at least one below',
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
                          '$feature Audio: [word] ([Spanish])',
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
    // EXACT per requirements: Check if at least one style is selected
    if (!_isAnyStyleSelected) {
      // Show warning dialog with EXACT mother tongue logic
      final shouldUseDefaults = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('⚠️ No Translation Styles Selected'),
          content: Text(
            'You haven\'t selected any translation styles.\n\n'
            'Based on your mother tongue (${_getLanguageName(_motherTongue)}), would you like to:\n\n'
            '${_getDefaultsExplanation()}\n\n'
            'Choose an option:'
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Go Back & Select Manually'),
            ),
            TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Use Smart Defaults'),
            ),
          ],
        ),
      );
      
      if (shouldUseDefaults == true) {
        // EXACT per requirements: Apply intelligent defaults based on mother tongue
        setState(() {
          _applyIntelligentDefaults();
        });
      } else {
        return; // User chose to go back
      }
    }
    
    final updatedSettings = {
      'microphoneMode': 'continuousListening',
      'motherTongue': _getMotherTongueString(_motherTongue),
      'appMode': _getAppModeString(_appMode),
      
      // Fluency practice settings
      'pronunciationFeedback': _pronunciationFeedback,
      'grammarCorrection': _grammarCorrection,
      'vocabularyEnhancement': _vocabularyEnhancement,
      'realTimeCorrection': _realTimeCorrection,
      
      // EXACT per requirements: Word-by-word audio settings
      'germanWordByWord': _germanWordByWord,
      'englishWordByWord': _englishWordByWord,
      
      // EXACT per requirements: Translation style preferences
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

  String _getDefaultsExplanation() {
    switch (_motherTongue) {
      case MotherTongue.spanish:
        return '• Enable German Colloquial translation\n• Enable English Colloquial translation';
      case MotherTongue.english:
        return '• Enable Spanish translation (automatic)\n• Enable German Colloquial translation';
      case MotherTongue.german:
        return '• Enable Spanish translation (automatic)\n• Enable English Colloquial translation';
      default:
        return '• Enable German Colloquial translation\n• Enable English Colloquial translation';
    }
  }

  void _applyIntelligentDefaults() {
    switch (_motherTongue) {
      case MotherTongue.spanish:
        // EXACT: Spanish → German and English colloquial by default
        _germanColloquial = true;
        _englishColloquial = true;
        break;
      case MotherTongue.english:
        // EXACT: English → German colloquial by default (Spanish is automatic)
        _germanColloquial = true;
        break;
      case MotherTongue.german:
        // EXACT: German → English colloquial by default (Spanish is automatic)
        _englishColloquial = true;
        break;
      default:
        // Other languages → German and English colloquial
        _germanColloquial = true;
        _englishColloquial = true;
        break;
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
                child: const Row(
                  children: [
                    Icon(Icons.mic, color: Colors.green, size: 24),
                    SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Continuous Listening', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600)),
                          SizedBox(height: 4),
                          Text('Microphone is always active and automatically sends when you speak', style: TextStyle(color: Colors.grey, fontSize: 14)),
                        ],
                      ),
                    ),
                    Icon(Icons.check_circle, color: Colors.green, size: 24),
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
                        child: Row(
                          children: [
                            Text(_getLanguageFlag(value), style: const TextStyle(fontSize: 18)),
                            const SizedBox(width: 8),
                            Text(_getLanguageName(value), style: const TextStyle(color: Colors.white)),
                          ],
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // App Mode Section (keep TRAVEL MODE and other modalities as requested)
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
                      fillColor: WidgetStateProperty.resolveWith((states) => states.contains(WidgetState.selected) ? Colors.cyan : Colors.grey),
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
                      fillColor: WidgetStateProperty.resolveWith((states) => states.contains(WidgetState.selected) ? Colors.cyan : Colors.grey),
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
                      fillColor: WidgetStateProperty.resolveWith((states) => states.contains(WidgetState.selected) ? Colors.cyan : Colors.grey),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Translation Styles Section (only show in Language Learning mode)
              if (_appMode == AppMode.languageLearning) ...[
                const Text('Translation Styles', style: TextStyle(color: Colors.cyan, fontSize: 16, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                
                // EXACT per requirements: Dynamic translation explanation
                _buildDynamicTranslationInfo(),
                
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
                              const Row(
                                children: [
                                  Text('🇩🇪', style: TextStyle(fontSize: 20)),
                                  SizedBox(width: 8),
                                  Text('German', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w500)),
                                ],
                              ),
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
                              // EXACT per requirements: German Word-by-Word Audio Toggle
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  const Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text('Word-by-Word Audio', style: TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w500)),
                                        SizedBox(height: 2),
                                        Text('Format: [German word] ([Spanish equivalent])', style: TextStyle(color: Colors.grey, fontSize: 13)),
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
                              const Row(
                                children: [
                                  Text('🇺🇸', style: TextStyle(fontSize: 20)),
                                  SizedBox(width: 8),
                                  Text('English', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w500)),
                                ],
                              ),
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
                              // EXACT per requirements: English Word-by-Word Audio Toggle
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  const Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text('Word-by-Word Audio', style: TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w500)),
                                        SizedBox(height: 2),
                                        Text('Format: [English word] ([Spanish equivalent])', style: TextStyle(color: Colors.grey, fontSize: 13)),
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