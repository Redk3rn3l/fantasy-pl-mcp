#!/bin/bash
# Update server with TCP bridge for remote n8n connection

set -e

echo "🔄 Adding TCP bridge for remote n8n connection..."

cd /opt/mcp-server

# Pull latest changes
git pull origin main
venv/bin/pip install -e .

# Stop old stdio service (we'll use TCP bridge instead)
systemctl stop mcp-stdio 2>/dev/null || true

# Create and start TCP bridge service
bash tcp-service.sh
systemctl start mcp-tcp

# Show status
systemctl status mcp-tcp --no-pager

# Get server IP
SERVER_IP=$(curl -s -4 ifconfig.me)

echo ""
echo "✅ TCP Bridge running!"
echo ""
echo "🔧 Configure your n8n MCP Client node:"
echo "   SSE Endpoint: tcp://$SERVER_IP:8001"
echo ""
echo "📋 Commands:"
echo "   Check status: systemctl status mcp-tcp"
echo "   View logs: journalctl -u mcp-tcp -f"