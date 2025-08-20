# n8n Configuration for MCP Server

## MCP Client Node Setup

### Option 1: Direct MCP Protocol (Recommended)

**MCP Client Node Configuration:**
- **Server Command**: `/opt/mcp-server/venv/bin/fpl-mcp-stdio`
- **Server Arguments**: (leave empty)
- **Authentication**: None

**Alternative Server Commands:**
- `/opt/mcp-server/venv/bin/python`
- **Arguments**: `-m fpl_mcp.stdio_server`

### Option 2: HTTP API (if MCP Client doesn't work)

### 1. SSE Node (for connection monitoring)
```json
{
  "url": "http://YOUR_SERVER_IP:8000/mcp/stream",
  "options": {
    "reconnect": true,
    "reconnectInterval": 5000
  }
}
```

### 2. Get Available Tools
```json
{
  "method": "POST",
  "url": "http://YOUR_SERVER_IP:8000/mcp/call",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "method": "tools/list"
  }
}
```

### 3. Get Available Resources
```json
{
  "method": "POST", 
  "url": "http://YOUR_SERVER_IP:8000/mcp/call",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "method": "resources/list"
  }
}
```

## Tool Calls

### Call Any Tool
```json
{
  "method": "POST",
  "url": "http://YOUR_SERVER_IP:8000/mcp/call",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "method": "tools/call",
    "params": {
      "name": "TOOL_NAME",
      "arguments": {}
    }
  }
}
```

### Call Tool with FPL Credentials (when needed)
```json
{
  "method": "POST",
  "url": "http://YOUR_SERVER_IP:8000/mcp/call",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "method": "tools/call",
    "params": {
      "name": "TOOL_NAME",
      "arguments": {}
    },
    "credentials": {
      "email": "user@example.com",
      "password": "user_password",
      "team_id": "user_team_id"
    }
  }
}
```

## Resource Access

### Read Any Resource
```json
{
  "method": "POST",
  "url": "http://YOUR_SERVER_IP:8000/mcp/call", 
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "method": "resources/read",
    "params": {
      "uri": "RESOURCE_URI"
    }
  }
}
```

## Health Check
```json
{
  "method": "GET",
  "url": "http://YOUR_SERVER_IP:8000/health"
}
```

## Server Capabilities
```json
{
  "method": "GET",
  "url": "http://YOUR_SERVER_IP:8000/mcp/capabilities"
}
```

---

**Note**: Replace `YOUR_SERVER_IP` with your actual server IP address.
All existing MCP tools and resources are available through these endpoints.