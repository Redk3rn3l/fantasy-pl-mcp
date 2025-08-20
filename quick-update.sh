#!/bin/bash
# Quick update script - run this on your Linode server

set -e

echo "🔄 Updating to stdio MCP server..."

cd /opt/mcp-server

# Stop old service
systemctl stop mcp-sse 2>/dev/null || true

# Update code
git pull origin main
venv/bin/pip install -e .

# Create stdio service
bash mcp-stdio-service.sh

# Start new service
systemctl start mcp-stdio
systemctl status mcp-stdio --no-pager

echo ""
echo "✅ Done! Use in n8n MCP Client:"
echo "   Server Command: /opt/mcp-server/venv/bin/fpl-mcp-stdio"