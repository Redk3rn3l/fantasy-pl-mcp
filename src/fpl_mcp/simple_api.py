#!/usr/bin/env python3
"""
Simple HTTP API for FPL data - easy n8n integration
"""
import asyncio
import json
import logging
import subprocess
from typing import Dict, Any, Optional, List
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
        
        # Initialize request first
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "simple-api",
                    "version": "1.0.0"
                }
            }
        }
        
        # Send initialization
        init_json = json.dumps(init_request) + "\n"
        self.mcp_process.stdin.write(init_json.encode())
        await self.mcp_process.stdin.drain()
        
        # Read init response
        if self.mcp_process.stdout:
            init_response_line = await self.mcp_process.stdout.readline()
            logger.info(f"Init response: {init_response_line.decode().strip()}")
        
        # Send tool call request
        request = {
            "jsonrpc": "2.0",
            "id": 2,
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
            logger.info(f"Tool response: {response}")
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
            "gameweek": "/gameweek",
            "players": "/players", 
            "player_analysis": "/player/{player_name}/analysis",
            "blank_gameweeks": "/blank-gameweeks",
            "double_gameweeks": "/double-gameweeks",
            "compare_players": "/compare-players"
        }
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "service": "fpl-simple-api"}

@app.get("/gameweek")
async def get_gameweek_status():
    """Get current gameweek status"""
    try:
        response = await fpl_api.call_mcp_tool("get_gameweek_status")
        return response.get("result", response)
    except Exception as e:
        logger.error(f"Error getting gameweek status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/players")
async def analyze_players(
    position: Optional[str] = Query(None, description="Filter by position"),
    team: Optional[str] = Query(None, description="Filter by team"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    limit: Optional[int] = Query(20, description="Number of players to return")
):
    """Get and analyze players"""
    try:
        args = {
            "position": position,
            "team": team,
            "min_price": min_price,
            "max_price": max_price,
            "limit": limit
        }
        # Remove None values
        args = {k: v for k, v in args.items() if v is not None}
        
        response = await fpl_api.call_mcp_tool("analyze_players", args)
        return response.get("result", response)
    except Exception as e:
        logger.error(f"Error analyzing players: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player/{player_name}/analysis")
async def analyze_player_fixtures(player_name: str, num_fixtures: Optional[int] = Query(5, description="Number of fixtures")):
    """Analyze player fixtures"""
    try:
        response = await fpl_api.call_mcp_tool("analyze_player_fixtures", {
            "player_name": player_name,
            "num_fixtures": num_fixtures
        })
        return response.get("result", response)
    except Exception as e:
        logger.error(f"Error analyzing player fixtures: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/blank-gameweeks")
async def get_blank_gameweeks(num_gameweeks: Optional[int] = Query(5, description="Number of gameweeks to check")):
    """Get blank gameweeks"""
    try:
        response = await fpl_api.call_mcp_tool("get_blank_gameweeks", {"num_gameweeks": num_gameweeks})
        return response.get("result", response)
    except Exception as e:
        logger.error(f"Error getting blank gameweeks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/double-gameweeks")
async def get_double_gameweeks(num_gameweeks: Optional[int] = Query(5, description="Number of gameweeks to check")):
    """Get double gameweeks"""
    try:
        response = await fpl_api.call_mcp_tool("get_double_gameweeks", {"num_gameweeks": num_gameweeks})
        return response.get("result", response)
    except Exception as e:
        logger.error(f"Error getting double gameweeks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compare-players")
async def compare_players(player_names: List[str]):
    """Compare multiple players"""
    try:
        response = await fpl_api.call_mcp_tool("compare_players", {"player_names": player_names})
        return response.get("result", response)
    except Exception as e:
        logger.error(f"Error comparing players: {e}")
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