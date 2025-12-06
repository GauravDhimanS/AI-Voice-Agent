"""
Test script for Speech-to-Text module.
"""

import logging
from pathlib import Path
from modules.stt import SpeechToText
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_stt_basic():
    """Test basic STT functionality."""
    print("\n" + "="*60)
    print("TEST 1: Basic Speech-to-Text")
    print("="*60)
    
    # Initialize STT
    stt = SpeechToText()
    print(f"\n✓ Initialized: {stt}")
    
    # Test with a sample audio file
    test_audio = Config.TEST_AUDIO_DIR / "Recording.m4a"
    
    if not test_audio.exists():
        print(f"\n⚠ Test audio not found: {test_audio}")
        print("Please record a short German audio clip and save it as:")
        print(f"  {test_audio}")
        print("\nExample recording (Linux):")
        print(f"  arecord -d 5 -f cd {test_audio}")
        print("\nExample recording (Mac):")
        print(f"  sox -d -r 16000 {test_audio} trim 0 5")
        return
    
    # Transcribe
    result = stt.transcribe(test_audio)
    
    # Display results
    print(f"\n📝 Transcription Results:")
    print(f"  Text: {result['text']}")
    print(f"  Language: {result['language']} ({result['language_probability']:.1%})")
    print(f"  Confidence: {result['confidence']:.1%}")
    print(f"  Duration: {result['duration']:.2f}s")
    print(f"\n  Segments:")
    for seg in result['segments']:
        print(f"    [{seg['start']:.1f}s-{seg['end']:.1f}s] {seg['text']}")


# def test_stt_medical_terms():
#     """Test transcription of medical terminology."""
#     print("\n" + "="*60)
#     print("TEST 2: Medical Terminology Recognition")
#     print("="*60)
    
#     medical_terms = [
#         "Halsschmerzen",
#         "Ohrenschmerzen",
#         "Krankschreibung",
#         "Rezept",
#         "Akuttermin"
#     ]
    
#     print(f"\n📋 Expected terms: {', '.join(medical_terms)}")
#     print("\nPlease record yourself saying these terms:")
    
#     test_audio = Config.TEST_AUDIO_DIR / "test_english.wav"
    
#     if not test_audio.exists():
#         print(f"  Save recording as: {test_audio}")
#         return
    
#     stt = SpeechToText()
#     result = stt.transcribe(test_audio)
    
#     print(f"\n✓ Transcribed: {result['text']}")
    
#     # Check which terms were recognized
#     recognized = [term for term in medical_terms if term.lower() in result['text'].lower()]
#     print(f"\n✓ Recognized terms: {', '.join(recognized)}")
#     print(f"  Accuracy: {len(recognized)}/{len(medical_terms)}")


# def test_stt_performance():
#     """Test STT performance metrics."""
#     print("\n" + "="*60)
#     print("TEST 3: Performance Metrics")
#     print("="*60)
    
#     import time
    
#     stt = SpeechToText()
#     test_audio = Config.TEST_AUDIO_DIR / "test_german.wav"
    
#     if not test_audio.exists():
#         print(f"⚠ Test audio not found: {test_audio}")
#         return
    
#     # Measure processing time
#     print("\n⏱ Measuring processing time...")
    
#     start = time.time()
#     result = stt.transcribe(test_audio)
#     end = time.time()
    
#     processing_time = end - start
#     audio_duration = result['duration']
#     real_time_factor = processing_time / audio_duration
    
#     print(f"\n📊 Performance:")
#     print(f"  Audio duration: {audio_duration:.2f}s")
#     print(f"  Processing time: {processing_time:.2f}s")
#     print(f"  Real-time factor: {real_time_factor:.2f}x")
    
#     if real_time_factor < 1.0:
#         print(f"  ✓ EXCELLENT: Faster than real-time!")
#     elif real_time_factor < 2.0:
#         print(f"  ✓ GOOD: Acceptable for production")
#     else:
#         print(f"  ⚠ SLOW: May need optimization")
    
#     # Statistics
#     stats = stt.get_stats()
#     print(f"\n📈 Statistics:")
#     for key, value in stats.items():
#         print(f"  {key}: {value:.2f}")


# def create_sample_audio():
#     """Helper to create a test audio file using TTS."""
#     print("\n" + "="*60)
#     print("HELPER: Create Sample Audio")
#     print("="*60)
    
#     print("\nThis will create a sample audio file using Piper TTS.")
#     print("Make sure you have Piper installed!")
    
#     import subprocess
    
#     test_text = "Guten Tag, ich brauche einen Termin. Ich habe Halsschmerzen."
#     test_audio = Config.TEST_AUDIO_DIR / "test_german.wav"
    
#     try:
#         # Create audio using Piper
#         subprocess.run(
#             ["piper", "--model", "de_DE-thorsten-medium.onnx", 
#              "--output_file", str(test_audio)],
#             input=test_text.encode(),
#             check=True
#         )
#         print(f"\n✓ Created test audio: {test_audio}")
#         print(f"  Text: {test_text}")
#     except FileNotFoundError:
#         print("\n⚠ Piper not found. Please install Piper TTS first.")
#     except Exception as e:
#         print(f"\n✗ Failed to create audio: {e}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Speech-to-Text Module Test Suite")
    print("="*60)
    
    # Run tests
    test_stt_basic()
    #test_stt_medical_terms()
    #test_stt_performance()
    
    print("\n✓ All tests complete!\n")