#!/bin/bash
# Create systemd service for MCP stdio server

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

echo "✅ MCP stdio service created and enabled"
echo "Start with: systemctl start mcp-stdio"
echo "Check status: systemctl status mcp-stdio"