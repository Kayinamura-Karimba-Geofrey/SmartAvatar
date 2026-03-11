import os
import pyttsx3

class TTSEngine:
    def __init__(self):
        """
        Initializes the Text-to-Speech engine using pyttsx3.
        """
        print("Loading pyttsx3 TTS model...")
        self.engine = pyttsx3.init()
        # Set speaking rate (optional speed up)
        self.engine.setProperty('rate', 175) 
        
    def speak(self, text: str, save_path: str = None):
        """
        Speaks the text out loud directly.
        """
        print(f"Speaking: '{text}'")
        self.engine.say(text)
        if save_path:
            self.engine.save_to_file(text, save_path)
        self.engine.runAndWait()

    def synthesize(self, text: str, output_path: str = "output.wav") -> str:
        """
        Converts text to speech and saves it as a WAV file.
        """
        print(f"Synthesizing speech for: '{text}'")
        self.engine.save_to_file(text, output_path)
        self.engine.runAndWait()
        return output_path

if __name__ == "__main__":
    # Example usage for testing locally
    tts = TTSEngine()
    # tts.synthesize("Hello, I am your smart assistant.", "response.wav")
