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
            "current_gameweek": "/gameweek",
            "all_gameweeks": "/gameweeks",
            "all_players": "/players", 
            "all_teams": "/teams",
            "all_fixtures": "/fixtures",
            "gameweek_fixtures": "/fixtures/gameweek/{gameweek_id}",
            "team_fixtures": "/fixtures/team/{team_name}",
            "player_search": "/player/{player_name}",
            "team_search": "/team/{team_name}",
            "player_fixtures": "/player/{player_name}/fixtures",
            "blank_gameweeks": "/blank-gameweeks",
            "double_gameweeks": "/double-gameweeks",
            "gameweek_status": "/gameweek-status",
            "analyze_player_fixtures": "/analyze/player-fixtures",
            "analyze_players": "/analyze/players",
            "analyze_fixtures": "/analyze/fixtures",
            "compare_players": "/compare-players",
            "check_authentication": "/auth/check",
            "my_team": "/auth/my-team",
            "get_team": "/auth/team/{team_id}",
            "manager_info": "/auth/manager",
            "prompts": "/prompts/{prompt_type}"
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

@app.get("/fixtures/gameweek/{gameweek_id}")
async def get_gameweek_fixtures(gameweek_id: int):
    """Get fixtures for a specific gameweek"""
    try:
        fixtures_data = await fixtures.get_fixtures_resource(gameweek_id=gameweek_id)
        return {"gameweek": gameweek_id, "fixtures": fixtures_data}
    except Exception as e:
        logger.error(f"Error getting gameweek fixtures: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/fixtures/team/{team_name}")
async def get_team_fixtures_endpoint(team_name: str):
    """Get fixtures for a specific team"""
    try:
        fixtures_data = await fixtures.get_fixtures_resource(team_name=team_name)
        return {"team": team_name, "fixtures": fixtures_data}
    except Exception as e:
        logger.error(f"Error getting team fixtures: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/gameweek-status")
async def get_gameweek_status():
    """Get precise information about current, previous, and next gameweeks"""
    try:
        gameweeks = await api.get_gameweeks()
        
        # Find current, previous, and next gameweeks
        current_gw = next((gw for gw in gameweeks if gw.get("is_current")), None)
        previous_gw = next((gw for gw in gameweeks if gw.get("is_previous")), None)
        next_gw = next((gw for gw in gameweeks if gw.get("is_next")), None)
        
        # Determine exact current gameweek status
        current_status = "Not Started"
        if current_gw:
            import datetime
            deadline = datetime.datetime.strptime(current_gw["deadline_time"], "%Y-%m-%dT%H:%M:%SZ")
            now = datetime.datetime.utcnow()
            
            if now < deadline:
                current_status = "Upcoming"
                time_until = deadline - now
                hours_until = time_until.total_seconds() / 3600
                
                if hours_until < 24:
                    current_status = "Imminent (< 24h)"
            else:
                if current_gw.get("finished"):
                    current_status = "Complete"
                else:
                    current_status = "In Progress"
        
        return {
            "current_gameweek": current_gw and current_gw["id"],
            "current_status": current_status,
            "previous_gameweek": previous_gw and previous_gw["id"],
            "next_gameweek": next_gw and next_gw["id"],
            "season_progress": f"GW {current_gw and current_gw['id']}/38" if current_gw else "Unknown",
            "exact_timing": {
                "current_deadline": current_gw and current_gw["deadline_time"],
                "next_deadline": next_gw and next_gw["deadline_time"]
            }
        }
    except Exception as e:
        logger.error(f"Error getting gameweek status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/players")
async def analyze_players_endpoint(request: Dict[str, Any]):
    """Filter and analyze FPL players based on multiple criteria"""
    try:
        position = request.get("position")
        team = request.get("team")
        min_price = request.get("min_price")
        max_price = request.get("max_price")
        min_points = request.get("min_points")
        min_ownership = request.get("min_ownership")
        max_ownership = request.get("max_ownership")
        form_threshold = request.get("form_threshold")
        sort_by = request.get("sort_by", "points")
        sort_order = request.get("sort_order", "desc")
        limit = request.get("limit", 20)
        
        # Get all players
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
                
            # Points filter
            if min_points is not None and player.get("points", 0) < min_points:
                continue
                
            # Ownership filters
            try:
                ownership = float(player.get("selected_by_percent", 0))
                if min_ownership is not None and ownership < min_ownership:
                    continue
                if max_ownership is not None and ownership > max_ownership:
                    continue
            except (ValueError, TypeError):
                pass
                
            # Form filter
            try:
                form = float(player.get("form", 0))
                if form_threshold is not None and form < form_threshold:
                    continue
            except (ValueError, TypeError):
                pass
                
            filtered_players.append(player)
        
        # Sort results
        reverse = sort_order.lower() != "asc"
        try:
            numeric_fields = ["points", "price", "form", "selected_by_percent"]
            if sort_by in numeric_fields:
                filtered_players.sort(
                    key=lambda p: float(p.get(sort_by, 0)) 
                    if p.get(sort_by) is not None else 0,
                    reverse=reverse
                )
            else:
                filtered_players.sort(
                    key=lambda p: p.get(sort_by, ""), 
                    reverse=reverse
                )
        except (KeyError, ValueError):
            filtered_players.sort(
                key=lambda p: float(p.get("points", 0)), 
                reverse=True
            )
        
        # Calculate summary stats
        total_players = len(filtered_players)
        average_points = sum(float(p.get("points", 0)) for p in filtered_players) / max(1, total_players)
        average_price = sum(float(p.get("price", 0)) for p in filtered_players) / max(1, total_players)
        
        return {
            "summary": {
                "total_matches": total_players,
                "average_points": round(average_points, 1),
                "average_price": round(average_price, 2),
                "filters_applied": {
                    "position": normalized_position,
                    "team": team,
                    "min_price": min_price,
                    "max_price": max_price,
                    "min_points": min_points,
                    "min_ownership": min_ownership,
                    "max_ownership": max_ownership,
                    "form_threshold": form_threshold
                }
            },
            "players": filtered_players[:limit]
        }
        
    except Exception as e:
        logger.error(f"Error analyzing players: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Authentication endpoints (require FPL credentials)
@app.get("/auth/check")
async def check_fpl_authentication():
    """Check if FPL authentication is working correctly"""
    try:
        from .fpl.auth_manager import get_auth_manager
        
        auth_manager = get_auth_manager()
        team_id = auth_manager.team_id
        
        if not team_id:
            return {
                "authenticated": False,
                "error": "No team ID found in credentials",
                "setup_instructions": "Run 'fpl-mcp-config setup' to configure your FPL credentials"
            }
        
        # Try to get basic team info as authentication test
        try:
            entry_data = await auth_manager.get_entry_data()
            
            return {
                "authenticated": True,
                "team_name": entry_data.get("name"),
                "manager_name": f"{entry_data.get('player_first_name')} {entry_data.get('player_last_name')}",
                "overall_rank": entry_data.get("summary_overall_rank"),
                "team_id": team_id
            }
        except Exception as e:
            return {
                "authenticated": False,
                "error": f"Authentication failed: {str(e)}",
                "setup_instructions": "Check your FPL credentials and ensure they are correct"
            }
            
    except Exception as e:
        logger.error(f"Authentication check failed: {e}")
        return {
            "authenticated": False,
            "error": str(e),
            "setup_instructions": "Run 'fpl-mcp-config setup' to configure your FPL credentials"
        }

@app.get("/auth/my-team")
async def get_my_team():
    """View your authenticated team (requires authentication)"""
    try:
        from .fpl.auth_manager import get_auth_manager
        
        auth_manager = get_auth_manager()
        team_id = auth_manager.team_id
        
        if not team_id:
            raise HTTPException(status_code=401, detail="Authentication required. Run 'fpl-mcp-config setup'")
        
        # Get team data
        team_data = await auth_manager.get_team_data()
        return {"team_id": team_id, "team_data": team_data}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting my team: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/team/{team_id}")
async def get_team_by_id(team_id: int):
    """View any team with a specific ID (requires authentication)"""
    try:
        from .fpl.auth_manager import get_auth_manager
        
        auth_manager = get_auth_manager()
        
        if not auth_manager.team_id:
            raise HTTPException(status_code=401, detail="Authentication required. Run 'fpl-mcp-config setup'")
        
        # Get team data
        team_data = await auth_manager.get_team_data(team_id)
        return {"team_id": team_id, "team_data": team_data}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/manager")
async def get_manager_info():
    """Get manager details (requires authentication)"""
    try:
        from .fpl.auth_manager import get_auth_manager
        
        auth_manager = get_auth_manager()
        
        if not auth_manager.team_id:
            raise HTTPException(status_code=401, detail="Authentication required. Run 'fpl-mcp-config setup'")
        
        # Get manager data
        entry_data = await auth_manager.get_entry_data()
        return {"manager_info": entry_data}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting manager info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Prompt templates
@app.get("/prompts/{prompt_type}")
async def get_prompt_template(
    prompt_type: str,
    budget: Optional[float] = Query(None, description="Budget for transfer advice"),
    position: Optional[str] = Query(None, description="Position filter"),
    player_name: Optional[str] = Query(None, description="Player name for analysis"),
    player_list: Optional[str] = Query(None, description="Comma-separated player list"),
    max_ownership: Optional[float] = Query(10.0, description="Max ownership for differentials"),
    available_chips: Optional[str] = Query(None, description="Available chips")
):
    """Get prompt templates for various FPL analysis"""
    try:
        if prompt_type == "transfer_advice":
            if budget is None:
                raise HTTPException(status_code=400, detail="budget parameter required for transfer advice")
            
            position_text = f"a {position}" if position else "any position"
            
            return {
                "prompt_type": "transfer_advice",
                "prompt": (
                    f"I need transfer advice for my Fantasy Premier League team. "
                    f"I have £{budget}m to spend on {position_text}. "
                    f"\n\nPlease recommend the best options considering:"
                    f"\n1. Current form and consistency"
                    f"\n2. Upcoming fixture difficulty"
                    f"\n3. Value for money compared to similar players"
                    f"\n4. Blank/double gameweeks that might affect performance"
                    f"\n5. Expected returns based on xG, xA, and other advanced metrics"
                    f"\n\nFor each recommendation, please explain your reasoning and any potential risks."
                )
            }
            
        elif prompt_type == "player_analysis":
            if not player_name:
                raise HTTPException(status_code=400, detail="player_name parameter required for player analysis")
            
            return {
                "prompt_type": "player_analysis", 
                "prompt": (
                    f"Please provide a comprehensive analysis of {player_name} as an FPL asset. "
                    f"I'd like to understand:"
                    f"\n\n1. Recent form, performance statistics, and underlying metrics (xG, xA)"
                    f"\n2. Upcoming fixtures and their difficulty ratings"
                    f"\n3. Value for money compared to their price point"
                    f"\n4. Consistency of returns and minutes played (rotation risks)"
                    f"\n5. Consider other similar players in the same position and price range"
                    f"\n6. Any potential blank or double gameweeks that might affect their performance"
                    f"\n7. Any injury concerns or fitness issues"
                    f"\n8. Any other relevant factors that could impact their performance"
                    f"\n\nBased on this analysis, would you recommend buying, holding, or selling this player for the upcoming gameweeks?"
                )
            }
            
        elif prompt_type == "team_rating":
            if not player_list:
                raise HTTPException(status_code=400, detail="player_list parameter required for team rating")
            
            budget_remaining = budget or 0.0
            
            return {
                "prompt_type": "team_rating",
                "prompt": (
                    f"Please rate and analyze my Fantasy Premier League team consisting of the following players:\n\n{player_list}"
                    f"\n\nI have £{budget_remaining}m remaining in my budget."
                    f"\n\nPlease provide:"
                    f"\n1. An overall rating of my team (1-10)"
                    f"\n2. Strengths and weaknesses in my team structure"
                    f"\n3. Analysis of fixture coverage for the upcoming gameweeks"
                    f"\n4. Suggested improvements or transfers to consider based on player form, fixtures and value"
                    f"\n5. Players who might be rotation risks (based on minutes played) or have challenging fixtures"
                    f"\n6. Any players I should consider captaining in the upcoming gameweek"
                    f"\n7. Any injury concerns or fitness issues that might affect my players"
                    f"\n\nFor each recommendation, please explain your reasoning and any potential risks."
                )
            }
            
        elif prompt_type == "differential_players":
            budget_text = f" with a maximum price of £{budget}m" if budget else ""
            
            return {
                "prompt_type": "differential_players",
                "prompt": (
                    f"I'm looking for differential players with less than {max_ownership}% ownership{budget_text} "
                    f"who could provide good value in the coming gameweeks."
                    f"\n\nPlease suggest differentials for each position (GKP, DEF, MID, FWD) considering:"
                    f"\n1. Recent form and underlying performance statistics"
                    f"\n2. Upcoming fixture difficulty"
                    f"\n3. Expected minutes and rotation risk"
                    f"\n4. Set-piece involvement and penalty duties"
                    f"\n5. Team attacking/defensive strength"
                    f"\n\nFor each player, please explain why they might outperform their ownership percentage."
                )
            }
            
        elif prompt_type == "chip_strategy":
            if not available_chips:
                raise HTTPException(status_code=400, detail="available_chips parameter required for chip strategy")
            
            return {
                "prompt_type": "chip_strategy",
                "prompt": (
                    f"I still have the following FPL chips available: {available_chips}."
                    f"\n\nPlease advise on the optimal strategy for using these chips considering:"
                    f"\n1. Upcoming blank and double gameweeks"
                    f"\n2. Fixture difficulty swings for top teams"
                    f"\n3. Potential injury crises or international breaks"
                    f"\n4. The current stage of the season"
                    f"\n\nFor each chip, suggest specific gameweeks or scenarios when I should consider using them, "
                    f"and explain the reasoning behind your recommendations."
                )
            }
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown prompt type: {prompt_type}. Available: transfer_advice, player_analysis, team_rating, differential_players, chip_strategy")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating prompt: {e}")
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