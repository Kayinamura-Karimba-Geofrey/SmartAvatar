import os
import subprocess

def convert_to_wav(input_path: str, output_path: str):
    """
    Converts any audio file to a standard .wav format using FFmpeg.
    """
    # Dynamically find the ffmpeg binary
    local_ffmpeg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg_bin", "ffmpeg.exe")
    
    # If not found locally, fallback to system ffmpeg
    ffmpeg_cmd = local_ffmpeg_path if os.path.exists(local_ffmpeg_path) else "ffmpeg"

    command = [
        ffmpeg_cmd,
        "-y",               # Overwrite output file if it exists
        "-i", input_path,   # Input file
        "-ar", "16000",     # Audio sampling rate (16kHz for Whisper compatibility)
        "-ac", "1",         # Audio channels (mono)
        output_path         # Output file
    ]
    
    print(f"Converting {input_path} to {output_path}...")
    try:
        # Run the command and capture output
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg conversion failed: {e.stderr}")
        raise RuntimeError(f"FFmpeg conversion failed: {e.stderr}")
    
    return output_path
