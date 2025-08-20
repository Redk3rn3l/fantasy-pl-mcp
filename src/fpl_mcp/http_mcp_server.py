#!/usr/bin/env python3
"""
HTTP server that wraps MCP stdio for n8n compatibility
"""
import asyncio
import json
import logging
from typing import Dict, Any
import subprocess
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("http-mcp-server")

app = FastAPI(title="FPL MCP HTTP Server")

class MCPHTTPServer:
    def __init__(self):
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
    
    async def send_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request to MCP process and get response"""
        await self.start_mcp_process()
        
        if not self.mcp_process or not self.mcp_process.stdin:
            raise Exception("MCP process not available")
            
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

mcp_server = MCPHTTPServer()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mcp-http"}

@app.get("/capabilities")
async def get_capabilities():
    """Get MCP server capabilities"""
    try:
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "n8n-mcp-client",
                    "version": "1.0.0"
                }
            }
        }
        response = await mcp_server.send_mcp_request(request)
        return response
    except Exception as e:
        logger.error(f"Error getting capabilities: {e}")
        return {"error": str(e)}

@app.post("/mcp/call")
async def mcp_call(request: Request):
    """Handle MCP method calls"""
    try:
        body = await request.json()
        
        # Add jsonrpc fields if missing
        if "jsonrpc" not in body:
            body["jsonrpc"] = "2.0"
        if "id" not in body:
            body["id"] = 1
            
        response = await mcp_server.send_mcp_request(body)
        return response
    except Exception as e:
        logger.error(f"Error in MCP call: {e}")
        return {"error": str(e)}

@app.get("/mcp/stream")
async def mcp_stream():
    """SSE endpoint for real-time MCP communication"""
    async def event_generator():
        try:
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connected', 'message': 'MCP server connected'})}\n\n"
            
            # Keep connection alive
            while True:
                await asyncio.sleep(30)
                yield f"data: {json.dumps({'type': 'ping', 'timestamp': asyncio.get_event_loop().time()})}\n\n"
                
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*"
        }
    )

def run_http_server():
    """Entry point for HTTP MCP server"""
    uvicorn.run(
        "fpl_mcp.http_mcp_server:app",
        host="0.0.0.0",
        port=8002,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    run_http_server()