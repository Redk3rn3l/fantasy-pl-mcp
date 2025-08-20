#!/bin/bash
# Fix firewall to allow port 8080

echo "🔥 Opening port 8080 in firewall..."

# Check if ufw is active
if command -v ufw &> /dev/null; then
    echo "Using ufw firewall..."
    ufw allow 8080/tcp
    ufw status
fi

# Check if iptables is used
if command -v iptables &> /dev/null; then
    echo "Checking iptables..."
    iptables -I INPUT -p tcp --dport 8080 -j ACCEPT
    # Make it persistent if iptables-persistent is available
    if command -v iptables-save &> /dev/null; then
        iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
    fi
fi

# Test if port is accessible
echo "🧪 Testing port 8080..."
netstat -tlnp | grep :8080 || ss -tlnp | grep :8080

echo "✅ Port 8080 should now be accessible"
echo "Test: curl http://$(curl -s -4 ifconfig.me):8080/health"