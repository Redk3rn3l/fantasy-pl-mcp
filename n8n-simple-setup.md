# Simple n8n Setup - HTTP API Only

## What This Does
- Cleans up all complex MCP protocols
- Deploys a simple HTTP API on port 8080
- Easy to use with n8n HTTP Request nodes

## Deployment

Run this on your Linode server:
```bash
cd /opt/mcp-server
git pull origin main
bash simple-deploy.sh
```

## n8n Setup

1. **Delete** the MCP Client and MCP Server Trigger nodes
2. **Use HTTP Request nodes** instead:

### Get Fixtures
- **Method**: GET
- **URL**: `http://172.105.168.35:8080/fixtures`
- **Query Parameters**: `gameweek=1` (optional)

### Get Teams
- **Method**: GET  
- **URL**: `http://172.105.168.35:8080/teams`

### Get Players
- **Method**: GET
- **URL**: `http://172.105.168.35:8080/players`
- **Query Parameters**: `position=goalkeeper` (optional)

### Get Standings
- **Method**: GET
- **URL**: `http://172.105.168.35:8080/standings`

### Get Player Details
- **Method**: GET
- **URL**: `http://172.105.168.35:8080/player/123`

### Get Team Details
- **Method**: GET
- **URL**: `http://172.105.168.35:8080/team/1`

## Example n8n Workflow

```
Manual Trigger → HTTP Request (Get Fixtures) → Code Node (Process Data) → Response
```

Much simpler than MCP protocol! 🎯

## API Documentation

Visit: `http://172.105.168.35:8080/docs` for interactive API docs