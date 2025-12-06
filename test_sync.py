"""
Test script to demonstrate the synchronization issue and verify the fix.

This simulates concurrent requests hitting the server and shows whether
race conditions occur.
"""

import asyncio
import aiohttp
import time
from pathlib import Path

# Test audio file (should exist from your tests)
TEST_AUDIO = Path("test_audio/sample.wav")

# Choose which server to test
SERVER_ORIGINAL = "http://localhost:8000/api/voice"
SERVER_FIXED = "http://localhost:8001/api/voice"


async def send_audio_chunk(session, url, session_id, chunk_num, delay=0):
    """Send an audio chunk to the server."""
    if delay > 0:
        await asyncio.sleep(delay)

    # Create a simple WAV if test file doesn't exist
    if not TEST_AUDIO.exists():
        print(f"Warning: {TEST_AUDIO} not found, using placeholder")
        # You'd need to create a test file or use a real recording
        return None

    start_time = time.time()
    print(f"[Chunk {chunk_num}] Sending at {start_time:.2f}s...")

    try:
        with open(TEST_AUDIO, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('audio', f, filename='test.wav', content_type='audio/wav')
            data.add_field('session_id', session_id)
            data.add_field('mime_type', 'audio/wav')

            async with session.post(url, data=data) as response:
                result = await response.json()
                end_time = time.time()
                duration = end_time - start_time

                print(f"[Chunk {chunk_num}] Response at {end_time:.2f}s (took {duration:.2f}s)")
                print(f"  User: {result.get('user_text', 'N/A')}")
                print(f"  Agent: {result.get('reply_text', 'N/A')[:80]}...")

                return {
                    'chunk': chunk_num,
                    'start': start_time,
                    'end': end_time,
                    'duration': duration,
                    'user_text': result.get('user_text'),
                    'reply_text': result.get('reply_text')
                }

    except Exception as e:
        print(f"[Chunk {chunk_num}] ERROR: {e}")
        return None


async def test_parallel_requests(url, num_chunks=3):
    """
    Send multiple chunks in parallel (simulates the race condition).

    This is what happens in the ORIGINAL version - all chunks sent without
    waiting for previous ones to complete.
    """
    print("\n" + "="*70)
    print(f"TEST: Parallel Requests (Original Behavior)")
    print(f"Sending {num_chunks} chunks simultaneously to {url}")
    print("="*70 + "\n")

    session_id = "test-parallel-" + str(int(time.time()))

    async with aiohttp.ClientSession() as session:
        # Send all chunks at once (PARALLEL)
        tasks = [
            send_audio_chunk(session, url, session_id, i)
            for i in range(num_chunks)
        ]

        results = await asyncio.gather(*tasks)

    # Analyze results
    print("\n" + "-"*70)
    print("ANALYSIS:")
    print("-"*70)

    replies = [r['reply_text'] for r in results if r and r['reply_text']]
    unique_replies = set(replies)

    print(f"Total requests: {num_chunks}")
    print(f"Successful responses: {len([r for r in results if r])}")
    print(f"Unique agent replies: {len(unique_replies)}")

    if len(unique_replies) < len(replies):
        print("⚠️  DUPLICATE RESPONSES DETECTED!")
        print(f"   Same response repeated {len(replies) - len(unique_replies)} times")
    else:
        print("✓  No duplicate responses")

    return results


async def test_sequential_requests(url, num_chunks=3):
    """
    Send chunks sequentially (simulates the FIXED version).

    Each chunk waits for the previous one to complete before sending.
    """
    print("\n" + "="*70)
    print(f"TEST: Sequential Requests (Fixed Behavior)")
    print(f"Sending {num_chunks} chunks one-by-one to {url}")
    print("="*70 + "\n")

    session_id = "test-sequential-" + str(int(time.time()))

    async with aiohttp.ClientSession() as session:
        results = []
        for i in range(num_chunks):
            result = await send_audio_chunk(session, url, session_id, i)
            results.append(result)

    # Analyze results
    print("\n" + "-"*70)
    print("ANALYSIS:")
    print("-"*70)

    replies = [r['reply_text'] for r in results if r and r['reply_text']]
    unique_replies = set(replies)

    print(f"Total requests: {num_chunks}")
    print(f"Successful responses: {len([r for r in results if r])}")
    print(f"Unique agent replies: {len(unique_replies)}")

    if len(unique_replies) < len(replies):
        print("⚠️  DUPLICATE RESPONSES DETECTED!")
    else:
        print("✓  All responses unique (expected with sequential processing)")

    return results


async def test_overlapping_requests(url, num_chunks=3, interval=1.0):
    """
    Send chunks with slight delays (simulates chunks sent every 2 seconds).

    This is the realistic scenario - chunks sent at regular intervals while
    previous ones might still be processing.
    """
    print("\n" + "="*70)
    print(f"TEST: Overlapping Requests (Realistic Scenario)")
    print(f"Sending {num_chunks} chunks with {interval}s interval to {url}")
    print("="*70 + "\n")

    session_id = "test-overlap-" + str(int(time.time()))

    async with aiohttp.ClientSession() as session:
        # Send chunks with staggered start times
        tasks = [
            send_audio_chunk(session, url, session_id, i, delay=i * interval)
            for i in range(num_chunks)
        ]

        results = await asyncio.gather(*tasks)

    # Analyze results
    print("\n" + "-"*70)
    print("ANALYSIS:")
    print("-"*70)

    # Check for overlaps
    overlaps = 0
    for i in range(len(results) - 1):
        if results[i] and results[i+1]:
            if results[i]['end'] > results[i+1]['start']:
                overlaps += 1
                print(f"⚠️  Chunk {i} and {i+1} overlapped!")
                print(f"   Chunk {i} ended at {results[i]['end']:.2f}s")
                print(f"   Chunk {i+1} started at {results[i+1]['start']:.2f}s")

    if overlaps > 0:
        print(f"\n⚠️  {overlaps} overlapping requests detected (indicates race conditions)")
    else:
        print("\n✓  No overlapping requests (good!)")

    # Check for duplicates
    replies = [r['reply_text'] for r in results if r and r['reply_text']]
    unique_replies = set(replies)

    if len(unique_replies) < len(replies):
        print(f"⚠️  {len(replies) - len(unique_replies)} duplicate responses")
    else:
        print("✓  All responses unique")

    return results


async def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("SYNCHRONIZATION TEST SUITE")
    print("="*70)
    print("\nThis script tests for race conditions by sending multiple")
    print("audio chunks to the server and checking for duplicates.")
    print("\nMake sure one of the servers is running:")
    print("  Original: uvicorn server:app --port 8000")
    print("  Fixed:    uvicorn server_fixed:app --port 8001")
    print("="*70)

    # Check which servers are available
    available_servers = []

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/api/health", timeout=2) as resp:
                if resp.status == 200:
                    available_servers.append(("Original", SERVER_ORIGINAL))
                    print("\n✓ Original server running on port 8000")
    except:
        print("\n✗ Original server not running on port 8000")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8001/api/health", timeout=2) as resp:
                if resp.status == 200:
                    available_servers.append(("Fixed", SERVER_FIXED))
                    print("✓ Fixed server running on port 8001")
    except:
        print("✗ Fixed server not running on port 8001")

    if not available_servers:
        print("\n❌ No servers running! Start at least one server first.")
        return

    print("\n" + "="*70)

    # Test each available server
    for name, url in available_servers:
        print(f"\n{'='*70}")
        print(f"TESTING: {name} Server ({url})")
        print("="*70)

        # Test 1: Parallel (worst case)
        await test_parallel_requests(url, num_chunks=3)
        await asyncio.sleep(2)  # Brief pause between tests

        # Test 2: Overlapping (realistic case)
        await test_overlapping_requests(url, num_chunks=3, interval=1.5)
        await asyncio.sleep(2)

        # Test 3: Sequential (control)
        await test_sequential_requests(url, num_chunks=3)

    print("\n" + "="*70)
    print("TESTS COMPLETE")
    print("="*70)
    print("\nCompare results between Original and Fixed servers.")
    print("Fixed server should show no duplicates and no overlaps.")
    print("="*70 + "\n")


if __name__ == "__main__":
    # Check if test audio exists
    if not TEST_AUDIO.exists():
        print(f"\n⚠️  Warning: Test audio file not found at {TEST_AUDIO}")
        print("This script needs a real audio file to test with.")
        print("You can:")
        print("  1. Record a short audio file and save as test_audio/sample.wav")
        print("  2. Or modify TEST_AUDIO path in the script")
        print("\nExiting...\n")
    else:
        asyncio.run(main())
