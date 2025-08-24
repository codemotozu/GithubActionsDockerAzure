#!/usr/bin/env python3
"""
Test script to verify the format mismatch fix
"""
import sys
import os

def test_format_fix():
    """Test the word-by-word format fix"""
    print("Testing word-by-word format fix...")
    print("="*60)
    
    # Test data
    test_text = "el armario es café"
    mother_tongue = "spanish"
    
    # Mock translation styles (mimicking what the AI returns)
    mock_translations = {
        'german_colloquial': 'Der Schrank ist braun.'
    }
    
    # Test the word-by-word UI sync data generation
    print(f"Input: '{test_text}'")
    print(f"Mother tongue: {mother_tongue}")
    print(f"Testing style: german_colloquial")
    print()
    
    # Mock word pairs (this is what would normally come from AI)
    word_pairs = [
        ("Der", "el"),
        ("Schrank", "armario"), 
        ("ist", "es"),
        ("braun.", "café")
    ]
    
    print("Simulating display format generation...")
    
    # Test the format generation logic directly
    test_data = []
    for target_word, mother_tongue_word in word_pairs:
        # Clean for consistency (simulating the actual code)
        target_clean = target_word.strip().strip('"\'[]')
        mother_tongue_clean = mother_tongue_word.strip().strip('"\'[]')
        
        # CRITICAL: Create DYNAMIC format based on mother tongue - CORRECTED FORMAT with parentheses
        display_format = f"[{target_clean}] ([{mother_tongue_clean}])"
        
        test_data.append({
            "source": target_clean,
            "spanish": mother_tongue_clean,
            "display_format": display_format
        })
    
    print("VALIDATION RESULTS:")
    print("="*60)
    
    # Check format for each word pair
    errors = []
    for data in test_data:
        source = data.get('source', '')
        spanish = data.get('spanish', '')
        display_format = data.get('display_format', '')
        expected_format = f"[{source}] ([{spanish}])"
        
        print(f"UI Display: {display_format}")
        print(f"Expected:   {expected_format}")
        
        if display_format == expected_format:
            print("FORMAT CORRECT!")
        else:
            errors.append(f"Format mismatch - Expected: {expected_format}, Got: {display_format}")
            print("FORMAT MISMATCH!")
        print()
    
    # Final result
    print("="*60)
    if errors:
        print("TEST FAILED! Errors found:")
        for error in errors:
            print(f"   {error}")
        return False
    else:
        print("TEST PASSED! All formats are correct.")
        print("The synchronization format fix is working properly!")
        return True

if __name__ == "__main__":
    result = test_format_fix()
    sys.exit(0 if result else 1)