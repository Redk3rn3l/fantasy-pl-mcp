import asyncio
import json
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from mcp.server.fastmcp import FastMCP
import mcp.types as types

logger = logging.getLogger(__name__)

class MCPSSETransport:
    """SSE transport for MCP server to work with n8n"""
    
    def __init__(self, mcp_server: FastMCP):
        self.mcp_server = mcp_server
        self.app = FastAPI(title="MCP SSE Server")
        self.setup_cors()
        self.setup_routes()
        
    def setup_cors(self):
        """Setup CORS for external access"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """Setup SSE endpoints"""
        
        @self.app.get("/health")
        async def health():
            return {"status": "healthy", "service": "mcp-sse"}
        
        @self.app.get("/mcp/capabilities")
        async def get_capabilities():
            """Get MCP server capabilities"""
            try:
                resources = await self.mcp_server.list_resources()
                tools = await self.mcp_server.list_tools()
                
                return {
                    "capabilities": {
                        "resources": len(resources.resources) if resources else 0,
                        "tools": len(tools.tools) if tools else 0
                    },
                    "resources": [r.dict() for r in resources.resources] if resources else [],
                    "tools": [t.dict() for t in tools.tools] if tools else []
                }
            except Exception as e:
                logger.error(f"Error getting capabilities: {e}")
                return {"error": str(e)}
        
        @self.app.post("/mcp/call")
        async def call_mcp_method(request: Request):
            """Call MCP method and return result"""
            try:
                body = await request.json()
                method = body.get("method")
                params = body.get("params", {})
                credentials = body.get("credentials", {})  # Optional credentials from frontend
                
                # Set credentials temporarily if provided
                if credentials:
                    import os
                    if credentials.get("email"):
                        os.environ["FPL_EMAIL"] = credentials["email"]
                    if credentials.get("password"):
                        os.environ["FPL_PASSWORD"] = credentials["password"]
                    if credentials.get("team_id"):
                        os.environ["FPL_TEAM_ID"] = str(credentials["team_id"])
                
                if method == "resources/list":
                    result = await self.mcp_server.list_resources()
                    return {"success": True, "result": result.dict()}
                
                elif method == "resources/read":
                    uri = params.get("uri")
                    if not uri:
                        return {"success": False, "error": "URI required"}
                    result = await self.mcp_server.read_resource(types.ReadResourceRequest(uri=uri))
                    return {"success": True, "result": result.dict()}
                
                elif method == "tools/list":
                    result = await self.mcp_server.list_tools()
                    return {"success": True, "result": result.dict()}
                
                elif method == "tools/call":
                    name = params.get("name")
                    arguments = params.get("arguments", {})
                    if not name:
                        return {"success": False, "error": "Tool name required"}
                    
                    request_obj = types.CallToolRequest(
                        name=name,
                        arguments=arguments
                    )
                    result = await self.mcp_server.call_tool(request_obj)
                    return {"success": True, "result": result.dict()}
                
                else:
                    return {"success": False, "error": f"Unknown method: {method}"}
                    
            except Exception as e:
                logger.error(f"Error calling MCP method: {e}")
                return {"success": False, "error": str(e)}
        
        @self.app.get("/mcp/stream")
        async def mcp_stream():
            """SSE endpoint for n8n"""
            
            async def event_generator():
                yield f"data: {json.dumps({'type': 'connected'})}\n\n"
                
                while True:
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    await asyncio.sleep(30)
            
            return StreamingResponse(
                event_generator(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the SSE server"""
        uvicorn.run(self.app, host=host, port=port)

async def main_sse():
    """Run MCP server with SSE transport"""
    from .__main__ import mcp
    
    sse_transport = MCPSSETransport(mcp)
    sse_transport.run()

def run_sse():
    """Entry point for SSE transport"""
    asyncio.run(main_sse())