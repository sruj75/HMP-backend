from livekit.plugins import openai, groq
import os

session = AgentSession(
    # OpenAI SDK with Groq backend - LangChain compatible!
    llm=openai.LLM(
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    ),
    
    # Native Groq for audio (doesn't affect LangChain)
    stt=groq.STT(model="whisper-large-v3-turbo"),
    tts=groq.TTS(model="playai-tts"),
    
    # No VAD/turn detection - manual control as planned
)
