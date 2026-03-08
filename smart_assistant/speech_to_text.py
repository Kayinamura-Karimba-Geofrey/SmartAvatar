import whisper
import os

class STTEngine:
    def __init__(self, model_name="base"):
        """
        Initializes the Speech-to-Text engine using OpenAI's Whisper model.
        Available models: tiny, base, small, medium, large.
        """
        print(f"Loading Whisper model '{model_name}'...")
        self.model = whisper.load_model(model_name)
        
    def transcribe(self, audio_file_path: str) -> str:
        """
        Transcribes the given audio file to text.
        """
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
        print(f"Transcribing audio from: {audio_file_path}")
        result = self.model.transcribe(audio_file_path)
        return result["text"].strip()

if __name__ == "__main__":
    # Example usage for testing locally
    stt = STTEngine()
    # Create a dummy audio file first or provide a real path to test
    # text = stt.transcribe("sample_audio.wav")
    # print(f"Transcribed Text: {text}")
