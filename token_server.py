from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import time
import uuid
from livekit import api
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Allow any domain (development-friendly)
    allow_credentials=True,        # Allow authentication headers  
    allow_methods=["GET", "POST"], # Allow the methods you use
    allow_headers=["*"],           # Allow any headers
)

# Data models (Pydantic automatically validates these)
class TokenRequest(BaseModel):
    user_id: str = None  # Optional - we'll generate if not provided

class TokenResponse(BaseModel):
    token: str
    room_name: str
    server_url: str
    expires_in: int  # seconds until token expires

@app.post("/token", response_model=TokenResponse)
async def create_token(request: TokenRequest):
    """Generate a room token for voice agent access"""
    
    # Generate user ID if not provided
    user_id = request.user_id or f"user-{uuid.uuid4()}"
    
    # Room naming strategy: one persistent room per user
    room_name = f"voice-{user_id}"
    
    # Create JWT token using LiveKit SDK
    token = (
        api.AccessToken(
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET")
        )
        .with_identity(user_id)
        .with_name(f"User {user_id}")
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                # Permissions for voice agent
                can_publish=True,     # Can send audio
                can_subscribe=True,   # Can receive audio  
                can_publish_data=True # Can send text messages
            )
        )
        .with_ttl(1800)  # 30 minutes
        .to_jwt()
    )
    
    return TokenResponse(
        token=token,
        room_name=room_name, 
        server_url=os.getenv("LIVEKIT_URL"),
        expires_in=1800  # 30 minutes
    )

# Health check endpoint - lets Railway or any monitoring tool verify the backend is running
@app.get("/health")
async def health_check():
    """
    Simple GET endpoint to check if the service is alive.
    Returns status, current time, and service name.
    """
    return {
        "status": "healthy",              # Shows service is up
        "timestamp": time.time(),         # Current server time (for freshness)
        "service": "voice-ai-backend"     # Identifies which service this is
    }
