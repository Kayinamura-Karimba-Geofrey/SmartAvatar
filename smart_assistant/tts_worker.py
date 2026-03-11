"""
Standalone TTS worker script.
Invoked via subprocess by TTSEngine so it runs isolated from FastAPI's async loop.
Usage: python tts_worker.py "text to say" output_path.wav
"""
import sys
import pyttsx3

def run_tts(text: str, output_path: str):
    engine = pyttsx3.init()
    engine.setProperty('rate', 175)
    engine.save_to_file(text, output_path)
    engine.runAndWait()
    engine.stop()

if __name__ == "__main__":
    text = sys.argv[1]
    output_path = sys.argv[2]
    run_tts(text, output_path)
