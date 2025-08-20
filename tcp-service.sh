#!/bin/bash
# Create systemd service for MCP TCP bridge

cat > /etc/systemd/system/mcp-tcp.service << 'EOF'
[Unit]
Description=FPL MCP TCP Bridge
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/mcp-server
Environment=PATH=/opt/mcp-server/venv/bin
EnvironmentFile=/opt/mcp-server/.env
ExecStart=/opt/mcp-server/venv/bin/fpl-mcp-tcp
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable mcp-tcp

echo "✅ MCP TCP bridge service created and enabled"
echo "Start with: systemctl start mcp-tcp"
echo "Check status: systemctl status mcp-tcp"