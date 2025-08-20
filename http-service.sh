#!/bin/bash
# Create systemd service for HTTP MCP server

cat > /etc/systemd/system/mcp-http.service << 'EOF'
[Unit]
Description=FPL MCP HTTP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/mcp-server
Environment=PATH=/opt/mcp-server/venv/bin
EnvironmentFile=/opt/mcp-server/.env
ExecStart=/opt/mcp-server/venv/bin/fpl-mcp-http
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable mcp-http

echo "✅ MCP HTTP service created and enabled"
echo "Start with: systemctl start mcp-http"
echo "Check status: systemctl status mcp-http"