# What's Included - Quick Reference

## ✅ Yes, Everything is Covered!

This guide includes complete instructions for:
1. ✅ **MCP Server Configuration** (exact code, versions, settings)
2. ✅ **Software Versions** (tested versions that work)
3. ✅ **Discovery Requests** (exact curl commands to trigger lazy registration)

---

## 1. MCP Server Configuration 🔧

### Where to find it:

**File:** `MCP_AIRS_GATEWAY_DEPLOYMENT_GUIDE.md` (lines 17-85)  
**File:** `SETUP_CHECKLIST.md` (Step 3)  
**File:** `MCP_AIRS_QUICKSTART.md` (Minimal Working Server section)

### What's included:

**Complete Python Code:**
```python
from mcp.server.mcpserver import MCPServer
import json

# Create MCP server with version info
mcp = MCPServer(
    name="my-mcp-server",           # Server name (will appear in gateway UI)
    version="1.0.0",                 # CRITICAL: Version must be specified!
    description="My MCP Server"      # Description
)

# Define a simple tool using @mcp.tool() decorator
@mcp.tool()
async def hello_world(name: str = "World") -> str:
    """
    Say hello to someone.
    
    Args:
        name: Name to greet
        
    Returns:
        JSON string with greeting
    """
    result = {"message": f"Hello, {name}!"}
    return json.dumps(result)

# CRITICAL: Create SSE app (not streamable_http_app)
# AIRS Gateway requires SSE transport
app = mcp.sse_app(
    sse_path="/sse",           # SSE endpoint path
    message_path="/messages"    # Messages endpoint path
)
```

**Requirements File:**
```txt
mcp==1.1.2
httpx==0.27.2
uvicorn==0.32.1
starlette==0.41.3
```

**Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY mcp_server.py .
EXPOSE 8001
CMD ["uvicorn", "mcp_server:app", "--host", "0.0.0.0", "--port", "8001"]
```

**Kubernetes Deployment:**
- Complete YAML for deployment
- Service configuration
- Health checks
- Resource limits

---

## 2. Software Versions 📦

### Where to find it:

**File:** `MCP_AIRS_GATEWAY_DEPLOYMENT_GUIDE.md` (Prerequisites section, line 9-13)  
**File:** `README.md` (Tested Configuration section)

### Tested & Working Versions:

| Software | Version | Source |
|----------|---------|--------|
| **Python** | 3.11 | Official Python image |
| **MCP SDK** | `mcp==1.1.2` | PyPI |
| **httpx** | `0.27.2` | PyPI |
| **uvicorn** | `0.32.1` | PyPI |
| **starlette** | `0.41.3` | PyPI (dependency) |
| **AIRS Gateway** | v2.15.0 | registry.portkey.ai/airsgw/gateway_enterprise:2.15.0 |
| **Kubernetes** | 1.36+ | Any version supporting apps/v1 |

**Critical Version Notes:**
- ✅ Use `mcp==1.1.2` (exact version tested)
- ✅ Use `MCPServer` class (modern API)
- ✅ Use `sse_app()` not `streamable_http_app()`
- ⚠️ AIRS Gateway v2.15.0 specifically tested (self-hosted)

---

## 3. Discovery Requests (Trigger Lazy Registration) 🎯

### Where to find it:

**File:** `MCP_AIRS_GATEWAY_DEPLOYMENT_GUIDE.md` (Section: "Trigger Capability Discovery", lines 370-550)  
**File:** `SETUP_CHECKLIST.md` (Step 8)  
**File:** `MCP_AIRS_QUICKSTART.md` (Trigger Discovery section)  
**File:** `README.md` (Fastest Path to Success section)

### Option 1: Curl Commands (Quickest)

**Step 1: Initialize Request**
```bash
# Replace these values:
API_KEY="your-api-key-here"           # From Settings → API Keys
GATEWAY_URL="http://airs-gw.airs-gw.svc.cluster.local:8788"
SERVER_SLUG="my-mcp-server"           # From gateway registration

# Send initialize request
curl -X POST "${GATEWAY_URL}/${SERVER_SLUG}/mcp" \
  -H "x-portkey-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    }
  }'
```

**Expected Response:**
```
event: message
data: {"jsonrpc":"2.0","id":"1","result":{"protocolVersion":"2024-11-05","capabilities":{...},"serverInfo":{"name":"my-mcp-server","version":"1.0.0"}}}
```

**Step 2: List Tools Request**
```bash
# Send tools/list request
curl -X POST "${GATEWAY_URL}/${SERVER_SLUG}/mcp" \
  -H "x-portkey-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "tools/list",
    "params": {}
  }'
```

**Expected Response:**
```
event: message
data: {"jsonrpc":"2.0","id":"2","result":{"tools":[{"name":"hello_world","description":"Say hello to someone","inputSchema":{...}}]}}
```

### Option 2: Python Script (Full Example)

**File:** `MCP_AIRS_GATEWAY_DEPLOYMENT_GUIDE.md` has complete Python script (lines 420-520)

Key parts of the script:
```python
import asyncio
import httpx
import json
import uuid
import re

async def trigger_discovery(server_slug: str, api_key: str, gateway_url: str):
    mcp_url = f"{gateway_url}/{server_slug}/mcp"
    
    headers = {
        "x-portkey-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"  # Both required!
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "discovery-client", "version": "1.0.0"}
            }
        }
        response = await client.post(mcp_url, json=init_request, headers=headers)
        # Parse SSE response...
        
        # List tools
        tools_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/list",
            "params": {}
        }
        response = await client.post(mcp_url, json=tools_request, headers=headers)
        # Parse SSE response...
```

### Option 3: Kubernetes Job (Run in Cluster)

**File:** `MCP_AIRS_GATEWAY_DEPLOYMENT_GUIDE.md` (lines 530-580)

Complete K8s Job manifest that:
- Creates a pod with Python
- Installs httpx
- Runs discovery script
- Deletes when complete

### Critical Request Details

**Endpoint Format:**
```
http://{gateway-host}:8788/{server-slug}/mcp
                                         ↑
                                    NO /sse suffix!
```

**Required Headers:**
| Header | Value | Why |
|--------|-------|-----|
| `x-portkey-api-key` | Your API key | Gateway authentication |
| `Content-Type` | `application/json` | Request format |
| `Accept` | `application/json, text/event-stream` | **Both required!** Gateway returns SSE format |

**Request Format (JSON-RPC 2.0):**
```json
{
  "jsonrpc": "2.0",
  "id": "unique-id-here",
  "method": "initialize" OR "tools/list",
  "params": { ... }
}
```

**Response Format (SSE):**
```
event: message
data: {"jsonrpc":"2.0","id":"unique-id","result":{...}}
```

---

## Quick File Navigator

**Want to deploy a server from scratch?**
→ Read `MCP_AIRS_GATEWAY_DEPLOYMENT_GUIDE.md` (complete guide)

**Just need the discovery commands?**
→ Read `MCP_AIRS_QUICKSTART.md` (one page)

**Want a guided checklist?**
→ Follow `SETUP_CHECKLIST.md` (step-by-step with checkboxes)

**Confused about gateway UI fields?**
→ Read `AIRS_GATEWAY_UI_FIELDS.md` (visual guide)

---

## Summary Checklist

Your coworker can verify they have everything:

- [ ] MCP server code with `version="X.Y.Z"` ✓
- [ ] Using `mcp==1.1.2` package ✓
- [ ] Using `mcp.sse_app()` not `streamable_http_app()` ✓
- [ ] Requirements.txt with exact versions ✓
- [ ] Dockerfile for building image ✓
- [ ] Kubernetes deployment YAML ✓
- [ ] API key with `mcp.invoke` permission ✓
- [ ] Server registered in gateway with SSE transport ✓
- [ ] Curl commands to trigger discovery ✓
- [ ] Python script alternative ✓
- [ ] Expected request/response formats ✓

**Everything is included!** 🎉

---

**Last updated:** 2026-07-31
