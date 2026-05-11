import os
import sys
import uuid
from dotenv import load_dotenv

# Add the current directory to sys.path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from response_engine import ResponseEngine
from elevenlabs_tts import ElevenLabsTTSEngine

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

def test_workflow():
    print("--- Starting Backend Workflow Validation ---")
    
    # 1. Initialize Engines
    print("\n[Step 1] Initializing Engines...")
    try:
        response_engine = ResponseEngine()
        tts_engine = ElevenLabsTTSEngine()
        print("Engines initialized successfully.")
    except Exception as e:
        print(f"FAILED to initialize engines: {e}")
        return

    # 2. Test AI Response
    print("\n[Step 2] Testing AI Integration (OpenRouter)...")
    test_query = "Hello! Can you tell me a very short joke?"
    try:
        ai_response = response_engine.generate_response(test_query)
        print(f"AI Response received: {ai_response}")
    except Exception as e:
        print(f"FAILED to get AI response: {e}")
        return

    # 3. Test TTS Integration
    print("\n[Step 3] Testing TTS Integration (ElevenLabs)...")
    try:
        shared_dir = os.getenv("SHARED_AUDIO_DIR", "shared_audio")
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        shared_path = os.path.join(root_dir, shared_dir)
        os.makedirs(shared_path, exist_ok=True)
        
        output_filename = f"test_output_{uuid.uuid4().hex[:8]}.wav"
        output_path = os.path.join(shared_path, output_filename)
        
        print(f"Saving audio to: {output_path}")
        tts_engine.synthesize(ai_response, output_path)
        
        if os.path.exists(output_path):
            print(f"SUCCESS: Audio file generated at {output_path}")
            print(f"File size: {os.path.getsize(output_path)} bytes")
        else:
            print(f"FAILED: Audio file was not created.")
    except Exception as e:
        print(f"FAILED during TTS synthesis: {e}")
        return

    print("\n--- Backend Workflow Validation Complete ---")

if __name__ == "__main__":
    test_workflow()
