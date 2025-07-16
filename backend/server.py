from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import json
import base64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class RiskZone(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # "circle", "rectangle", "polygon"
    coordinates: List[float]  # [x, y, width, height] for rectangle, [x, y, radius] for circle, [x1, y1, x2, y2, ...] for polygon
    description: str
    difficulty: str  # "easy", "medium", "hard"
    points: int = 1
    explanation: str = ""

class GameImage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    image_data: str  # base64 encoded image
    risk_zones: List[RiskZone] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class GameConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    time_limit: int = 300  # seconds (5 minutes)
    max_clicks: int = 17
    target_risks: int = 15
    images: List[str] = []  # Image IDs
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class GameSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    player_name: str
    team_name: str = ""
    current_image_index: int = 0
    found_risks: List[str] = []  # Risk zone IDs
    clicks_used: int = 0
    time_remaining: int = 0
    score: int = 0
    status: str = "active"  # "active", "completed", "timeout"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class GameResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    game_id: str
    player_name: str
    team_name: str = ""
    total_score: int
    total_risks_found: int
    total_time_spent: int
    image_results: List[Dict[str, Any]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Image Management Routes
@api_router.post("/images/upload")
async def upload_image(
    name: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        # Read file content
        file_content = await file.read()
        
        # Convert to base64
        image_base64 = base64.b64encode(file_content).decode('utf-8')
        
        # Create image record
        image_doc = GameImage(
            name=name,
            image_data=image_base64
        )
        
        # Save to database
        await db.images.insert_one(image_doc.dict())
        
        return {"id": image_doc.id, "name": image_doc.name, "message": "Image uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")

@api_router.get("/images")
async def get_images():
    try:
        images = await db.images.find().to_list(100)
        return images
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching images: {str(e)}")

@api_router.get("/images/{image_id}")
async def get_image(image_id: str):
    try:
        image = await db.images.find_one({"id": image_id})
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        return image
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching image: {str(e)}")

@api_router.put("/images/{image_id}/risk-zones")
async def update_risk_zones(image_id: str, risk_zones: List[RiskZone]):
    try:
        # Update risk zones for the image
        result = await db.images.update_one(
            {"id": image_id},
            {
                "$set": {
                    "risk_zones": [zone.dict() for zone in risk_zones],
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return {"message": "Risk zones updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating risk zones: {str(e)}")

# Game Configuration Routes
@api_router.post("/games")
async def create_game(game: GameConfig):
    try:
        await db.games.insert_one(game.dict())
        return game
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating game: {str(e)}")

@api_router.get("/games")
async def get_games():
    try:
        games = await db.games.find().to_list(100)
        return games
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching games: {str(e)}")

@api_router.get("/games/{game_id}")
async def get_game(game_id: str):
    try:
        game = await db.games.find_one({"id": game_id})
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        return game
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching game: {str(e)}")

# Game Session Routes
@api_router.post("/sessions")
async def create_session(session: GameSession):
    try:
        await db.sessions.insert_one(session.dict())
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

@api_router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    try:
        session = await db.sessions.find_one({"id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching session: {str(e)}")

@api_router.put("/sessions/{session_id}")
async def update_session(session_id: str, session_data: dict):
    try:
        result = await db.sessions.update_one(
            {"id": session_id},
            {"$set": session_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating session: {str(e)}")

@api_router.post("/sessions/{session_id}/click")
async def handle_click(session_id: str, click_data: dict):
    try:
        session = await db.sessions.find_one({"id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get current game and image
        game = await db.games.find_one({"id": session["game_id"]})
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        current_image_id = game["images"][session["current_image_index"]]
        image = await db.images.find_one({"id": current_image_id})
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Check if click hits any risk zone
        click_x = click_data.get("x")
        click_y = click_data.get("y")
        hit_risk = None
        
        for risk_zone in image.get("risk_zones", []):
            if risk_zone["type"] == "circle":
                cx, cy, radius = risk_zone["coordinates"]
                distance = ((click_x - cx) ** 2 + (click_y - cy) ** 2) ** 0.5
                if distance <= radius:
                    hit_risk = risk_zone
                    break
            elif risk_zone["type"] == "rectangle":
                x, y, width, height = risk_zone["coordinates"]
                if x <= click_x <= x + width and y <= click_y <= y + height:
                    hit_risk = risk_zone
                    break
        
        # Update session
        new_clicks = session["clicks_used"] + 1
        new_found_risks = session["found_risks"].copy()
        new_score = session["score"]
        
        if hit_risk and hit_risk["id"] not in new_found_risks:
            new_found_risks.append(hit_risk["id"])
            new_score += hit_risk["points"]
        
        await db.sessions.update_one(
            {"id": session_id},
            {
                "$set": {
                    "clicks_used": new_clicks,
                    "found_risks": new_found_risks,
                    "score": new_score
                }
            }
        )
        
        return {
            "hit": hit_risk is not None,
            "risk_zone": hit_risk,
            "clicks_used": new_clicks,
            "score": new_score,
            "found_risks": len(new_found_risks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error handling click: {str(e)}")

# Results Routes
@api_router.post("/results")
async def save_result(result: GameResult):
    try:
        await db.results.insert_one(result.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving result: {str(e)}")

@api_router.get("/results")
async def get_results():
    try:
        results = await db.results.find().to_list(100)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching results: {str(e)}")

@api_router.get("/results/game/{game_id}")
async def get_game_results(game_id: str):
    try:
        results = await db.results.find({"game_id": game_id}).to_list(100)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching game results: {str(e)}")

# Add default sample images
@api_router.post("/setup/sample-images")
async def create_sample_images():
    try:
        sample_images = [
            {
                "name": "Industrial Safety Factory",
                "url": "https://images.unsplash.com/photo-1489348557694-c552c1eee72d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODF8MHwxfHNlYXJjaHwxfHxpbmR1c3RyaWFsJTIwd29ya3BsYWNlJTIwc2FmZXR5fGVufDB8fHx8MTc1MjY1MjU2OHww&ixlib=rb-4.1.0&q=85"
            },
            {
                "name": "Laser Cutting Machine",
                "url": "https://images.unsplash.com/photo-1738162837329-2f2a2cdebb5e?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODF8MHwxfHNlYXJjaHwzfHxpbmR1c3RyaWFsJTIwd29ya3BsYWNlJTIwc2FmZXR5fGVufDB8fHx8MTc1MjY1MjU2OHww&ixlib=rb-4.1.0&q=85"
            },
            {
                "name": "Factory Floor",
                "url": "https://images.unsplash.com/photo-1716643863806-989dd76ae093?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDN8MHwxfHNlYXJjaHwzfHxmYWN0b3J5fGVufDB8fHx8MTc1MjY1MjU3Nnww&ixlib=rb-4.1.0&q=85"
            }
        ]
        
        created_images = []
        for sample in sample_images:
            # For now, we'll store the URL as a placeholder
            # In production, you'd fetch and convert to base64
            image_doc = GameImage(
                name=sample["name"],
                image_data=sample["url"]  # Using URL as placeholder
            )
            
            await db.images.insert_one(image_doc.dict())
            created_images.append({"id": image_doc.id, "name": image_doc.name})
        
        return {"message": "Sample images created", "images": created_images}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating sample images: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()