from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import shutil
import os

from speech_to_text import STTEngine
from text_to_speech import TTSEngine
from response_engine import ResponseEngine
from utils import convert_to_wav

app = FastAPI(
    title="Smart Conversational Assistant API",
    description="An API supporting Voice and Text interaction"
)

# Initialize engines
print("Starting up the FastAPI application...")
stt_engine = STTEngine()
tts_engine = TTSEngine()
response_engine = ResponseEngine()

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Index.html not found. Please wait while I create it."


class TextRequest(BaseModel):
    text: str

@app.post("/text")
async def handle_text(request: TextRequest):
    """
    Accepts text input and returns a text response.
    """
    user_input = request.text
    response_text = response_engine.generate_response(user_input)
    
    return {
        "input": user_input,
        "response": response_text
    }

@app.post("/voice")
async def handle_voice(audio_file: UploadFile = File(...)):
    """
    Accepts an audio file, converts it to text, generates a text response, 
    and synthesizes the response into an audio file.
    """
    temp_raw_path = f"raw_{audio_file.filename}"
    temp_wav_path = f"conv_{os.path.splitext(audio_file.filename)[0]}.wav"
    output_audio_path = f"response_{os.path.splitext(audio_file.filename)[0]}.wav"
    
    try:
        # 1. Save uploaded file temporarily to disk
        with open(temp_raw_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
            
        # 1.5 Convert uploaded audio to .wav
        convert_to_wav(temp_raw_path, temp_wav_path)

        # 2. Convert Audio to Text (STT)
        user_text = stt_engine.transcribe(temp_wav_path)
        
        # 3. Generate Response
        response_text = response_engine.generate_response(user_text)
        
        # 4. Convert Response to Audio (TTS)
        tts_engine.synthesize(response_text, output_audio_path)
        
        # Clean up input temporary files
        if os.path.exists(temp_raw_path):
            os.remove(temp_raw_path)
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)
        
        # Return both text and the generated audio file
        # The synthesized audio file is returned as a FileResponse, and we can 
        # add the textual conversation pieces via custom headers.
        headers = {
            "X-Transcribed-Text": user_text,
            "X-Response-Text": response_text
        }
        
        return FileResponse(
            path=output_audio_path, 
            media_type="audio/wav", 
            filename="response.wav",
            headers=headers
        )
        
    except Exception as e:
        if os.path.exists(temp_raw_path):
            os.remove(temp_raw_path)
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)
        return JSONResponse(status_code=500, content={"error": str(e)})

# Start server: uvicorn main:app --reload
