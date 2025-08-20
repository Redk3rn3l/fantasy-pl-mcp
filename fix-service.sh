#!/bin/bash
# Fix service startup issues

set -e

echo "🔧 Fixing service startup..."

cd /opt/mcp-server

# Pull latest changes
git pull origin main
venv/bin/pip install -e .

# Check what's wrong
echo "📋 Checking logs..."
journalctl -u fpl-api --no-pager -l -n 20

echo ""
echo "🧪 Testing direct command..."
venv/bin/fpl-mcp-direct &
DIRECT_PID=$!
sleep 3

if kill -0 $DIRECT_PID 2>/dev/null; then
    echo "✅ Direct command works"
    kill $DIRECT_PID
else
    echo "❌ Direct command failed"
fi

echo ""
echo "🔧 Recreating service with error handling..."

cat > /etc/systemd/system/fpl-api.service << 'EOF'
[Unit]
Description=FPL Direct HTTP API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/mcp-server
Environment=PATH=/opt/mcp-server/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=PYTHONPATH=/opt/mcp-server/src
EnvironmentFile=-/opt/mcp-server/.env
ExecStart=/opt/mcp-server/venv/bin/python -m fpl_mcp.direct_api
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl stop fpl-api 2>/dev/null || true
systemctl start fpl-api

echo "📊 New service status:"
systemctl status fpl-api --no-pager -l

echo ""
echo "📋 Recent logs:"
journalctl -u fpl-api --no-pager -l -n 10