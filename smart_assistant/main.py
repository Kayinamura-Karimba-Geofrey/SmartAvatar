import uuid
import os
import time
import asyncio
import shutil
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, File, UploadFile, Request, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

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

# Thread pool for blocking operations
executor = ThreadPoolExecutor(max_workers=4)

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
    return "Index.html not found."


class TextRequest(BaseModel):
    text: str

@app.post("/text")
async def handle_text(request: TextRequest):
    user_input = request.text
    response_text = response_engine.generate_response(user_input)
    return {"input": user_input, "response": response_text}


@app.post("/voice")
async def handle_voice(background_tasks: BackgroundTasks, audio_file: UploadFile = File(...)):
    """
    Accepts an audio file (any format), converts it to WAV,
    transcribes it, generates a response, synthesizes TTS, and returns the audio.
    """
    # Use a unique ID per request to avoid file collisions
    req_id = uuid.uuid4().hex
    temp_raw_path = f"raw_{req_id}{os.path.splitext(audio_file.filename)[1]}"
    temp_wav_path = f"conv_{req_id}.wav"
    output_audio_path = f"response_{req_id}.wav"

    # Read file content immediately in the async context
    audio_bytes = await audio_file.read()

    def process_voice():
        """Blocking pipeline — runs in a thread pool."""
        start_total = time.time()

        # 1. Save raw upload
        with open(temp_raw_path, "wb") as f:
            f.write(audio_bytes)
        print(f"DEBUG [{req_id}]: Save raw took {time.time()-start_total:.2f}s")

        # 2. Convert to .wav (16kHz mono)
        t = time.time()
        convert_to_wav(temp_raw_path, temp_wav_path)
        print(f"DEBUG [{req_id}]: Conversion took {time.time()-t:.2f}s")

        # 3. Transcribe
        t = time.time()
        user_text = stt_engine.transcribe(temp_wav_path)
        print(f"DEBUG [{req_id}]: STT took {time.time()-t:.2f}s → '{user_text}'")

        # 4. Generate response
        t = time.time()
        response_text = response_engine.generate_response(user_text)
        print(f"DEBUG [{req_id}]: Response took {time.time()-t:.2f}s → '{response_text}'")

        # 5. Synthesize TTS
        t = time.time()
        tts_engine.synthesize(response_text, output_audio_path)
        print(f"DEBUG [{req_id}]: TTS took {time.time()-t:.2f}s")

        print(f"DEBUG [{req_id}]: Total = {time.time()-start_total:.2f}s")

        # Cleanup temp input files
        for p in [temp_raw_path, temp_wav_path]:
            if os.path.exists(p):
                os.remove(p)

        return user_text, response_text

    try:
        loop = asyncio.get_event_loop()
        user_text, response_text = await loop.run_in_executor(executor, process_voice)

        # ASCII-safe headers
        safe_user_text = user_text.encode('ascii', errors='replace').decode('ascii')
        safe_response_text = response_text.encode('ascii', errors='replace').decode('ascii')

        headers = {
            "X-Transcribed-Text": safe_user_text,
            "X-Response-Text": safe_response_text,
            "Access-Control-Expose-Headers": "X-Transcribed-Text, X-Response-Text",
        }

        # Schedule output file deletion after the response is sent
        background_tasks.add_task(lambda: os.remove(output_audio_path) if os.path.exists(output_audio_path) else None)

        return FileResponse(
            path=output_audio_path,
            media_type="audio/wav",
            filename="response.wav",
            headers=headers
        )

    except Exception as e:
        print(f"ERROR [{req_id}] in /voice: {e}")
        for p in [temp_raw_path, temp_wav_path, output_audio_path]:
            if os.path.exists(p):
                os.remove(p)
        return JSONResponse(status_code=500, content={"error": str(e)})

# Start server: uvicorn main:app --reload
