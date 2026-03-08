from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import shutil
import os

from speech_to_text import STTEngine
from text_to_speech import TTSEngine
from response_engine import ResponseEngine

app = FastAPI(
    title="Smart Conversational Assistant API",
    description="An API supporting Voice and Text interaction"
)

# Initialize engines. This is done globally so models stay loaded in memory.
# Note: Loading Whisper and Coqui TTS will take a few moments upon server startup.
print("Starting up the FastAPI application...")
stt_engine = STTEngine()
tts_engine = TTSEngine()
response_engine = ResponseEngine()

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
    temp_input_path = f"temp_{audio_file.filename}"
    output_audio_path = f"response_{audio_file.filename}"
    
    try:
        # 1. Save uploaded file temporarily to disk
        with open(temp_input_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
            
        # 2. Convert Audio to Text (STT)
        user_text = stt_engine.transcribe(temp_input_path)
        
        # 3. Generate Response
        response_text = response_engine.generate_response(user_text)
        
        # 4. Convert Response to Audio (TTS)
        tts_engine.synthesize(response_text, output_audio_path)
        
        # Clean up input temporary file
        os.remove(temp_input_path)
        
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
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        return JSONResponse(status_code=500, content={"error": str(e)})

# Start server: uvicorn main:app --reload
