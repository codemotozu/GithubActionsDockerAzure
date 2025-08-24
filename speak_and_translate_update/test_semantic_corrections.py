#!/usr/bin/env python3
"""
Test script to verify semantic corrections are working properly.
This simulates the exact scenario from the console output where 'I → me' should be corrected to 'I → yo'.
"""

import sys
import os
sys.path.append('./server')

def test_semantic_corrections():
    """Test that semantic corrections fix the exact issues from the console"""
    
    print("🔧 TESTING SEMANTIC CORRECTIONS SYSTEM")
    print("=" * 60)
    print()
    
    try:
        from server.app.application.services.translation_service import TranslationService
        
        service = TranslationService()
        
        # Test cases based on the console errors
        test_cases = [
            # English to Spanish corrections
            {
                'name': 'English I→me correction',
                'pairs': [('I', 'me'), ('am', 'soy'), ('happy', 'feliz')],
                'is_german': False,
                'expected_corrections': [('I', 'yo')]
            },
            {
                'name': 'English multiple corrections',
                'pairs': [('I', 'me'), ('have', 'tengo'), ('the', 'los'), ('and', 'y')],
                'is_german': False,
                'expected_corrections': [('I', 'yo'), ('the', 'la')]
            },
            # German to Spanish corrections
            {
                'name': 'German ich→me correction',
                'pairs': [('ich', 'me'), ('bin', 'levanté'), ('früh', 'temprano')],
                'is_german': True,
                'expected_corrections': [('ich', 'yo'), ('bin', 'soy')]
            },
            {
                'name': 'German multiple corrections',
                'pairs': [('ich', 'necesito'), ('bin', 'levanté'), ('das', 'el'), ('und', 'y')],
                'is_german': True,
                'expected_corrections': [('ich', 'yo'), ('bin', 'soy'), ('das', 'la')]
            }
        ]
        
        all_passed = True
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"Test {i}: {test_case['name']}")
            print("-" * 40)
            
            # Apply semantic corrections
            corrected_pairs = service._fix_common_semantic_mismatches(
                test_case['pairs'], 
                is_german=test_case['is_german']
            )
            
            print(f"Original pairs: {test_case['pairs']}")
            print(f"Corrected pairs: {corrected_pairs}")
            
            # Check if expected corrections were applied
            test_passed = True
            for expected_source, expected_target in test_case['expected_corrections']:
                found_correction = False
                for source, target in corrected_pairs:
                    if source == expected_source and target.lower() == expected_target.lower():
                        found_correction = True
                        break
                
                if not found_correction:
                    print(f"❌ FAILED: Expected '{expected_source} → {expected_target}' not found")
                    test_passed = False
                    all_passed = False
                else:
                    print(f"✅ PASSED: '{expected_source} → {expected_target}' correctly applied")
            
            if test_passed:
                print(f"✅ Test {i} PASSED")
            else:
                print(f"❌ Test {i} FAILED")
            
            print()
        
        # Summary
        print("🎯 SEMANTIC CORRECTIONS TEST SUMMARY")
        print("=" * 40)
        if all_passed:
            print("✅ ALL TESTS PASSED!")
            print("🎵 Users will now see and hear correct translations:")
            print("   - I → yo (not I → me)")
            print("   - ich → yo (not ich → me)")
            print("   - bin → soy (not bin → levanté)")
            print("   - das → la (not das → el)")
            print()
            print("🔧 System automatically corrects semantic mismatches")
            print("🎤 Audio will speak the corrected translations")
            print("📱 UI will display the corrected translations")
        else:
            print("❌ SOME TESTS FAILED!")
            print("   Check the semantic correction mappings")
        
        return all_passed
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test Error: {e}")
        return False

if __name__ == "__main__":
    success = test_semantic_corrections()
    
    if success:
        print("\n🎉 Semantic corrections are working correctly!")
        print("Users will now hear the correct translations in both UI and audio.")
    else:
        print("\n🚨 Semantic corrections need to be fixed.")
    
    exit(0 if success else 1)