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

try:
    from speech_to_text import STTEngine
    from text_to_speech import TTSEngine
except ImportError:
    from fallbacks import STTEnginePlaceholder as STTEngine
    from fallbacks import TTSEnginePlaceholder as TTSEngine

from response_engine import ResponseEngine

try:
    from utils import convert_to_wav
except ImportError:
    def convert_to_wav(i, o): shutil.copy(i, o)

app = FastAPI(
    title="SmartAvatar API",
    description="A voice-and-text AI assistant powered by OpenRouter (LLM), Whisper (STT), and pyttsx3 (TTS).",
    version="2.0.0",
)

# ─── Engine Initialization ────────────────────────────────────────────────────
print("Starting SmartAvatar API...")

stt_engine      = STTEngine()
tts_engine      = TTSEngine()
response_engine = ResponseEngine()

# Thread pool for blocking I/O operations
executor = ThreadPoolExecutor(max_workers=4)

# ─── Static Files ─────────────────────────────────────────────────────────────
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def get_index():
    """Serve the SmartAvatar web UI."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse("<h2>SmartAvatar is running. Place your index.html in the static/ folder.</h2>")


class TextRequest(BaseModel):
    text: str


@app.post("/text", tags=["Chat"])
async def handle_text(request: TextRequest):
    """
    Text-based chat endpoint.
    Sends user text to the LLM and returns the assistant's reply.
    """
    user_input   = request.text
    response_text = response_engine.generate_response(user_input)
    return {"input": user_input, "response": response_text}


@app.post("/voice", tags=["Voice"])
async def handle_voice(background_tasks: BackgroundTasks, audio_file: UploadFile = File(...)):
    """
    Full voice pipeline:
      1. Receive uploaded audio (any format)
      2. Convert to 16kHz mono WAV (Whisper-compatible)
      3. Transcribe with Whisper (STT)
      4. Generate AI response via OpenRouter (LLM)
      5. Synthesize reply to WAV (TTS)
      6. Return audio file + transcription headers
    """
    req_id          = uuid.uuid4().hex
    ext             = os.path.splitext(audio_file.filename or "audio.webm")[1] or ".webm"
    temp_raw_path   = f"raw_{req_id}{ext}"
    temp_wav_path   = f"conv_{req_id}.wav"
    output_audio_path = f"response_{req_id}.wav"

    # Read bytes immediately in async context
    audio_bytes = await audio_file.read()

    def process_voice():
        """Full blocking voice pipeline — executed in a thread pool."""
        start_total = time.time()

        # 1. Save raw upload
        with open(temp_raw_path, "wb") as f:
            f.write(audio_bytes)
        print(f"[{req_id}] Saved raw upload ({len(audio_bytes)} bytes) in {time.time()-start_total:.2f}s")

        # 2. Convert to WAV
        t = time.time()
        convert_to_wav(temp_raw_path, temp_wav_path)
        print(f"[{req_id}] Audio conversion took {time.time()-t:.2f}s")

        # 3. Transcribe with Whisper
        t = time.time()
        user_text = stt_engine.transcribe(temp_wav_path)
        print(f"[{req_id}] STT ({time.time()-t:.2f}s): '{user_text}'")

        # 4. Generate LLM response
        t = time.time()
        response_text = response_engine.generate_response(user_text)
        print(f"[{req_id}] LLM ({time.time()-t:.2f}s): '{response_text}'")

        # 5. Synthesize TTS
        t = time.time()
        tts_engine.synthesize(response_text, output_audio_path)
        print(f"[{req_id}] TTS took {time.time()-t:.2f}s")

        print(f"[{req_id}] Total pipeline: {time.time()-start_total:.2f}s")

        # Cleanup temp input files
        for p in [temp_raw_path, temp_wav_path]:
            if os.path.exists(p):
                os.remove(p)

        return user_text, response_text

    try:
        loop = asyncio.get_event_loop()
        user_text, response_text = await loop.run_in_executor(executor, process_voice)

        # Sanitize headers (ASCII only)
        safe_user_text     = user_text.encode("ascii", errors="replace").decode("ascii")
        safe_response_text = response_text.encode("ascii", errors="replace").decode("ascii")

        headers = {
            "X-Transcribed-Text": safe_user_text,
            "X-Response-Text":    safe_response_text,
            "Access-Control-Expose-Headers": "X-Transcribed-Text, X-Response-Text",
        }

        # Delete the response audio after it's been sent
        background_tasks.add_task(
            lambda: os.remove(output_audio_path) if os.path.exists(output_audio_path) else None
        )

        return FileResponse(
            path=output_audio_path,
            media_type="audio/wav",
            filename="response.wav",
            headers=headers,
        )

    except Exception as e:
        print(f"[ERROR {req_id}] /voice pipeline failed: {e}")
        for p in [temp_raw_path, temp_wav_path, output_audio_path]:
            if os.path.exists(p):
                os.remove(p)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/reset", tags=["Chat"])
async def reset_conversation():
    """Clears the LLM conversation history for a fresh session."""
    response_engine.reset_conversation()
    return {"status": "ok", "message": "Conversation history cleared."}


@app.get("/health", tags=["System"])
async def health_check():
    """Returns the current status of all engines."""
    return {
        "status":     "ok",
        "stt_engine": stt_engine.__class__.__name__,
        "tts_engine": tts_engine.__class__.__name__,
        "llm_model":  response_engine.model,
    }

# Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000
