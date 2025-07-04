from livekit.plugins import openai
import os

session = AgentSession(
    # LLM: Groq via OpenAI compatibility
    llm=openai.LLM(
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    ),
    
    # STT: Groq Whisper via OpenAI compatibility
    stt=openai.STT(
        model="whisper-large-v3-turbo",  # Fast, multilingual, best price/performance
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    ),
    
    # TTS: Groq PlayAI via OpenAI compatibility
    tts=openai.TTS(
        model="playai-tts",  # English TTS
        voice="Arista-PlayAI",  # Or any of the 19 available voices
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    ),
    
    # No VAD/turn detection - manual control as planned
)
