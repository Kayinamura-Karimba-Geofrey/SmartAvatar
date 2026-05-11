import os
import time

class STTEnginePlaceholder:
    def __init__(self, model_name="tiny"):
        print("STT Engine (Fallback) ready. Real Whisper model is not loaded yet.")
        
    def transcribe(self, audio_file_path: str) -> str:
        print(f"Fallback transcription for: {audio_file_path}")
        return "This is a placeholder transcription (STT currently in fallback mode)."

class TTSEnginePlaceholder:
    def __init__(self):
        print("TTS Engine (Fallback) ready.")

    def synthesize(self, text: str, output_path: str = "output.wav") -> str:
        print(f"Fallback synthesis for: '{text}'")
        # In a real scenario, we might want to return a silent or pre-recorded wav
        # For now, let's just pretend we saved it.
        # But script.js expects a file it can play.
        # I'll create an empty wav file if possible, or just skip.
        with open(output_path, "wb") as f:
            # Minimal WAV header for a silent file
            f.write(b'RIFF$ \x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00')
        return output_path
