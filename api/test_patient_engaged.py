#!/usr/bin/env python3
"""
Test script for the patient_engaged parameter functionality
"""
import json
import sys
import unittest
from unittest.mock import patch, MagicMock

# Import the Flask app
from main import app, lambda_handler


class TestPatientEngagedParameter(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_patient_engaged_true(self):
        """Test the predict endpoint with patient_engaged=true."""
        test_data = {
            "features": [1.0, 2.0, 3.0, 4.0],
            "patient_engaged": True,
            "model_version": "v1"
        }
        
        # Mock the Sagemaker response
        mock_response = {
            'Body': MagicMock()
        }
        mock_response['Body'].read.return_value.decode.return_value = json.dumps({
            "prediction": 0.85
        })
        
        with patch('main.sagemaker_runtime.invoke_endpoint', return_value=mock_response):
            response = self.app.post('/predict',
                                   data=json.dumps(test_data),
                                   content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.get_data(as_text=True))
            self.assertEqual(response_data['status'], 'success')
            # Since multiplier is 1, prediction should remain unchanged
            self.assertEqual(response_data['prediction'], 0.85)
    
    def test_patient_engaged_false(self):
        """Test the predict endpoint with patient_engaged=false."""
        test_data = {
            "features": [1.0, 2.0, 3.0, 4.0],
            "patient_engaged": False,
            "model_version": "v1"
        }
        
        # Mock the Sagemaker response
        mock_response = {
            'Body': MagicMock()
        }
        mock_response['Body'].read.return_value.decode.return_value = json.dumps({
            "prediction": 0.85
        })
        
        with patch('main.sagemaker_runtime.invoke_endpoint', return_value=mock_response):
            response = self.app.post('/predict',
                                   data=json.dumps(test_data),
                                   content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.get_data(as_text=True))
            self.assertEqual(response_data['status'], 'success')
            # Since patient_engaged is false, no multiplier should be applied
            self.assertEqual(response_data['prediction'], 0.85)
    
    def test_patient_engaged_missing(self):
        """Test the predict endpoint without patient_engaged parameter."""
        test_data = {
            "features": [1.0, 2.0, 3.0, 4.0],
            "model_version": "v1"
        }
        
        # Mock the Sagemaker response
        mock_response = {
            'Body': MagicMock()
        }
        mock_response['Body'].read.return_value.decode.return_value = json.dumps({
            "prediction": 0.85
        })
        
        with patch('main.sagemaker_runtime.invoke_endpoint', return_value=mock_response):
            response = self.app.post('/predict',
                                   data=json.dumps(test_data),
                                   content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.get_data(as_text=True))
            self.assertEqual(response_data['status'], 'success')
            # Since patient_engaged is missing, no multiplier should be applied
            self.assertEqual(response_data['prediction'], 0.85)
    
    def test_combined_parameters(self):
        """Test the predict endpoint with multiple parameters including patient_engaged."""
        test_data = {
            "features": [1.0, 2.0, 3.0, 4.0],
            "patient_engaged": True,
            "bad_weather": True,
            "transport_issues": True,
            "model_version": "v1"
        }
        
        # Mock the Sagemaker response
        mock_response = {
            'Body': MagicMock()
        }
        mock_response['Body'].read.return_value.decode.return_value = json.dumps({
            "prediction": 1.0
        })
        
        with patch('main.sagemaker_runtime.invoke_endpoint', return_value=mock_response):
            response = self.app.post('/predict',
                                   data=json.dumps(test_data),
                                   content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.get_data(as_text=True))
            self.assertEqual(response_data['status'], 'success')
            # Expected: 1.0 * 0.955 * 0.85 * 1 = 0.81175
            expected_result = 1.0 * 0.955 * 0.85 * 1
            self.assertAlmostEqual(response_data['prediction'], expected_result, places=5)


def main():
    """Run the tests."""
    print("Running patient_engaged parameter tests...")
    
    # Run unit tests
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "="*60)
    print("MANUAL TEST - patient_engaged Parameter")
    print("="*60)
    
    # Test the Flask app directly
    with app.test_client() as client:
        # Test 1: patient_engaged = true
        print("\n1. Testing with patient_engaged=true:")
        test_data = {
            "features": [1.0, 2.0, 3.0],
            "patient_engaged": True,
            "request_id": "test_patient_engaged_true"
        }
        
        # Mock Sagemaker response for manual test
        mock_response = {
            'Body': MagicMock()
        }
        mock_response['Body'].read.return_value.decode.return_value = json.dumps({
            "prediction": 0.9
        })
        
        try:
            with patch('main.sagemaker_runtime.invoke_endpoint', return_value=mock_response):
                response = client.post('/predict',
                                     data=json.dumps(test_data),
                                     content_type='application/json')
                print(f"   Status Code: {response.status_code}")
                print(f"   Response: {response.get_data(as_text=True)}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 2: patient_engaged = false
        print("\n2. Testing with patient_engaged=false:")
        test_data = {
            "features": [1.0, 2.0, 3.0],
            "patient_engaged": False,
            "request_id": "test_patient_engaged_false"
        }
        
        try:
            with patch('main.sagemaker_runtime.invoke_endpoint', return_value=mock_response):
                response = client.post('/predict',
                                     data=json.dumps(test_data),
                                     content_type='application/json')
                print(f"   Status Code: {response.status_code}")
                print(f"   Response: {response.get_data(as_text=True)}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 3: Combined with other parameters
        print("\n3. Testing with all parameters:")
        test_data = {
            "features": [1.0, 2.0, 3.0],
            "patient_engaged": True,
            "bad_weather": True,
            "transport_issues": True,
            "request_id": "test_all_params"
        }
        
        # Use prediction of 1.0 for easy calculation
        mock_response['Body'].read.return_value.decode.return_value = json.dumps({
            "prediction": 1.0
        })
        
        try:
            with patch('main.sagemaker_runtime.invoke_endpoint', return_value=mock_response):
                response = client.post('/predict',
                                     data=json.dumps(test_data),
                                     content_type='application/json')
                print(f"   Status Code: {response.status_code}")
                response_data = json.loads(response.get_data(as_text=True))
                print(f"   Response: {response.get_data(as_text=True)}")
                print(f"   Expected calculation: 1.0 * 0.955 * 0.85 * 1 = {1.0 * 0.955 * 0.85 * 1}")
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n" + "="*60)
    print("patient_engaged parameter tests completed!")
    print("="*60)
    print("\nThe new 'patient_engaged' parameter:")
    print("- Applies a multiplier of 1 when true (no change to prediction)")
    print("- Is ignored when false or missing")
    print("- Works correctly in combination with other parameters")
    print("- Maintains backward compatibility")


if __name__ == '__main__':
    main()