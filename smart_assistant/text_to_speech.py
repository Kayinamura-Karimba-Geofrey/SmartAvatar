import os
import pyttsx3

class TTSEngine:
    def __init__(self):
        """
        Initializes the Text-to-Speech engine using pyttsx3.
        """
        print("Loading pyttsx3 TTS model...")
        self.engine = pyttsx3.init()
        
    def speak(self, text: str, save_path: str = None):
        """
        Speaks the text out loud directly. Re-initializes for stability.
        """
        engine = pyttsx3.init()
        print(f"Speaking: '{text}'")
        engine.say(text)
        if save_path:
            engine.save_to_file(text, save_path)
        engine.runAndWait()
        engine.stop() # Explicitly stop to free the driver

    def synthesize(self, text: str, output_path: str = "output.wav") -> str:
        """
        Converts text to speech and saves it as a WAV file.
        """
        engine = pyttsx3.init()
        print(f"Synthesizing speech for: '{text}'")
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        engine.stop()
        return output_path

if __name__ == "__main__":
    # Example usage for testing locally
    tts = TTSEngine()
    # tts.synthesize("Hello, I am your smart assistant.", "response.wav")
