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

## Testing the API

Use `curl` to test the endpoint with sample images:

```bash
curl -X POST "http://127.0.0.1:8000/extract-aadhaar" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "front_image=@/path/to/your/front_image.jpg" \
     -F "back_image=@/path/to/your/back_image.jpg"
```

## Cloud Deployment
Since this is a standard FastAPI app with a `requirements.txt`, you can deploy it easily using Docker, AWS Elastic Beanstalk, GCP Cloud Run, or any platform that runs Python applications.
