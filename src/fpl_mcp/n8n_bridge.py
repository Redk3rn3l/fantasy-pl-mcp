#!/usr/bin/env python3
"""
Bridge MCP server to n8n using MCP Server Trigger webhooks
"""
import asyncio
import json
import logging
import httpx
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("n8n-mcp-bridge")

app = FastAPI(title="FPL MCP to n8n Bridge")

class N8nMCPBridge:
    def __init__(self, n8n_webhook_url: str):
        self.n8n_webhook_url = n8n_webhook_url
        self.mcp_process = None
        
    async def start_mcp_process(self):
        """Start the MCP stdio process"""
        if self.mcp_process is None:
            self.mcp_process = await asyncio.create_subprocess_exec(
                "/opt/mcp-server/venv/bin/fpl-mcp-stdio",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            logger.info("MCP stdio process started")
    
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool and get response"""
        await self.start_mcp_process()
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        # Send to MCP process
        request_json = json.dumps(request) + "\n"
        self.mcp_process.stdin.write(request_json.encode())
        await self.mcp_process.stdin.drain()
        
        # Read response
        response_line = await self.mcp_process.stdout.readline()
        response = json.loads(response_line.decode().strip())
        return response
    
    async def forward_to_n8n(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Forward request to n8n webhook"""
        async with httpx.AsyncClient() as client:
            response = await client.post(self.n8n_webhook_url, json=data)
            return response.json()

# Global bridge instance
bridge = None

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "n8n-mcp-bridge"}

@app.post("/tools/list")
async def list_tools():
    """List available MCP tools"""
    global bridge
    if not bridge:
        raise HTTPException(status_code=500, detail="Bridge not configured")
    
    # Get tools from MCP server
    await bridge.start_mcp_process()
    
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list"
    }
    
    request_json = json.dumps(request) + "\n"
    bridge.mcp_process.stdin.write(request_json.encode())
    await bridge.mcp_process.stdin.drain()
    
    response_line = await bridge.mcp_process.stdout.readline()
    response = json.loads(response_line.decode().strip())
    return response

@app.post("/tools/call")
async def call_tool(request: Dict[str, Any]):
    """Call MCP tool"""
    global bridge
    if not bridge:
        raise HTTPException(status_code=500, detail="Bridge not configured")
    
    tool_name = request.get("tool_name")
    arguments = request.get("arguments", {})
    n8n_data = request.get("n8n_data", {})
    
    if not tool_name:
        raise HTTPException(status_code=400, detail="tool_name required")
    
    # Call MCP tool
    mcp_response = await bridge.call_mcp_tool(tool_name, arguments)
    
    # Forward to n8n if webhook configured
    if bridge.n8n_webhook_url and n8n_data:
        n8n_payload = {
            "mcp_response": mcp_response,
            "tool_name": tool_name,
            "arguments": arguments,
            **n8n_data
        }
        n8n_response = await bridge.forward_to_n8n(n8n_payload)
        return {
            "mcp_response": mcp_response,
            "n8n_response": n8n_response
        }
    
    return mcp_response

@app.post("/configure")
async def configure_bridge(config: Dict[str, Any]):
    """Configure n8n webhook URL"""
    global bridge
    webhook_url = config.get("webhook_url")
    if not webhook_url:
        raise HTTPException(status_code=400, detail="webhook_url required")
    
    bridge = N8nMCPBridge(webhook_url)
    return {"status": "configured", "webhook_url": webhook_url}

def run_n8n_bridge():
    """Entry point for n8n bridge"""
    uvicorn.run(
        "fpl_mcp.n8n_bridge:app",
        host="0.0.0.0",
        port=8003,
        log_level="info"
    )

if __name__ == "__main__":
    run_n8n_bridge()