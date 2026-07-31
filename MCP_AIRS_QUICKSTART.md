# MCP + AIRS Gateway Quick Start

**TL;DR: Get MCP server capabilities showing in AIRS Gateway UI**

## ⚠️ Prerequisites

**Create AIRS Gateway API Key First!**
1. AIRS Gateway UI → **Settings → API Keys**
2. Click **Create API Key**
3. Name: `mcp-client-key`
4. Permissions: Check ☑ **`mcp.invoke`** ← Required!
5. Copy the key (e.g., `your-api-key-here`)

---

## The Secret Sauce

**Why version shows "--"**: Gateway uses lazy initialization - it won't discover capabilities until you make requests through the proxy.

**The fix**: Send two JSON-RPC requests through the gateway to trigger discovery.

---

## Minimal Working Server

```python
# mcp_server.py
from mcp.server.mcpserver import MCPServer
import json

mcp = MCPServer(
    name="my-server",
    version="1.0.0"  # ← CRITICAL! Must specify version
)

@mcp.tool()
async def my_tool(input: str) -> str:
    return json.dumps({"result": input})

# ← CRITICAL! Use sse_app() not streamable_http_app()
app = mcp.sse_app(sse_path="/sse", message_path="/messages")
```

**Requirements**: `mcp==1.1.2`

---

## Gateway Configuration

In AIRS Gateway UI (actual field names):

| Field | Value |
|---------|-------|
| **Name** | `My Server` |
| **Short Description** | `Optional description` |
| **URL** | `http://your-service:8001/sse` ← Full endpoint! |
| **Server Type** | SSE (Server-Sent Events) |
| **Authentication** | None |

---

## Trigger Discovery

**Critical headers:**
```bash
-H "x-portkey-api-key: YOUR_KEY"
-H "Content-Type: application/json"
-H "Accept: application/json, text/event-stream"  # ← Both required!
```

**Request 1 - Initialize:**
```bash
curl -X POST "http://gateway:8788/my-server/mcp" \
  -H "x-portkey-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}'
```

**Request 2 - List Tools:**
```bash
curl -X POST "http://gateway:8788/my-server/mcp" \
  -H "x-portkey-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":"2","method":"tools/list","params":{}}'
```

**Result**: Refresh gateway UI → version and tools now visible!

---

## Common Gotchas

| Problem | Solution |
|---------|----------|
| Version shows "--" | Add `version="1.0.0"` to `MCPServer()` constructor |
| 406 Not Acceptable | Add both Accept headers (json + event-stream) |
| 404 Not Found | Use `/my-server/mcp` not `/my-server/mcp/sse` |
| Connection timeout | Check **URL** field ends with `/sse` |
| Transport error | Set Server Type to "SSE (Server-Sent Events)" |
| Tools not appearing | Use `mcp.sse_app()` not `streamable_http_app()` |

---

## Verification Checklist

- [ ] MCP server has `version="X.Y.Z"` in code
- [ ] Using `mcp.sse_app()` (check code)
- [ ] Gateway **Server Type** = "SSE (Server-Sent Events)"
- [ ] Gateway **URL** field = endpoint ending with `/sse`
- [ ] Both Accept headers in discovery request
- [ ] Sent both `initialize` and `tools/list`
- [ ] Both returned 200 OK
- [ ] Refreshed gateway UI

✅ After discovery: Version and tool count appear in UI (no more "--")

---

**Full guide**: See `MCP_AIRS_GATEWAY_DEPLOYMENT_GUIDE.md`
