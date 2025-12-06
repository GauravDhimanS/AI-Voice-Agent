# GPU Acceleration Guide

This guide explains how to enable GPU acceleration for the AI Voice Agent to achieve even faster performance.

## Current Status: CPU-Only ⚠️

**Right now, the system runs entirely on CPU:**
- ❌ STT (Faster-Whisper): CPU (`config.py: STT_DEVICE = "cpu"`)
- ❌ LLM (Ollama): CPU (default)
- ❌ TTS (Piper): CPU (no GPU support available)

## Components That Support GPU

### 1. Speech-to-Text (Faster-Whisper) ✅ GPU Supported

**Performance Gain**: 3-5x faster transcription

**Current**: ~0.5-1s on CPU
**With GPU**: ~0.1-0.2s on CUDA

#### How to Enable

**Step 1: Install CUDA Toolkit** (NVIDIA GPUs only)
```bash
# Download from: https://developer.nvidia.com/cuda-downloads
# Install CUDA 11.8 or 12.x
```

**Step 2: Install GPU-enabled dependencies**
```bash
# Uninstall CPU-only version
pip uninstall faster-whisper

# Install GPU-enabled version with CuBLAS support
pip install faster-whisper[cuda]

# Or for specific CUDA version:
pip install faster-whisper
pip install nvidia-cublas-cu12  # For CUDA 12.x
# OR
pip install nvidia-cublas-cu11  # For CUDA 11.x
```

**Step 3: Update config.py**
```python
# config.py
STT_DEVICE = "cuda"              # Changed from "cpu"
STT_COMPUTE_TYPE = "float16"     # GPU works best with float16
```

**Step 4: Verify GPU is being used**
```bash
python -c "from faster_whisper import WhisperModel; model = WhisperModel('base', device='cuda'); print('GPU working!')"
```

### 2. LLM (Ollama) ✅ GPU Supported

**Performance Gain**: 5-10x faster response generation

**Current**: ~2-3s for response on CPU
**With GPU**: ~0.3-0.5s for response on GPU

#### How to Enable

**Step 1: Check if Ollama is already using GPU**
```bash
# On Windows/Linux with NVIDIA GPU
ollama list
# If GPU is available, it's likely already being used
```

**Step 2: Force GPU usage (if needed)**

Ollama automatically detects and uses GPU if available. To verify:

```bash
# Pull a model and watch for GPU usage
ollama pull llama3.1:8b

# Run model and monitor GPU
nvidia-smi  # Should show ollama process
```

**Step 3: Check GPU memory**
```bash
# Monitor GPU usage while running
nvidia-smi -l 1  # Updates every second
```

**For AMD GPUs (ROCm)**:
```bash
# Set environment variable
export OLLAMA_ROCM=1
ollama serve
```

**For Apple Silicon (Metal)**:
Ollama automatically uses Metal acceleration on M1/M2/M3 Macs.

### 3. Text-to-Speech (Piper) ❌ No GPU Support

Piper ONNX models run on CPU only. However, TTS is already fast (~0.3-0.5s per sentence), so GPU acceleration would provide minimal benefit.

## Complete GPU Setup Guide

### For NVIDIA GPUs (Windows/Linux)

#### Prerequisites
- NVIDIA GPU with compute capability 6.0+ (GTX 1060 or newer)
- CUDA Toolkit 11.8 or 12.x
- cuDNN library

#### Installation Steps

**1. Install CUDA Toolkit**
```bash
# Download from https://developer.nvidia.com/cuda-downloads
# Choose your OS and follow instructions

# Verify installation
nvcc --version
```

**2. Install cuDNN**
```bash
# Download from https://developer.nvidia.com/cudnn
# Extract and copy files to CUDA installation directory
```

**3. Update Python dependencies**
```bash
# In your voice_agent virtual environment
cd AIVoiceAgent
./voice_agent/Scripts/activate  # Windows
# source voice_agent/bin/activate  # Linux/Mac

# Install GPU-enabled Faster-Whisper
pip uninstall faster-whisper
pip install faster-whisper

# Install CUDA support for Faster-Whisper
pip install nvidia-cublas-cu12  # For CUDA 12.x
pip install nvidia-cudnn-cu12
```

**4. Update config.py**
```python
# config.py
class Config:
    # STT Configuration - GPU Enabled
    STT_MODEL_SIZE = "base"          # or "small" for even faster
    STT_DEVICE = "cuda"              # Changed from "cpu"
    STT_COMPUTE_TYPE = "float16"     # GPU optimized (changed from "int8")
    STT_LANGUAGE = "en"
    STT_MIN_CONFIDENCE = 0.6
```

**5. Restart Ollama with GPU**
```bash
# Ollama should auto-detect GPU
# Verify with:
nvidia-smi

# You should see "ollama" process using GPU memory
```

**6. Test GPU Acceleration**
```bash
# Test STT with GPU
python test_stt.py test_basic_transcription

# Check logs for "device=cuda"
tail data/agent.log

# Test full voice agent
python main.py --text
```

### For AMD GPUs (Linux only)

**1. Install ROCm**
```bash
# Follow AMD ROCm installation guide for your distro
# https://rocm.docs.amd.com/
```

**2. Enable ROCm for Ollama**
```bash
export OLLAMA_ROCM=1
ollama serve
```

**3. Faster-Whisper with ROCm**
ROCm support for Faster-Whisper is experimental. CPU may be better option.

### For Apple Silicon (M1/M2/M3)

**1. Ollama with Metal**
Ollama automatically uses Metal acceleration on Apple Silicon - no configuration needed!

**2. Faster-Whisper with CoreML**
```bash
# Install CoreML support
pip install faster-whisper

# Update config.py
STT_DEVICE = "cpu"  # CoreML not directly supported yet
# CPU on M1/M2/M3 is already very fast due to Neural Engine
```

## Performance Comparison

### Speech-to-Text (STT)

| Hardware | Model | Time per 5s audio | Speedup |
|----------|-------|-------------------|---------|
| CPU (Intel i7) | base | ~0.8s | 1x |
| CPU (Intel i7) | medium | ~1.5s | - |
| GPU (RTX 3060) | base | ~0.15s | **5x** |
| GPU (RTX 3060) | medium | ~0.3s | **5x** |
| GPU (RTX 4090) | base | ~0.08s | **10x** |

### LLM Response (Ollama)

| Hardware | Model | Tokens/sec | Time for 50 tokens |
|----------|-------|------------|-------------------|
| CPU (Intel i7) | llama3.1:8b | ~15 tok/s | ~3.3s |
| GPU (RTX 3060) | llama3.1:8b | ~60 tok/s | ~0.8s |
| GPU (RTX 4090) | llama3.1:8b | ~120 tok/s | ~0.4s |

### Overall Response Time

| Setup | Time to First Audio | Total Response |
|-------|---------------------|----------------|
| **CPU Only** (current) | 1-2s | 2-4s |
| **STT GPU + LLM CPU** | 0.8-1.2s | 1.5-3s |
| **STT CPU + LLM GPU** | 1.2-1.8s | 1-2s |
| **STT GPU + LLM GPU** | **0.5-0.8s** | **0.8-1.5s** |

## Verifying GPU Usage

### Check STT is using GPU

**Method 1: Check logs**
```bash
python main.py --text --debug

# In logs, look for:
# "Initializing STT with model=base, device=cuda"
```

**Method 2: Monitor GPU**
```bash
# While running voice agent, in another terminal:
nvidia-smi -l 1

# You should see python process using GPU memory
```

### Check Ollama is using GPU

```bash
# While agent is running:
nvidia-smi

# Look for "ollama" process
# GPU Memory Usage should be ~3-8GB for llama3.1:8b
```

### Benchmark Script

Create a test script to compare CPU vs GPU:

```python
# benchmark_gpu.py
import time
from modules import SpeechToText
from pathlib import Path

# Test audio file
audio_file = Path("test_audio/test.wav")

# CPU benchmark
print("Testing CPU...")
stt_cpu = SpeechToText(model_size="base", device="cpu")
start = time.time()
result = stt_cpu.transcribe(audio_file)
cpu_time = time.time() - start
print(f"CPU: {cpu_time:.3f}s")

# GPU benchmark
print("\nTesting GPU...")
stt_gpu = SpeechToText(model_size="base", device="cuda")
start = time.time()
result = stt_gpu.transcribe(audio_file)
gpu_time = time.time() - start
print(f"GPU: {gpu_time:.3f}s")

print(f"\nSpeedup: {cpu_time/gpu_time:.2f}x")
```

## Troubleshooting

### "CUDA out of memory"

**Solution 1**: Use smaller STT model
```python
STT_MODEL_SIZE = "tiny"  # Uses less GPU memory
```

**Solution 2**: Reduce Ollama model size
```bash
ollama pull llama3.2:3b  # Smaller model
```

**Solution 3**: Close other GPU applications

### "CUDA not available" or "No CUDA GPUs are available"

**Check CUDA installation**:
```bash
nvidia-smi
nvcc --version
```

**Check PyTorch CUDA**:
```bash
python -c "import torch; print(torch.cuda.is_available())"
```

**Reinstall CUDA support**:
```bash
pip install nvidia-cublas-cu12 --force-reinstall
```

### Ollama not using GPU

**Check GPU compatibility**:
```bash
# Ollama requires compute capability 6.0+
nvidia-smi --query-gpu=compute_cap --format=csv
```

**Force GPU usage**:
```bash
# Set environment variable
export CUDA_VISIBLE_DEVICES=0
ollama serve
```

### Slower on GPU than CPU

This can happen with very small workloads due to GPU initialization overhead.

**Solution**: Use larger models to benefit from GPU:
```python
STT_MODEL_SIZE = "small"  # or "medium"
```

## Recommended GPU Configurations

### Budget Setup (GTX 1660 / RTX 3050)
```python
# config.py
STT_MODEL_SIZE = "base"
STT_DEVICE = "cuda"
STT_COMPUTE_TYPE = "float16"
LLM_MODEL = "llama3.2:3b"  # Smaller model for limited VRAM
```

**Expected**: 2-3x speedup, ~0.8-1.2s response time

### Mid-Range Setup (RTX 3060 / 3070)
```python
# config.py
STT_MODEL_SIZE = "small"
STT_DEVICE = "cuda"
STT_COMPUTE_TYPE = "float16"
LLM_MODEL = "llama3.1:8b"
```

**Expected**: 4-5x speedup, ~0.5-0.8s response time

### High-End Setup (RTX 4080 / 4090)
```python
# config.py
STT_MODEL_SIZE = "medium"  # Best accuracy
STT_DEVICE = "cuda"
STT_COMPUTE_TYPE = "float16"
LLM_MODEL = "llama3.1:8b"
```

**Expected**: 8-10x speedup, ~0.3-0.5s response time

## Summary

### What Uses GPU Now: **NOTHING** ❌
- STT: CPU (config.py: `STT_DEVICE = "cpu"`)
- LLM: CPU (Ollama default on your system)
- TTS: CPU (no GPU support)

### What CAN Use GPU:
- ✅ **STT (Faster-Whisper)**: 3-5x speedup with CUDA
- ✅ **LLM (Ollama)**: 5-10x speedup with CUDA
- ❌ **TTS (Piper)**: No GPU support

### How to Enable GPU:
1. Install CUDA Toolkit + cuDNN
2. Install GPU-enabled Faster-Whisper: `pip install nvidia-cublas-cu12`
3. Update `config.py`: `STT_DEVICE = "cuda"`, `STT_COMPUTE_TYPE = "float16"`
4. Verify Ollama is using GPU: `nvidia-smi`

### Expected Performance with GPU:
- Current (CPU only): 1-2s time to first audio
- With GPU: **0.5-0.8s** time to first audio
- **Overall speedup: 2-4x faster**

---

**Ready to enable GPU? Follow the "Complete GPU Setup Guide" section above!**
