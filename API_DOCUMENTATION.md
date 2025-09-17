# Flask API Documentation - Patient Attendance Prediction

This documentation provides instructions for running and using the Flask API for patient attendance prediction locally.

## Quick Setup

### Prerequisites
- Python 3.11
- pip (Python package installer)
- pipenv (recommended) or pip with virtual environment

### Installation

1. **Navigate to the API directory:**
   ```bash
   cd api
   ```

2. **Install dependencies using pipenv (recommended):**
   ```bash
   pip install pipenv
   pipenv install
   pipenv shell
   ```

   **Or using pip with virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install flask tensorflow pandas numpy scikit-learn joblib boto3
   ```

3. **Run the Flask API locally:**
   ```bash
   python main.py
   ```

   The API will start on `http://localhost:4150` with debug mode enabled.

## API Endpoints

### POST /predict

Predicts patient attendance probability based on patient demographics and appointment details.

**URL:** `http://localhost:4150/predict`
**Method:** `POST`  
**Content-Type:** `application/json`

#### Required Parameters

| Parameter | Type | Description | Valid Values |
|-----------|------|-------------|--------------|
| `sex` | integer | Patient gender | `0` (male) or `1` (female) |
| `date_of_appointment` | string | Appointment date | Format: `dd/mm/yyyy` |
| `age` | integer | Patient age | Range: 1-120 years |

#### Optional Parameters

| Parameter | Type | Description | Effect |
|-----------|------|-------------|--------|
| `bad_weather` | boolean | Weather conditions | Reduces probability by 4.5% |
| `transport_issues` | boolean | Transportation problems | Reduces probability by 15% |
| `patient_engaged` | boolean | Patient engagement level | Increases probability by 11% |

#### Request Examples

**Basic Request:**
```bash
curl -X POST http://localhost:4150/predict \
  -H "Content-Type: application/json" \
  -d '{
    "sex": 1,
    "date_of_appointment": "15/09/2024",
    "age": 40
  }'
```

**Request with Optional Parameters:**
```bash
curl -X POST http://localhost:4150/predict \
  -H "Content-Type: application/json" \
  -d '{
    "sex": 0,
    "date_of_appointment": "20/09/2024",
    "age": 35,
    "bad_weather": false,
    "transport_issues": false,
    "patient_engaged": true
  }'
```

**Using Python requests:**
```python
import requests
import json

# Basic prediction
data = {
    "sex": 1,
    "date_of_appointment": "21/09/2024",
    "age": 30
}

response = requests.post(
    'http://localhost:4150/predict',
    headers={'Content-Type': 'application/json'},
    data=json.dumps(data)
)

result = response.json()
print(f"Attendance probability: {result['will_attend_probability']:.1%}")
```

#### Response Format

**Success Response (200):**
```json
{
    "status": "success",
    "prediction": 0.75,
    "will_attend_probability": 0.75,
    "predicted_attendance": 1,
    "confidence": 0.75,
    "model_details": {
        "input": {
            "sex": 1,
            "date_of_appointment": "15/09/2024",
            "age": 40
        }
    }
}
```

**Error Response (400/500):**
```json
{
    "error": "Missing required fields: ['age']",
    "required_fields": ["sex", "date_of_appointment", "age"]
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Request status: "success" or "error" |
| `prediction` | float | Probability of attendance (0.0 - 1.0) |
| `will_attend_probability` | float | Same as prediction |
| `predicted_attendance` | integer | Binary prediction: 1 (will attend) or 0 (won't attend) |
| `confidence` | float | Model confidence level (0.0 - 1.0) |
| `model_details` | object | Input parameters used for prediction |

## Testing the API

### Using the Test Script

Run the included test script to verify the model works:

```bash
python test_prediction.py
```

### Manual Testing Examples

**Test Case 1: Female, 40 years old, Sunday appointment**
```bash
curl -X POST http://localhost:4150/predict \
  -H "Content-Type: application/json" \
  -d '{"sex": 1, "date_of_appointment": "15/09/2024", "age": 40}'
```

**Test Case 2: Male, 35 years old, Monday appointment**
```bash
curl -X POST http://localhost:4150/predict \
  -H "Content-Type: application/json" \
  -d '{"sex": 0, "date_of_appointment": "16/09/2024", "age": 35}'
```

**Test Case 3: Female with transport issues**
```bash
curl -X POST http://localhost:4150/predict \
  -H "Content-Type: application/json" \
  -d '{
    "sex": 1,
    "date_of_appointment": "18/09/2024",
    "age": 25,
    "transport_issues": true
  }'
```

## Error Handling

### Common Errors

**Missing JSON data:**
```json
{
    "error": "No JSON data provided"
}
```

**Invalid sex value:**
```json
{
    "error": "sex must be 0 (male) or 1 (female)"
}
```

**Invalid date format:**
```json
{
    "error": "date_of_appointment must be in dd/mm/yyyy format"
}
```

**Invalid age:**
```json
{
    "error": "age must be a valid age between 1-120 years"
}
```

## Troubleshooting

### API Won't Start
- Ensure Python 3.11 is installed
- Check all dependencies are installed: `pipenv install` or `pip install -r requirements.txt`
- Verify you're in the correct directory (`api/`)

### Model Loading Errors
- Ensure the trained model files are present in the `api/` directory
- Check that TensorFlow is properly installed

### HTTP 500 Errors
- Check the console output for detailed error messages
- Ensure all required model files are accessible
- Verify input data types match the expected format

### Connection Issues
- Confirm the API is running on `http://localhost:4150`
- Check firewall settings if accessing from another machine
- Ensure the Flask app started successfully (look for "Running on http://127.0.0.1:4150")

## Production Notes

- This documentation is for local development only
- For production deployment, consider using a WSGI server like Gunicorn
- The API also includes AWS Lambda support via the `lambda_handler` function
- Disable debug mode in production by setting `app.run(debug=False)`