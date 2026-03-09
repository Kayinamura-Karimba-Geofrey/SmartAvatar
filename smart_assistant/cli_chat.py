import argparse
import os
import platform

from response_engine import ResponseEngine

def main():
    parser = argparse.ArgumentParser(description="CLI for Smart Conversational Assistant")
    parser.add_argument("--mode", choices=["text", "voice"], default="text", help="Interaction mode: `text` or `voice`")
    parser.add_argument("--audio", type=str, help="Path to input audio file (required if mode is voice)")
    
    args = parser.parse_args()
    
    print("="*50)
    print("Initializing components...")
    response_engine = ResponseEngine()
    
    if args.mode == "text":
        print("="*50)
        print("Interactive Text Mode Started. Type 'exit' or 'quit' to stop.")
        while True:
            try:
                user_input = input("\nYou: ")
                if user_input.lower() in ["exit", "quit", "q"]:
                    print("Goodbye!")
                    break
                    
                response = response_engine.generate_response(user_input)
                print(f"Assistant: {response}")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
                
    elif args.mode == "voice":
        if not args.audio:
            print("Error: --audio argument is required when in voice mode.")
            return
            
        if not os.path.exists(args.audio):
            print(f"Error: Audio file '{args.audio}' not found.")
            return
            
        print("Loading heavy ML audio models...")
        from speech_to_text import STTEngine
        from text_to_speech import TTSEngine
        stt_engine = STTEngine()
        tts_engine = TTSEngine()
        
        print("="*50)
        print(f"Processing audio file: {args.audio}")
        
        # 1. Pipeline: Transcribe -> Response -> Synthesize
        transcribed_text = stt_engine.transcribe(args.audio)
        print(f"\nYou said: '{transcribed_text}'")
        
        response_text = response_engine.generate_response(transcribed_text)
        print(f"Assistant says: '{response_text}'")
        
        # Speak the response out loud and save it in one go (prevents blocking bugs)
        output_file = "cli_response.wav"
        tts_engine.speak(response_text, save_path=output_file)
        
        print(f"\nResponse audio saved to: {output_file}")
        print("\n" + "="*50)
        print("TALK TO THE ASSISTANT (TEXT MODE)")
        print("Type your response below. Type 'exit' to quit.")
        print("="*50)
        
        while True:
            try:
                user_input = input("\nYou (Type or provide .wav path): ")
                if user_input.lower() in ["exit", "quit", "q"]:
                    print("Goodbye!")
                    break
                
                # Check if user provided a path to an audio file
                if user_input.endswith(".wav") and os.path.exists(user_input):
                    print(f"Processing follow-up audio: {user_input}")
                    user_text = stt_engine.transcribe(user_input)
                    print(f"You said (from audio): '{user_text}'")
                    response = response_engine.generate_response(user_text)
                else:
                    response = response_engine.generate_response(user_input)
                
                print(f"Assistant: {response}")
                tts_engine.speak(response)
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error in interaction: {e}")
                print("Continuing...")
        
if __name__ == "__main__":
    main()
