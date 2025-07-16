# Imports - bringing in tools we need
from dotenv import load_dotenv  # For reading .env files
from livekit import agents     # Main LiveKit framework
from livekit.agents import AgentSession, Agent, RoomInputOptions  # Specific classes we need
from livekit.plugins import openai, groq, silero, noise_cancellation  # Audio processing plugins
from livekit.plugins.turn_detector import multilingual  # Turn detection
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
            Feel free to engage naturally - the system will detect when you should speak."""
        )
        logger.info("Assistant initialized with automatic voice detection")


# Async Functions (can pause and wait)
async def entrypoint(ctx: agents.JobContext):  # Main function that runs when user joins
    """
    This function runs when a user joins the room.
    It sets up the voice agent with automatic voice detection.
    """
    logger.info(f"User joined room: {ctx.room.name} - Setting up automatic voice agent")
    
    try:
        # Create the voice agent session following the resource pattern
        logger.info("Creating AgentSession with VAD and turn detection (Groq hybrid)")
        session = AgentSession(
            # STT: Native Groq for audio
            stt=groq.STT(
                model="whisper-large-v3-turbo",
                language="en"
            ),
            
            # LLM: OpenAI SDK with Groq backend - LangChain compatible!
            llm=openai.LLM(
                model="llama-3.1-8b-instant",
                api_key=os.getenv("GROQ_API_KEY"),  # Get from environment
                base_url="https://api.groq.com/openai/v1"
            ),
            
            # TTS: Native Groq for speech
            tts=groq.TTS(
                model="playai-tts",
                voice="Arista-PlayAI"
            ),
            
            # VAD: Voice Activity Detection - detects when user is speaking
            vad=silero.VAD.load(),
            
            # Turn Detection: Knows when conversation turns should happen
            turn_detection=multilingual.MultilingualModel(),
        )
        logger.info("AgentSession created successfully with VAD and turn detection")

        # Start the session with our Assistant and noise cancellation
        logger.info("Starting AgentSession with noise cancellation")
        await session.start(
            room=ctx.room,    # The room the user joined
            agent=Assistant(), # Create an instance of our Assistant class
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(),  # Background voice cancellation
            ),
        )

        # Connect to the LiveKit room
        await ctx.connect()  # Wait for connection to complete
        logger.info("Successfully connected to LiveKit room with automatic voice detection")

        # Send initial greeting
        logger.info("Generating initial greeting for user")
        await session.generate_reply(
            instructions="Greet the user and let them know you're ready to chat naturally. Explain they can just start talking."
        )
        logger.info("Initial greeting sent to user")
        
    except Exception as e:
        logger.error(f"Error in entrypoint: {str(e)}", exc_info=True)
        raise  # Re-raise the exception so LiveKit knows something went wrong


# Main guard - only runs when script is executed directly
if __name__ == "__main__":
    logger.info("Starting LiveKit agent worker with automatic voice detection")
    # Start the LiveKit agent worker
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint)  # Pass our entrypoint function
    )
