import os
import json
from PIL import Image
from openai import OpenAI
from google import genai
from google.genai import types
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables (API Keys) from .env file
load_dotenv()

# Initialize API Clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def transcribe_audio(audio_path: str) -> str:
    """
    Takes an audio file path (Urdu/Roman Urdu voice note), 
    sends it to OpenAI Whisper, and returns the English translation.
    """
    try:
        with open(audio_path, "rb") as audio_file:
            response = openai_client.audio.translations.create(
                model="whisper-1", 
                file=audio_file
            )
        return response.text
    except Exception as e:
        logger.error(f"Error in audio transcription: {e}")
        return "Audio could not be transcribed."

def analyze_civic_issue(image_path: str, text_description: str) -> dict:
    """
    Takes a local image path and translated text, opens via PIL, 
    sends to Gemini Vision (gemini-3.6-flash), and forces a strict JSON output matching our SQLite schema.
    """
    try:
        # Prompt as per Project Description specifications
        prompt = f"""
        You are an expert civic issue triage AI. 
        Analyze the provided image and the citizen's description: "{text_description}".
        
        Categorize the issue into strictly one of these 3 categories: "Garbage", "Pothole", or "Sewerage".
        If it's not a valid civic issue (e.g., a selfie, a random object), set is_valid_civic_issue to false.
        
        You must return ONLY a JSON object with this exact schema:
        {{
            "is_valid_civic_issue": boolean,
            "category": "Garbage" | "Pothole" | "Sewerage" | "Other",
            "severity": "Critical" | "High" | "Medium" | "Low",
            "reasoning": "string explaining your decision briefly",
            "recommended_action": "string suggesting the repair crew/tools needed"
        }}
        """

        # Open local image using PIL to avoid file URI/remote path issues
        pil_image = None
        if image_path and os.path.exists(image_path):
            pil_image = Image.open(image_path)
        else:
            raise FileNotFoundError(f"Image not found at path: {image_path}")

        # Using Gemini to analyze PIL image and text with JSON schema enforcement
        response = gemini_client.models.generate_content(
            model='gemini-3.6-flash',
            contents=[
                pil_image, 
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        
        # Parse the JSON string returned by Gemini into a Python dictionary
        return json.loads(response.text)
        
    except Exception as e:
        logger.error(f"Error in multimodal analysis: {e}")
        return {
            "is_valid_civic_issue": False,
            "category": "Other",
            "severity": "Low",
            "reasoning": f"AI Processing Error: {str(e)}",
            "recommended_action": "Manual review required."
        }

# --- For Local Testing Only ---
if __name__ == "__main__":
    print("AI Engine is ready for integration!")