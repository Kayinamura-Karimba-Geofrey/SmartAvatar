import os
import subprocess
import sys


class TTSEngine:
    def __init__(self):
        """
        Initializes the Text-to-Speech engine.
        pyttsx3 is run in a subprocess to avoid deadlocking FastAPI's async event loop.
        """
        print("TTS Engine ready (subprocess mode).")
        # Path to the isolated worker script
        self._worker_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tts_worker.py")

    def speak(self, text: str, save_path: str = None):
        """
        Speaks the text by delegating to the worker script.
        If save_path is given, audio is also saved there.
        """
        self.synthesize(text, save_path or "speak_output.wav")

    def synthesize(self, text: str, output_path: str = "output.wav") -> str:
        """
        Converts text to speech and saves it as a WAV file via a subprocess.
        This avoids pyttsx3's runAndWait() from blocking FastAPI's event loop.
        """
        print(f"Synthesizing speech for: '{text}'")
        result = subprocess.run(
            [sys.executable, self._worker_script, text, output_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            print(f"TTS Worker stderr: {result.stderr}")
            raise RuntimeError(f"TTS subprocess failed: {result.stderr}")
        return output_path


if __name__ == "__main__":
    # Example usage for testing locally
    tts = TTSEngine()
    tts.synthesize("Hello, I am your smart assistant.", "response.wav")
    print("Done. Check response.wav")
