"""
Central configuration for the voice agent system.
"""
from pathlib import Path

class Config:
    # Project paths
    PROJECT_ROOT = Path(__file__).parent
    TEST_AUDIO_DIR = PROJECT_ROOT / "test_audio"
    DATA_DIR = PROJECT_ROOT / "data"
    VOICE_MODELS_DIR = PROJECT_ROOT / "voice_models"
    OUTPUT_AUDIO_DIR = DATA_DIR / "output_audio"
    
    # STT Configuration
    # Options: tiny, base, small, medium, large
    # Recommendation: "base" for speed, "small" for balance, "medium" for accuracy
    STT_MODEL_SIZE = "small"  # Changed from "medium" for faster transcription
    STT_DEVICE = "cuda"
    STT_COMPUTE_TYPE = "float32"  # Changed from "float32" for faster inference
    STT_LANGUAGE = "en"

    STT_INITIAL_PROMPT = (
        "Common medical terms: sore throat, ear pain, "
        "fever, cough, appointment, acute visit, prescription, "
        "sick note, referral."
    )

    STT_MIN_CONFIDENCE = 0.6  # Lowered from 0.7 to be less strict
    STT_ENABLE_VAD = True
    STT_ENABLE_NOISE_REDUCTION = True

    # TTS Configuration
    TTS_MODEL_PATH = VOICE_MODELS_DIR / "en_US-lessac-medium.onnx"  # Professional US English voice
    TTS_SAMPLE_RATE = 22050  # Default Piper sample rate
    TTS_ENABLE_PLAYBACK = True  # Auto-play generated audio
    TTS_SAVE_AUDIO = True  # Save generated audio files

    # Note: To customize voice parameters (speed, noise, etc.), edit the
    # .onnx.json config file's "inference" section

    # Audio Recording Configuration
    AUDIO_SAMPLE_RATE = 16000  # Sample rate for recording (16kHz is good for speech)
    AUDIO_CHANNELS = 1  # Mono recording
    AUDIO_CHUNK_SIZE = 1024  # Audio chunk size for streaming
    AUDIO_SILENCE_THRESHOLD = 500  # Silence threshold for voice detection
    AUDIO_SILENCE_DURATION = 2.0  # Seconds of silence to end recording
    AUDIO_MAX_RECORDING_TIME = 10.0  # Maximum recording time in seconds
    AUDIO_FORMAT = "int16"  # Audio format for recording
    RECORDING_DIR = DATA_DIR / "recordings"  # Directory for saved recordings

    # LLM Configuration
    # Model options: llama3.1:8b (recommended), llama3.2:3b (faster), qwen2.5:3b (faster)
    LLM_MODEL = "llama3.1:8b"
    LLM_BASE_URL = "http://localhost:11434"
    LLM_TEMPERATURE = 0.7  # 0.0 = deterministic, 1.0 = creative
    LLM_MAX_TOKENS = 150  # Reduced from 200 for faster responses
    LLM_TIMEOUT = 60  # seconds
    LLM_NUM_CTX = 2048  # Context window size (smaller = faster)
    
    # Conversation settings
    CONVERSATION_MAX_TURNS = 20  # Prevent infinite loops
    CONVERSATION_STYLE = "professional-casual"
    
    # Emergency keywords that require immediate human escalation
    EMERGENCY_KEYWORDS = [
        "chest pain", "can't breathe", "breathing difficulty",
        "severe bleeding", "unconscious", "suicide", "overdose",
        "heart attack", "stroke", "severe allergic reaction"
    ]
    
    # Practice information (customize per practice)
    PRACTICE_NAME = "Medical Practice"
    PRACTICE_HOURS = "Monday-Friday, 8:00 AM - 6:00 PM"
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FILE = DATA_DIR / "agent.log"
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist."""
        cls.TEST_AUDIO_DIR.mkdir(exist_ok=True)
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.VOICE_MODELS_DIR.mkdir(exist_ok=True)
        cls.OUTPUT_AUDIO_DIR.mkdir(exist_ok=True)
        cls.RECORDING_DIR.mkdir(exist_ok=True)

# Initialize directories
Config.ensure_directories()