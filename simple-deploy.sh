#!/bin/bash
# Simple deployment - clean up and deploy HTTP API only

set -e

echo "🧹 Cleaning up unused services..."

cd /opt/mcp-server

# Stop and disable all complex services
systemctl stop mcp-sse 2>/dev/null || true
systemctl stop mcp-tcp 2>/dev/null || true
systemctl stop mcp-http 2>/dev/null || true
systemctl stop mcp-n8n 2>/dev/null || true
systemctl stop mcp-stdio 2>/dev/null || true

systemctl disable mcp-sse 2>/dev/null || true
systemctl disable mcp-tcp 2>/dev/null || true
systemctl disable mcp-http 2>/dev/null || true
systemctl disable mcp-n8n 2>/dev/null || true
systemctl disable mcp-stdio 2>/dev/null || true

# Remove service files
rm -f /etc/systemd/system/mcp-sse.service
rm -f /etc/systemd/system/mcp-tcp.service
rm -f /etc/systemd/system/mcp-http.service
rm -f /etc/systemd/system/mcp-n8n.service
rm -f /etc/systemd/system/mcp-stdio.service

systemctl daemon-reload

echo "✅ Cleaned up unused services"

# Pull latest and install
echo "📥 Updating code..."
git pull origin main
venv/bin/pip install -e .

# Create simple API service
echo "🚀 Setting up simple HTTP API..."
cat > /etc/systemd/system/fpl-api.service << 'EOF'
[Unit]
Description=FPL Simple HTTP API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/mcp-server
Environment=PATH=/opt/mcp-server/venv/bin
EnvironmentFile=/opt/mcp-server/.env
ExecStart=/opt/mcp-server/venv/bin/fpl-mcp-direct
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable fpl-api
systemctl start fpl-api

# Show status
systemctl status fpl-api --no-pager

# Get server IP
SERVER_IP=$(curl -s -4 ifconfig.me)

echo ""
echo "✅ Simple FPL API is running!"
echo ""
echo "📊 API Endpoints:"
echo "   Base URL: http://$SERVER_IP:8080"
echo "   Health: http://$SERVER_IP:8080/health"
echo "   Fixtures: http://$SERVER_IP:8080/fixtures"
echo "   Teams: http://$SERVER_IP:8080/teams"
echo "   Players: http://$SERVER_IP:8080/players"
echo "   Standings: http://$SERVER_IP:8080/standings"
echo ""
echo "🔧 Use these URLs in your n8n HTTP Request nodes!"
echo ""
echo "📋 Commands:"
echo "   Check status: systemctl status fpl-api"
echo "   View logs: journalctl -u fpl-api -f"
echo "   API docs: http://$SERVER_IP:8080/docs"