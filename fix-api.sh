#!/bin/bash
# Fix API service to use direct API

set -e

echo "🔧 Fixing API service..."

cd /opt/mcp-server

# Pull latest changes
git pull origin main
venv/bin/pip install -e .

# Stop the service
systemctl stop fpl-api

# Update service to use direct API
cat > /etc/systemd/system/fpl-api.service << 'EOF'
[Unit]
Description=FPL Direct HTTP API
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

# Reload and restart
systemctl daemon-reload
systemctl start fpl-api

# Check status
systemctl status fpl-api --no-pager

# Get server IP
SERVER_IP=$(curl -s -4 ifconfig.me)

echo ""
echo "✅ Direct API is running!"
echo ""
echo "📊 Test endpoints:"
echo "   Health: http://$SERVER_IP:8080/health"
echo "   Gameweek: http://$SERVER_IP:8080/gameweek"
echo "   Players: http://$SERVER_IP:8080/players?limit=5"
echo "   Teams: http://$SERVER_IP:8080/teams"
echo ""
echo "📋 Commands:"
echo "   Check logs: journalctl -u fpl-api -f"