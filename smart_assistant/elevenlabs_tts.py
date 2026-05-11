import os
import wave
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

# Load environment variables from the .env file at project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

class ElevenLabsTTSEngine:
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key or self.api_key == "your_elevenlabs_api_key_here":
            print("WARNING: ELEVENLABS_API_KEY is not set or is still a placeholder.")
        
        self.client = ElevenLabs(api_key=self.api_key)
        # Standard voice ID (Rachel is '21m00Tcm4TlvDq8ikWAM')
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM") 
        
    def synthesize(self, text: str, output_path: str) -> str:
        """
        Converts text to speech using ElevenLabs API and saves it as a WAV file.
        """
        print(f"ElevenLabs synthesizing: '{text[:50]}...'")
        
        try:
            # Generate audio as raw PCM
            audio_generator = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id="eleven_multilingual_v2",
                output_format="pcm_44100" 
            )
            
            # Collect the bytes
            audio_data = b"".join(audio_generator)
            
            # Write to a WAV file with headers
            with wave.open(output_path, "wb") as wav_file:
                wav_file.setnchannels(1)      # Mono
                wav_file.setsampwidth(2)      # 16-bit (2 bytes)
                wav_file.setframerate(44100)  # Match requested sample rate
                wav_file.writeframes(audio_data)
            
            print(f"WAV Audio saved to: {output_path}")
            return output_path
        except Exception as e:
            print(f"Error in ElevenLabs synthesis: {e}")
            # Fallback to mp3 if PCM fails (some accounts don't support PCM)
            try:
                print("Attempting fallback to MP3...")
                audio_generator = self.client.text_to_speech.convert(
                    text=text,
                    voice_id=self.voice_id,
                    model_id="eleven_multilingual_v2",
                    output_format="mp3_44100_128"
                )
                mp3_path = output_path.replace(".wav", ".mp3")
                with open(mp3_path, "wb") as f:
                    for chunk in audio_generator:
                        f.write(chunk)
                print(f"MP3 Fallback saved to: {mp3_path}")
                return mp3_path
            except Exception as fallback_error:
                print(f"Fallback also failed: {fallback_error}")
                raise e

if __name__ == "__main__":
    # Test
    tts = ElevenLabsTTSEngine()
    try:
        tts.synthesize("Hello, this is a test of the WAV output with ElevenLabs.", "test_elevenlabs.wav")
    except Exception as e:
        print(f"Test failed: {e}")
