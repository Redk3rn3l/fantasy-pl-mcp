#!/usr/bin/env python3
"""
Direct HTTP API using FPL modules directly (bypass MCP complexity)
"""
import logging
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import FPL modules directly
from .fpl.api import api
from .fpl.resources import players, teams, gameweeks, fixtures
from .fpl.cache import get_cached_player_data
from .fpl.utils.position_utils import normalize_position

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fpl-direct-api")

app = FastAPI(title="FPL Direct API", description="Direct HTTP API for Fantasy Premier League data")

# Add CORS for n8n
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """API info"""
    return {
        "name": "FPL Direct API",
        "version": "1.0.0",
        "description": "Direct HTTP API for Fantasy Premier League data",
        "endpoints": {
            "health": "/health",
            "gameweek": "/gameweek",
            "players": "/players", 
            "teams": "/teams",
            "fixtures": "/fixtures",
            "player_search": "/player/{player_name}",
            "team_search": "/team/{team_name}"
        }
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "service": "fpl-direct-api"}

@app.get("/gameweek")
async def get_current_gameweek():
    """Get current gameweek information"""
    try:
        gameweek_data = await gameweeks.get_current_gameweek_resource()
        return gameweek_data
    except Exception as e:
        logger.error(f"Error getting current gameweek: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/players")
async def get_all_players(
    position: Optional[str] = Query(None, description="Filter by position"),
    team: Optional[str] = Query(None, description="Filter by team"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    limit: Optional[int] = Query(20, description="Number of players to return")
):
    """Get all players with optional filters"""
    try:
        all_players = await get_cached_player_data()
        
        # Apply filters
        filtered_players = []
        normalized_position = normalize_position(position) if position else None
        
        for player in all_players:
            # Position filter
            if normalized_position and player.get("position") != normalized_position:
                continue
                
            # Team filter
            if team and not (
                team.lower() in player.get("team", "").lower() or 
                team.lower() in player.get("team_short", "").lower()
            ):
                continue
                
            # Price filters
            player_price = player.get("price", 0)
            if min_price is not None and player_price < min_price:
                continue
            if max_price is not None and player_price > max_price:
                continue
                
            filtered_players.append(player)
        
        # Sort by total points and limit
        filtered_players.sort(key=lambda p: p.get("points", 0), reverse=True)
        
        return {
            "players": filtered_players[:limit],
            "total_found": len(filtered_players),
            "filters_applied": {
                "position": normalized_position,
                "team": team,
                "min_price": min_price,
                "max_price": max_price,
                "limit": limit
            }
        }
    except Exception as e:
        logger.error(f"Error getting players: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/teams")
async def get_all_teams():
    """Get all Premier League teams"""
    try:
        teams_data = await teams.get_teams_resource()
        return {"teams": teams_data}
    except Exception as e:
        logger.error(f"Error getting teams: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/fixtures")
async def get_all_fixtures(
    gameweek: Optional[int] = Query(None, description="Specific gameweek"),
    team_name: Optional[str] = Query(None, description="Team name filter")
):
    """Get fixtures"""
    try:
        if gameweek:
            fixtures_data = await fixtures.get_fixtures_resource(gameweek_id=gameweek)
        elif team_name:
            fixtures_data = await fixtures.get_fixtures_resource(team_name=team_name)
        else:
            fixtures_data = await fixtures.get_fixtures_resource()
            
        return {"fixtures": fixtures_data}
    except Exception as e:
        logger.error(f"Error getting fixtures: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player/{player_name}")
async def find_player_by_name(player_name: str):
    """Find player by name"""
    try:
        player_matches = await players.find_players_by_name(player_name)
        if not player_matches:
            raise HTTPException(status_code=404, detail=f"No player found matching '{player_name}'")
        
        return {
            "query": player_name,
            "matches": player_matches
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding player: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/team/{team_name}")
async def find_team_by_name(team_name: str):
    """Find team by name"""
    try:
        team = await teams.get_team_by_name(team_name)
        if not team:
            raise HTTPException(status_code=404, detail=f"No team found matching '{team_name}'")
        
        return team
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding team: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player/{player_name}/fixtures")
async def get_player_fixtures(player_name: str, num_fixtures: Optional[int] = Query(5, description="Number of fixtures")):
    """Get player's upcoming fixtures"""
    try:
        # Find the player first
        player_matches = await players.find_players_by_name(player_name)
        if not player_matches:
            raise HTTPException(status_code=404, detail=f"No player found matching '{player_name}'")
        
        player = player_matches[0]
        player_fixtures = await fixtures.get_player_fixtures(player["id"], num_fixtures)
        
        return {
            "player": {
                "name": player["name"],
                "team": player["team"],
                "position": player["position"]
            },
            "fixtures": player_fixtures
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting player fixtures: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def run_direct_api():
    """Entry point for direct API"""
    uvicorn.run(
        "fpl_mcp.direct_api:app",
        host="0.0.0.0",
        port=8080,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    run_direct_api()