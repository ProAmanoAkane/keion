"""Web page routes for Keion."""

from pathlib import Path

from fastapi import APIRouter, Request, WebSocket
from fastapi.templating import Jinja2Templates

from ..utils import get_players, get_stats

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("/")
async def index(request: Request):
    """Render the main dashboard page."""
    # Get initial data
    stats = await get_stats(request)
    players = await get_players(request)

    # Render template with data
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Keion Dashboard",
            "stats": stats,
            "players": players,
        },
    )


@router.get("/components/players")
async def get_players_component(request: Request):
    """Get players component HTML."""
    players = await get_players(request)
    return templates.TemplateResponse(
        "components/players.html",
        {"request": request, "players": players},
    )


@router.get("/components/stats")
async def get_stats_component(request: Request):
    """Get stats component HTML."""
    stats = await get_stats(request)
    return templates.TemplateResponse(
        "components/stats.html",
        {"request": request, "stats": stats},
    )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    try:
        while True:
            await websocket.receive_text()
            # Send updates about player status
            stats = await get_stats(websocket)
            players = await get_players(websocket)
            await websocket.send_json({"stats": stats, "players": players})
    except Exception:
        await websocket.close()
