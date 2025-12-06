"""
Voice model download script for Piper TTS.

This script downloads the recommended voice model for the medical voice agent.
"""

import sys
import urllib.request
from pathlib import Path
from config import Config

# Voice model to download
VOICE_NAME = "en_US-lessac-medium"
BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium"

FILES = [
    f"{VOICE_NAME}.onnx",
    f"{VOICE_NAME}.onnx.json"
]


def download_file(url: str, dest_path: Path):
    """Download a file with progress indication."""
    print(f"Downloading: {dest_path.name}")
    print(f"From: {url}")

    try:
        def report_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(100, (downloaded / total_size) * 100) if total_size > 0 else 0
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)

            # Print progress bar
            bar_length = 40
            filled = int(bar_length * percent / 100)
            bar = '=' * filled + '-' * (bar_length - filled)
            print(f'\r[{bar}] {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)', end='')

        urllib.request.urlretrieve(url, dest_path, reporthook=report_progress)
        print()  # New line after progress
        print(f"✓ Downloaded: {dest_path.name}")
        return True

    except Exception as e:
        print(f"\n✗ Failed to download: {e}")
        return False


def main():
    """Download voice model files."""
    print("="*70)
    print("PIPER TTS VOICE MODEL DOWNLOADER")
    print("="*70)
    print(f"\nVoice: {VOICE_NAME}")
    print(f"Destination: {Config.VOICE_MODELS_DIR}")
    print()

    # Ensure directory exists
    Config.VOICE_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Download each file
    success_count = 0
    for filename in FILES:
        dest_path = Config.VOICE_MODELS_DIR / filename

        # Check if already exists
        if dest_path.exists():
            print(f"⚠ File already exists: {filename}")
            response = input("  Overwrite? (y/n): ").strip().lower()
            if response != 'y':
                print("  Skipping...")
                success_count += 1
                continue

        # Download
        url = f"{BASE_URL}/{filename}"
        if download_file(url, dest_path):
            success_count += 1

        print()

    # Summary
    print("="*70)
    if success_count == len(FILES):
        print("✓ SUCCESS! All voice model files are ready.")
        print(f"\nFiles installed in: {Config.VOICE_MODELS_DIR}")
        print("\nYou can now run:")
        print("  python test_tts.py test_basic_synthesis")
    else:
        print(f"⚠ WARNING: Only {success_count}/{len(FILES)} files were downloaded.")
        print("\nPlease check the errors above and try again.")
        print("You can also download manually from:")
        print(f"  {BASE_URL}")
        return 1

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nDownload cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
