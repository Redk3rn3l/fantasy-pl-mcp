#!/usr/bin/env python3
"""
MCP server that runs over stdio for n8n MCP Client integration
"""
import logging
import sys

# Set up logging to file (not stdout since that's used for MCP communication)
logging.basicConfig(
    filename='/tmp/fpl-mcp-stdio.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fpl-mcp-stdio")

def run_stdio():
    """Entry point for stdio MCP server"""
    try:
        logger.info("Starting FPL MCP server over stdio")
        
        # Import and run the existing MCP server
        from .__main__ import mcp
        
        # FastMCP's run() method handles stdio automatically
        mcp.run()
        
    except KeyboardInterrupt:
        logger.info("FPL MCP stdio server stopped")
    except Exception as e:
        logger.error(f"Error running MCP stdio server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_stdio()