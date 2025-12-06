"""
Integration test for the complete voice agent system.

This script tests the full conversation flow in text mode.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import VoiceAgent
from config import Config
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_text_mode_conversation():
    """Test a complete conversation in text mode."""
    print("\n" + "="*70)
    print("INTEGRATION TEST: Text Mode Conversation")
    print("="*70)
    print("\nThis test simulates a complete appointment booking conversation.")
    print("The agent will ask questions, and you can type your responses.")
    print("\nType 'exit' to end the conversation early.\n")

    try:
        # Create agent in text mode
        agent = VoiceAgent(
            text_mode=True,
            save_recordings=False,
            save_responses=False
        )

        # Run conversation
        agent.run_conversation()

        # Show final state
        state = agent.get_state()

        print("\n" + "="*70)
        print("FINAL CONVERSATION STATE")
        print("="*70)
        print(f"Stage: {state.stage.value}")
        print(f"Patient Name: {state.patient_name or 'Not collected'}")
        print(f"Reason: {state.reason or 'Not collected'}")
        print(f"Preferred Date: {state.preferred_date or 'Not collected'}")
        print(f"Preferred Time: {state.preferred_time or 'Not collected'}")
        print(f"Total Turns: {len(state.conversation_history)}")
        print("="*70)

        return True

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False


def test_simulated_conversation():
    """Test with simulated user inputs."""
    print("\n" + "="*70)
    print("INTEGRATION TEST: Simulated Conversation")
    print("="*70)

    try:
        from modules import MedicalConversationAgent

        # Create agent
        agent = MedicalConversationAgent()

        # Simulated conversation
        test_inputs = [
            "Hi, I need to book an appointment",
            "My name is John Smith",
            "I have a sore throat and fever",
            "Tomorrow afternoon would be good",
            "Yes, that works for me"
        ]

        print("\nSimulating conversation...\n")

        for i, user_input in enumerate(test_inputs, 1):
            print(f"Turn {i}:")
            print(f"  User: {user_input}")

            response = agent.chat(user_input)
            print(f"  Agent: {response}")

            # Check for emergency
            if agent.state.emergency_detected:
                print("  ⚠️  EMERGENCY DETECTED!")
                break

            # Check if complete
            if agent.is_complete():
                print("  ✓ Conversation complete!")
                break

            print()

        # Show final state
        state = agent.state

        print("\n" + "="*70)
        print("SIMULATION RESULTS")
        print("="*70)
        print(f"Completed: {agent.is_complete()}")
        print(f"Final Stage: {state.stage.value}")
        print(f"Patient Name: {state.patient_name}")
        print(f"Reason: {state.reason}")
        print(f"Preferred Date: {state.preferred_date}")
        print(f"Preferred Time: {state.preferred_time}")
        print("="*70)

        return True

    except Exception as e:
        logger.error(f"Simulation failed: {e}", exc_info=True)
        return False


def test_emergency_detection():
    """Test emergency keyword detection."""
    print("\n" + "="*70)
    print("INTEGRATION TEST: Emergency Detection")
    print("="*70)

    try:
        from modules import MedicalConversationAgent

        agent = MedicalConversationAgent()

        # Test emergency phrases
        emergency_phrases = [
            "I'm having severe chest pain",
            "I can't breathe properly",
            "Someone had a heart attack"
        ]

        print("\nTesting emergency detection...\n")

        for phrase in emergency_phrases:
            print(f"Input: '{phrase}'")
            response = agent.chat(phrase)
            print(f"Response: {response}")
            print(f"Emergency Detected: {agent.state.emergency_detected}")
            print()

            # Reset for next test
            agent = MedicalConversationAgent()

        print("✓ Emergency detection test complete")
        return True

    except Exception as e:
        logger.error(f"Emergency test failed: {e}", exc_info=True)
        return False


def main():
    """Run all integration tests."""
    print("\n" + "="*70)
    print("VOICE AGENT INTEGRATION TEST SUITE")
    print("="*70)

    tests = {
        'Simulated Conversation': test_simulated_conversation,
        'Emergency Detection': test_emergency_detection,
        'Interactive Text Mode': test_text_mode_conversation,
    }

    # Ask which test to run
    print("\nAvailable tests:")
    for i, name in enumerate(tests.keys(), 1):
        print(f"  {i}. {name}")
    print(f"  {len(tests) + 1}. Run all automated tests (skip interactive)")

    try:
        choice = input("\nSelect test (1-{}): ".format(len(tests) + 1)).strip()
        choice_num = int(choice)

        if choice_num == len(tests) + 1:
            # Run automated tests only
            results = {}
            for name, test_func in tests.items():
                if name != 'Interactive Text Mode':
                    results[name] = test_func()

            # Summary
            print("\n" + "="*70)
            print("TEST SUMMARY")
            print("="*70)
            for name, passed in results.items():
                status = "✓ PASSED" if passed else "✗ FAILED"
                print(f"{status}: {name}")
            print("="*70)

        elif 1 <= choice_num <= len(tests):
            # Run selected test
            test_name = list(tests.keys())[choice_num - 1]
            test_func = tests[test_name]
            test_func()
        else:
            print("Invalid choice")

    except (ValueError, IndexError):
        print("Invalid input")
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")


if __name__ == "__main__":
    main()
