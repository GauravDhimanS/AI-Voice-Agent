"""
Text-to-Speech module using Piper TTS.

Features:
- Local, fast neural text-to-speech
- Professional English voices
- Customizable speech speed and tone
- Audio file generation and playback
- Medical-friendly natural speech
"""

import logging
from pathlib import Path
from typing import Optional, Dict
import wave
from datetime import datetime
import tempfile
import os

try:
    from piper.voice import PiperVoice
    import sounddevice as sd
    import numpy as np
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install piper-tts sounddevice")
    raise

from config import Config

logger = logging.getLogger(__name__)


class TextToSpeech:
    """
    Handles text-to-speech conversion with medical-friendly natural speech.
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        sample_rate: int = Config.TTS_SAMPLE_RATE
    ):
        """
        Initialize the TTS engine.

        Args:
            model_path: Path to Piper .onnx model file
            sample_rate: Audio sample rate in Hz

        Note:
            To customize speech parameters (speed, noise, etc.), edit the
            .onnx.json config file's "inference" section. For example:
            {
                "inference": {
                    "noise_scale": 0.667,
                    "length_scale": 1.0,
                    "noise_w": 0.8
                }
            }
        """
        self.model_path = model_path or Config.TTS_MODEL_PATH
        self.sample_rate = sample_rate

        logger.info(f"Initializing TTS with model={self.model_path}")

        # Load Piper voice model
        try:
            self._load_model()
            logger.info("Piper TTS model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Piper model: {e}")
            logger.info("To download voice models, visit: https://github.com/rhasspy/piper/releases")
            raise

        # Statistics
        self.total_syntheses = 0
        self.total_characters = 0

    def _load_model(self):
        """Load the Piper voice model."""
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Voice model not found at {self.model_path}\n"
                f"Download models from: https://github.com/rhasspy/piper/releases\n"
                f"Place the .onnx and .onnx.json files in: {Config.VOICE_MODELS_DIR}"
            )

        # Check for config file
        config_path = Path(str(self.model_path) + ".json")
        if not config_path.exists():
            raise FileNotFoundError(
                f"Model config not found at {config_path}\n"
                f"Both .onnx and .onnx.json files are required"
            )

        # Load the voice
        self.voice = PiperVoice.load(str(self.model_path))
        logger.debug(f"Loaded voice model: {self.model_path.stem}")

    def synthesize(
        self,
        text: str,
        output_path: Optional[Path] = None,
        auto_play: bool = Config.TTS_ENABLE_PLAYBACK,
        save_audio: bool = Config.TTS_SAVE_AUDIO
    ) -> Dict:
        """
        Convert text to speech with optional playback and file saving.

        Args:
            text: Text to convert to speech
            output_path: Path to save audio file (auto-generated if None)
            auto_play: Automatically play the generated audio
            save_audio: Save the audio to a file

        Returns:
            Dict with:
                - text: Input text
                - audio_path: Path to saved audio file (if saved)
                - duration: Audio duration in seconds
                - sample_rate: Audio sample rate
                - character_count: Number of characters synthesized
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        text = text.strip()
        logger.info(f"Synthesizing: '{text[:100]}...'")

        try:
            # Determine output file path
            if save_audio and output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = Config.OUTPUT_AUDIO_DIR / f"tts_{timestamp}.wav"
            elif output_path:
                output_path = Path(output_path)

            # Synthesize directly to file
            if save_audio or auto_play:
                # We need a file for both saving and playing
                temp_file = output_path if save_audio else Path(tempfile.mktemp(suffix='.wav'))

                # Synthesize to file using synthesize_wav method
                with wave.open(str(temp_file), 'wb') as wav_file:
                    self.voice.synthesize_wav(text, wav_file)

                # Verify the file was created
                if not temp_file.exists() or temp_file.stat().st_size == 0:
                    raise ValueError("Piper failed to generate audio")

                # Read the file to get audio data for playback/duration
                import soundfile as sf
                audio_data, sample_rate = sf.read(str(temp_file), dtype='float32')

                # Ensure mono
                if len(audio_data.shape) > 1:
                    audio_data = np.mean(audio_data, axis=1)

                duration = len(audio_data) / sample_rate

                # Play if requested
                if auto_play:
                    self._play_audio(audio_data)
                    logger.info("Audio playback complete")

                # Clean up temp file if not saving
                if not save_audio and temp_file.exists():
                    os.remove(temp_file)
                    final_path = None
                else:
                    final_path = temp_file
                    logger.info(f"Audio saved to: {final_path}")
            else:
                # Neither save nor play - just generate for stats
                audio_data = self._generate_audio(text)
                duration = len(audio_data) / self.sample_rate
                final_path = None
                sample_rate = self.sample_rate

            # Update statistics
            self.total_syntheses += 1
            self.total_characters += len(text)

            logger.info(f"Synthesis complete: {duration:.2f}s, {len(text)} characters")

            return {
                "text": text,
                "audio_path": final_path,
                "duration": duration,
                "sample_rate": sample_rate,
                "character_count": len(text)
            }

        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            raise

    def _generate_audio(self, text: str) -> np.ndarray:
        """
        Generate audio data from text using Piper.

        Args:
            text: Input text

        Returns:
            Audio data as numpy array
        """
        # Create a temporary WAV file for synthesis
        temp_fd, temp_path = tempfile.mkstemp(suffix='.wav')

        try:
            # Close the file descriptor
            os.close(temp_fd)

            # Let Piper write directly to the file path
            # Open in write mode and let Piper configure it
            with wave.open(temp_path, 'wb') as wav_file:
                # Piper will configure and write to this file
                self.voice.synthesize_wav(text, wav_file)

            # Verify file was written
            if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                raise ValueError("Piper failed to generate audio (empty file)")

            # Read back the audio data using soundfile for reliability
            import soundfile as sf
            audio_data, sample_rate = sf.read(temp_path, dtype='float32')

            # Ensure it's mono
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)

            logger.debug(f"Generated audio: {len(audio_data)} samples at {sample_rate}Hz")

            return audio_data

        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            raise
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temp file: {cleanup_error}")

    def _save_wav(self, audio_data: np.ndarray, output_path: Path):
        """
        Save audio data to WAV file.

        Args:
            audio_data: Audio data as numpy array
            output_path: Output file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to int16
        audio_int16 = (audio_data * 32767).astype(np.int16)

        # Write WAV file
        with wave.open(str(output_path), 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_int16.tobytes())

    def _play_audio(self, audio_data: np.ndarray):
        """
        Play audio data through the default audio device.

        Args:
            audio_data: Audio data as numpy array
        """
        try:
            sd.play(audio_data, self.sample_rate, blocking=True)
        except Exception as e:
            logger.warning(f"Audio playback failed: {e}")
            logger.info("Audio was generated successfully but could not be played")

    def synthesize_simple(self, text: str) -> Path:
        """
        Simple synthesis returning audio file path (convenience method).

        Args:
            text: Text to convert to speech

        Returns:
            Path to saved audio file
        """
        result = self.synthesize(text, auto_play=False, save_audio=True)
        return result["audio_path"]

    def speak(self, text: str):
        """
        Synthesize and immediately play audio without saving (convenience method).

        Args:
            text: Text to speak
        """
        self.synthesize(text, auto_play=True, save_audio=False)

    def get_stats(self) -> Dict:
        """
        Get synthesis statistics.

        Returns:
            Dict with usage statistics
        """
        return {
            "total_syntheses": self.total_syntheses,
            "total_characters": self.total_characters,
            "avg_characters_per_synthesis": (
                self.total_characters / self.total_syntheses
                if self.total_syntheses > 0 else 0
            )
        }

    def synthesize_streaming(self, text_stream, auto_play: bool = True):
        """
        Synthesize and play text as it streams in, sentence by sentence.
        This significantly reduces perceived latency.

        Args:
            text_stream: Iterator/generator yielding text chunks
            auto_play: Whether to play audio as it's generated

        Yields:
            Dict with synthesis results for each sentence
        """
        buffer = ""
        sentence_endings = ['.', '!', '?', '\n']

        for chunk in text_stream:
            buffer += chunk

            # Check if we have a complete sentence
            for ending in sentence_endings:
                if ending in buffer:
                    # Split on sentence ending
                    sentences = buffer.split(ending)

                    # Process all complete sentences (all but last)
                    for sentence in sentences[:-1]:
                        sentence = sentence.strip()
                        if sentence:
                            sentence_with_ending = sentence + ending
                            try:
                                result = self.synthesize(
                                    sentence_with_ending,
                                    auto_play=auto_play,
                                    save_audio=False
                                )
                                yield result
                            except Exception as e:
                                logger.error(f"Streaming synthesis failed for sentence: {e}")

                    # Keep the last incomplete part
                    buffer = sentences[-1]
                    break

        # Synthesize any remaining text in buffer
        if buffer.strip():
            try:
                result = self.synthesize(
                    buffer.strip(),
                    auto_play=auto_play,
                    save_audio=False
                )
                yield result
            except Exception as e:
                logger.error(f"Streaming synthesis failed for final buffer: {e}")

    def __repr__(self):
        return f"TextToSpeech(model={self.model_path.stem}, rate={self.sample_rate}Hz)"


# Convenience function for quick usage
def synthesize_text(text: str, output_path: Optional[Path] = None) -> Path:
    """
    Quick synthesis function (creates new TTS instance).

    Args:
        text: Text to convert to speech
        output_path: Optional output file path

    Returns:
        Path to saved audio file
    """
    tts = TextToSpeech()
    result = tts.synthesize(text, output_path=output_path, auto_play=False, save_audio=True)
    return result["audio_path"]


def speak_text(text: str):
    """
    Quick speak function (creates new TTS instance and plays audio).

    Args:
        text: Text to speak
    """
    tts = TextToSpeech()
    tts.speak(text)
