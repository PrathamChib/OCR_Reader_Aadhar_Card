# Aadhaar OCR API

A production-ready open source API to extract details from an Indian Aadhaar card using the Gemini 1.5 Flash model and FastAPI.

## Structure
```
aadhaar_api/
├── main.py
├── requirements.txt
├── README.md
```

## Setup and Run Locally

1. **Install dependencies:**
Open your terminal in this directory and run:
```bash
pip install -r requirements.txt
```

2. **Start the API server:**
```bash
uvicorn main:app --reload
```
The server will be running on `http://127.0.0.1:8000`.

*Note: The script currently defaults to your provided API key. If you want to change it, set the `GEMINI_API_KEY` environment variable before running the server:*
```bash
export GEMINI_API_KEY="your_api_key"
uvicorn main:app --reload
```

## Testing the API (Base64 Input)

This endpoint now accepts JSON with Base64 image strings (plain Base64 or `data:image/...;base64,...` format).

1. Convert your images to Base64 (macOS example):

```bash
FRONT_B64=$(base64 -i /path/to/your/front_image.jpg)
BACK_B64=$(base64 -i /path/to/your/back_image.jpg)
```

2. Call the API:

```bash
curl -X POST "http://127.0.0.1:8000/extract-aadhaar" \
     -H "accept: application/json" \
     -H "Content-Type: application/json" \
     -d "{
       \"front_image_base64\": \"${FRONT_B64}\",
       \"back_image_base64\": \"${BACK_B64}\"
     }"
```

### Input format

```json
{
  "front_image_base64": "<base64-string-or-data-url>",
  "back_image_base64": "<base64-string-or-data-url>"
}
```

### Response format

```json
{
  "name": "string",
  "dob": "DD/MM/YYYY or empty string",
  "gender": "Male/Female/Transgender or empty string",
  "aadhaar_number": "12 digit string or empty string",
  "address": "string"
}
```

### Resource limits

- Each decoded image is limited to 8MB.
- Images are resized to at most 1024x1024 before OCR to keep memory usage low on 512MB Render instances.

## Cloud Deployment
Since this is a standard FastAPI app with a `requirements.txt`, you can deploy it easily using Docker, AWS Elastic Beanstalk, GCP Cloud Run, or any platform that runs Python applications.
