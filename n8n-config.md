# n8n Configuration for MCP Server

## Basic Setup

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