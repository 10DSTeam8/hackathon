from flask import Flask, request, jsonify
import boto3
import json
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = Flask(__name__)

# Initialize AWS Sagemaker client
sagemaker_runtime = boto3.client('sagemaker-runtime')

@app.route("/predict", methods=["POST"])
def predict():
    """
    POST endpoint that accepts JSON data and makes a call to AWS Sagemaker model
    """
    try:
        # Get JSON data from request with force=False and silent=True to handle errors gracefully
        data = request.get_json(force=False, silent=True)
        
        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Log the incoming request
        logger.info(f"Received prediction request: {json.dumps(data)}")
        
        # TODO: Replace with actual Sagemaker endpoint name
        endpoint_name = "sagemaker-endpoint-name"
        
        # Prepare the payload for Sagemaker
        payload = json.dumps(data)
        
        # Make the call to Sagemaker
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=payload
        )
        
        # Parse the response
        result = json.loads(response['Body'].read().decode())
        
        logger.info(f"Sagemaker response: {json.dumps(result)}")

        # Extract the prediction value and apply multipliers
        prediction = result['prediction']
        
        if 'bad_weather' in data and data['bad_weather']:
            prediction = prediction * 0.955

        if 'transport_issues' in data and data['transport_issues']:
            prediction = prediction * 0.85

        if 'patient_engaged' in data and data['patient_engaged']:
            prediction = prediction * 1 # placeholder multiplier
        
        return jsonify({
            "status": "success",
            "prediction": prediction
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Lambda handler for AWS Lambda deployment
def lambda_handler(event, context):
    """
    AWS Lambda handler function
    """
    try:
        # Create a test client for the Flask app
        with app.test_client() as client:
            # Extract the HTTP method and path from the event
            method = event.get('httpMethod', 'POST')
            path = event.get('path', '/predict')
            
            # Get the body from the event
            body = event.get('body', '{}')
            
            # Make the request to the Flask app
            if method == 'POST':
                response = client.post(path, 
                                     data=body, 
                                     content_type='application/json')
            else:
                response = client.get(path)
            
            return {
                'statusCode': response.status_code,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': response.get_data(as_text=True)
            }
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                "status": "error",
                "message": str(e)
            })
        }

if __name__ == "__main__":
    app.run(debug=True)
