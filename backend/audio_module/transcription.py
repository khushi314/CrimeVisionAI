"""
Audio transcription entry point wrapping AudioService for Flask Blueprint consumption.
"""

from typing import Dict, Any

try:
    from backend.services.audio_service import AudioService
except ImportError:
    from services.audio_service import AudioService

_audio_service = AudioService()


def process_witness_audio(audio_path: str) -> Dict[str, Any]:
    """Run Whisper multilingual transcription and forensic fact extraction on `audio_path`."""
    return _audio_service.transcribe_multilingual(audio_path)
