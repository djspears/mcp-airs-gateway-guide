# MCP Server + AIRS Gateway Integration Guide

**Complete guide to deploy an MCP server and integrate it with Palo Alto AIRS Gateway v2.15.0**

This guide shows you how to deploy an MCP server that successfully displays capabilities (server version and tools) in the AIRS Gateway UI.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [MCP Server Code](#mcp-server-code)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [AIRS Gateway Configuration](#airs-gateway-configuration)
6. [Trigger Capability Discovery](#trigger-capability-discovery)
7. [Verify in Gateway UI](#verify-in-gateway-ui)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Software Versions (Tested & Working)

- **Python**: 3.11
- **MCP SDK**: `mcp==1.1.2` (pip package)
- **AIRS Gateway**: v2.15.0 (registry.portkey.ai/airsgw/gateway_enterprise:2.15.0)
- **Kubernetes**: 1.36+ (any version supporting apps/v1)

### Required Knowledge

- Basic Kubernetes/Docker
- Understanding of MCP (Model Context Protocol)
- Access to AIRS Gateway UI

---

## MCP Server Code

### 1. Create MCP Server File

Create `mcp_server.py` with the following code:

```python
"""
MCP Server - SSE Transport for AIRS Gateway
Uses modern MCP SDK (mcp==1.1.2)
"""

import json
import httpx
from mcp.server.mcpserver import MCPServer

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

@mcp.tool()
async def get_data(topic: str) -> str:
    """
    Get some data about a topic.
    
    Args:
        topic: Topic to get data about
        
    Returns:
        JSON string with data
    """
    result = {
        "topic": topic,
        "data": f"Here is information about {topic}"
    }
    return json.dumps(result)

# CRITICAL: Create SSE app (not streamable_http_app)
# AIRS Gateway requires SSE transport
app = mcp.sse_app(
    sse_path="/sse",           # SSE endpoint path
    message_path="/messages"    # Messages endpoint path
)

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy"}
```

**Key Points:**
- ✅ Use `MCPServer` class (modern API)
- ✅ Specify `version="1.0.0"` (required for gateway to display version)
- ✅ Use `mcp.sse_app()` not `streamable_http_app()` (gateway requires SSE)
- ✅ Tools return JSON strings
- ✅ Include health check endpoint

### 2. Create Requirements File

Create `requirements.txt`:

```txt
mcp==1.1.2
httpx==0.27.2
uvicorn==0.32.1
starlette==0.41.3
```

### 3. Create Server Entrypoint

Create `run_server.py`:

```python
"""Run the MCP server with uvicorn"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "mcp_server:app",
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
```

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy MCP server code
COPY mcp_server.py .
COPY run_server.py .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8001/health')"

# Expose port
EXPOSE 8001

# Run server
CMD ["python", "run_server.py"]
```

### Build and Push

```bash
# Build
docker build -t your-registry/mcp-server:1.0.0 .

# Push
docker push your-registry/mcp-server:1.0.0
```

---

## Kubernetes Deployment

### 1. Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: mcp-services
```

### 2. Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-server
  namespace: mcp-services
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mcp-server
  template:
    metadata:
      labels:
        app: mcp-server
    spec:
      containers:
      - name: mcp-server
        image: your-registry/mcp-server:1.0.0
        ports:
        - containerPort: 8001
          name: http
        env:
        - name: PORT
          value: "8001"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

### 3. Service

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: mcp-server
  namespace: mcp-services
spec:
  type: ClusterIP
  selector:
    app: mcp-server
  ports:
  - port: 8001
    targetPort: 8001
    protocol: TCP
    name: http
```

### Deploy to Kubernetes

```bash
kubectl apply -f namespace.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# Verify deployment
kubectl get pods -n mcp-services
kubectl logs -n mcp-services deployment/mcp-server
```

### Test the MCP Server Directly

```bash
# Port forward for testing
kubectl port-forward -n mcp-services service/mcp-server 8001:8001

# Test health endpoint
curl http://localhost:8001/health

# Test SSE endpoint (should return 200 OK and wait for events)
curl -N -H "Accept: text/event-stream" http://localhost:8001/sse
```

---

## AIRS Gateway Configuration

### Step 1: Access AIRS Gateway UI

Navigate to your AIRS Gateway UI (typically `http://your-gateway-host:80`)

### Step 2: Create API Key ⚠️ REQUIRED

**You MUST create an API key with `mcp.invoke` permission to trigger discovery!**

```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️  CRITICAL: API Key Required for Discovery               │
│                                                             │
│ Without this API key, you won't be able to trigger         │
│ capability discovery and the gateway will show "--"        │
│ for version and tools.                                     │
└─────────────────────────────────────────────────────────────┘
```

**Steps:**

1. Go to **Settings → API Keys**
2. Click **Create API Key**
3. Name: `mcp-client-key` (or any descriptive name)
4. Permissions: Check ☑ **`mcp.invoke`** ← This permission is required!
5. Click **Create**
6. **Copy and save the API key** (e.g., `your-api-key-here`)
   - You'll need this for the discovery script
   - Store it securely (it won't be shown again)

### Step 3: Register MCP Server

1. Go to **MCP Registry** (or **MCP Servers** section)
2. Click **Add MCP Server** or **Register Server**
3. Fill in the form:

**Critical Settings:**

| Field | Value | Notes |
|-------|-------|-------|
| **Name** | `News Fetcher` | Display name (can be anything) |
| **Short Description** | `Fetch news articles from major sources` | Optional description text |
| **URL** | `http://mcp-server.mcp-services.svc.cluster.local:8001/sse` | ⚠️ Full URL to SSE endpoint |
| **Server Type** | `SSE (Server-Sent Events)` | Select SSE option (supports streaming) |
| **Authentication** | `None` or configure as needed | Auth method for client→server |
| **Passthrough headers** | Leave empty (optional) | Custom headers to forward |

**Example Configuration:**

```
Name:                News Fetcher
Short Description:   Fetch news articles from major sources (CNN, Fox, NYT, etc.)
URL:                 http://mcp-server.mcp-services.svc.cluster.local:8001/sse
Server Type:         SSE (Server-Sent Events)
                     [Recommended for most integrations. Supports streaming responses...]
Authentication:      None
Passthrough headers: (leave empty)
```

**Important Notes:**
- The **URL** field is where you put the full server endpoint including `/sse`
- **Server Type** should be "SSE (Server-Sent Events)" not Streamable HTTP
- **Short Description** is optional but helps document what the server does

4. Click **Save** or **Register**

### Example of Correctly Configured Server

Here's what a working configuration looks like in the edit form:

```
Update MCP integration

Name *
News Fetcher

Short Description (Optional)
Fetch news articles from major sources (CNN, Fox, NYT, etc.)

URL *
http://mcp-server.mcp-services.svc.cluster.local:8001/sse

Server Type
☑ SSE (Server-Sent Events)
  Recommended for most integrations. Supports streaming responses over standard HTTP connections.

Passthrough headers (Optional)
[Leave empty]

Authentication
None
```

**Note**: The **URL** field (marked with *) is where you put the full SSE endpoint URL!

### What You'll See Initially

After registration, the server will show:
- **Status**: Active ✅
- **Version**: `--` (not discovered yet)
- **Tools**: `--` (not discovered yet)

This is normal! The gateway uses **lazy initialization** and won't discover capabilities until a client connects.

---

## Trigger Capability Discovery

The AIRS Gateway won't show server version and tools until a client makes requests through the gateway proxy. Here's how to trigger discovery:

### Option 1: Simple curl Test

```bash
# Replace MY_API_KEY with your actual API key
API_KEY="your-api-key-here"
GATEWAY_URL="http://airs-gw.airs-gw.svc.cluster.local:8788"
SERVER_SLUG="my-mcp-server"

# Step 1: Initialize
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

# Step 2: List tools
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

**Expected Response Format:**
```
event: message
data: {"jsonrpc":"2.0","id":"1","result":{"protocolVersion":"2024-11-05","capabilities":{...},"serverInfo":{"name":"my-mcp-server","version":"1.0.0"}}}
```

### Option 2: Python Discovery Script

Create `trigger_discovery.py`:

```python
#!/usr/bin/env python3
"""Trigger AIRS Gateway MCP server discovery"""

import asyncio
import httpx
import json
import uuid
import re
import os


async def trigger_discovery(server_slug: str, api_key: str, gateway_url: str):
    """Trigger gateway to discover MCP server capabilities"""
    
    mcp_url = f"{gateway_url}/{server_slug}/mcp"
    
    print(f"Triggering discovery for: {server_slug}")
    print(f"Gateway URL: {mcp_url}")
    print()
    
    # Required headers
    headers = {
        "x-portkey-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"  # Both required!
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Initialize
        print("1. Sending initialize request...")
        init_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "discovery-client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = await client.post(mcp_url, json=init_request, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Initialize failed: {response.status_code}")
            print(response.text)
            return False
        
        # Parse SSE response
        init_result = parse_sse_response(response.text)
        server_info = init_result.get("result", {}).get("serverInfo", {})
        
        print(f"✅ Server: {server_info.get('name')}")
        print(f"   Version: {server_info.get('version')}")
        print()
        
        # Step 2: List tools
        print("2. Listing tools...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/list",
            "params": {}
        }
        
        response = await client.post(mcp_url, json=tools_request, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Tools list failed: {response.status_code}")
            return False
        
        tools_result = parse_sse_response(response.text)
        tools = tools_result.get("result", {}).get("tools", [])
        
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool.get('name')}")
        print()
        
        print("✅ Discovery complete!")
        print("   Check the AIRS Gateway UI - capabilities should now be visible")
        return True


def parse_sse_response(text: str) -> dict:
    """Parse SSE formatted response to extract JSON-RPC message"""
    # SSE format: "event: message\ndata: {json}\n\n"
    match = re.search(r'data: ({.*})', text)
    if match:
        return json.loads(match.group(1))
    return {}


if __name__ == "__main__":
    # Configuration
    API_KEY = os.getenv("AIRS_GATEWAY_API_KEY", "your-api-key-here")
    GATEWAY_URL = "http://airs-gw.airs-gw.svc.cluster.local:8788"
    SERVER_SLUG = "my-mcp-server"
    
    print("="*70)
    print("MCP Server Discovery via AIRS Gateway")
    print("="*70)
    print()
    
    success = asyncio.run(trigger_discovery(SERVER_SLUG, API_KEY, GATEWAY_URL))
    exit(0 if success else 1)
```

Run it:

```bash
# Install dependencies
pip install httpx

# Set your API key
export AIRS_GATEWAY_API_KEY="your-api-key-here"

# Run discovery
python trigger_discovery.py
```

### Option 3: Kubernetes Job

Create `k8s-discovery-job.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: airs-gateway-api-key
  namespace: mcp-services
type: Opaque
stringData:
  api-key: "your-api-key-here"  # Replace with your key
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: discovery-script
  namespace: mcp-services
data:
  trigger_discovery.py: |
    # [Paste the Python script from Option 2 here]
---
apiVersion: batch/v1
kind: Job
metadata:
  name: mcp-discovery
  namespace: mcp-services
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: discovery
        image: python:3.11-slim
        command:
        - /bin/bash
        - -c
        - |
          pip install -q httpx &&
          python /scripts/trigger_discovery.py
        env:
        - name: AIRS_GATEWAY_API_KEY
          valueFrom:
            secretKeyRef:
              name: airs-gateway-api-key
              key: api-key
        volumeMounts:
        - name: script
          mountPath: /scripts
      volumes:
      - name: script
        configMap:
          name: discovery-script
  backoffLimit: 2
```

Deploy and run:

```bash
kubectl apply -f k8s-discovery-job.yaml
kubectl logs -n mcp-services job/mcp-discovery
```

---

## Verify in Gateway UI

After running the discovery trigger, refresh the AIRS Gateway UI:

### Before Discovery:
```
Server Name: my-mcp-server
Status: Active
Version: --
Tools: --
```

### After Discovery:
```
Server Name: my-mcp-server
Status: Active
Version: 1.0.0
Tools: 2

Capabilities:
✓ hello_world (tool)
✓ get_data (tool)
```

You should now see:
- ✅ **Version**: `1.0.0` (instead of `--`)
- ✅ **Tools count**: `2` (instead of `--`)
- ✅ **Capabilities section** with tool names and schemas
- ✅ **Checkboxes** to enable/disable individual tools

---

## Troubleshooting

### Problem: Version shows "--" after discovery

**Cause**: MCP server didn't include version in MCPServer constructor

**Solution**: 
```python
# Wrong - no version
mcp = MCPServer(name="my-server")

# Correct - include version
mcp = MCPServer(name="my-server", version="1.0.0")
```

### Problem: Tools show "--" after discovery

**Cause**: Discovery wasn't triggered or tools/list request failed

**Solution**: Run the discovery script again and check for errors

### Problem: 404 Not Found on gateway endpoint

**Cause**: Wrong endpoint path

**Solution**: 
- Endpoint should be: `http://gateway:8788/{server-slug}/mcp`
- NOT: `http://gateway:8788/{server-slug}/mcp/sse`

### Problem: 406 Not Acceptable

**Cause**: Missing Accept headers

**Solution**: Include BOTH accept types:
```bash
-H "Accept: application/json, text/event-stream"
```

### Problem: Connection timeout

**Causes**:
1. Server URL is wrong in gateway config (check the "URL" field!)
2. Network connectivity issue
3. Server is not running

**Solution**:
```bash
# Test server directly
kubectl run -n mcp-services curl-test --image=curlimages/curl --rm -i --restart=Never -- \
  curl -v http://mcp-server.mcp-services.svc.cluster.local:8001/health

# Should return: {"status":"healthy"}
```

**Important**: Make sure the **URL** field contains the full endpoint with `/sse` at the end:
- ✅ Correct: `http://mcp-server:8001/sse`
- ❌ Wrong: `http://mcp-server:8001`

### Problem: "Failed to restore session"

**Cause**: Gateway session management issue (known bug in v2.15.0 for some servers)

**Solution**: 
- Ensure you're using SSE transport (not Streamable HTTP)
- Each request should be independent (not relying on session state)
- Try re-registering the server in the gateway UI

### Problem: Tools not showing up even after discovery

**Cause**: Tool definitions incorrect or not returning proper types

**Solution**:
```python
# Tools must return strings (preferably JSON)
@mcp.tool()
async def my_tool(param: str) -> str:  # Return type MUST be str
    result = {"data": "value"}
    return json.dumps(result)  # Return JSON string
```

---

## Critical Configuration Checklist

Use this checklist to ensure everything is configured correctly:

### MCP Server Code
- [ ] Using `mcp==1.1.2` package
- [ ] `MCPServer(version="X.Y.Z")` includes version
- [ ] Using `mcp.sse_app()` not `streamable_http_app()`
- [ ] Tools decorated with `@mcp.tool()`
- [ ] Tools return `str` type (JSON strings)
- [ ] Health endpoint exists at `/health`

### Docker/Kubernetes
- [ ] Server listens on `0.0.0.0:8001`
- [ ] Service exposes port 8001
- [ ] Health checks pass
- [ ] Logs show "Application startup complete"

### AIRS Gateway Configuration
- [ ] **URL** field: `http://<service>.<namespace>.svc.cluster.local:8001/sse` (must end with /sse)
- [ ] **Server Type**: SSE (Server-Sent Events) selected
- [ ] **Name**: Descriptive name (e.g., "News Fetcher")
- [ ] **Authentication**: None (or configured as needed)
- [ ] API key created with `mcp.invoke` permission

### Discovery Trigger
- [ ] Endpoint: `http://gateway:8788/{slug}/mcp` (no /sse suffix)
- [ ] Header: `x-portkey-api-key: <your-key>`
- [ ] Header: `Content-Type: application/json`
- [ ] Header: `Accept: application/json, text/event-stream` (both!)
- [ ] Sent `initialize` method
- [ ] Sent `tools/list` method
- [ ] Both returned 200 OK

### Gateway UI Verification
- [ ] Status shows "Active"
- [ ] Version shows actual version (not "--")
- [ ] Tools shows count (not "--")
- [ ] Capabilities section lists tools with schemas
- [ ] Can enable/disable individual tools

---

## Quick Reference

### Working Endpoint Pattern
```
POST http://airs-gw:8788/{server-slug}/mcp
Headers:
  x-portkey-api-key: {api-key}
  Content-Type: application/json
  Accept: application/json, text/event-stream
Body: {JSON-RPC request}
```

### Minimal Working MCP Server
```python
from mcp.server.mcpserver import MCPServer
import json

mcp = MCPServer(name="test", version="1.0.0")

@mcp.tool()
async def test_tool(input: str) -> str:
    return json.dumps({"result": input})

app = mcp.sse_app(sse_path="/sse", message_path="/messages")
```

### Server Registration Settings (Actual UI Fields)
- **Name**: `My Server` (display name)
- **Short Description**: `Optional description of what this server does`
- **URL**: `http://<service>:8001/sse` ← Full endpoint URL!
- **Server Type**: SSE (Server-Sent Events)
- **Authentication**: None (or configure as needed)
- **Passthrough headers**: Leave empty (optional)

### Discovery JSON-RPC Sequence
1. `initialize` → Get serverInfo (name, version)
2. `tools/list` → Get tools array with schemas

---

## Additional Resources

- **MCP Protocol Spec**: https://spec.modelcontextprotocol.io/
- **MCP Python SDK**: https://github.com/modelcontextprotocol/python-sdk
- **AIRS Gateway Docs**: https://docs.portkey.ai/ (for SaaS) or check your self-hosted docs
- **Working Example**: See news-fetcher server in this repository

---

## Summary

**The key to success:**

1. ✅ Use `mcp==1.1.2` with `MCPServer` class
2. ✅ Include `version="X.Y.Z"` in constructor
3. ✅ Use `sse_app()` for transport
4. ✅ Register in gateway with Transport=**SSE**
5. ✅ Trigger discovery with both Accept headers
6. ✅ Send `initialize` and `tools/list` requests

Once discovery completes, the gateway UI will show:
- Server version (instead of "--")
- Tool count (instead of "--")
- Full capabilities with allow/deny controls

Good luck! 🚀
