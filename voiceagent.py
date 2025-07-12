# Imports - bringing in tools we need
from dotenv import load_dotenv  # For reading .env files
from livekit import agents     # Main LiveKit framework
from livekit.agents import AgentSession, Agent, RoomInputOptions  # Specific classes we need
from livekit.plugins import openai, groq     # Audio processing plugins (removed noise_cancellation)
import os  # Built-in module for environment variables

# Load environment variables from .env file
load_dotenv()  # Now we can use os.getenv("GROQ_API_KEY")


class Assistant(Agent):  # Our Assistant class inherits from Agent
    def __init__(self) -> None:  # Constructor method (runs when object is created)
        super().__init__(        # Call parent class constructor
            instructions="""You are a helpful voice AI assistant. 
            Keep responses conversational and concise since they will be spoken aloud.
            The user controls when to speak and when to stop, so wait for their input."""
        )

    async def handle_room_events(self, event):
        """Listen for frontend control signals"""
        if event.type == "start_listening":
            # Start STT
            pass
        elif event.type == "stop_listening":
            # Stop STT, process response
            pass
        elif event.type == "interrupt":
            # Stop current TTS
            pass


# Async Functions (can pause and wait)
async def entrypoint(ctx: agents.JobContext):  # Main function that runs when user joins
    """
    This function runs when a user joins the room.
    It sets up the voice agent and starts the conversation.
    """
    
    # Create the voice agent session with your hybrid approach
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

    # Start the session with our Assistant (removed noise_cancellation)
    await session.start(  # Wait for this to complete
        room=ctx.room,    # The room the user joined
        agent=Assistant(), # Create an instance of our Assistant class
        # Simplified room options without noise cancellation
    )

    # Connect to the LiveKit room
    await ctx.connect()  # Wait for connection to complete

    # Send initial greeting
    await session.generate_reply(
        instructions="Greet the user and let them know you're ready to help. Explain they can tap to speak."
    )


# Main guard - only runs when script is executed directly
if __name__ == "__main__":
    # Start the LiveKit agent worker
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint)  # Pass our entrypoint function
    )
