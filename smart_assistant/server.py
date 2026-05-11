import os
import uuid
import shutil
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from dotenv import load_dotenv

# Import our engines
from response_engine import ResponseEngine
from elevenlabs_tts import ElevenLabsTTSEngine
from speech_to_text import STTEngine
from utils import convert_to_wav # If we have this for voice processing

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

app = Flask(__name__, static_folder='static')
CORS(app) # Enable CORS for all routes

# Configuration
SHARED_AUDIO_DIR = os.getenv("SHARED_AUDIO_DIR", "shared_audio")
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED_AUDIO_PATH = os.path.join(ROOT_DIR, SHARED_AUDIO_DIR)
os.makedirs(SHARED_AUDIO_PATH, exist_ok=True)

# Initialize engines
response_engine = ResponseEngine()
tts_engine = ElevenLabsTTSEngine()
stt_engine = STTEngine()

@app.route('/')
def index():
    """Serve the web UI."""
    return send_from_directory('static', 'index.html')

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "status": "online",
        "message": "SmartAvatar Backend is running",
        "shared_audio_dir": SHARED_AUDIO_DIR
    })

@app.route('/text', methods=['POST'])
@app.route('/chat', methods=['POST']) # Support both aliases
def text_chat():
    """
    Text-based chat endpoint.
    Matches frontend expectations from script.js.
    """
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided"}), 400

    user_text = data['text']
    try:
        ai_response = response_engine.generate_response(user_text)
        
        # Optional: Generate audio for the shared directory (for Unreal)
        audio_filename = f"chat_{uuid.uuid4().hex[:8]}.wav"
        audio_full_path = os.path.join(SHARED_AUDIO_PATH, audio_filename)
        
        # We don't necessarily need to call TTS here if the web UI uses browser TTS,
        # but for Unreal Engine integration, we SHOULD generate it.
        try:
            tts_engine.synthesize(ai_response, audio_full_path)
        except Exception as tts_err:
            print(f"Non-critical TTS error: {tts_err}")

        return jsonify({
            "response": ai_response,
            "audio_file": audio_filename
        })
    except Exception as e:
        print(f"Error in text chat: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/voice', methods=['POST'])
def voice_chat():
    """
    Full voice pipeline for the Web UI:
    1. Receive audio blob
    2. Transcribe (STT)
    3. Generate AI Response
    4. Synthesize Audio (TTS)
    5. Return audio file with metadata headers
    """
    if 'audio_file' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    audio_file = request.files['audio_file']
    req_id = uuid.uuid4().hex
    temp_raw = f"temp_{req_id}_raw"
    temp_wav = f"temp_{req_id}.wav"
    output_wav = f"response_{req_id}.wav"
    output_full_path = os.path.join(SHARED_AUDIO_PATH, output_wav)

    try:
        # 1. Save raw audio
        audio_file.save(temp_raw)
        
        # 2. Convert to WAV (Whisper needs 16kHz mono usually, but whisper library handles many)
        # We'll use a simple copy if conversion util is missing or failed
        try:
            convert_to_wav(temp_raw, temp_wav)
        except:
            shutil.copy(temp_raw, temp_wav)

        # 3. Transcribe
        user_text = stt_engine.transcribe(temp_wav)
        print(f"Transcribed: {user_text}")

        # 4. AI Response
        ai_response = response_engine.generate_response(user_text)
        print(f"AI: {ai_response}")

        # 5. TTS
        tts_engine.synthesize(ai_response, output_full_path)

        # 6. Prepare response with headers (as expected by script.js)
        with open(output_full_path, 'rb') as f:
            audio_data = f.read()

        response = Response(audio_data, mimetype='audio/wav')
        response.headers['X-Transcribed-Text'] = user_text.encode('ascii', 'ignore').decode('ascii')
        response.headers['X-Response-Text'] = ai_response.encode('ascii', 'ignore').decode('ascii')
        response.headers['Access-Control-Expose-Headers'] = 'X-Transcribed-Text, X-Response-Text'
        
        return response

    except Exception as e:
        print(f"Error in voice pipeline: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        # Cleanup temp files
        for p in [temp_raw, temp_wav]:
            if os.path.exists(p):
                os.remove(p)

@app.route('/audio/<filename>')
def get_audio(filename):
    return send_from_directory(SHARED_AUDIO_PATH, filename)

@app.route('/reset', methods=['POST'])
def reset():
    response_engine.reset_conversation()
    return jsonify({"status": "success", "message": "Conversation reset"})

if __name__ == '__main__':
    print(f"Starting SmartAvatar Flask Server...")
    app.run(host='0.0.0.0', port=5000, debug=False)
