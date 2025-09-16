#!/usr/bin/env python3
"""
Test script for the Flask Lambda API with Sagemaker integration
"""
import json
import sys
import unittest
from unittest.mock import patch, MagicMock

# Import the Flask app
from main import app, lambda_handler


class TestFlaskSagemakerAPI(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_predict_endpoint_with_valid_json(self):
        """Test the predict endpoint with valid JSON data."""
        test_data = {
            "features": [1.0, 2.0, 3.0, 4.0],
            "model_version": "v1",
            "metadata": {
                "timestamp": "2025-09-16T13:56:00Z",
                "user_id": "test_user"
            }
        }
        
        # Mock the Sagemaker response since we don't have a real endpoint
        mock_response = {
            'Body': MagicMock()
        }
        mock_response['Body'].read.return_value.decode.return_value = json.dumps({
            "prediction": 0.85,
            "confidence": 0.92
        })
        
        with patch('main.sagemaker_runtime.invoke_endpoint', return_value=mock_response):
            response = self.app.post('/predict',
                                   data=json.dumps(test_data),
                                   content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.get_data(as_text=True))
            self.assertEqual(response_data['status'], 'success')
            self.assertIn('prediction', response_data)
    
    def test_predict_endpoint_no_json(self):
        """Test the predict endpoint with no JSON data."""
        response = self.app.post('/predict', content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response_data['error'], 'No JSON data provided')
    
    def test_predict_endpoint_sagemaker_error(self):
        """Test the predict endpoint when Sagemaker returns an error."""
        test_data = {"test": "data"}
        
        with patch('main.sagemaker_runtime.invoke_endpoint', side_effect=Exception("Sagemaker endpoint not found")):
            response = self.app.post('/predict',
                                   data=json.dumps(test_data),
                                   content_type='application/json')
            
            self.assertEqual(response.status_code, 500)
            response_data = json.loads(response.get_data(as_text=True))
            self.assertEqual(response_data['status'], 'error')
            self.assertIn('Sagemaker endpoint not found', response_data['message'])
    
    def test_lambda_handler_post(self):
        """Test the Lambda handler with a POST request."""
        event = {
            'httpMethod': 'POST',
            'path': '/predict',
            'body': json.dumps({"test": "data"})
        }
        context = {}
        
        # Mock the Sagemaker response
        mock_response = {
            'Body': MagicMock()
        }
        mock_response['Body'].read.return_value.decode.return_value = json.dumps({
            "prediction": 0.75
        })
        
        with patch('main.sagemaker_runtime.invoke_endpoint', return_value=mock_response):
            result = lambda_handler(event, context)
            
            self.assertEqual(result['statusCode'], 200)
            self.assertEqual(result['headers']['Content-Type'], 'application/json')
            
            response_body = json.loads(result['body'])
            self.assertEqual(response_body['status'], 'success')
    
    def test_lambda_handler_error(self):
        """Test the Lambda handler with an error scenario."""
        event = {
            'httpMethod': 'POST',
            'path': '/predict',
            'body': json.dumps({"test": "data"})
        }
        context = {}
        
        with patch('main.sagemaker_runtime.invoke_endpoint', side_effect=Exception("Test error")):
            result = lambda_handler(event, context)
            
            self.assertEqual(result['statusCode'], 500)
            response_body = json.loads(result['body'])
            self.assertEqual(response_body['status'], 'error')


def main():
    """Run the tests."""
    print("Running Flask Sagemaker API tests...")
    
    # Run unit tests
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "="*50)
    print("MANUAL TEST - Flask App Functionality")
    print("="*50)
    
    # Test the Flask app directly
    with app.test_client() as client:
        # Test 1: Valid JSON
        print("\n1. Testing with valid JSON data:")
        test_data = {
            "features": [1.0, 2.0, 3.0],
            "request_id": "test_123"
        }
        
        try:
            response = client.post('/predict',
                                 data=json.dumps(test_data),
                                 content_type='application/json')
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.get_data(as_text=True)}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 2: No JSON data
        print("\n2. Testing with no JSON data:")
        try:
            response = client.post('/predict', content_type='application/json')
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.get_data(as_text=True)}")
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n" + "="*50)
    print("Tests completed!")
    print("="*50)
    print("\nNOTE: Actual Sagemaker calls will fail without proper AWS configuration.")
    print("Replace 'your-sagemaker-endpoint-name' in main.py with your actual endpoint name.")


if __name__ == '__main__':
    main()