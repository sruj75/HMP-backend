# Imports - bringing in tools we need
from dotenv import load_dotenv  # For reading .env files
from livekit import agents     # Main LiveKit framework
from livekit.agents import AgentSession, Agent, RoomInputOptions  # Specific classes we need
from livekit.plugins import openai, groq     # Audio processing plugins (removed noise_cancellation)
import os  # Built-in module for environment variables
import logging  # Add logging for debugging

# Configure logging - this helps us see what's happening
logging.basicConfig(
    level=logging.INFO,  # Show INFO level and above messages
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Timestamp, logger name, level, message
)
logger = logging.getLogger(__name__)  # Create logger for this file

# Load environment variables from .env file
load_dotenv()  # Now we can use os.getenv("GROQ_API_KEY")


class Assistant(Agent):  # Our Assistant class inherits from Agent
    def __init__(self) -> None:  # Constructor method (runs when object is created)
        super().__init__(        # Call parent class constructor
            instructions="""You are a helpful voice AI assistant. 
            Keep responses conversational and concise since they will be spoken aloud.
            The user controls when to speak and when to stop, so wait for their input."""
        )
        # Track conversation state for manual control
        self.is_listening = False  # Are we currently recording user speech?
        self.is_speaking = False   # Are we currently playing AI response?
        self.is_processing = False # Are we currently processing (STT→LLM→TTS)?
        logger.info("Assistant initialized with voice-optimized instructions")

    async def handle_room_events(self, event):
        """
        Handle frontend control signals for 2-tap flow:
        Tap 1: interrupt → Stop AI speaking + Start listening automatically  
        Tap 2: stop_listening → Stop listening + Process response
        """
        logger.info(f"Received room event: {event.type} | Current state: listening={self.is_listening}, speaking={self.is_speaking}, processing={self.is_processing}")
        
        if event.type == "start_listening":
            logger.info("Starting STT - user began speaking")
            self.is_listening = True
            self.is_speaking = False
            self.is_processing = False
            # Start STT
            pass
            
        elif event.type == "stop_listening":
            logger.info("Stopping STT - processing user input")
            self.is_listening = False
            self.is_processing = True
            # Stop STT, process response (STT → LLM → TTS)
            pass
            
        elif event.type == "interrupt":
            logger.info("🔄 2-TAP FLOW: Interrupting current TTS + Auto-starting STT")
            # Step 1: Stop current TTS/processing
            self.is_speaking = False
            self.is_processing = False
            # Stop current TTS
            pass
            
            # Step 2: Automatically start listening (2-tap flow)
            logger.info("Auto-starting STT after interrupt - user can now speak")
            self.is_listening = True
            # Start STT automatically
            pass
            
        else:
            logger.warning(f"Unknown event type received: {event.type}")


# Async Functions (can pause and wait)
async def entrypoint(ctx: agents.JobContext):  # Main function that runs when user joins
    """
    This function runs when a user joins the room.
    It sets up the voice agent and starts the conversation.
    """
    logger.info(f"User joined room: {ctx.room.name} - Setting up voice agent")
    
    try:
        # Create the voice agent session with your hybrid approach
        logger.info("Creating AgentSession with hybrid Groq configuration")
        session = AgentSession(
            # LLM: OpenAI SDK with Groq backend - LangChain compatible!
            llm=openai.LLM(
                model="llama-3.1-8b-instant",
                api_key=os.getenv("GROQ_API_KEY"),  # Get from environment
                base_url="https://api.groq.com/openai/v1"
            ),
            
            # STT: Native Groq for audio (doesn't affect LangChain)
            stt=groq.STT(
                model="whisper-large-v3-turbo",
                language="en"
            ),
            
            # TTS: Native Groq for speech
            tts=groq.TTS(
                model="playai-tts",
                voice="Arista-PlayAI"
            ),
            
            # No VAD/turn detection - manual control as planned
        )
        logger.info("AgentSession created successfully with hybrid configuration")

        # Start the session with our Assistant (removed noise_cancellation)
        logger.info("Starting AgentSession and connecting to room")
        await session.start(  # Wait for this to complete
            room=ctx.room,    # The room the user joined
            agent=Assistant(), # Create an instance of our Assistant class
            # Simplified room options without noise cancellation
        )

        # Connect to the LiveKit room
        await ctx.connect()  # Wait for connection to complete
        logger.info("Successfully connected to LiveKit room")

        # Send initial greeting
        logger.info("Generating initial greeting for user")
        await session.generate_reply(
            instructions="Greet the user and let them know you're ready to help. Explain they can tap to speak."
        )
        logger.info("Initial greeting sent to user")
        
    except Exception as e:
        logger.error(f"Error in entrypoint: {str(e)}", exc_info=True)
        raise  # Re-raise the exception so LiveKit knows something went wrong


# Main guard - only runs when script is executed directly
if __name__ == "__main__":
    logger.info("Starting LiveKit agent worker")
    # Start the LiveKit agent worker
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint)  # Pass our entrypoint function
    )
