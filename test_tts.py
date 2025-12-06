"""
Test suite for Text-to-Speech module.

Run individual tests:
    python test_tts.py test_basic_synthesis
    python test_tts.py test_medical_responses
    python test_tts.py test_long_text
    python test_tts.py test_batch_synthesis
    python test_tts.py test_convenience_functions
    python test_tts.py test_interactive

Run all tests:
    python test_tts.py all
"""

import sys
import logging
from pathlib import Path
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from modules.tts import TextToSpeech, synthesize_text, speak_text
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_basic_synthesis():
    """Test basic text-to-speech synthesis."""
    print("\n" + "="*70)
    print("TEST 1: Basic Text-to-Speech Synthesis")
    print("="*70)

    try:
        # Initialize TTS
        print("\n1. Initializing TTS engine...")
        tts = TextToSpeech()
        print(f"   {tts}")

        # Test simple synthesis
        print("\n2. Testing basic synthesis...")
        test_text = "Hello, I am your medical appointment assistant."

        result = tts.synthesize(
            test_text,
            auto_play=True,  # Play the audio
            save_audio=True   # Save to file
        )

        print(f"\n✓ Synthesis Results:")
        print(f"   Text: {result['text']}")
        print(f"   Duration: {result['duration']:.2f} seconds")
        print(f"   Sample Rate: {result['sample_rate']} Hz")
        print(f"   Characters: {result['character_count']}")
        print(f"   Audio File: {result['audio_path']}")

        # Verify file exists
        if result['audio_path'] and result['audio_path'].exists():
            file_size = result['audio_path'].stat().st_size
            print(f"   File Size: {file_size:,} bytes")

        print("\n✓ Test passed!")
        return True

    except FileNotFoundError as e:
        print(f"\n⚠ Voice model not found!")
        print(f"\nTo use TTS, you need to download a Piper voice model:")
        print(f"1. Visit: https://github.com/rhasspy/piper/releases")
        print(f"2. Download a voice (e.g., en_US-lessac-medium)")
        print(f"3. Place .onnx and .onnx.json files in: {Config.VOICE_MODELS_DIR}")
        print(f"\nError details: {e}")
        return False

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        logger.exception("Test failed")
        return False


def test_medical_responses():
    """Test TTS with medical appointment responses."""
    print("\n" + "="*70)
    print("TEST 2: Medical Appointment Responses")
    print("="*70)

    try:
        print("\n1. Initializing TTS engine...")
        tts = TextToSpeech()

        # Medical appointment scenarios
        scenarios = [
            "Good morning! How can I help you today?",
            "I'd be happy to help you schedule an appointment. May I have your name please?",
            "Thank you. What is the reason for your visit?",
            "I understand. What date and time would work best for you?",
            "Great! I have you scheduled for tomorrow at 2 PM. Is there anything else I can help you with?",
            "Thank you for calling. Have a great day!"
        ]

        print(f"\n2. Synthesizing {len(scenarios)} medical responses...")

        for i, text in enumerate(scenarios, 1):
            print(f"\n   Scenario {i}/{len(scenarios)}:")
            print(f"   '{text}'")

            start_time = time.time()
            result = tts.synthesize(
                text,
                auto_play=False,  # Don't auto-play to speed up test
                save_audio=True
            )
            elapsed = time.time() - start_time

            print(f"   ✓ Generated in {elapsed:.2f}s (duration: {result['duration']:.2f}s)")

        # Show statistics
        stats = tts.get_stats()
        print(f"\n✓ Statistics:")
        print(f"   Total syntheses: {stats['total_syntheses']}")
        print(f"   Total characters: {stats['total_characters']}")
        print(f"   Avg characters/synthesis: {stats['avg_characters_per_synthesis']:.1f}")

        print("\n✓ Test passed!")
        return True

    except FileNotFoundError as e:
        print(f"\n⚠ Voice model not found! See test_basic_synthesis for setup instructions.")
        return False

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        logger.exception("Test failed")
        return False


def test_long_text():
    """Test synthesis with longer medical dialogue."""
    print("\n" + "="*70)
    print("TEST 3: Long Text Synthesis")
    print("="*70)

    try:
        test_text = (
            "Thank you for calling our medical practice. "
            "I have successfully scheduled your appointment for tomorrow "
            "at two PM with Doctor Smith. Please arrive fifteen minutes early "
            "to complete any necessary paperwork. If you need to cancel or "
            "reschedule, please call us at least twenty-four hours in advance. "
            "Is there anything else I can help you with today?"
        )

        print(f"\n1. Testing long text synthesis...")
        print(f"   Text length: {len(test_text)} characters")
        print(f"   '{test_text[:80]}...'")

        tts = TextToSpeech()
        result = tts.synthesize(
            test_text,
            auto_play=True,
            save_audio=True
        )

        print(f"\n✓ Synthesis Results:")
        print(f"   Duration: {result['duration']:.2f}s")
        print(f"   Characters/second: {len(test_text)/result['duration']:.1f}")
        print(f"   Audio file: {result['audio_path'].name}")

        print("\n✓ Test passed!")
        return True

    except FileNotFoundError as e:
        print(f"\n⚠ Voice model not found! See test_basic_synthesis for setup instructions.")
        return False

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        logger.exception("Test failed")
        return False


def test_batch_synthesis():
    """Test batch synthesis performance."""
    print("\n" + "="*70)
    print("TEST 4: Batch Synthesis Performance")
    print("="*70)

    try:
        print("\n1. Initializing TTS engine...")
        tts = TextToSpeech()

        # Generate multiple short responses
        responses = [
            f"Your appointment is confirmed for slot {i}."
            for i in range(1, 11)
        ]

        print(f"\n2. Synthesizing {len(responses)} responses...")

        start_time = time.time()
        total_audio_duration = 0

        for i, text in enumerate(responses, 1):
            result = tts.synthesize(
                text,
                auto_play=False,
                save_audio=False  # Don't save to speed up test
            )
            total_audio_duration += result['duration']

            if i % 5 == 0:
                print(f"   Processed {i}/{len(responses)}...")

        elapsed = time.time() - start_time

        print(f"\n✓ Performance Results:")
        print(f"   Total processing time: {elapsed:.2f}s")
        print(f"   Total audio duration: {total_audio_duration:.2f}s")
        print(f"   Real-time factor: {total_audio_duration/elapsed:.2f}x")
        print(f"   Avg time per synthesis: {elapsed/len(responses):.3f}s")

        print("\n✓ Test passed!")
        return True

    except FileNotFoundError as e:
        print(f"\n⚠ Voice model not found! See test_basic_synthesis for setup instructions.")
        return False

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        logger.exception("Test failed")
        return False


def test_interactive():
    """Interactive TTS testing."""
    print("\n" + "="*70)
    print("TEST 5: Interactive Text-to-Speech")
    print("="*70)
    print("\nType text to hear it spoken (or 'quit' to exit)")
    print("Examples:")
    print("  - 'Hello, how are you today?'")
    print("  - 'Your appointment is confirmed for tomorrow at 2 PM.'")
    print("="*70)

    try:
        tts = TextToSpeech()
        print(f"\nTTS Engine ready: {tts}")

        while True:
            text = input("\nEnter text: ").strip()

            if text.lower() in ['quit', 'exit', 'q']:
                print("Exiting...")
                break

            if not text:
                print("⚠ Please enter some text")
                continue

            try:
                print("Synthesizing...")
                result = tts.synthesize(
                    text,
                    auto_play=True,
                    save_audio=True
                )
                print(f"✓ Done! ({result['duration']:.2f}s, saved to {result['audio_path'].name})")

            except Exception as e:
                print(f"✗ Error: {e}")

        # Show statistics
        stats = tts.get_stats()
        print(f"\nSession Statistics:")
        print(f"  Syntheses: {stats['total_syntheses']}")
        print(f"  Characters: {stats['total_characters']}")

        return True

    except FileNotFoundError as e:
        print(f"\n⚠ Voice model not found! See test_basic_synthesis for setup instructions.")
        return False

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return True

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        logger.exception("Test failed")
        return False


def test_convenience_functions():
    """Test convenience functions."""
    print("\n" + "="*70)
    print("TEST 6: Convenience Functions")
    print("="*70)

    try:
        print("\n1. Testing synthesize_text() convenience function...")
        text1 = "This is a convenience function test."
        audio_path = synthesize_text(text1)
        print(f"   ✓ Audio saved to: {audio_path}")

        print("\n2. Testing speak_text() convenience function...")
        text2 = "This text will be spoken immediately."
        speak_text(text2)
        print(f"   ✓ Speech complete")

        print("\n✓ Test passed!")
        return True

    except FileNotFoundError as e:
        print(f"\n⚠ Voice model not found! See test_basic_synthesis for setup instructions.")
        return False

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        logger.exception("Test failed")
        return False


def main():
    """Run tests based on command line argument."""
    print("\n" + "="*70)
    print("TTS MODULE TEST SUITE")
    print("="*70)

    tests = {
        'test_basic_synthesis': test_basic_synthesis,
        'test_medical_responses': test_medical_responses,
        'test_long_text': test_long_text,
        'test_batch_synthesis': test_batch_synthesis,
        'test_convenience_functions': test_convenience_functions,
        'test_interactive': test_interactive,
    }

    if len(sys.argv) > 1:
        test_name = sys.argv[1]

        if test_name == 'all':
            # Run all non-interactive tests
            results = {}
            for name, test_func in tests.items():
                if name != 'test_interactive':
                    results[name] = test_func()

            # Summary
            print("\n" + "="*70)
            print("TEST SUMMARY")
            print("="*70)
            for name, passed in results.items():
                status = "✓ PASSED" if passed else "✗ FAILED"
                print(f"{status}: {name}")

            total = len(results)
            passed = sum(results.values())
            print(f"\nTotal: {passed}/{total} tests passed")

        elif test_name in tests:
            tests[test_name]()
        else:
            print(f"\nUnknown test: {test_name}")
            print(f"Available tests: {', '.join(tests.keys())}, all")
    else:
        print("\nUsage: python test_tts.py <test_name>")
        print(f"Available tests: {', '.join(tests.keys())}, all")
        print("\nExample: python test_tts.py test_basic_synthesis")


if __name__ == "__main__":
    main()
