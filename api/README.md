# Flask Lambda API with AWS Sagemaker Integration

This is a Flask-based Lambda API that accepts POST requests with JSON data and makes calls to AWS Sagemaker AI models using boto3.

## Features

- **Single POST Endpoint**: `/predict` endpoint that accepts JSON data
- **AWS Sagemaker Integration**: Uses boto3 to invoke Sagemaker models
- **Lambda Compatible**: Includes proper Lambda handler for AWS deployment
- **Error Handling**: Comprehensive error handling for various scenarios
- **Logging**: Detailed logging for monitoring and debugging
- **CORS Support**: Includes CORS headers for web integration

## API Endpoint

### POST /predict

Accepts JSON data and forwards it to a configured Sagemaker endpoint.

**Request:**
```json
{
  "features": [1.0, 2.0, 3.0, 4.0],
  "model_version": "v1",
  "metadata": {
    "timestamp": "2025-09-16T13:56:00Z",
    "user_id": "test_user"
  }
}
```

**Success Response (200):**
```json
{
  "status": "success",
  "prediction": {
    "result": 0.85,
    "confidence": 0.92
  }
}
```

**Error Response (400/500):**
```json
{
  "status": "error",
  "message": "Error description"
}
```

## Setup and Installation

1. Install dependencies:
```bash
pipenv install
```

2. Configure your Sagemaker endpoint:
   - Edit `main.py` line 31
   - Replace `"your-sagemaker-endpoint-name"` with your actual endpoint name

3. Configure AWS credentials:
   - Set up AWS CLI or environment variables
   - Ensure proper IAM permissions for Sagemaker access

## Running the Application

### Local Development
```bash
pipenv run python main.py
```
The app will run on `http://127.0.0.1:5000`

### AWS Lambda Deployment
The `lambda_handler` function is ready for AWS Lambda deployment. The handler processes API Gateway events and returns proper responses.

## Testing

Run the comprehensive test suite:
```bash
pipenv run python test_app.py
```

The tests include:
- Valid JSON request handling
- Error handling for missing JSON
- Sagemaker error scenarios
- Lambda handler functionality

## Files

- `main.py`: Main Flask application with Lambda handler
- `test_app.py`: Comprehensive test suite
- `test_predict.http`: HTTP test file for manual testing
- `Pipfile`: Dependencies configuration

## Dependencies

- **Flask**: Web framework
- **boto3**: AWS SDK for Sagemaker integration
- **json**: JSON handling
- **logging**: Application logging

## Notes

- The application includes proper error handling for AWS authentication issues
- Sagemaker endpoint name must be configured before deployment
- All tests pass successfully with proper mocking
- Ready for AWS Lambda deployment with API Gateway integration