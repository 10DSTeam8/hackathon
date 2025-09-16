# AWS Lambda Deployment Guide

This guide explains how to deploy the Flask API to AWS Lambda using the provided deployment script.

## Quick Start

1. **Run the deployment script:**
   ```bash
   cd api/
   python deploy.py
   ```

2. **Upload to AWS Lambda:**
   - The script creates `lambda_deployment_package.zip` (~14.33 MB)
   - Upload this zip file directly to AWS Lambda

3. **Configure Lambda:**
   - Set handler to: `main.lambda_handler`
   - Set runtime to: Python 3.11
   - Configure timeout (recommend 30+ seconds)

## Deployment Script Features

The `deploy.py` script automatically:

### ✅ Dependency Management
- Extracts production dependencies from Pipfile
- Installs only required packages (Flask, boto3, etc.)
- Excludes development dependencies

### ✅ File Optimization
- Copies only essential application files (`main.py`)
- Excludes test files, documentation, and development files
- Removes unnecessary package files:
  - `__pycache__` directories
  - `.dist-info` directories
  - Documentation and example files
  - Unused package components

### ✅ Package Creation
- Creates deployment-ready zip file
- Optimized for Lambda execution
- Maintains proper file structure and permissions

## Package Contents

The deployment package includes:
- `main.py` - Main Flask application with Lambda handler
- All production Python dependencies:
  - Flask (web framework)
  - boto3 (AWS SDK)
  - botocore (boto3 core)
  - werkzeug (WSGI utilities)
  - jinja2 (templating)
  - click (CLI utilities)
  - markupsafe (string handling)
  - itsdangerous (security utilities)
  - blinker (signals)
  - python-dateutil (date utilities)
  - urllib3 (HTTP client)
  - jmespath (JSON matching)
  - s3transfer (S3 transfer utilities)

## AWS Lambda Configuration

### Handler Configuration
```
Handler: main.lambda_handler
Runtime: Python 3.11
```

### Recommended Settings
- **Memory:** 512 MB (minimum for ML workloads)
- **Timeout:** 30 seconds (adjust based on Sagemaker response times)
- **Environment Variables:**
  - `SAGEMAKER_ENDPOINT_NAME` - Your Sagemaker endpoint name

### Required IAM Permissions
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sagemaker:InvokeEndpoint"
            ],
            "Resource": "arn:aws:sagemaker:*:*:endpoint/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
```

## API Gateway Integration

### Method: POST
### Path: `/predict`
### Integration Type: Lambda Proxy Integration

### Example Event Structure
```json
{
    "httpMethod": "POST",
    "path": "/predict",
    "body": "{\"features\": [1.0, 2.0, 3.0], \"model_version\": \"v1\"}"
}
```

## Testing the Deployment

### 1. Test with curl
```bash
curl -X POST https://your-api-gateway-url/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [1.0, 2.0, 3.0], "request_id": "test_123"}'
```

### 2. Expected Response
```json
{
    "status": "success",
    "prediction": {
        "result": 0.85,
        "confidence": 0.92
    }
}
```

## Deployment Workflow

```
Local Development
       ↓
   Run deploy.py
       ↓
Create ZIP package
       ↓
Upload to Lambda
       ↓
Configure Handler
       ↓
Set IAM Permissions
       ↓
Test API Gateway
       ↓
Production Ready
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Verify all dependencies are in the package
   - Check Python version compatibility

2. **Timeout Errors**
   - Increase Lambda timeout setting
   - Optimize Sagemaker endpoint performance

3. **Memory Issues**
   - Increase Lambda memory allocation
   - Monitor CloudWatch logs for memory usage

4. **Permission Errors**
   - Verify IAM role has Sagemaker permissions
   - Check endpoint name configuration

### Debugging Steps

1. **Check CloudWatch Logs:**
   ```
   /aws/lambda/your-function-name
   ```

2. **Test Locally First:**
   ```bash
   cd api/
   pipenv run python main.py
   ```

3. **Validate Package Contents:**
   - Ensure main.py is in the root of the zip
   - Verify all dependencies are present

## Performance Optimization

### Cold Start Reduction
- Keep package size minimal (current: ~14MB)
- Use provisioned concurrency for high-traffic APIs
- Consider Lambda layers for large dependencies

### Memory and Timeout
- Monitor actual usage in CloudWatch
- Adjust memory allocation based on workload
- Set appropriate timeout for Sagemaker calls

## Security Considerations

1. **Environment Variables:**
   - Store sensitive configuration in environment variables
   - Use AWS Systems Manager Parameter Store for secrets

2. **VPC Configuration:**
   - Configure VPC if accessing private resources
   - Ensure proper security groups

3. **API Gateway Security:**
   - Enable API keys if needed
   - Configure CORS properly
   - Consider WAF for additional protection

## Monitoring and Logging

### CloudWatch Metrics
- Invocation count
- Error rate
- Duration
- Throttles

### Custom Logging
The application includes structured logging:
```python
logger.info(f"Received prediction request: {json.dumps(data)}")
logger.info(f"Sagemaker response: {json.dumps(result)}")
logger.error(f"Error processing request: {str(e)}")
```

## Next Steps

1. **Update Sagemaker Endpoint:**
   - Replace `"sagemaker-endpoint-name"` in main.py
   - Or use environment variable: `SAGEMAKER_ENDPOINT_NAME`

2. **Configure Monitoring:**
   - Set up CloudWatch alarms
   - Configure error notifications

3. **Scale as Needed:**
   - Monitor usage patterns
   - Configure auto-scaling policies
   - Consider regional deployment for global access