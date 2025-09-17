#!/usr/bin/env python3
"""
Test script to verify the attendance prediction model works correctly
"""

import logging
from attendance_model import AttendancePredictor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_predictions():
    """Test multiple prediction scenarios"""
    
    try:
        # Initialize predictor
        predictor = AttendancePredictor()
        
        # Load the trained model
        predictor.load_model()
        logger.info("Model loaded successfully")
        
        # Test cases
        test_cases = [
            {"sex": 1, "date_of_appointment": "15/09/2024", "age": 40, "description": "Female, 40 years old, Sunday appointment"},
            {"sex": 0, "date_of_appointment": "16/09/2024", "age": 35, "description": "Male, 35 years old, Monday appointment"},
            {"sex": 1, "date_of_appointment": "21/09/2024", "age": 30, "description": "Female, 30 years old, Saturday appointment"},
            {"sex": 0, "date_of_appointment": "20/09/2024", "age": 45, "description": "Male, 45 years old, Friday appointment"},
            {"sex": 1, "date_of_appointment": "18/09/2024", "age": 25, "description": "Female, 25 years old, Wednesday appointment"}
        ]
        
        print("\n" + "="*80)
        print("ATTENDANCE PREDICTION TEST RESULTS")
        print("="*80)
        
        for i, test_case in enumerate(test_cases, 1):
            result = predictor.predict(
                sex=test_case["sex"],
                date_of_appointment=test_case["date_of_appointment"],
                age=test_case["age"]
            )
            
            print(f"\nTest Case {i}: {test_case['description']}")
            print(f"  Input: Sex={test_case['sex']}, Date={test_case['date_of_appointment']}, Age={test_case['age']}")
            print(f"  Probability of Attending: {result['will_attend_probability']:.1%}")
            print(f"  Predicted Attendance: {'Will Attend' if result['predicted_attendance'] == 1 else 'Will NOT Attend'}")
            print(f"  Confidence: {result['confidence']:.1%}")
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*80)
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_predictions()
    if success:
        print("\n✅ Model prediction functionality verified successfully!")
    else:
        print("\n❌ Model prediction test failed!")
        exit(1)