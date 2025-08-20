#!/usr/bin/env python3
"""
TCP bridge for MCP stdio server to allow remote connections
"""
import asyncio
import logging
import subprocess
import json
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-tcp-bridge")

class MCPTCPBridge:
    def __init__(self, host: str = "0.0.0.0", port: int = 8001):
        self.host = host
        self.port = port
        
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming TCP connection and bridge to MCP stdio"""
        client_addr = writer.get_extra_info('peername')
        logger.info(f"Client connected: {client_addr}")
        
        # Start MCP stdio process
        process = await asyncio.create_subprocess_exec(
            "/opt/mcp-server/venv/bin/fpl-mcp-stdio",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        async def forward_client_to_mcp():
            """Forward data from TCP client to MCP process"""
            try:
                while True:
                    data = await reader.read(8192)
                    if not data:
                        break
                    if process.stdin:
                        process.stdin.write(data)
                        await process.stdin.drain()
            except Exception as e:
                logger.error(f"Error forwarding client to MCP: {e}")
            finally:
                if process.stdin:
                    process.stdin.close()
        
        async def forward_mcp_to_client():
            """Forward data from MCP process to TCP client"""
            try:
                while True:
                    if not process.stdout:
                        break
                    data = await process.stdout.read(8192)
                    if not data:
                        break
                    writer.write(data)
                    await writer.drain()
            except Exception as e:
                logger.error(f"Error forwarding MCP to client: {e}")
            finally:
                writer.close()
                await writer.wait_closed()
        
        # Run both forwarding tasks concurrently
        try:
            await asyncio.gather(
                forward_client_to_mcp(),
                forward_mcp_to_client(),
                return_exceptions=True
            )
        finally:
            # Cleanup
            if process.returncode is None:
                process.terminate()
                await process.wait()
            logger.info(f"Client disconnected: {client_addr}")
    
    async def start_server(self):
        """Start the TCP bridge server"""
        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
        
        addr = server.sockets[0].getsockname()
        logger.info(f"MCP TCP Bridge running on {addr[0]}:{addr[1]}")
        logger.info(f"Connect n8n to: {addr[0]}:{addr[1]}")
        
        async with server:
            await server.serve_forever()

def run_tcp_bridge():
    """Entry point for TCP bridge"""
    bridge = MCPTCPBridge(host="0.0.0.0", port=8001)
    try:
        asyncio.run(bridge.start_server())
    except KeyboardInterrupt:
        logger.info("TCP bridge stopped")

if __name__ == "__main__":
    run_tcp_bridge()