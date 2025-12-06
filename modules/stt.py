"""
Speech-to-Text module using Faster-Whisper.

Features:
- GPU acceleration
- German language optimization
- Medical vocabulary context
- Noise reduction
- Voice Activity Detection
- Confidence scoring
"""

import logging
from pathlib import Path
from typing import Optional, Dict, List
import numpy as np

try:
    from faster_whisper import WhisperModel
    import noisereduce as nr
    import soundfile as sf
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install faster-whisper noisereduce soundfile")
    raise

from config import Config

logger = logging.getLogger(__name__)


class SpeechToText:
    """
    Handles speech-to-text conversion with medical context awareness.
    """
    
    def __init__(
        self,
        model_size: str = Config.STT_MODEL_SIZE,
        device: str = Config.STT_DEVICE,
        compute_type: str = Config.STT_COMPUTE_TYPE,
        language: str = Config.STT_LANGUAGE
    ):
        """
        Initialize the STT engine.
        
        Args:
            model_size: Whisper model size (tiny/base/small/medium/large)
            device: Processing device (cuda/cpu)
            compute_type: Computation precision (float16/int8/float32)
            language: Target language code
        """
        logger.info(f"Initializing STT with model={model_size}, device={device}")
        
        self.model_size = model_size
        self.device = device
        self.language = language
        
        # Load Whisper model
        try:
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type
            )
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
        
        # Medical context for better recognition
        self.initial_prompt = Config.STT_INITIAL_PROMPT
        
        # Statistics
        self.total_transcriptions = 0
        self.total_duration = 0.0
    
    def preprocess_audio(
        self, 
        audio_path: Path,
        reduce_noise: bool = Config.STT_ENABLE_NOISE_REDUCTION
    ) -> np.ndarray:
        """
        Preprocess audio: load, convert to mono, reduce noise.
        
        Args:
            audio_path: Path to audio file
            reduce_noise: Whether to apply noise reduction
            
        Returns:
            Preprocessed audio as numpy array
        """
        try:
            # Load audio file
            audio, sample_rate = sf.read(audio_path)
            
            # Convert stereo to mono if needed
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)
            
            # Apply noise reduction
            if reduce_noise:
                logger.debug("Applying noise reduction...")
                audio = nr.reduce_noise(
                    y=audio, 
                    sr=sample_rate,
                    stationary=True,
                    prop_decrease=0.8
                )
            
            logger.debug(f"Audio preprocessed: {len(audio)/sample_rate:.2f}s @ {sample_rate}Hz")
            return audio
            
        except Exception as e:
            logger.error(f"Audio preprocessing failed: {e}")
            raise
    
    def transcribe(
        self, 
        audio_path: Path,
        use_context: bool = True,
        vad_filter: bool = Config.STT_ENABLE_VAD
    ) -> Dict:
        """
        Transcribe audio file to text with metadata.
        
        Args:
            audio_path: Path to audio file (.wav, .mp3, etc.)
            use_context: Use medical vocabulary context
            vad_filter: Use Voice Activity Detection to filter silence
            
        Returns:
            Dict with:
                - text: Transcribed text
                - language: Detected language
                - confidence: Average confidence score
                - segments: List of segment details
                - duration: Audio duration in seconds
        """
        logger.info(f"Transcribing: {audio_path}")
        
        try:
            # Preprocess audio
            audio_path = Path(audio_path)
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Transcribe with Whisper
            segments, info = self.model.transcribe(
                str(audio_path),
                language=self.language,
                initial_prompt=self.initial_prompt if use_context else None,
                vad_filter=vad_filter,
                beam_size=5,  # Better quality, slightly slower
                word_timestamps=False  # Set True if you need word-level timing
            )
            
            # Collect segments
            transcription_segments = []
            full_text = []
            total_confidence = 0.0
            segment_count = 0
            
            for segment in segments:
                segment_info = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "confidence": getattr(segment, 'avg_logprob', 0.0)
                }
                transcription_segments.append(segment_info)
                full_text.append(segment.text.strip())
                
                # Track confidence (Whisper returns log probabilities)
                # Convert logprob to approximate confidence (0-1)
                confidence = np.exp(segment_info["confidence"])
                total_confidence += confidence
                segment_count += 1
                
                logger.debug(
                    f"  [{segment.start:.1f}s-{segment.end:.1f}s] "
                    f"{segment.text.strip()} (conf: {confidence:.2f})"
                )
            
            # Calculate average confidence
            avg_confidence = total_confidence / segment_count if segment_count > 0 else 0.0
            
            # Combine text
            full_transcript = " ".join(full_text)
            
            # Build result
            result = {
                "text": full_transcript,
                "language": info.language,
                "language_probability": info.language_probability,
                "confidence": avg_confidence,
                "segments": transcription_segments,
                "duration": info.duration,
                "model": self.model_size
            }
            
            # Update statistics
            self.total_transcriptions += 1
            self.total_duration += info.duration
            
            # Log result
            logger.info(f"Transcription complete: '{full_transcript[:100]}...'")
            logger.info(f"  Language: {info.language} ({info.language_probability:.2%})")
            logger.info(f"  Confidence: {avg_confidence:.2%}")
            logger.info(f"  Duration: {info.duration:.2f}s")

            # Warn if low confidence
            if avg_confidence < Config.STT_MIN_CONFIDENCE:
                logger.warning(
                    f"Low confidence transcription ({avg_confidence:.2%}). "
                    "Consider asking patient to repeat."
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
    
    def transcribe_simple(self, audio_path: Path) -> str:
        """
        Simple transcription returning only text (convenience method).
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        result = self.transcribe(audio_path)
        return result["text"]
    
    def get_stats(self) -> Dict:
        """
        Get transcription statistics.
        
        Returns:
            Dict with usage statistics
        """
        return {
            "total_transcriptions": self.total_transcriptions,
            "total_duration_seconds": self.total_duration,
            "avg_duration_seconds": (
                self.total_duration / self.total_transcriptions 
                if self.total_transcriptions > 0 else 0
            )
        }
    
    def __repr__(self):
        return (
            f"SpeechToText(model={self.model_size}, device={self.device}, "
            f"language={self.language})"
        )


# Convenience function for quick usage
def transcribe_audio(audio_path: Path) -> str:
    """
    Quick transcription function (creates new STT instance).
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Transcribed text
    """
    stt = SpeechToText()
    return stt.transcribe_simple(audio_path)