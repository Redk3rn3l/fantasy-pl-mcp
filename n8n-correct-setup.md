# Correct n8n Setup for MCP Integration

## The Issue
You were using the **MCP Client Tool** node, but that's for n8n to connect TO external MCP servers. For your use case, you need the **MCP Server Trigger** node.

## Correct Setup

### Step 1: Use MCP Server Trigger Node (Not MCP Client!)

1. **Delete** the current "MCP Client Tool" node
2. **Add** the "MCP Server Trigger" node instead
3. Configure the MCP Server Trigger:
   - **Authentication**: None (or set up if needed)
   - **Path**: `/mcp/fpl` (or any path you want)

The MCP Server Trigger will give you a webhook URL like:
```
https://your-n8n-instance.hostinger.com/webhook/mcp/fpl
```

### Step 2: Deploy n8n Bridge

Run this on your Linode server:
```bash
cd /opt/mcp-server
git pull origin main
bash n8n-setup.sh
```

### Step 3: Configure Bridge

Tell the bridge your n8n webhook URL:
```bash
curl -X POST http://172.105.168.35:8003/configure \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://your-n8n-instance.hostinger.com/webhook/mcp/fpl"}'
```

### Step 4: Test Connection

```bash
# List available FPL tools
curl http://172.105.168.35:8003/tools/list

# Call a tool (example)
curl -X POST http://172.105.168.35:8003/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "get_fixtures", 
    "arguments": {},
    "n8n_data": {"user": "test"}
  }'
```

## How It Works

1. **MCP Server Trigger** creates a webhook endpoint in n8n
2. **n8n Bridge** (port 8003) receives requests and calls your MCP tools
3. **Bridge** forwards results to your n8n webhook
4. **n8n workflow** processes the FPL data

## API Endpoints

- **Health**: `http://172.105.168.35:8003/health`
- **List Tools**: `http://172.105.168.35:8003/tools/list`
- **Call Tool**: `http://172.105.168.35:8003/tools/call`
- **Configure**: `http://172.105.168.35:8003/configure`

This is the correct architecture for integrating your FPL MCP server with n8n!