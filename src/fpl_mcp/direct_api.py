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
from .fpl.tools.comparisons import compare_player_stats

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
            "gameweeks": "/gameweeks",
            "players": "/players", 
            "teams": "/teams",
            "fixtures": "/fixtures",
            "player_search": "/player/{player_name}",
            "team_search": "/team/{team_name}",
            "player_fixtures": "/player/{player_name}/fixtures",
            "analyze_player_fixtures": "/analyze/player-fixtures",
            "blank_gameweeks": "/blank-gameweeks",
            "double_gameweeks": "/double-gameweeks",
            "compare_players": "/compare-players",
            "analyze_fixtures": "/analyze/fixtures"
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

@app.get("/gameweeks")
async def get_all_gameweeks():
    """Get all gameweeks information"""
    try:
        gameweeks_data = await gameweeks.get_gameweeks_resource()
        return {"gameweeks": gameweeks_data}
    except Exception as e:
        logger.error(f"Error getting gameweeks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/player-fixtures")
async def analyze_player_fixtures(request: Dict[str, Any]):
    """Analyze player fixtures"""
    try:
        player_name = request.get("player_name")
        num_fixtures = request.get("num_fixtures", 5)
        
        if not player_name:
            raise HTTPException(status_code=400, detail="player_name is required")
        
        # Find the player
        player_matches = await players.find_players_by_name(player_name)
        if not player_matches:
            raise HTTPException(status_code=404, detail=f"No player found matching '{player_name}'")
        
        player = player_matches[0]
        player_fixtures = await fixtures.get_player_fixtures(player["id"], num_fixtures)
        
        # Calculate difficulty score
        total_difficulty = sum(f.get("difficulty", 3) for f in player_fixtures)
        avg_difficulty = total_difficulty / len(player_fixtures) if player_fixtures else 3
        fixture_score = (6 - avg_difficulty) * 2 if player_fixtures else 0
        
        return {
            "player": {
                "id": player["id"],
                "name": player["name"],
                "team": player["team"],
                "position": player["position"]
            },
            "fixtures": player_fixtures,
            "analysis": {
                "difficulty_score": round(fixture_score, 1),
                "fixtures_analyzed": len(player_fixtures),
                "home_matches": sum(1 for f in player_fixtures if f.get("location") == "home"),
                "away_matches": sum(1 for f in player_fixtures if f.get("location") == "away"),
                "assessment": "Excellent fixtures" if fixture_score >= 8 else 
                           "Good fixtures" if fixture_score >= 6 else
                           "Average fixtures" if fixture_score >= 4 else
                           "Difficult fixtures"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing player fixtures: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/blank-gameweeks")
async def get_blank_gameweeks(num_gameweeks: Optional[int] = Query(5, description="Number of gameweeks to check")):
    """Get blank gameweeks"""
    try:
        blank_gameweeks = await fixtures.get_blank_gameweeks(num_gameweeks)
        return {
            "blank_gameweeks": blank_gameweeks,
            "summary": f"Found {len(blank_gameweeks)} blank gameweeks in the next {num_gameweeks} gameweeks"
        }
    except Exception as e:
        logger.error(f"Error getting blank gameweeks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/double-gameweeks")
async def get_double_gameweeks(num_gameweeks: Optional[int] = Query(5, description="Number of gameweeks to check")):
    """Get double gameweeks"""
    try:
        double_gameweeks = await fixtures.get_double_gameweeks(num_gameweeks)
        return {
            "double_gameweeks": double_gameweeks,
            "summary": f"Found {len(double_gameweeks)} double gameweeks in the next {num_gameweeks} gameweeks"
        }
    except Exception as e:
        logger.error(f"Error getting double gameweeks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compare-players")
async def compare_players_endpoint(request: Dict[str, Any]):
    """Compare multiple players"""
    try:
        player_names = request.get("player_names", [])
        metrics = request.get("metrics", ["points", "form", "goals", "assists", "bonus"])
        
        if not player_names or len(player_names) < 2:
            raise HTTPException(status_code=400, detail="At least 2 player names required")
        
        # Find all players
        players_data = {}
        for name in player_names:
            matches = await players.find_players_by_name(name)
            if not matches:
                raise HTTPException(status_code=404, detail=f"No player found matching '{name}'")
            players_data[name] = matches[0]
        
        # Build comparison
        comparison = {
            "players": {
                name: {
                    "id": player["id"],
                    "name": player["name"],
                    "team": player["team"],
                    "position": player["position"],
                    "price": player["price"],
                    "status": "available" if player["status"] == "a" else "unavailable"
                } for name, player in players_data.items()
            },
            "metrics_comparison": {}
        }
        
        # Compare metrics
        for metric in metrics:
            metric_values = {}
            for name, player in players_data.items():
                if metric in player:
                    try:
                        value = float(player[metric])
                    except (ValueError, TypeError):
                        value = player[metric]
                    metric_values[name] = value
            
            if metric_values:
                comparison["metrics_comparison"][metric] = metric_values
        
        # Find best performer for each metric
        comparison["best_performers"] = {}
        for metric, values in comparison["metrics_comparison"].items():
            if all(isinstance(v, (int, float)) for v in values.values()):
                higher_is_better = metric not in ["price"]
                if higher_is_better:
                    best_name = max(values.items(), key=lambda x: x[1])[0]
                else:
                    best_name = min(values.items(), key=lambda x: x[1])[0]
                comparison["best_performers"][metric] = best_name
        
        return comparison
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing players: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/fixtures")
async def analyze_fixtures_endpoint(request: Dict[str, Any]):
    """Analyze fixtures for different entities"""
    try:
        entity_type = request.get("entity_type", "player")  # player, team, position
        entity_name = request.get("entity_name")
        num_gameweeks = request.get("num_gameweeks", 5)
        
        if not entity_name:
            raise HTTPException(status_code=400, detail="entity_name is required")
        
        # Get current gameweek
        gameweeks_data = await api.get_gameweeks()
        current_gameweek = None
        for gw in gameweeks_data:
            if gw.get("is_current"):
                current_gameweek = gw.get("id")
                break
        
        if current_gameweek is None:
            raise HTTPException(status_code=500, detail="Could not determine current gameweek")
        
        result = {
            "entity_type": entity_type,
            "entity_name": entity_name,
            "current_gameweek": current_gameweek,
            "analysis_range": list(range(current_gameweek + 1, current_gameweek + num_gameweeks + 1))
        }
        
        if entity_type == "player":
            # Find player
            player_matches = await players.find_players_by_name(entity_name)
            if not player_matches:
                raise HTTPException(status_code=404, detail=f"No player found matching '{entity_name}'")
            
            player = player_matches[0]
            result["player"] = {
                "id": player["id"],
                "name": player["name"],
                "team": player["team"],
                "position": player["position"]
            }
            
            # Get fixtures
            player_fixtures = await fixtures.get_player_fixtures(player["id"], num_gameweeks)
            
            # Calculate analysis
            total_difficulty = sum(f.get("difficulty", 3) for f in player_fixtures)
            avg_difficulty = total_difficulty / len(player_fixtures) if player_fixtures else 3
            fixture_score = (6 - avg_difficulty) * 2
            
            result["fixtures"] = player_fixtures
            result["fixture_analysis"] = {
                "difficulty_score": round(fixture_score, 1),
                "fixtures_analyzed": len(player_fixtures),
                "home_matches": sum(1 for f in player_fixtures if f.get("location") == "home"),
                "away_matches": sum(1 for f in player_fixtures if f.get("location") == "away"),
                "assessment": "Excellent fixtures" if fixture_score >= 8 else 
                           "Good fixtures" if fixture_score >= 6 else
                           "Average fixtures" if fixture_score >= 4 else
                           "Difficult fixtures"
            }
        
        elif entity_type == "team":
            # Find team
            team = await teams.get_team_by_name(entity_name)
            if not team:
                raise HTTPException(status_code=404, detail=f"No team found matching '{entity_name}'")
            
            result["team"] = {
                "id": team["id"],
                "name": team["name"],
                "short_name": team["short_name"]
            }
            
            # Get fixtures for team
            team_fixtures = await fixtures.get_fixtures_resource(team_name=team["name"])
            
            # Filter to upcoming fixtures
            upcoming_fixtures = [
                f for f in team_fixtures 
                if f["gameweek"] in result["analysis_range"]
            ]
            
            result["fixtures"] = upcoming_fixtures
            result["fixture_analysis"] = {
                "fixtures_analyzed": len(upcoming_fixtures),
                "home_matches": sum(1 for f in upcoming_fixtures if f["home_team"]["name"] == team["name"]),
                "away_matches": sum(1 for f in upcoming_fixtures if f["away_team"]["name"] == team["name"])
            }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing fixtures: {e}")
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