#!/bin/bash
# Setup n8n bridge for MCP integration

set -e

echo "🔄 Setting up n8n MCP bridge..."

cd /opt/mcp-server

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main
venv/bin/pip install -e .

# Stop other services
systemctl stop mcp-http 2>/dev/null || true
systemctl stop mcp-tcp 2>/dev/null || true

# Create n8n bridge service
cat > /etc/systemd/system/mcp-n8n.service << 'EOF'
[Unit]
Description=FPL MCP n8n Bridge
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/mcp-server
Environment=PATH=/opt/mcp-server/venv/bin
EnvironmentFile=/opt/mcp-server/.env
ExecStart=/opt/mcp-server/venv/bin/fpl-mcp-n8n
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable mcp-n8n
systemctl start mcp-n8n

# Show status
systemctl status mcp-n8n --no-pager

# Get server IP
SERVER_IP=$(curl -s -4 ifconfig.me)

echo ""
echo "✅ n8n MCP bridge running!"
echo ""
echo "📋 Next steps:"
echo "1. In n8n, DELETE the 'MCP Client Tool' node"
echo "2. ADD the 'MCP Server Trigger' node instead"
echo "3. Configure your n8n webhook URL:"
echo ""
echo "   curl -X POST http://$SERVER_IP:8003/configure \\"
echo '     -H "Content-Type: application/json" \'
echo '     -d '\''{"webhook_url": "YOUR_N8N_WEBHOOK_URL"}'\'''
echo ""
echo "📊 Bridge endpoints:"
echo "   Health: http://$SERVER_IP:8003/health"
echo "   List Tools: http://$SERVER_IP:8003/tools/list"
echo "   Call Tool: http://$SERVER_IP:8003/tools/call"
echo ""
echo "📋 Commands:"
echo "   Check status: systemctl status mcp-n8n"
echo "   View logs: journalctl -u mcp-n8n -f"