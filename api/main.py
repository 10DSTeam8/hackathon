from flask import Flask, request, jsonify
import json
import logging
from attendance_model import AttendancePredictor

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = Flask(__name__)

# Initialize the attendance predictor
predictor = AttendancePredictor()

@app.route("/predict", methods=["POST"])
def predict():
    """
    POST endpoint that accepts JSON data and predicts patient attendance using TensorFlow model
    Expected input: {"sex": 0|1, "date_of_appointment": "dd/mm/yyyy", "age": XX}
    """
    try:
        # Get JSON data from request
        data = request.get_json(force=False, silent=True)
        
        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Log the incoming request
        logger.info(f"Received prediction request: {json.dumps(data)}")
        
        # Validate required fields
        required_fields = ['sex', 'date_of_appointment', 'age']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "error": f"Missing required fields: {missing_fields}",
                "required_fields": required_fields
            }), 400
        
        # Extract and validate input data
        sex = data['sex']
        date_of_appointment = data['date_of_appointment']
        age = data['age']
        
        # Validate data types and ranges
        if not isinstance(sex, int) or sex not in [0, 1]:
            return jsonify({"error": "sex must be 0 (male) or 1 (female)"}), 400
            
        if not isinstance(date_of_appointment, str):
            return jsonify({"error": "date_of_appointment must be a string in dd/mm/yyyy format"}), 400
            
        # Validate date format
        try:
            from datetime import datetime
            datetime.strptime(date_of_appointment, '%d/%m/%Y')
        except ValueError:
            return jsonify({"error": "date_of_appointment must be in dd/mm/yyyy format"}), 400
            
        if not isinstance(age, int) or not (1 <= age <= 120):
            return jsonify({"error": "age must be a valid age between 1-120 years"}), 400
        
        # Make prediction using TensorFlow model
        result = predictor.predict(sex, date_of_appointment, age)
        
        logger.info(f"Model prediction: {json.dumps(result)}")
        
        # Apply optional multipliers if provided (maintaining compatibility)
        base_prediction = result['will_attend_probability']
        
        if 'bad_weather' in data and data['bad_weather']:
            base_prediction = base_prediction * 0.955

        if 'transport_issues' in data and data['transport_issues']:
            base_prediction = base_prediction * 0.85

        if 'patient_engaged' in data and data['patient_engaged']:
            base_prediction = base_prediction * 1.11
        
        # Ensure probability stays within [0, 1] range
        final_prediction = max(0.0, min(1.0, base_prediction))
        
        return jsonify({
            "status": "success",
            "prediction": final_prediction,
            "will_attend_probability": final_prediction,
            "predicted_attendance": int(final_prediction >= 0.5),
            "confidence": float(max(final_prediction, 1 - final_prediction)),
            "model_details": {
                "input": {
                    "sex": sex,
                    "date_of_appointment": date_of_appointment,
                    "age": age
                }
            }
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
    app.run(debug=True, port=4150)
