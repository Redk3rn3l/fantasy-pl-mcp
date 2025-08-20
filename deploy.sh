#!/bin/bash
# Deploy MCP server with SSE transport on Linode

set -e

echo "🚀 Deploying MCP Server with SSE transport..."

# Update system
echo "📦 Updating system..."
apt update && apt upgrade -y

# Install dependencies
echo "🔧 Installing dependencies..."
apt install -y python3 python3-pip python3-venv git curl

# Setup firewall
echo "🔒 Configuring firewall..."
ufw --force enable
ufw allow ssh
ufw allow 8000/tcp

# Create project directory and copy current files
echo "📁 Setting up project directory..."
mkdir -p /opt/mcp-server
cp -r . /opt/mcp-server/
cd /opt/mcp-server

# Setup Python environment
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Create environment file template
echo "⚙️ Creating environment template..."
cat > .env << 'EOF'
# FPL Credentials
FPL_EMAIL=
FPL_PASSWORD=
FPL_TEAM_ID=
EOF

# Create systemd service
echo "🔄 Creating system service..."
cat > /etc/systemd/system/mcp-sse.service << 'EOF'
[Unit]
Description=MCP Server with SSE Transport
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/mcp-server
Environment=PATH=/opt/mcp-server/venv/bin
EnvironmentFile=/opt/mcp-server/.env
ExecStart=/opt/mcp-server/venv/bin/fpl-mcp-sse
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable service
echo "🎯 Enabling service..."
systemctl daemon-reload
systemctl enable mcp-sse

# Get server IP
SERVER_IP=$(curl -s ifconfig.me)

echo "✅ Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "1. Edit /opt/mcp-server/.env with your FPL credentials"
echo "2. Start service: systemctl start mcp-sse"
echo "3. Check status: systemctl status mcp-sse"
echo ""
echo "🌐 Server endpoints are available at:"
echo "   Health: http://${SERVER_IP}:8000/health"
echo "   Capabilities: http://${SERVER_IP}:8000/mcp/capabilities"
echo "   SSE Stream: http://${SERVER_IP}:8000/mcp/stream"
echo "   MCP Call: http://${SERVER_IP}:8000/mcp/call"
echo ""
echo "📋 Use these URLs in your n8n on Hostinger"