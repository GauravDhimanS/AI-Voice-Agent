"""
Comprehensive setup and diagnostic test for the AI Voice Agent.

This script tests all components to ensure everything is working correctly:
- Dependencies
- GPU/CUDA availability
- Voice models
- Ollama LLM server
- Web server functionality

Run this before starting the voice agent to diagnose any issues.
"""

import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test all required imports."""
    logger.info("Testing imports...")
    try:
        import torch
        import faster_whisper
        import soundfile
        import sounddevice
        import requests
        import fastapi
        import uvicorn
        from piper.voice import PiperVoice
        logger.info("✓ All required packages imported successfully")
        return True
    except ImportError as e:
        logger.error(f"✗ Import failed: {e}")
        logger.error("Run: pip install -r requirements.txt")
        return False

def test_cuda():
    """Test CUDA availability."""
    logger.info("\nTesting CUDA/GPU support...")
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            logger.info(f"✓ CUDA is available")
            logger.info(f"  PyTorch version: {torch.__version__}")
            logger.info(f"  CUDA version: {torch.version.cuda}")
            logger.info(f"  GPU: {torch.cuda.get_device_name(0)}")
        else:
            logger.warning("⚠ CUDA not available - will use CPU (slower)")
            logger.info("  PyTorch version: " + torch.__version__)
        return True
    except Exception as e:
        logger.error(f"✗ CUDA test failed: {e}")
        return False

def test_voice_models():
    """Test if voice models exist."""
    logger.info("\nTesting voice models...")
    from config import Config

    model_path = Config.TTS_MODEL_PATH
    config_path = Path(str(model_path) + ".json")

    if not model_path.exists():
        logger.error(f"✗ Voice model not found: {model_path}")
        logger.error("Download from: https://github.com/rhasspy/piper/releases")
        return False

    if not config_path.exists():
        logger.error(f"✗ Voice model config not found: {config_path}")
        return False

    logger.info(f"✓ Voice model found: {model_path.name}")
    return True

def test_ollama():
    """Test Ollama server connection."""
    logger.info("\nTesting Ollama server...")
    try:
        import requests
        from config import Config

        response = requests.get(f"{Config.LLM_BASE_URL}/api/tags", timeout=5)
        response.raise_for_status()

        models = response.json().get('models', [])
        model_names = [m['name'] for m in models]

        logger.info(f"✓ Ollama server is running")
        logger.info(f"  Available models: {', '.join(model_names)}")

        if Config.LLM_MODEL in model_names:
            logger.info(f"✓ Required model '{Config.LLM_MODEL}' is available")
        else:
            logger.warning(f"⚠ Required model '{Config.LLM_MODEL}' not found")
            logger.info(f"  Run: ollama pull {Config.LLM_MODEL}")
            return False

        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Cannot connect to Ollama: {e}")
        logger.error("  Start Ollama: ollama serve")
        return False

def test_directories():
    """Test that all required directories exist."""
    logger.info("\nTesting directories...")
    from config import Config

    Config.ensure_directories()
    logger.info("✓ All required directories created/verified")
    return True

def test_stt():
    """Test Speech-to-Text module."""
    logger.info("\nTesting STT module...")
    try:
        from modules.stt import SpeechToText
        stt = SpeechToText()
        logger.info(f"✓ STT initialized: {stt.model_size} on {stt.device}")
        return True
    except Exception as e:
        logger.error(f"✗ STT initialization failed: {e}")
        return False

def test_tts():
    """Test Text-to-Speech module."""
    logger.info("\nTesting TTS module...")
    try:
        from modules.tts import TextToSpeech
        tts = TextToSpeech()
        logger.info(f"✓ TTS initialized: {tts.model_path.name}")
        return True
    except Exception as e:
        logger.error(f"✗ TTS initialization failed: {e}")
        return False

def test_llm():
    """Test LLM module."""
    logger.info("\nTesting LLM module...")
    try:
        from modules.llm import MedicalConversationAgent
        llm = MedicalConversationAgent()
        logger.info(f"✓ LLM initialized: {llm.model}")
        return True
    except Exception as e:
        logger.error(f"✗ LLM initialization failed: {e}")
        return False

def test_server():
    """Test that server can be imported."""
    logger.info("\nTesting server module...")
    try:
        import server
        logger.info("✓ Server module imports successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Server import failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("="*70)
    logger.info("AI VOICE AGENT - SETUP DIAGNOSTIC")
    logger.info("="*70)

    tests = [
        ("Imports", test_imports),
        ("CUDA/GPU", test_cuda),
        ("Directories", test_directories),
        ("Voice Models", test_voice_models),
        ("Ollama Server", test_ollama),
        ("STT Module", test_stt),
        ("TTS Module", test_tts),
        ("LLM Module", test_llm),
        ("Server Module", test_server),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            logger.error(f"✗ {name} test crashed: {e}")
            results[name] = False

    # Summary
    logger.info("\n" + "="*70)
    logger.info("SUMMARY")
    logger.info("="*70)

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")

    logger.info("="*70)
    logger.info(f"Result: {passed}/{total} tests passed")

    if passed == total:
        logger.info("\n🎉 All tests passed! Your setup is ready.")
        logger.info("\nTo start the voice agent:")
        logger.info("  1. Terminal mode: python main.py")
        logger.info("  2. Web UI mode: uvicorn server:app --host 0.0.0.0 --port 8000")
        logger.info("     Then open: http://localhost:8000/web/")
        return 0
    else:
        logger.error("\n⚠ Some tests failed. Fix the issues above before starting.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
