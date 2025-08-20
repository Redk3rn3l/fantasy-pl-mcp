# n8n Configuration for MCP Server

## Basic Setup

### 1. SSE Node (for connection monitoring)
```json
{
  "url": "http://172.105.168.35:8000/mcp/stream",
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
  "url": "http://172.105.168.35:8000/mcp/call",
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
  "url": "http://172.105.168.35:8000/mcp/call",
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
  "url": "http://172.105.168.35:8000/mcp/call",
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
  "url": "http://172.105.168.35:8000/mcp/call", 
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
  "url": "http://172.105.168.35:8000/health"
}
```

## Server Capabilities
```json
{
  "method": "GET",
  "url": "http://172.105.168.35:8000/mcp/capabilities"
}
```

---

**Note**: Replace `172.105.168.35` with your actual Linode server IP if different.
All existing MCP tools and resources are available through these endpoints.