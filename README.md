# AI Voice Agent for Medical Appointment Booking

A complete voice-enabled system that automates medical appointment scheduling through natural conversation. The system uses local AI models for speech recognition, conversation management, and speech synthesis.

## Features

- **Speech-to-Text (STT)**: Fast, accurate transcription using Faster-Whisper
- **Conversation AI (LLM)**: Natural dialogue using Ollama (llama3.1:8b)
- **Text-to-Speech (TTS)**: Professional voice synthesis using Piper
- **Complete Voice Loop**: Listen → Transcribe → Process → Respond → Speak
- **Emergency Detection**: Identifies urgent medical situations
- **Session Management**: Tracks conversation state and history
- **Dual Mode**: Voice or text-based interaction

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Download TTS voice model
python download_voice_model.py
```

### 2. Setup Ollama

Make sure Ollama is running with the llama3.1:8b model:

```bash
# Install Ollama from https://ollama.ai
# Then pull the model:
ollama pull llama3.1:8b

# Start Ollama (it usually runs automatically)
ollama serve
```

### 3. Run the Agent

**Text Mode** (no voice I/O, good for testing):
```bash
python main.py --text
```

**Voice Mode** (full voice interaction with streaming for low latency):
```bash
python main.py
```

**Note**: Voice mode uses streaming responses for significantly lower latency (~1-2s to first audio vs 4-7s)

**With options**:
```bash
python main.py --text --debug                  # Text mode with debug logging
python main.py --no-save-recordings            # Don't save audio recordings
python main.py --no-save-responses             # Don't save TTS responses
```

## Project Structure

```
AIVoiceAgent/
├── main.py                     # Main orchestrator
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── download_voice_model.py     # Voice model downloader
├── modules/
│   ├── __init__.py
│   ├── stt.py                  # Speech-to-Text module
│   ├── llm.py                  # LLM conversation agent
│   └── tts.py                  # Text-to-Speech module
├── test_stt.py                 # STT tests
├── test_llm.py                 # LLM tests
├── test_tts.py                 # TTS tests
├── test_integration.py         # Full integration tests
├── data/
│   ├── recordings/             # Saved audio recordings
│   ├── output_audio/           # TTS generated audio
│   └── agent.log               # Session logs
├── voice_models/               # Piper TTS voice models
└── test_audio/                 # Test audio files
```

## Usage Examples

### Text Mode (Interactive Testing)

```bash
$ python main.py --text

======================================================================
MEDICAL APPOINTMENT VOICE AGENT
======================================================================
Practice: Medical Practice
Hours: Monday-Friday, 8:00 AM - 6:00 PM
Mode: Text
======================================================================

🤖 Agent: Hello! Welcome to Medical Practice. How can I help you today?

👤 You: I need to book an appointment
🤖 Agent: I'd be happy to help you schedule an appointment. May I have your name please?

👤 You: John Smith
🤖 Agent: Thank you, John. What is the reason for your visit?

👤 You: I have a sore throat
🤖 Agent: I understand. What date and time would work best for you?

👤 You: Tomorrow afternoon
🤖 Agent: Great! I have you scheduled for tomorrow afternoon. Is there anything else I can help you with?

👤 You: No, that's all
🤖 Agent: Thank you for calling. Have a great day!
```

### Voice Mode

```bash
$ python main.py

======================================================================
MEDICAL APPOINTMENT VOICE AGENT
======================================================================
Practice: Medical Practice
Hours: Monday-Friday, 8:00 AM - 6:00 PM
Mode: Voice
======================================================================

[Agent speaks welcome message]
🎤 Listening... (speak now)
[You speak your request]
🔄 Transcribing...
👤 You said: I need to book an appointment
🤔 Processing...
🤖 Agent: I'd be happy to help you schedule an appointment...
🔊 Speaking...
[Agent's response is spoken aloud]
```

## Testing

### Individual Module Tests

```bash
# Test Speech-to-Text
python test_stt.py test_basic_transcription

# Test LLM Conversation
python test_llm.py test_conversation_flow

# Test Text-to-Speech
python test_tts.py test_basic_synthesis
```

### Integration Tests

```bash
# Run integration test suite
python test_integration.py

# Test text mode conversation
python test_integration.py
# Select option 3 for interactive text conversation
```

### Run All Tests

```bash
# STT tests
python test_stt.py all

# LLM tests
python test_llm.py all

# TTS tests
python test_tts.py all
```

## Configuration

Edit `config.py` to customize:

### STT Settings
- `STT_MODEL_SIZE`: Whisper model size (tiny/base/small/medium/large)
- `STT_LANGUAGE`: Language code (e.g., "en", "de")
- `STT_MIN_CONFIDENCE`: Minimum confidence threshold

### TTS Settings
- `TTS_MODEL_PATH`: Path to Piper voice model
- `TTS_SAMPLE_RATE`: Audio sample rate

### LLM Settings
- `LLM_MODEL`: Ollama model name
- `LLM_BASE_URL`: Ollama API URL
- `LLM_TEMPERATURE`: Response creativity (0.0-1.0)

### Audio Recording
- `AUDIO_SAMPLE_RATE`: Recording sample rate
- `AUDIO_MAX_RECORDING_TIME`: Max recording duration
- `AUDIO_SILENCE_DURATION`: Silence detection threshold

### Conversation
- `CONVERSATION_MAX_TURNS`: Maximum conversation turns
- `EMERGENCY_KEYWORDS`: Emergency detection keywords
- `PRACTICE_NAME`: Your practice name
- `PRACTICE_HOURS`: Practice operating hours

## Conversation Flow

The agent follows a structured conversation flow:

1. **GREETING** - Welcome the patient
2. **NAME_COLLECTION** - Get patient's name
3. **REASON_COLLECTION** - Understand reason for visit
4. **DATETIME_COLLECTION** - Get preferred appointment time
5. **CONFIRMATION** - Confirm all details
6. **COMPLETED** - Finish conversation

The agent automatically:
- Detects emergency keywords and escalates
- Extracts appointment information from natural language
- Maintains conversation context
- Handles edge cases and errors gracefully

## Safety Features

- **Emergency Detection**: Recognizes life-threatening situations
- **Human Escalation**: Transfers complex cases to staff
- **No Medical Advice**: Only books appointments
- **Conversation Limits**: Prevents infinite loops
- **Confidence Thresholds**: Ensures transcription quality
- **Session Logging**: Tracks all interactions

## Troubleshooting

### "Voice model not found"
Run the voice model downloader:
```bash
python download_voice_model.py
```

### "Ollama connection failed"
Ensure Ollama is running:
```bash
ollama serve
```

### "Audio device not found"
Check your microphone is connected and accessible. Use text mode as fallback:
```bash
python main.py --text
```

### Low transcription confidence
- Speak more clearly
- Reduce background noise
- Move closer to microphone
- Adjust `STT_MIN_CONFIDENCE` in config.py

## System Requirements

- **Python**: 3.8+
- **OS**: Windows, macOS, or Linux
- **RAM**: 4GB minimum (8GB recommended for medium Whisper model)
- **Disk**: 2GB for models
- **Microphone**: Required for voice mode
- **Speakers**: Required for voice mode
- **Internet**: Only for initial setup (downloading models)

## Local & Private

This system runs **completely offline** after setup:
- Speech recognition: Local Whisper model
- Conversation AI: Local Ollama model
- Speech synthesis: Local Piper model
- No cloud APIs or data transmission
- Patient privacy protected

## Performance

### Optimized Response Times (with streaming):
- **Time to first audio**: ~1-2 seconds (85% faster!)
- **Perceived latency**: ~1-3 seconds total
- Speech recognition: ~0.5-1 seconds (using base model)
- LLM response: Streaming (user hears response immediately)
- Speech synthesis: Streaming (sentence-by-sentence playback)

### Legacy Response Times (non-streaming):
- Speech recognition: ~1-2 seconds per utterance
- LLM response: ~2-4 seconds
- Speech synthesis: ~0.5-1 seconds
- **Total turn time**: ~4-7 seconds

**See [LATENCY_OPTIMIZATION.md](LATENCY_OPTIMIZATION.md) for detailed performance tuning guide.**

## Development

### Adding New Features

The modular architecture makes it easy to extend:

- **New conversation stages**: Edit `ConversationStage` enum in `modules/llm.py`
- **Custom voice**: Download different Piper voice and update `config.py`
- **Different LLM**: Change `LLM_MODEL` in `config.py`
- **Enhanced STT**: Adjust Whisper model size in `config.py`

### Code Structure

- **main.py**: `VoiceAgent` class orchestrates all components
- **modules/stt.py**: `SpeechToText` handles audio → text
- **modules/llm.py**: `MedicalConversationAgent` manages dialogue
- **modules/tts.py**: `TextToSpeech` handles text → audio
- **config.py**: Centralized configuration

## License

This project is for educational and research purposes.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review test files for usage examples
3. Check logs in `data/agent.log`

## Acknowledgments

Built with:
- [Faster-Whisper](https://github.com/guillaumekln/faster-whisper) - Speech recognition
- [Ollama](https://ollama.ai) - Local LLM inference
- [Piper](https://github.com/rhasspy/piper) - Text-to-speech

---

**Note**: This is a proof-of-concept system. For production medical use, ensure compliance with HIPAA and local regulations.
