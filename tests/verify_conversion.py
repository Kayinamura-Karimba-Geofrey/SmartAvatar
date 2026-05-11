import os
import sys
# Add current directory to path so we can import utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import convert_to_wav

def test_conversion():
    # Use the existing test_input.wav as a source for another wav
    # In a real scenario, we'd use an mp3, but we can verify wav-to-wav conversion first
    input_file = os.path.join(os.path.dirname(__file__), "test_input.wav")
    output_file = os.path.join(os.path.dirname(__file__), "test_output_conversion.wav")
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found. Please ensure it exists.")
        return

    try:
        convert_to_wav(input_file, output_file)
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            print(f"SUCCESS: Converted file created at {output_file} (Size: {size} bytes)")
            
            # Basic validation: check if it's a WAV file by header
            with open(output_file, 'rb') as f:
                header = f.read(4)
                if header == b'RIFF':
                    print("SUCCESS: File has valid RIFF header.")
                else:
                    print(f"FAILURE: File header is {header}, expected RIFF.")
        else:
            print("FAILURE: Output file was not created.")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        # Cleanup
        if os.path.exists(output_file):
            os.remove(output_file)

if __name__ == "__main__":
    test_conversion()
