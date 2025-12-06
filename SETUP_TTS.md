# Text-to-Speech Setup Guide

This guide will help you set up Piper TTS for the voice agent.

## Prerequisites

Make sure you have installed the required dependencies:

```bash
pip install -r requirements.txt
```

## Downloading Voice Models

Piper TTS requires voice model files to work. Follow these steps:

### Step 1: Choose a Voice

Visit the Piper voices repository to browse available voices:
- **GitHub**: https://github.com/rhasspy/piper/blob/master/VOICES.md
- **Samples**: https://rhasspy.github.io/piper-samples/

**Recommended voices for medical assistant:**
- `en_US-lessac-medium` - Professional, clear US English (RECOMMENDED)
- `en_US-amy-medium` - Friendly female US English
- `en_US-ryan-high` - Professional male US English

### Step 2: Download Voice Files

1. Go to the Piper releases page:
   https://github.com/rhasspy/piper/releases

2. Find the latest release and download BOTH files for your chosen voice:
   - `en_US-lessac-medium.onnx` (model file)
   - `en_US-lessac-medium.onnx.json` (config file)

   Example direct links (v1.2.0):
   - https://github.com/rhasspy/piper/releases/download/v1.2.0/voice-en_US-lessac-medium.tar.gz

3. Extract the files if they're in a .tar.gz archive

### Step 3: Place Voice Files

Copy the downloaded files to the `voice_models` directory:

```
AIVoiceAgent/
└── voice_models/
    ├── en_US-lessac-medium.onnx
    └── en_US-lessac-medium.onnx.json
```

The `voice_models` directory is automatically created when you run the code.

### Alternative: Using wget/curl (Linux/Mac)

```bash
cd voice_models

# Download lessac medium voice
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

### Alternative: Using PowerShell (Windows)

```powershell
cd voice_models

# Download lessac medium voice
Invoke-WebRequest -Uri "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx" -OutFile "en_US-lessac-medium.onnx"
Invoke-WebRequest -Uri "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json" -OutFile "en_US-lessac-medium.onnx.json"
```

## Configuration

The default configuration in `config.py` is already set up for `en_US-lessac-medium`:

```python
TTS_MODEL_PATH = VOICE_MODELS_DIR / "en_US-lessac-medium.onnx"
TTS_VOICE = "en_US-lessac-medium"
```

If you want to use a different voice, update these settings in `config.py`.

## Testing

Once the voice files are in place, test the TTS module:

### Basic Test
```bash
python test_tts.py test_basic_synthesis
```

### Medical Responses Test
```bash
python test_tts.py test_medical_responses
```

### Interactive Test
```bash
python test_tts.py test_interactive
```

### Run All Tests
```bash
python test_tts.py all
```

## Troubleshooting

### Error: "Voice model not found"
- Make sure both `.onnx` and `.onnx.json` files are in the `voice_models` directory
- Check that the filenames match exactly (case-sensitive)
- Verify the path in `config.py` matches your downloaded voice

### Error: "Audio playback failed"
- This is normal on some systems (e.g., headless servers)
- Audio files are still generated successfully in `data/output_audio/`
- You can disable auto-playback: `tts.synthesize(text, auto_play=False)`

### Slow Performance
- Consider using a smaller model (e.g., `low` quality instead of `medium` or `high`)
- Medium quality models are recommended for good balance of quality and speed

## Voice Model Sizes

- **Low**: Fastest, smaller file size, decent quality
- **Medium**: Good balance (RECOMMENDED)
- **High**: Best quality, slower, larger file size

## Additional Resources

- **Piper GitHub**: https://github.com/rhasspy/piper
- **Voice Samples**: https://rhasspy.github.io/piper-samples/
- **HuggingFace Repo**: https://huggingface.co/rhasspy/piper-voices
- **Documentation**: https://github.com/rhasspy/piper/blob/master/README.md

## Quick Start (Summary)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download voice model (choose one method)
# Method A: Manual download from https://github.com/rhasspy/piper/releases
# Method B: Use wget/curl/PowerShell commands above

# 3. Test it
python test_tts.py test_basic_synthesis

# 4. Use in your code
from modules.tts import TextToSpeech

tts = TextToSpeech()
tts.speak("Hello, welcome to our medical practice!")
```

## Success!

If everything is set up correctly, you should hear a clear, professional voice saying your text. The TTS module is now ready to integrate with the full voice agent system!
