#!/bin/bash
# Deploy stdio MCP server update to Linode

SERVER_IP="172.105.168.35"

echo "🚀 Deploying stdio MCP server update to $SERVER_IP..."

# Create update script on server
ssh root@$SERVER_IP << 'ENDSSH'
cd /opt/mcp-server

echo "🔄 Updating MCP server with stdio support..."

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
cat > /etc/systemd/system/mcp-stdio.service << 'EOF'
[Unit]
Description=FPL MCP Server (stdio)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/mcp-server
Environment=PATH=/opt/mcp-server/venv/bin
EnvironmentFile=/opt/mcp-server/.env
ExecStart=/opt/mcp-server/venv/bin/fpl-mcp-stdio
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable mcp-stdio

# Start stdio service
echo "▶️  Starting stdio service..."
systemctl start mcp-stdio

# Check status
echo "📊 Service status:"
systemctl status mcp-stdio --no-pager -l

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
ENDSSH

echo "✅ Stdio MCP server deployed successfully!"