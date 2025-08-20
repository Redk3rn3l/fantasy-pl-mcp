#!/bin/bash
# Update script for Linode server to add stdio MCP server support

set -e

echo "🔄 Updating MCP server with stdio support..."

# Navigate to server directory
cd /opt/mcp-server

# Stop existing services
echo "⏹️  Stopping existing services..."
systemctl stop mcp-sse 2>/dev/null || true

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Reinstall package with new entry points
echo "📦 Reinstalling package..."
venv/bin/pip install -e .

# Create stdio service
echo "🚀 Setting up stdio service..."
bash mcp-stdio-service.sh

# Start stdio service
echo "▶️  Starting stdio service..."
systemctl start mcp-stdio

# Check status
echo "📊 Service status:"
systemctl status mcp-stdio --no-pager -l

# Show stdio command for n8n
echo ""
echo "✅ Update complete!"
echo ""
echo "🔧 Configure your n8n MCP Client node with:"
echo "   Server Command: /opt/mcp-server/venv/bin/fpl-mcp-stdio"
echo "   Server Arguments: (leave empty)"
echo ""
echo "📋 Available commands:"
echo "   Check stdio logs: tail -f /tmp/fpl-mcp-stdio.log"
echo "   Service status: systemctl status mcp-stdio"
echo "   Restart service: systemctl restart mcp-stdio"