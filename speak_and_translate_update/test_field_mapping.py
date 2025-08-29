#!/usr/bin/env python3
"""Test to verify Pydantic field alias mapping is working"""

from pydantic import BaseModel, Field
from typing import Optional
import json

class TranslationStylePreferences(BaseModel):
    """Simplified version of the model for testing"""
    # German styles - ALL can be selected simultaneously
    german_native: bool = Field(False, alias="germanNative")
    german_colloquial: bool = Field(False, alias="germanColloquial")
    german_informal: bool = Field(False, alias="germanInformal")
    german_formal: bool = Field(False, alias="germanFormal")
    
    # English styles - ALL can be selected simultaneously
    english_native: bool = Field(False, alias="englishNative")
    english_colloquial: bool = Field(False, alias="englishColloquial")
    english_informal: bool = Field(False, alias="englishInformal")
    english_formal: bool = Field(False, alias="englishFormal")
    
    # Mother tongue for dynamic translation
    mother_tongue: Optional[str] = Field("spanish", alias="motherTongue")
    
    model_config = {"populate_by_name": True}

def test_field_mapping():
    """Test that camelCase fields map correctly to snake_case"""
    print("Testing Pydantic field alias mapping...")
    
    # Test data - this is what the frontend sends
    test_data = {
        "motherTongue": "spanish",
        "germanNative": True,
        "germanColloquial": False,
        "germanInformal": False,
        "germanFormal": True,
        "englishNative": True,
        "englishColloquial": False,
        "englishInformal": False,
        "englishFormal": True,
    }
    
    print(f"\nInput (camelCase): {json.dumps(test_data, indent=2)}")
    
    try:
        # Parse using Pydantic model
        parsed = TranslationStylePreferences(**test_data)
        
        print(f"\nParsed object fields (snake_case):")
        print(f"  german_native: {parsed.german_native}")
        print(f"  german_colloquial: {parsed.german_colloquial}")
        print(f"  german_formal: {parsed.german_formal}")
        print(f"  english_native: {parsed.english_native}")
        print(f"  english_colloquial: {parsed.english_colloquial}")
        print(f"  english_formal: {parsed.english_formal}")
        print(f"  mother_tongue: {parsed.mother_tongue}")
        
        # Test JSON serialization
        json_output = parsed.model_dump()
        print(f"\nJSON output (snake_case): {json.dumps(json_output, indent=2)}")
        
        # Test alias serialization
        json_camel = parsed.model_dump(by_alias=True)
        print(f"\nJSON with aliases (camelCase): {json.dumps(json_camel, indent=2)}")
        
        # Verify expectations
        expected_true = parsed.german_native and parsed.german_formal and parsed.english_native and parsed.english_formal
        expected_false = not (parsed.german_colloquial or parsed.english_colloquial)
        
        if expected_true and expected_false:
            print(f"\n✅ SUCCESS: Field mapping works correctly!")
            print("  Native and Formal fields are True")
            print("  Colloquial fields are False")
            return True
        else:
            print(f"\n❌ FAILURE: Field mapping produced incorrect values!")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_field_mapping()
    exit(0 if success else 1)