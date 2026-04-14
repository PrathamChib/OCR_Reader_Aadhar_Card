import os
import json
import io
import base64
import binascii
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import google.generativeai as genai
from PIL import Image

app = FastAPI(
    title="Aadhaar OCR API",
    description="API to extract structured information from Indian Aadhaar cards using Gemini 1.5 Flash",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure the API key correctly relies on Environment Variables ONLY for security
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("Warning: GEMINI_API_KEY is not set.")

# Initialize the Gemini model
model = genai.GenerativeModel("gemini-flash-latest")

class AadhaarData(BaseModel):
    name: str = Field(default="")
    dob: str = Field(default="")
    gender: str = Field(default="")
    aadhaar_number: str = Field(default="")
    address: str = Field(default="")

class AadhaarBase64Request(BaseModel):
    front_image_base64: str = Field(..., min_length=20)
    back_image_base64: str = Field(..., min_length=20)

def parse_json_response(text: str) -> dict:
    """Parses the JSON response from Gemini, handling potential markdown."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}

def format_data(data: dict) -> dict:
    """Formats and cleans up the extracted data."""
    # Ensure Aadhaar is strictly digits, length checked
    aadhaar_num = data.get("aadhaar_number", "")
    clean_aadhaar = "".join(filter(str.isdigit, str(aadhaar_num)))
    if len(clean_aadhaar) == 12:
        data["aadhaar_number"] = clean_aadhaar
    else:
        data["aadhaar_number"] = ""
        
    # Ensure DOB is formatted if possible
    dob = str(data.get("dob", "")).replace("-", "/").replace(".", "/")
    data["dob"] = dob
    
    return data

MAX_IMAGE_BYTES = 8 * 1024 * 1024  # 8MB max per image payload
MAX_IMAGE_DIMENSION = (1024, 1024)

def _strip_data_url_prefix(image_base64: str) -> str:
    """Supports plain base64 and data URL formats."""
    if "," in image_base64 and image_base64.lower().startswith("data:image"):
        return image_base64.split(",", 1)[1]
    return image_base64

def decode_base64_to_image(image_base64: str, label: str) -> Image.Image:
    """Decodes base64 into a PIL image with validation and memory constraints."""
    cleaned = _strip_data_url_prefix(image_base64.strip())

    try:
        image_bytes = base64.b64decode(cleaned, validate=True)
    except binascii.Error as exc:
        raise HTTPException(status_code=400, detail=f"{label} is not valid base64.") from exc

    if not image_bytes:
        raise HTTPException(status_code=400, detail=f"{label} is empty after decoding.")

    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"{label} exceeds {MAX_IMAGE_BYTES // (1024 * 1024)}MB limit."
        )

    try:
        image = Image.open(io.BytesIO(image_bytes))
        image = image.convert("RGB")
        image.thumbnail(MAX_IMAGE_DIMENSION)
        return image
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"{label} is not a valid image.") from exc

@app.post("/extract-aadhaar", response_model=AadhaarData)
async def extract_aadhaar(payload: AadhaarBase64Request):
    try:
        # Decode base64 payload into compressed PIL images for low-memory OCR on Render.
        front_pil = decode_base64_to_image(payload.front_image_base64, "front_image_base64")
        back_pil = decode_base64_to_image(payload.back_image_base64, "back_image_base64")

        # Prompt specifying the task and expected strict JSON output
        prompt = """
        You are an expert OCR AI that extracts structured data from Indian Aadhaar cards.
        I am giving you two images: the front side and the back side of an Aadhaar card.
        
        Please read both Aadhaar images, extract text, identify the correct fields, and return strict JSON format.
        Do not add any markdown, explanation or text outside the JSON block.

        Expected JSON format:
        {
          "name": "<extracted full name>",
          "dob": "<extracted date of birth in DD/MM/YYYY format>",
          "gender": "<extracted gender: Male, Female, or Transgender>",
          "aadhaar_number": "<extracted 12-digit Aadhaar number as a continuous string without spaces>",
          "address": "<extracted full address from the back side>"
        }
        
        If a field cannot be found, leave it as an empty string ("").
        """

        # Call Gemini model
        response = model.generate_content([prompt, front_pil, back_pil])
        
        if not response.text:
            raise ValueError("No text generated by the model.")

        # Parse and format the data
        parsed_data = parse_json_response(response.text)
        formatted_data = format_data(parsed_data)

        # Validate with Pydantic
        result = AadhaarData(**formatted_data)
        
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
