import os

class STTEngine:
    def __init__(self, model_name="tiny"):
        """
        Placeholder for Speech-to-Text engine.
        Original Whisper implementation was missing from the environment.
        """
        try:
            import whisper
            print(f"Loading Whisper model '{model_name}'...")
            self.model = whisper.load_model(model_name)
            self.is_placeholder = False
        except ImportError:
            print("WARNING: Whisper library not found. STT will be disabled (placeholder mode).")
            self.model = None
            self.is_placeholder = True
        
    def transcribe(self, audio_file_path: str) -> str:
        """
        Transcribes the given audio file to text.
        """
        if self.is_placeholder:
            return "[STT Disabled: Whisper library not installed]"
            
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
        print(f"Transcribing audio from: {audio_file_path}")
        result = self.model.transcribe(audio_file_path)
        return result["text"].strip()

if __name__ == "__main__":
    stt = STTEngine()
    print(f"STT Mode: {'Placeholder' if stt.is_placeholder else 'Active'}")
