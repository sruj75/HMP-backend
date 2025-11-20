from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import time
import uuid
import datetime
from livekit import api
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

# CORS (Cross-Origin Resource Sharing) middleware allows your backend to accept requests from your Expo app (or any frontend).
# When the Expo app sends a POST request to /token, the browser first checks:
#   "Is this origin (the Expo app's URL) allowed to access this backend?"
# This middleware answers "yes" (for any domain, in development), so your create_token() function can be called from the Expo app.
# In production, you should restrict 'allow_origins' to your real frontend domain for better security.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Allow any domain (development-friendly; change to your frontend URL in production)
    allow_credentials=True,        # Allow cookies and authentication headers  
    allow_methods=["GET", "POST"], # Allow only the methods you use (GET and POST)
    allow_headers=["*"],           # Allow any headers (needed for custom headers from frontend)
)

# Data models (Pydantic automatically validates these)
class TokenRequest(BaseModel):
    user_id: str = None  # Optional - we'll generate if not provided

class TokenResponse(BaseModel):
    token: str
    server_url: str

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
        .with_room_config(
            api.RoomConfiguration(
                agents=[
                    api.RoomAgentDispatch(
                        metadata='{"from":"token_server"}'
                    )
                ],
            )
        )
        .with_ttl(datetime.timedelta(seconds=1800))  # 30 minutes
        .to_jwt()
    )
    
    return TokenResponse(
        token=token,
        server_url=os.getenv("LIVEKIT_URL"),
    )

# Health check endpoint
# Purpose:
# - This endpoint allows deployment platforms (like Railway), load balancers, or monitoring tools
#   to check if the backend service is running and responsive.
# - It is a simple GET endpoint that returns a JSON response indicating the service status.
# - Useful for automated uptime checks, deployment readiness, and debugging.
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
