"""
Test script for LLM Conversation Module.
"""

import logging
from modules.llm import MedicalConversationAgent, ConversationState
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_conversation_basic():
    """Test basic conversation flow."""
    print("\n" + "="*60)
    print("TEST 1: Basic Conversation Flow")
    print("="*60)
    
    agent = MedicalConversationAgent()
    print(f"\n✓ Initialized: {agent}")
    
    # Start conversation
    greeting, state = agent.start_conversation()
    print(f"\n🤖 Agent: {greeting}")
    
    # Simulate patient responses
    test_conversation = [
        "Hi, my name is John Smith",
        "I have a sore throat and need to see a doctor",
        "Tomorrow morning would be great",
        "Yes, that sounds perfect"
    ]
    
    for user_input in test_conversation:
        print(f"\n👤 Patient: {user_input}")
        response = agent.generate_response(user_input, state)
        print(f"🤖 Agent: {response}")
        
        # Show state
        print(f"\n📊 State: {state.stage.value}")
        print(f"   Collected: {state.get_collected_info()}")
    
    print(f"\n✓ Conversation complete!")
    print(f"   Total turns: {state.turn_count}")
    print(f"   Information complete: {state.is_complete()}")


def test_emergency_detection():
    """Test emergency keyword detection."""
    print("\n" + "="*60)
    print("TEST 2: Emergency Detection")
    print("="*60)
    
    agent = MedicalConversationAgent()
    _, state = agent.start_conversation()
    
    emergency_inputs = [
        "I'm having severe chest pain",
        "I can't breathe properly",
        "There's heavy bleeding that won't stop"
    ]
    
    print("\nTesting emergency detection:")
    for user_input in emergency_inputs:
        print(f"\n👤 Patient: {user_input}")
        response = agent.generate_response(user_input, state)
        print(f"🤖 Agent: {response}")
        
        if state.emergency_detected:
            print("✓ Emergency correctly detected!")
            state.emergency_detected = False  # Reset for next test


def test_information_extraction():
    """Test information extraction from user input."""
    print("\n" + "="*60)
    print("TEST 3: Information Extraction")
    print("="*60)
    
    agent = MedicalConversationAgent()
    
    test_cases = [
        {
            "input": "My name is Sarah Johnson",
            "stage": "collect_name",
            "expect": "name"
        },
        {
            "input": "I need to come in for a checkup",
            "stage": "collect_reason",
            "expect": "reason"
        },
        {
            "input": "Tomorrow afternoon would work",
            "stage": "collect_datetime",
            "expect": "date and time"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest case {i}: {test['stage']}")
        print(f"  Input: {test['input']}")
        
        state = ConversationState()
        extracted = agent._extract_information(test['input'], state)
        
        print(f"  Extracted: {extracted}")
        print(f"  Expected to find: {test['expect']}")


def test_interactive_conversation():
    """Interactive conversation test - chat with the agent."""
    print("\n" + "="*60)
    print("TEST 4: Interactive Conversation")
    print("="*60)
    print("\nYou can now chat with the agent!")
    print("Type 'quit' to exit.\n")
    
    agent = MedicalConversationAgent()
    greeting, state = agent.start_conversation()
    
    print(f"🤖 Agent: {greeting}\n")
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n✓ Conversation ended")
                print(f"   Final state: {state.to_dict()}")
                break
            
            response = agent.generate_response(user_input, state)
            print(f"🤖 Agent: {response}\n")
            
            # Show collected info
            collected = state.get_collected_info()
            if any(collected.values()):
                print(f"   [Collected: {', '.join(f'{k}={v}' for k, v in collected.items() if v)}]")
            
            if state.is_complete():
                print("\n✓ All information collected!")
                print(f"   Ready to book appointment for: {collected}\n")
                
        except KeyboardInterrupt:
            print("\n\n✓ Conversation interrupted")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}")
            break


def test_state_management():
    """Test conversation state management."""
    print("\n" + "="*60)
    print("TEST 5: State Management")
    print("="*60)
    
    state = ConversationState()
    print(f"\n📊 Initial state: {state.to_dict()}")
    
    # Simulate collecting information
    state.patient_name = "Alice Brown"
    state.add_turn("user", "My name is Alice Brown")
    
    state.reason = "Annual checkup"
    state.add_turn("user", "I need an annual checkup")
    
    state.preferred_date = "next Monday"
    state.preferred_time = "morning"
    state.add_turn("user", "Next Monday morning")
    
    print(f"\n📊 After collection: {state.to_dict()}")
    print(f"\n✓ Is complete: {state.is_complete()}")
    print(f"✓ Turn count: {state.turn_count}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("LLM Conversation Module Test Suite")
    print("="*60)
    
    # Check if Ollama is running
    try:
        import requests
        response = requests.get(f"{Config.LLM_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            print("\n✓ Ollama server is running")
        else:
            print("\n⚠ Ollama server responded with error")
    except Exception as e:
        print(f"\n✗ Cannot connect to Ollama at {Config.LLM_BASE_URL}")
        print("Please start Ollama first:")
        print("  1. Open a new terminal")
        print("  2. Run: ollama serve")
        print(f"\nError: {e}")
        exit(1)
    
    # Run tests
    print("\nWhich test would you like to run?")
    print("1. Basic Conversation Flow")
    print("2. Emergency Detection")
    print("3. Information Extraction")
    print("4. Interactive Chat (talk with the agent!)")
    print("5. State Management")
    print("6. Run all automated tests")
    
    choice = input("\nEnter choice (1-6): ").strip()
    
    if choice == "1":
        test_conversation_basic()
    elif choice == "2":
        test_emergency_detection()
    elif choice == "3":
        test_information_extraction()
    elif choice == "4":
        test_interactive_conversation()
    elif choice == "5":
        test_state_management()
    elif choice == "6":
        test_conversation_basic()
        test_emergency_detection()
        test_information_extraction()
        test_state_management()
    else:
        print("Invalid choice")
    
    print("\n✓ Tests complete!\n")