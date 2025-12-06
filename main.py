"""
Main Voice Agent Orchestrator

This module integrates STT, LLM, and TTS into a complete voice conversation system
for medical appointment booking.

Usage:
    python main.py              # Start voice agent
    python main.py --text       # Text-only mode (no voice I/O)
    python main.py --debug      # Enable debug logging
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import argparse

import sounddevice as sd
import soundfile as sf
import numpy as np

from modules import (
    SpeechToText,
    MedicalConversationAgent,
    ConversationState,
    ConversationStage,
    TextToSpeech
)
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class VoiceAgent:
    """
    Main voice agent that orchestrates the complete conversation flow:
    Listen → Transcribe → Process → Respond → Speak
    """

    def __init__(
        self,
        text_mode: bool = False,
        save_recordings: bool = True,
        save_responses: bool = True
    ):
        """
        Initialize the voice agent.

        Args:
            text_mode: If True, use text input/output instead of voice
            save_recordings: Save recorded audio files
            save_responses: Save TTS audio files
        """
        self.text_mode = text_mode
        self.save_recordings = save_recordings
        self.save_responses = save_responses

        logger.info("Initializing Voice Agent...")

        # Initialize components
        try:
            if not text_mode:
                logger.info("Loading Speech-to-Text model...")
                self.stt = SpeechToText()

                logger.info("Loading Text-to-Speech model...")
                self.tts = TextToSpeech()

            logger.info("Initializing conversation agent...")
            self.llm = MedicalConversationAgent()

            # Start conversation and get initial state
            welcome_msg, self.conversation_state = self.llm.start_conversation()
            self.initial_welcome = welcome_msg

            logger.info("Voice Agent initialized successfully!")

        except Exception as e:
            logger.error(f"Failed to initialize Voice Agent: {e}")
            raise

        # Session tracking
        self.session_id = None
        self.turn_count = 0

    def record_audio(self, max_duration: float = Config.AUDIO_MAX_RECORDING_TIME) -> Optional[Path]:
        """
        Record audio from microphone until silence is detected.

        Args:
            max_duration: Maximum recording duration in seconds

        Returns:
            Path to saved audio file, or None if recording failed
        """
        print("[Listening... speak now]")
        logger.info("Listening...")

        try:
            # Record audio
            recording = sd.rec(
                int(max_duration * Config.AUDIO_SAMPLE_RATE),
                samplerate=Config.AUDIO_SAMPLE_RATE,
                channels=Config.AUDIO_CHANNELS,
                dtype=Config.AUDIO_FORMAT
            )
            sd.wait()  # Wait for recording to finish

            # Remove silence from end using simple threshold
            # Find last non-silent frame
            threshold = Config.AUDIO_SILENCE_THRESHOLD
            non_silent = np.where(np.abs(recording) > threshold)[0]

            if len(non_silent) == 0:
                logger.warning("No speech detected in recording")
                return None

            # Trim silence
            recording = recording[:non_silent[-1] + Config.AUDIO_SAMPLE_RATE]

            # Save recording if requested
            if self.save_recordings:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = Config.RECORDING_DIR / f"recording_{timestamp}.wav"

                sf.write(
                    filename,
                    recording,
                    Config.AUDIO_SAMPLE_RATE
                )

                logger.info(f"Recording saved: {filename}")
                return filename
            else:
                # Create temporary file
                import tempfile
                temp_fd, temp_path = tempfile.mkstemp(suffix='.wav')
                import os
                os.close(temp_fd)

                sf.write(
                    temp_path,
                    recording,
                    Config.AUDIO_SAMPLE_RATE
                )

                return Path(temp_path)

        except Exception as e:
            logger.error(f"Recording failed: {e}")
            return None

    def listen(self) -> Optional[str]:
        """
        Listen to user input (voice or text) and convert to text.

        Returns:
            Transcribed text, or None if failed
        """
        if self.text_mode:
            # Text mode: get input from console
            try:
                user_input = input("\nYou: ").strip()
                return user_input if user_input else None
            except (EOFError, KeyboardInterrupt):
                return None
        else:
            # Voice mode: record and transcribe
            audio_file = self.record_audio()

            if audio_file is None:
                return None

            try:
                # Transcribe
                logger.info("Transcribing...")
                result = self.stt.transcribe(audio_file)

                if result['confidence'] < Config.STT_MIN_CONFIDENCE:
                    logger.warning(
                        f"Low confidence ({result['confidence']:.2%}). "
                        "Please speak more clearly."
                    )

                transcription = result['text']
                logger.info(f"You said: {transcription}")

                # Clean up temp file if not saving
                if not self.save_recordings and audio_file.exists():
                    audio_file.unlink()

                return transcription

            except Exception as e:
                logger.error(f"Transcription failed: {e}")
                return None

    def think(self, user_input: str) -> Optional[str]:
        """
        Process user input and generate response using LLM.

        Args:
            user_input: User's message

        Returns:
            Agent's response, or None if failed
        """
        try:
            logger.info("Processing...")
            # generate_response modifies state in-place and returns only response text
            response = self.llm.generate_response(
                user_input,
                self.conversation_state
            )
            logger.info(f"Agent: {response}")
            return response

        except Exception as e:
            logger.error(f"LLM processing failed: {e}")
            return "I'm sorry, I'm having trouble processing that. Could you please repeat?"

    def think_and_speak_streaming(self, user_input: str):
        """
        Process user input and stream response with real-time TTS.
        This significantly reduces perceived latency in voice mode.

        Args:
            user_input: User's message
        """
        try:
            logger.info("Processing with streaming...")

            # Get streaming response from LLM
            response_stream = self.llm.generate_response_streaming(
                user_input,
                self.conversation_state
            )

            # Stream TTS synthesis and playback
            for _ in self.tts.synthesize_streaming(response_stream, auto_play=True):
                pass  # Audio is played as it's generated

            logger.info("Streaming response complete")

        except Exception as e:
            logger.error(f"Streaming processing failed: {e}")
            self.speak("I'm sorry, I'm having trouble processing that. Could you please repeat?")

    def speak(self, text: str):
        """
        Convert text to speech and play it.

        Args:
            text: Text to speak
        """
        if self.text_mode:
            # Text mode: just print
            print(f"Agent: {text}")
        else:
            # Voice mode: synthesize and play
            try:
                logger.info("Speaking...")
                self.tts.synthesize(
                    text,
                    auto_play=True,
                    save_audio=self.save_responses
                )
            except Exception as e:
                logger.error(f"Speech synthesis failed: {e}")
                # Fallback to text
                print(f"Agent: {text}")

    def run_conversation(self):
        """
        Run the main conversation loop.
        """
        # Generate session ID
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info(f"Starting new session: {self.session_id}")

        # Use the welcome message from initialization
        self.speak(self.initial_welcome)
        self.turn_count = 0

        try:
            while self.turn_count < Config.CONVERSATION_MAX_TURNS:
                self.turn_count += 1
                logger.info(f"\n--- Turn {self.turn_count} ---")

                # Listen to user
                user_input = self.listen()

                if user_input is None:
                    logger.warning("No input received")
                    self.speak("I didn't catch that. Could you please repeat?")
                    continue

                # Check for exit commands (multiple variations)
                exit_keywords = ['exit', 'quit', 'goodbye', 'bye', 'hang up',
                               'end call', 'stop', 'done', 'that\'s all',
                               'nothing else', 'no thank you']
                if any(keyword in user_input.lower() for keyword in exit_keywords):
                    self.speak("Thank you for calling. Have a great day!")
                    logger.info("Call ended by user request")
                    break

                # Process and respond - use streaming in voice mode for lower latency
                if self.text_mode:
                    # Text mode: use standard response
                    response = self.think(user_input)
                    if response:
                        self.speak(response)
                else:
                    # Voice mode: use streaming for real-time response
                    self.think_and_speak_streaming(user_input)

                # Check if conversation is complete
                if self.conversation_state.stage == ConversationStage.COMPLETED:
                    self.speak("Your appointment is all set. Thank you for calling and have a great day!")
                    logger.info("Conversation completed successfully")
                    break

                # Check for emergency escalation
                if self.conversation_state.emergency_detected:
                    logger.warning("Emergency detected - ending conversation")
                    break

            # Check if max turns reached
            if self.turn_count >= Config.CONVERSATION_MAX_TURNS:
                logger.warning("Maximum conversation turns reached")
                self.speak(
                    "I notice we've been talking for a while. "
                    "Let me transfer you to a staff member who can help you further."
                )

        except KeyboardInterrupt:
            logger.info("Conversation interrupted by user")
            self.speak("Goodbye!")

        except Exception as e:
            logger.error(f"Conversation error: {e}", exc_info=True)
            self.speak(
                "I'm experiencing technical difficulties. "
                "Please call back or speak with a staff member."
            )

        finally:
            # Log session summary
            self.log_session_summary()

    def log_session_summary(self):
        """Log summary of the conversation session."""
        logger.info("\n" + "="*70)
        logger.info("SESSION SUMMARY")
        logger.info("="*70)
        logger.info(f"Session ID: {self.session_id}")
        logger.info(f"Total turns: {self.turn_count}")
        logger.info(f"Final stage: {self.conversation_state.stage.value}")
        logger.info(f"Patient name: {self.conversation_state.patient_name or 'Not collected'}")
        logger.info(f"Reason: {self.conversation_state.reason or 'Not collected'}")
        logger.info(f"Preferred date: {self.conversation_state.preferred_date or 'Not collected'}")
        logger.info(f"Preferred time: {self.conversation_state.preferred_time or 'Not collected'}")
        logger.info("="*70)

    def get_state(self) -> ConversationState:
        """Get current conversation state."""
        return self.conversation_state


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Medical Appointment Voice Agent"
    )
    parser.add_argument(
        '--text',
        action='store_true',
        help='Use text mode instead of voice'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    parser.add_argument(
        '--no-save-recordings',
        action='store_true',
        help='Do not save audio recordings'
    )
    parser.add_argument(
        '--no-save-responses',
        action='store_true',
        help='Do not save TTS responses'
    )

    args = parser.parse_args()

    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Print banner
    print("\n" + "="*70)
    print("MEDICAL APPOINTMENT VOICE AGENT")
    print("="*70)
    print(f"Practice: {Config.PRACTICE_NAME}")
    print(f"Hours: {Config.PRACTICE_HOURS}")
    print(f"Mode: {'Text' if args.text else 'Voice'}")
    print("="*70)
    print("\nPress Ctrl+C to exit\n")

    # Create and run agent
    try:
        agent = VoiceAgent(
            text_mode=args.text,
            save_recordings=not args.no_save_recordings,
            save_responses=not args.no_save_responses
        )

        agent.run_conversation()

    except KeyboardInterrupt:
        print("\n\nAgent stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
