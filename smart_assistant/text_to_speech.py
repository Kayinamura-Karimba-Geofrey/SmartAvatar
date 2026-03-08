import os
from TTS.api import TTS

class TTSEngine:
    def __init__(self, model_name="tts_models/en/vctk/vits"):
        """
        Initializes the Text-to-Speech engine using Coqui TTS.
        """
        print(f"Loading Coqui TTS model '{model_name}'...")
        # gpu=False assumes CPU usage by default. Set to True if testing on a GPU-enabled machine.
        self.tts = TTS(model_name=model_name, progress_bar=False, gpu=False)
        
    def synthesize(self, text: str, output_path: str = "output.wav") -> str:
        """
        Converts text to speech and saves it as a WAV file.
        """
        print(f"Synthesizing speech for: '{text}'")
        
        # Check if the model is multi-speaker which requires a speaker ID
        if self.tts.is_multi_speaker:
            # Using the first speaker from the available list arbitrarily
            self.tts.tts_to_file(text=text, file_path=output_path, speaker=self.tts.speakers[0])
        else:
            self.tts.tts_to_file(text=text, file_path=output_path)
            
        return output_path

if __name__ == "__main__":
    # Example usage for testing locally
    tts = TTSEngine()
    # tts.synthesize("Hello, I am your smart assistant.", "response.wav")
