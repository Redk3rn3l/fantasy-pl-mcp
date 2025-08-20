#!/bin/bash
# Update server with HTTP MCP server for n8n

set -e

echo "🔄 Setting up HTTP MCP server for n8n..."

cd /opt/mcp-server

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main
venv/bin/pip install -e .

# Stop other services
systemctl stop mcp-tcp 2>/dev/null || true
systemctl stop mcp-sse 2>/dev/null || true

# Create and start HTTP service
bash http-service.sh
systemctl start mcp-http

# Show status
systemctl status mcp-http --no-pager

# Get server IP
SERVER_IP=$(curl -s -4 ifconfig.me)

echo ""
echo "✅ HTTP MCP server running!"
echo ""
echo "🔧 Configure your n8n MCP Client node:"
echo "   SSE Endpoint: http://$SERVER_IP:8002/mcp/stream"
echo ""
echo "📋 Available endpoints:"
echo "   Health: http://$SERVER_IP:8002/health"
echo "   Capabilities: http://$SERVER_IP:8002/capabilities"
echo "   MCP Calls: http://$SERVER_IP:8002/mcp/call"
echo ""
echo "📊 Commands:"
echo "   Check status: systemctl status mcp-http"
echo "   View logs: journalctl -u mcp-http -f"