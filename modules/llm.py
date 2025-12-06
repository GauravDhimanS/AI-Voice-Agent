"""
LLM Conversation Module using Ollama.

Features:
- Natural conversation flow for medical appointment booking
- Intent extraction and structured data collection
- Emergency detection and escalation
- Conversation state management
- Safety guardrails (no medical advice)
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

try:
    import requests
except ImportError:
    print("Missing dependency: requests")
    print("Install with: pip install requests")
    raise

from config import Config

logger = logging.getLogger(__name__)


class ConversationStage(Enum):
    """Stages of the appointment booking conversation."""
    GREETING = "greeting"
    COLLECT_NAME = "collect_name"
    COLLECT_REASON = "collect_reason"
    COLLECT_DATETIME = "collect_datetime"
    CONFIRM_DETAILS = "confirm_details"
    BOOKING = "booking"
    COMPLETED = "completed"
    EMERGENCY = "emergency"
    TRANSFER_TO_HUMAN = "transfer_to_human"


class ConversationState:
    """Manages the state of a conversation."""
    
    def __init__(self):
        self.stage = ConversationStage.GREETING
        self.patient_name: Optional[str] = None
        self.reason: Optional[str] = None
        self.preferred_date: Optional[str] = None
        self.preferred_time: Optional[str] = None
        self.contact_info: Optional[str] = None
        self.history: List[Dict[str, str]] = []
        self.turn_count: int = 0
        self.emergency_detected: bool = False
        self.metadata: Dict[str, Any] = {}
    
    def add_turn(self, role: str, content: str):
        """Add a conversation turn to history."""
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.turn_count += 1
    
    def get_collected_info(self) -> Dict[str, Optional[str]]:
        """Get all collected patient information."""
        return {
            "name": self.patient_name,
            "reason": self.reason,
            "preferred_date": self.preferred_date,
            "preferred_time": self.preferred_time,
            "contact_info": self.contact_info
        }
    
    def is_complete(self) -> bool:
        """Check if all required information is collected."""
        return all([
            self.patient_name,
            self.reason,
            (self.preferred_date or self.preferred_time)
        ])
    
    def to_dict(self) -> Dict:
        """Convert state to dictionary for logging/storage."""
        return {
            "stage": self.stage.value,
            "collected_info": self.get_collected_info(),
            "turn_count": self.turn_count,
            "emergency_detected": self.emergency_detected,
            "is_complete": self.is_complete(),
            "metadata": self.metadata
        }


class MedicalConversationAgent:
    """
    Manages medical appointment booking conversations using LLM.
    """
    
    def __init__(
        self,
        model: str = Config.LLM_MODEL,
        base_url: str = Config.LLM_BASE_URL,
        temperature: float = Config.LLM_TEMPERATURE,
        max_tokens: int = Config.LLM_MAX_TOKENS
    ):
        """
        Initialize the conversation agent.
        
        Args:
            model: Ollama model name
            base_url: Ollama API base URL
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum response length
        """
        logger.info(f"Initializing conversation agent with model={model}")
        
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Test Ollama connection
        self._test_connection()
        
        # System prompt defining agent behavior
        self.system_prompt = self._build_system_prompt()
        
        logger.info("Conversation agent initialized")
    
    def _test_connection(self):
        """Test connection to Ollama server."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            logger.info("Connected to Ollama server")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            logger.error(f"Make sure Ollama is running at {self.base_url}")
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Please start Ollama: 'ollama serve'"
            )
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt that defines agent behavior."""
        return f"""You are a friendly and professional medical receptionist AI assistant for {Config.PRACTICE_NAME}.

Your ONLY job is to help patients schedule appointments. You must:

1. COLLECT REQUIRED INFORMATION:
   - Patient's full name
   - Reason for visit (symptoms or appointment type)
   - Preferred date and time

2. CONVERSATION STYLE:
   - Be warm, professional, and efficient
   - Use natural, conversational language
   - Keep responses SHORT (1-2 sentences maximum)
   - Ask ONE question at a time
   - Acknowledge what the patient says before moving to next question

3. CRITICAL RULES - YOU MUST FOLLOW THESE:
   - NEVER give medical advice or diagnose conditions
   - NEVER recommend treatments or medications
   - If patient describes emergency symptoms (chest pain, severe bleeding, can't breathe), say: "This sounds urgent. Please hang up and call emergency services immediately, or I can transfer you to a staff member now."
   - If patient asks medical questions, say: "I can't provide medical advice, but our doctor can address that during your appointment."
   - If confused or patient is angry, offer to transfer to a human staff member

4. PRACTICE INFORMATION:
   - Hours: {Config.PRACTICE_HOURS}
   - You can check available appointment slots

5. EXAMPLES OF GOOD RESPONSES:
   - "Good morning! I'm here to help you schedule an appointment. May I have your name, please?"
   - "Thank you, Mr. Smith. What brings you in today?"
   - "I understand you have a sore throat. When would you prefer to come in?"
   - "Let me check our availability for tomorrow morning."

Remember: Be helpful, concise, and focused on booking the appointment. Do not provide medical information."""
    
    def _detect_emergency(self, text: str) -> bool:
        """
        Detect emergency keywords in patient input.
        
        Args:
            text: Patient's message
            
        Returns:
            True if emergency detected
        """
        text_lower = text.lower()
        for keyword in Config.EMERGENCY_KEYWORDS:
            if keyword in text_lower:
                logger.warning(f" Emergency keyword detected: '{keyword}'")
                return True
        return False
    
    def _extract_information(self, text: str, state: ConversationState) -> Dict[str, Optional[str]]:
        """
        Extract structured information from patient's response.
        
        Args:
            text: Patient's message
            state: Current conversation state
            
        Returns:
            Dictionary of extracted information
        """
        extracted = {}
        text_lower = text.lower()
        
        # Extract name - look for common patterns
        if state.stage in [ConversationStage.GREETING, ConversationStage.COLLECT_NAME]:
            name_patterns = [
                r"(?:my name is|i'm|i am|this is|it's)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                r"^([A-Z][a-z]+\s+[A-Z][a-z]+)$",  # Just "John Smith"
                r"(?:call me|i go by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
            ]
            for pattern in name_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    # Make sure it's actually a name (has at least first and last)
                    if len(name.split()) >= 2:
                        extracted['name'] = name
                        logger.debug(f"Extracted name: {name}")
                        break
        
        # Extract reason - be more lenient
        if state.stage == ConversationStage.COLLECT_REASON:
            # Common symptom/reason keywords
            symptom_keywords = ['pain', 'ache', 'hurt', 'sore', 'fever', 'cough', 
                              'cold', 'flu', 'sick', 'checkup', 'appointment',
                              'prescription', 'refill', 'physical', 'exam']
            
            # Check if any symptom keyword is mentioned
            if any(keyword in text_lower for keyword in symptom_keywords):
                extracted['reason'] = text.strip()
                logger.debug(f"Extracted reason: {text.strip()}")
            # Or if they're giving a detailed explanation
            elif len(text.split()) > 3:
                extracted['reason'] = text.strip()
                logger.debug(f"Extracted reason (detailed): {text.strip()}")
        
        # Extract date mentions
        date_patterns = [
            (r'\btoday\b', 'today'),
            (r'\btomorrow\b', 'tomorrow'),
            (r'\bmonday\b', 'Monday'),
            (r'\btuesday\b', 'Tuesday'),
            (r'\bwednesday\b', 'Wednesday'),
            (r'\bthursday\b', 'Thursday'),
            (r'\bfriday\b', 'Friday'),
            (r'\bsaturday\b', 'Saturday'),
            (r'\bsunday\b', 'Sunday'),
            (r'\bnext week\b', 'next week'),
            (r'\bthis week\b', 'this week')
        ]
        
        for pattern, value in date_patterns:
            if re.search(pattern, text_lower):
                extracted['date_mention'] = value
                logger.debug(f"Extracted date: {value}")
                break
        
        # Extract time mentions
        time_patterns = [
            (r'\bmorning\b', 'morning'),
            (r'\bafternoon\b', 'afternoon'),
            (r'\bevening\b', 'evening'),
            (r'\b(\d{1,2})\s*(?:am|a\.m\.)\b', lambda m: f"{m.group(1)} AM"),
            (r'\b(\d{1,2})\s*(?:pm|p\.m\.)\b', lambda m: f"{m.group(1)} PM"),
        ]
        
        for pattern, value in time_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if callable(value):
                    extracted['time_mention'] = value(match)
                else:
                    extracted['time_mention'] = value
                logger.debug(f"Extracted time: {extracted['time_mention']}")
                break
        
        return extracted
    
    def _update_state(self, state: ConversationState, user_input: str, extracted: Dict):
        """
        Update conversation state based on extracted information.
        
        Args:
            state: Current conversation state
            user_input: Patient's message
            extracted: Extracted information
        """
        # Track if we made progress
        made_progress = False
        
        # Update name
        if 'name' in extracted and not state.patient_name:
            state.patient_name = extracted['name']
            made_progress = True
            logger.info(f"Collected name: {state.patient_name}")
            
            # Progress to next stage
            if state.stage == ConversationStage.GREETING:
                state.stage = ConversationStage.COLLECT_REASON
                logger.info("Moving to COLLECT_REASON stage")
        
        # Update reason
        if 'reason' in extracted and not state.reason:
            state.reason = extracted['reason']
            made_progress = True
            logger.info(f"Collected reason: {state.reason}")
            
            # Progress to next stage
            if state.stage == ConversationStage.COLLECT_REASON:
                state.stage = ConversationStage.COLLECT_DATETIME
                logger.info("Moving to COLLECT_DATETIME stage")
        
        # Update date preference
        if 'date_mention' in extracted:
            if not state.preferred_date:
                state.preferred_date = extracted['date_mention']
                made_progress = True
                logger.info(f"Collected date: {state.preferred_date}")
        
        # Update time preference
        if 'time_mention' in extracted:
            if not state.preferred_time:
                state.preferred_time = extracted['time_mention']
                made_progress = True
                logger.info(f"Collected time: {state.preferred_time}")

        # If patient explicitly confirms during confirmation stage, mark as completed
        if state.stage == ConversationStage.CONFIRM_DETAILS:
            confirmation_phrases = [
                "yes", "yeah", "yep", "confirmed", "looks good", "sounds good",
                "book it", "go ahead", "that is correct", "that's correct",
                "ok", "okay", "alright"
            ]
            user_lower = user_input.lower()
            if any(p in user_lower for p in confirmation_phrases):
                state.stage = ConversationStage.COMPLETED
                state.metadata["booking_confirmed"] = True
                logger.info("Booking confirmed by patient; moving to COMPLETED stage")
        
        # Check if we can progress to confirmation
        if state.is_complete() and state.stage != ConversationStage.CONFIRM_DETAILS:
            state.stage = ConversationStage.CONFIRM_DETAILS
            logger.info("Moving to CONFIRM_DETAILS stage - all info collected!")
        
        # If we're stuck in greeting stage and haven't collected name yet
        # but conversation has progressed, try to move to name collection
        if state.stage == ConversationStage.GREETING and state.turn_count > 2 and not state.patient_name:
            state.stage = ConversationStage.COLLECT_NAME
            logger.info("Moving to COLLECT_NAME stage (fallback)")
    
    def _build_context_prompt(self, state: ConversationState) -> str:
        """
        Build contextual prompt based on conversation state.
        
        Args:
            state: Current conversation state
            
        Returns:
            Context string to guide the LLM
        """
        collected = state.get_collected_info()
        
        context_parts = [
            f"CONVERSATION STATE: {state.stage.value}",
            f"Turn: {state.turn_count}"
        ]
        
        # Show what we have
        if collected['name']:
            context_parts.append(f"[OK] Patient name: {collected['name']}")
        else:
            context_parts.append("✗ Need: Patient name")
        
        if collected['reason']:
            context_parts.append(f"[OK] Reason: {collected['reason']}")
        else:
            context_parts.append("✗ Need: Reason for visit")
        
        if collected['preferred_date'] or collected['preferred_time']:
            context_parts.append(f"[OK] Timing: {collected['preferred_date'] or ''} {collected['preferred_time'] or ''}")
        else:
            context_parts.append("✗ Need: Preferred date/time")
        
        # Add EXPLICIT stage-specific instructions
        context_parts.append("\nNEXT ACTION:")
        
        if state.stage == ConversationStage.GREETING:
            context_parts.append("[TODO] Ask for patient's FULL NAME (first and last name)")
        elif state.stage == ConversationStage.COLLECT_NAME:
            context_parts.append("[TODO] The patient should provide their name. If you got it, move to asking WHY they need appointment")
        elif state.stage == ConversationStage.COLLECT_REASON:
            context_parts.append("[TODO] Ask WHY they need to visit (symptoms, checkup, etc)")
        elif state.stage == ConversationStage.COLLECT_DATETIME:
            if not collected['preferred_date']:
                context_parts.append("[TODO] Ask WHEN they want to come (which day)")
            elif not collected['preferred_time']:
                context_parts.append("[TODO] Ask what TIME they prefer (morning/afternoon/specific time)")
            else:
                context_parts.append("[TODO] You have date and time, move to confirmation")
        elif state.stage == ConversationStage.CONFIRM_DETAILS:
            context_parts.append("[TODO] SUMMARIZE all collected info and ask patient to confirm")
        
        return "\n".join(context_parts)
    
    def generate_response(
        self, 
        user_input: str, 
        state: ConversationState
    ) -> str:
        """
        Generate agent response to user input.
        
        Args:
            user_input: Patient's message
            state: Current conversation state
            
        Returns:
            Agent's response
        """
        logger.info(f"Generating response for: '{user_input[:50]}...'")
        
        # Check for emergency
        if self._detect_emergency(user_input):
            state.emergency_detected = True
            state.stage = ConversationStage.EMERGENCY
            return (
                "This sounds like an urgent medical situation. "
                "Please hang up and call emergency services immediately at 911, "
                "or I can transfer you to a staff member right now. What would you prefer?"
            )
        
        # Extract information from user input
        extracted = self._extract_information(user_input, state)
        
        # Update conversation state
        self._update_state(state, user_input, extracted)
        
        # Add user turn to history
        state.add_turn("user", user_input)
        
        # Build conversation history for LLM
        messages = []
        
        # Add system prompt
        messages.append({
            "role": "system",
            "content": self.system_prompt
        })
        
        # Add context about current state
        context = self._build_context_prompt(state)
        messages.append({
            "role": "system",
            "content": f"CURRENT CONTEXT:\n{context}"
        })
        
        # Add conversation history (last 5 turns to keep context manageable)
        recent_history = state.history[-5:]
        for turn in recent_history:
            messages.append({
                "role": turn["role"],
                "content": turn["content"]
            })
        
        # Call Ollama API with streaming
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True,  # Enable streaming
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens,
                        "num_ctx": Config.LLM_NUM_CTX
                    }
                },
                timeout=Config.LLM_TIMEOUT,
                stream=True
            )
            response.raise_for_status()

            # Collect the full response from stream
            assistant_message = ""
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if "message" in chunk:
                        content = chunk["message"].get("content", "")
                        assistant_message += content

            assistant_message = assistant_message.strip()

            # Add assistant turn to history
            state.add_turn("assistant", assistant_message)

            logger.info(f"Generated response: '{assistant_message[:50]}...'")

            return assistant_message

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to generate response: {e}")
            return (
                "I apologize, but I'm having trouble processing your request right now. "
                "Let me transfer you to a staff member who can help you."
            )
    
    def generate_response_streaming(
        self,
        user_input: str,
        state: ConversationState,
        chunk_callback=None
    ):
        """
        Generate a response with streaming support for lower latency.

        Args:
            user_input: User's message
            state: Current conversation state (modified in-place)
            chunk_callback: Optional callback function(chunk_text) called for each chunk

        Yields:
            Text chunks as they arrive from the LLM
        """
        # Check for emergency
        if self._detect_emergency(user_input):
            state.emergency_detected = True
            state.stage = ConversationStage.EMERGENCY
            emergency_msg = (
                "This sounds like an urgent medical situation. "
                "Please hang up and call emergency services immediately at 911, "
                "or I can transfer you to a staff member right now. What would you prefer?"
            )
            state.add_turn("user", user_input)
            state.add_turn("assistant", emergency_msg)
            yield emergency_msg
            return

        # Extract information from user input
        extracted = self._extract_information(user_input, state)

        # Update conversation state
        self._update_state(state, user_input, extracted)

        # Add user turn to history
        state.add_turn("user", user_input)

        # Build conversation history for LLM
        messages = []

        # Add system prompt
        messages.append({
            "role": "system",
            "content": self.system_prompt
        })

        # Add context about current state
        context = self._build_context_prompt(state)
        messages.append({
            "role": "system",
            "content": f"CURRENT CONTEXT:\n{context}"
        })

        # Add conversation history (last 5 turns to keep context manageable)
        recent_history = state.history[-5:]
        for turn in recent_history:
            messages.append({
                "role": turn["role"],
                "content": turn["content"]
            })

        # Call Ollama API with streaming
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens,
                        "num_ctx": Config.LLM_NUM_CTX
                    }
                },
                timeout=Config.LLM_TIMEOUT,
                stream=True
            )
            response.raise_for_status()

            # Stream the response
            assistant_message = ""
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if "message" in chunk:
                        content = chunk["message"].get("content", "")
                        if content:
                            assistant_message += content
                            if chunk_callback:
                                chunk_callback(content)
                            yield content

            # Add complete assistant turn to history
            state.add_turn("assistant", assistant_message.strip())

            logger.info(f"Generated streaming response: '{assistant_message[:50]}...'")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to generate streaming response: {e}")
            error_msg = (
                "I apologize, but I'm having trouble processing your request right now. "
                "Let me transfer you to a staff member who can help you."
            )
            state.add_turn("assistant", error_msg)
            yield error_msg

    def start_conversation(self) -> tuple[str, ConversationState]:
        """
        Start a new conversation.
        
        Returns:
            Tuple of (greeting message, initial conversation state)
        """
        logger.info("Starting new conversation")
        
        state = ConversationState()
        state.stage = ConversationStage.GREETING
        
        greeting = (
            f"Good day! Thank you for calling {Config.PRACTICE_NAME}. "
            "I'm here to help you schedule an appointment. May I have your name, please?"
        )
        
        state.add_turn("assistant", greeting)
        
        return greeting, state
    
    def __repr__(self):
        return f"MedicalConversationAgent(model={self.model})"


# Convenience function for quick testing
def quick_chat(message: str, state: Optional[ConversationState] = None) -> tuple[str, ConversationState]:
    """
    Quick chat function for testing.
    
    Args:
        message: User message
        state: Conversation state (creates new if None)
        
    Returns:
        Tuple of (response, updated_state)
    """
    agent = MedicalConversationAgent()
    
    if state is None:
        response, state = agent.start_conversation()
        return response, state
    
    response = agent.generate_response(message, state)
    return response, state
