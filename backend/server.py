from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
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
from bson import ObjectId
import csv
import io
import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Helper function to convert ObjectId to string
def serialize_doc(doc):
    """Convert MongoDB document to JSON serializable format"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if key == '_id':
                continue  # Skip MongoDB _id field
            elif isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, list):
                result[key] = [serialize_doc(item) for item in value]
            elif isinstance(value, dict):
                result[key] = serialize_doc(value)
            else:
                result[key] = value
        return result
    return doc

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
    color: str = "#ff0000"  # Risk zone color

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
    is_public: bool = False
    public_link: str = ""
    branding: Dict[str, Any] = {}

class GameSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    player_name: str
    team_name: str = ""
    current_image_index: int = 0
    found_risks: List[str] = []  # Risk zone IDs
    clicks_used: int = 0
    time_remaining: int = 0
    time_elapsed: int = 0
    score: int = 0
    status: str = "active"  # "active", "completed", "timeout"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    image_results: List[Dict[str, Any]] = []

class GameResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    game_id: str
    player_name: str
    team_name: str = ""
    total_score: int
    total_risks_found: int
    total_time_spent: int
    total_clicks_used: int
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
        return serialize_doc(images)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching images: {str(e)}")

@api_router.get("/images/{image_id}")
async def get_image(image_id: str):
    try:
        image = await db.images.find_one({"id": image_id})
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        return serialize_doc(image)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching image: {str(e)}")

@api_router.put("/images/{image_id}")
async def update_image(image_id: str, image_data: dict):
    try:
        image_data["updated_at"] = datetime.utcnow()
        result = await db.images.update_one(
            {"id": image_id},
            {"$set": image_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return {"message": "Image updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating image: {str(e)}")

@api_router.delete("/images/{image_id}")
async def delete_image(image_id: str):
    try:
        result = await db.images.delete_one({"id": image_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return {"message": "Image deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting image: {str(e)}")

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

@api_router.post("/images/{image_id}/duplicate")
async def duplicate_image(image_id: str):
    try:
        # Get original image
        original_image = await db.images.find_one({"id": image_id})
        if not original_image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Create duplicate
        duplicate_image = GameImage(
            name=f"{original_image['name']} (Copy)",
            image_data=original_image['image_data'],
            risk_zones=original_image.get('risk_zones', [])
        )
        
        # Save to database
        await db.images.insert_one(duplicate_image.dict())
        
        return {"id": duplicate_image.id, "name": duplicate_image.name, "message": "Image duplicated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error duplicating image: {str(e)}")

# Game Configuration Routes
@api_router.post("/games")
async def create_game(game: GameConfig):
    try:
        # Generate public link if public
        if game.is_public:
            game.public_link = f"game-{game.id}"
        
        await db.games.insert_one(game.dict())
        return game
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating game: {str(e)}")

@api_router.get("/games")
async def get_games():
    try:
        games = await db.games.find().to_list(100)
        return serialize_doc(games)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching games: {str(e)}")

@api_router.get("/games/{game_id}")
async def get_game(game_id: str):
    try:
        game = await db.games.find_one({"id": game_id})
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        return serialize_doc(game)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching game: {str(e)}")

@api_router.put("/games/{game_id}")
async def update_game(game_id: str, game_data: dict):
    try:
        game_data["updated_at"] = datetime.utcnow()
        result = await db.games.update_one(
            {"id": game_id},
            {"$set": game_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Game not found")
        
        return {"message": "Game updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating game: {str(e)}")

@api_router.delete("/games/{game_id}")
async def delete_game(game_id: str):
    try:
        result = await db.games.delete_one({"id": game_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Game not found")
        
        return {"message": "Game deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting game: {str(e)}")

@api_router.post("/games/{game_id}/duplicate")
async def duplicate_game(game_id: str):
    try:
        # Get original game
        original_game = await db.games.find_one({"id": game_id})
        if not original_game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Create duplicate
        duplicate_game = GameConfig(
            name=f"{original_game['name']} (Copy)",
            description=original_game.get('description', ''),
            time_limit=original_game.get('time_limit', 300),
            max_clicks=original_game.get('max_clicks', 17),
            target_risks=original_game.get('target_risks', 15),
            images=original_game.get('images', []),
            branding=original_game.get('branding', {})
        )
        
        # Save to database
        await db.games.insert_one(duplicate_game.dict())
        
        return {"id": duplicate_game.id, "name": duplicate_game.name, "message": "Game duplicated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error duplicating game: {str(e)}")

@api_router.get("/public/games/{public_link}")
async def get_public_game(public_link: str):
    try:
        game = await db.games.find_one({"public_link": public_link, "is_public": True})
        if not game:
            raise HTTPException(status_code=404, detail="Public game not found")
        return serialize_doc(game)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching public game: {str(e)}")

# Game Session Routes
@api_router.post("/sessions")
async def create_session(session: GameSession):
    try:
        # Get game to set initial time
        game = await db.games.find_one({"id": session.game_id})
        if game:
            session.time_remaining = game.get("time_limit", 300)
        
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
        return serialize_doc(session)
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
        
        # Check if game is still active
        if session["status"] != "active":
            return {"hit": False, "message": "Game is no longer active"}
        
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
        game_status = session["status"]
        
        if hit_risk and hit_risk["id"] not in new_found_risks:
            new_found_risks.append(hit_risk["id"])
            new_score += hit_risk["points"]
        
        # Check if game should end
        if new_clicks >= game["max_clicks"] or session["time_remaining"] <= 0:
            game_status = "completed"
            
            # Save final result
            result = GameResult(
                session_id=session_id,
                game_id=session["game_id"],
                player_name=session["player_name"],
                team_name=session["team_name"],
                total_score=new_score,
                total_risks_found=len(new_found_risks),
                total_time_spent=game["time_limit"] - session["time_remaining"],
                total_clicks_used=new_clicks,
                image_results=session.get("image_results", [])
            )
            
            await db.results.insert_one(result.dict())
        
        await db.sessions.update_one(
            {"id": session_id},
            {
                "$set": {
                    "clicks_used": new_clicks,
                    "found_risks": new_found_risks,
                    "score": new_score,
                    "status": game_status,
                    "completed_at": datetime.utcnow() if game_status == "completed" else None
                }
            }
        )
        
        return {
            "hit": hit_risk is not None,
            "risk_zone": hit_risk,
            "clicks_used": new_clicks,
            "score": new_score,
            "found_risks": len(new_found_risks),
            "game_status": game_status,
            "clicks_remaining": game["max_clicks"] - new_clicks,
            "time_remaining": session["time_remaining"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error handling click: {str(e)}")

@api_router.post("/sessions/{session_id}/timeout")
async def handle_timeout(session_id: str):
    try:
        session = await db.sessions.find_one({"id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Update session status to timeout
        await db.sessions.update_one(
            {"id": session_id},
            {
                "$set": {
                    "status": "timeout",
                    "completed_at": datetime.utcnow()
                }
            }
        )
        
        # Save final result
        game = await db.games.find_one({"id": session["game_id"]})
        result = GameResult(
            session_id=session_id,
            game_id=session["game_id"],
            player_name=session["player_name"],
            team_name=session["team_name"],
            total_score=session["score"],
            total_risks_found=len(session["found_risks"]),
            total_time_spent=game["time_limit"] if game else 300,
            total_clicks_used=session["clicks_used"],
            image_results=session.get("image_results", [])
        )
        
        await db.results.insert_one(result.dict())
        
        return {"message": "Session timed out", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error handling timeout: {str(e)}")

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
        return serialize_doc(results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching results: {str(e)}")

@api_router.get("/results/game/{game_id}")
async def get_game_results(game_id: str):
    try:
        results = await db.results.find({"game_id": game_id}).to_list(100)
        return serialize_doc(results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching game results: {str(e)}")

@api_router.get("/results/analytics/{game_id}")
async def get_game_analytics(game_id: str):
    try:
        results = await db.results.find({"game_id": game_id}).to_list(100)
        
        if not results:
            return {"total_players": 0, "average_score": 0, "average_time": 0}
        
        total_players = len(results)
        total_score = sum(r.get("total_score", 0) for r in results)
        total_time = sum(r.get("total_time_spent", 0) for r in results)
        
        analytics = {
            "total_players": total_players,
            "average_score": round(total_score / total_players, 2),
            "average_time": round(total_time / total_players, 2),
            "total_clicks": sum(r.get("total_clicks_used", 0) for r in results),
            "total_risks_found": sum(r.get("total_risks_found", 0) for r in results),
            "results": serialize_doc(results)
        }
        
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analytics: {str(e)}")

@api_router.get("/results/export/{game_id}")
async def export_results(game_id: str, format: str = "csv"):
    try:
        results = await db.results.find({"game_id": game_id}).to_list(100)
        
        if format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Player Name", "Team Name", "Score", "Risks Found", "Time Spent", "Clicks Used", "Date"])
            
            for result in results:
                writer.writerow([
                    result.get("player_name", ""),
                    result.get("team_name", ""),
                    result.get("total_score", 0),
                    result.get("total_risks_found", 0),
                    result.get("total_time_spent", 0),
                    result.get("total_clicks_used", 0),
                    result.get("created_at", "")
                ])
            
            output.seek(0)
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode()),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=game_results_{game_id}.csv"}
            )
        
        elif format == "excel":
            output = io.BytesIO()
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.title = "Game Results"
            
            # Headers
            headers = ["Player Name", "Team Name", "Score", "Risks Found", "Time Spent", "Clicks Used", "Date"]
            sheet.append(headers)
            
            # Data
            for result in results:
                sheet.append([
                    result.get("player_name", ""),
                    result.get("team_name", ""),
                    result.get("total_score", 0),
                    result.get("total_risks_found", 0),
                    result.get("total_time_spent", 0),
                    result.get("total_clicks_used", 0),
                    str(result.get("created_at", ""))
                ])
            
            workbook.save(output)
            output.seek(0)
            
            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=game_results_{game_id}.xlsx"}
            )
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting results: {str(e)}")

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