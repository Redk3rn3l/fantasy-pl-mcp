#!/usr/bin/env python3
"""
Simple HTTP API for FPL data - easy n8n integration
"""
import asyncio
import json
import logging
import subprocess
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fpl-simple-api")

app = FastAPI(title="FPL Simple API", description="Easy HTTP API for Fantasy Premier League data")

# Add CORS for n8n
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FPLSimpleAPI:
    def __init__(self):
        self.mcp_process = None
        
    async def start_mcp_process(self):
        """Start the MCP stdio process if not running"""
        if self.mcp_process is None or self.mcp_process.returncode is not None:
            self.mcp_process = await asyncio.create_subprocess_exec(
                "/opt/mcp-server/venv/bin/fpl-mcp-stdio",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            logger.info("MCP stdio process started")
    
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call MCP tool and return response"""
        await self.start_mcp_process()
        
        if not self.mcp_process or not self.mcp_process.stdin:
            raise Exception("MCP process not available")
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }
        
        # Send request
        request_json = json.dumps(request) + "\n"
        self.mcp_process.stdin.write(request_json.encode())
        await self.mcp_process.stdin.drain()
        
        # Read response
        if self.mcp_process.stdout:
            response_line = await self.mcp_process.stdout.readline()
            response = json.loads(response_line.decode().strip())
            return response
        
        raise Exception("No response from MCP process")

# Global API instance
fpl_api = FPLSimpleAPI()

@app.get("/")
async def root():
    """API info"""
    return {
        "name": "FPL Simple API",
        "version": "1.0.0",
        "description": "Easy HTTP API for Fantasy Premier League data",
        "endpoints": {
            "health": "/health",
            "fixtures": "/fixtures",
            "teams": "/teams", 
            "players": "/players",
            "standings": "/standings",
            "player_details": "/player/{player_id}",
            "team_details": "/team/{team_id}"
        }
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "service": "fpl-simple-api"}

@app.get("/fixtures")
async def get_fixtures(gameweek: Optional[int] = Query(None, description="Specific gameweek")):
    """Get fixtures data"""
    try:
        args = {"gameweek": gameweek} if gameweek else {}
        response = await fpl_api.call_mcp_tool("get_fixtures", args)
        return response.get("result", response)
    except Exception as e:
        logger.error(f"Error getting fixtures: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/teams")
async def get_teams():
    """Get all teams"""
    try:
        response = await fpl_api.call_mcp_tool("get_teams")
        return response.get("result", response)
    except Exception as e:
        logger.error(f"Error getting teams: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/players")
async def get_players(position: Optional[str] = Query(None, description="Filter by position")):
    """Get players data"""
    try:
        args = {"position": position} if position else {}
        response = await fpl_api.call_mcp_tool("get_players", args)
        return response.get("result", response)
    except Exception as e:
        logger.error(f"Error getting players: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/standings")
async def get_standings():
    """Get league standings"""
    try:
        response = await fpl_api.call_mcp_tool("get_standings")
        return response.get("result", response)
    except Exception as e:
        logger.error(f"Error getting standings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player/{player_id}")
async def get_player_details(player_id: int):
    """Get specific player details"""
    try:
        response = await fpl_api.call_mcp_tool("get_player_details", {"player_id": player_id})
        return response.get("result", response)
    except Exception as e:
        logger.error(f"Error getting player details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/team/{team_id}")
async def get_team_details(team_id: int):
    """Get specific team details"""
    try:
        response = await fpl_api.call_mcp_tool("get_team_details", {"team_id": team_id})
        return response.get("result", response)
    except Exception as e:
        logger.error(f"Error getting team details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def run_simple_api():
    """Entry point for simple API"""
    uvicorn.run(
        "fpl_mcp.simple_api:app",
        host="0.0.0.0",
        port=8080,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    run_simple_api()