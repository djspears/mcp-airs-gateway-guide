# MCP Server + AIRS Gateway Setup Checklist

**Complete this checklist to deploy an MCP server and get capabilities showing in AIRS Gateway UI.**

---

## ✅ Step-by-Step Checklist

### 1️⃣ Prerequisites

- [ ] Access to AIRS Gateway UI
- [ ] Kubernetes cluster access
- [ ] Docker registry access

---

### 2️⃣ Create AIRS Gateway API Key ⚠️ CRITICAL

```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️  THIS IS REQUIRED TO TRIGGER DISCOVERY!                 │
│ Without this API key, version and tools will show "--"     │
└─────────────────────────────────────────────────────────────┘
```

- [ ] Navigate to AIRS Gateway UI
- [ ] Go to **Settings → API Keys**
- [ ] Click **Create API Key**
- [ ] Enter name: `mcp-client-key`
- [ ] Check permission: ☑ **`mcp.invoke`**
- [ ] Click **Create**
- [ ] Copy and save the API key: `_______________________________`

**Example key:** `your-api-key-here`

---

### 3️⃣ Write MCP Server Code

- [ ] Create `mcp_server.py`:

```python
from mcp.server.mcpserver import MCPServer
import json

mcp = MCPServer(
    name="my-server",
    version="1.0.0"  # ← CRITICAL: Must specify version!
)

@mcp.tool()
async def my_tool(input: str) -> str:
    return json.dumps({"result": input})

app = mcp.sse_app(sse_path="/sse", message_path="/messages")
```

**Critical checks:**
- [ ] `MCPServer` has `version="X.Y.Z"`
- [ ] Using `mcp.sse_app()` NOT `streamable_http_app()`
- [ ] Tools return `str` type (JSON strings)

---

### 4️⃣ Create Dockerfile

- [ ] Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY mcp_server.py .
EXPOSE 8001
CMD ["uvicorn", "mcp_server:app", "--host", "0.0.0.0", "--port", "8001"]
```

- [ ] Create `requirements.txt`:

```
mcp==1.1.2
httpx==0.27.2
uvicorn==0.32.1
```

---

### 5️⃣ Build and Push Docker Image

- [ ] Build: `docker build -t your-registry/mcp-server:1.0.0 .`
- [ ] Push: `docker push your-registry/mcp-server:1.0.0`

---

### 6️⃣ Deploy to Kubernetes

- [ ] Create namespace: `kubectl create namespace mcp-services`
- [ ] Create deployment YAML (see full guide)
- [ ] Create service YAML (expose port 8001)
- [ ] Apply: `kubectl apply -f deployment.yaml -f service.yaml`
- [ ] Verify pod is running: `kubectl get pods -n mcp-services`
- [ ] Test health: `kubectl run curl-test --rm -i --image=curlimages/curl -- curl http://mcp-server:8001/health`

---

### 7️⃣ Register in AIRS Gateway UI

- [ ] Go to **MCP Registry** → **Add MCP Server**
- [ ] Fill out the form:

| Field | Value | ✓ |
|-------|-------|---|
| **Name** | `My MCP Server` | [ ] |
| **Short Description** | `Optional description` | [ ] |
| **URL** | `http://mcp-server.mcp-services.svc.cluster.local:8001/sse` | [ ] |
| **Server Type** | ☑ SSE (Server-Sent Events) | [ ] |
| **Authentication** | None | [ ] |

**Critical checks:**
- [ ] URL ends with `/sse`
- [ ] Server Type is "SSE (Server-Sent Events)" NOT Streamable HTTP
- [ ] URL is internal Kubernetes service URL

- [ ] Click **Save**

**What you'll see:** Version: `--`, Tools: `--` (This is normal! Discovery hasn't happened yet)

---

### 8️⃣ Trigger Capability Discovery 🎯

**This is the magic step that makes version and tools appear!**

**Option A: Using curl**

- [ ] Replace `MY_API_KEY` with your actual key
- [ ] Replace `my-mcp-server` with your server slug

```bash
API_KEY="your-api-key-here"  # Your key here
GATEWAY="http://airs-gw.airs-gw.svc.cluster.local:8788"
SLUG="my-mcp-server"  # Your server slug

# Step 1: Initialize
curl -X POST "${GATEWAY}/${SLUG}/mcp" \
  -H "x-portkey-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}'

# Step 2: List tools
curl -X POST "${GATEWAY}/${SLUG}/mcp" \
  -H "x-portkey-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":"2","method":"tools/list","params":{}}'
```

- [ ] Run initialize request
- [ ] Run tools/list request
- [ ] Both returned 200 OK

**Option B: Using Python script**

- [ ] Copy `trigger_discovery.py` from the full guide
- [ ] Set environment variable: `export AIRS_GATEWAY_API_KEY="your-key"`
- [ ] Run: `python trigger_discovery.py`
- [ ] Script completed successfully

---

### 9️⃣ Verify in Gateway UI ✨

- [ ] Go back to AIRS Gateway UI
- [ ] Navigate to **MCP Registry**
- [ ] Refresh the page
- [ ] Find your server

**Success looks like:**

```
My MCP Server
Active
|
http://airs-gw:8788/my-mcp-server/mcp  ← Proxy URL appears
|
Your Name
|
Created on: Date

Capabilities
Control which tools are exposed to your MCP client.

☑ my_tool         (tool)    [Schema ▾]
```

**Verification checklist:**
- [ ] Version shows actual version (e.g., "1.0.0") instead of "--"
- [ ] Tools shows count (e.g., "1") instead of "--"
- [ ] Capabilities section appears with tool list
- [ ] Each tool has a checkbox for enable/disable
- [ ] Proxy URL shows: `http://gateway:8788/{slug}/mcp`

---

## 🎉 Success!

If all checkboxes above are checked, you've successfully:
✅ Deployed an MCP server
✅ Registered it in AIRS Gateway
✅ Triggered capability discovery
✅ Gateway now shows server version and tool capabilities

---

## 🚨 If Something Failed

**Version still shows "--":**
- [ ] Check you used correct API key with `mcp.invoke` permission
- [ ] Verify both `initialize` and `tools/list` requests returned 200 OK
- [ ] Check MCP server has `version="X.Y.Z"` in code
- [ ] Restart MCP server pod and try discovery again

**Tools still show "--":**
- [ ] Verify `tools/list` request succeeded
- [ ] Check MCP server logs for errors
- [ ] Ensure tools are decorated with `@mcp.tool()`
- [ ] Verify tools return `str` type

**404 Not Found:**
- [ ] Check server slug in gateway matches URL: `/your-slug/mcp`
- [ ] Don't use `/sse` suffix in discovery URL
- [ ] Verify server is registered and "Active" in gateway

**406 Not Acceptable:**
- [ ] Add both Accept headers: `application/json, text/event-stream`
- [ ] Both are required!

**Connection timeout:**
- [ ] Check Server Type is set to "SSE (Server-Sent Events)"
- [ ] Verify URL ends with `/sse`
- [ ] Test backend server directly: `curl http://service:8001/health`

---

## 📚 Need More Help?

See the full guides:
- **MCP_AIRS_GATEWAY_DEPLOYMENT_GUIDE.md** - Complete guide
- **MCP_AIRS_QUICKSTART.md** - Quick reference
- **AIRS_GATEWAY_UI_FIELDS.md** - Field-by-field UI guide
- **Troubleshooting section** - In deployment guide

---

**Date:** 2026-07-31  
**Tested with:** AIRS Gateway v2.15.0, MCP SDK 1.1.2, Kubernetes 1.36.2
