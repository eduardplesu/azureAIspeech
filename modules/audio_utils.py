# modules/audio_utils.py
from pydub import AudioSegment

def convert_audio_to_wav(file_path: str) -> str:
    """
    Converts an audio file to WAV format with PCM encoding, 16kHz sample rate, and mono channel.
    If the file is already WAV, it is returned unchanged.
    Raises a ValueError if file_path is None or empty.
    """
    if not file_path:
        raise ValueError("No file path provided to convert_audio_to_wav.")
    
    # Check file extension (case-insensitive).
    if file_path.lower().endswith(".mp3"):
        wav_file_path = file_path.rsplit(".", 1)[0] + ".wav"
        audio = AudioSegment.from_file(file_path)
        # Convert to 16kHz, mono, 16-bit PCM.
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio.export(wav_file_path, format="wav")
        return wav_file_path
    
    # If already WAV, return the same file path.
    return file_path
