# MCP Server + AIRS Gateway Integration Guide

**Solve the "--" problem: Get your MCP server capabilities showing in Palo Alto AIRS Gateway UI**

---

## 🎯 The Problem

You've registered an MCP server in AIRS Gateway, but the UI shows:
- **Version:** `--` (instead of your actual version)
- **Tools:** `--` (instead of tool count)
- **Capabilities:** Empty (no tools listed)

**This guide shows you how to fix it!**

---

## 💡 The Root Cause

AIRS Gateway uses **lazy initialization** - it doesn't connect to or discover MCP server capabilities until a client actually makes requests through the gateway proxy.

Simply registering the server in the UI is not enough!

---

## ✅ The Solution

You need to **trigger capability discovery** by making two JSON-RPC requests through the gateway:

1. **`initialize`** - Gateway gets server name and version
2. **`tools/list`** - Gateway gets list of available tools

Once these requests succeed, the gateway caches the information and displays it in the UI.

---

## 🚀 Quick Start

### Option 1: Follow the Checklist (Recommended)

**→ [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md)** - Step-by-step guide with checkboxes

This walks you through:
1. Creating an API key with `mcp.invoke` permission ⚠️ CRITICAL
2. Deploying your MCP server
3. Registering it in the gateway
4. Triggering discovery
5. Verifying success

### Option 2: Read the Full Guide

**→ [MCP_AIRS_GATEWAY_DEPLOYMENT_GUIDE.md](MCP_AIRS_GATEWAY_DEPLOYMENT_GUIDE.md)** - Complete reference

Detailed guide with:
- MCP server code examples
- Docker/Kubernetes configs
- Gateway configuration
- Three ways to trigger discovery
- Comprehensive troubleshooting

### Option 3: Quick Reference

**→ [MCP_AIRS_QUICKSTART.md](MCP_AIRS_QUICKSTART.md)** - One-page cheat sheet

Minimal code and commands to get it working fast.

### Option 4: UI Field Guide

**→ [AIRS_GATEWAY_UI_FIELDS.md](AIRS_GATEWAY_UI_FIELDS.md)** - Visual UI walkthrough

Field-by-field explanation of the gateway registration form.

---

## ⚡ Fastest Path to Success

```bash
# 1. Create API key in AIRS Gateway UI
#    Settings → API Keys → Create
#    Name: mcp-client-key
#    Permission: ✓ mcp.invoke
#    Copy the key!

# 2. Register your MCP server in gateway UI
#    MCP Registry → Add MCP Server
#    Name: Your Server
#    URL: http://your-service:8001/sse
#    Server Type: SSE (Server-Sent Events)
#    Save

# 3. Run discovery (replace YOUR_KEY and YOUR_SLUG)
curl -X POST "http://gateway:8788/YOUR_SLUG/mcp" \
  -H "x-portkey-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}'

curl -X POST "http://gateway:8788/YOUR_SLUG/mcp" \
  -H "x-portkey-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":"2","method":"tools/list","params":{}}'

# 4. Refresh gateway UI
#    Version and tools should now be visible! ✨
```

---

## 🔑 Critical Requirements

### 1. API Key with `mcp.invoke` Permission
Without this, discovery won't work! Create it in:
**Settings → API Keys → Create → Check `mcp.invoke`**

### 2. MCP Server Must Have Version
```python
from mcp.server.mcpserver import MCPServer

mcp = MCPServer(
    name="my-server",
    version="1.0.0"  # ← MUST SPECIFY!
)
```

### 3. Use SSE Transport
```python
# Correct:
app = mcp.sse_app(sse_path="/sse", message_path="/messages")

# Wrong:
app = mcp.streamable_http_app()  # Don't use this!
```

### 4. Gateway Registration Settings
- **Server Type:** SSE (Server-Sent Events) ← Not Streamable HTTP!
- **URL:** Must end with `/sse` (e.g., `http://service:8001/sse`)
- **Authentication:** None (for basic setup)

### 5. Discovery Headers
Both Accept headers are required:
```
Accept: application/json, text/event-stream
```

---

## 🎉 Success Looks Like

**Before Discovery:**
```
My MCP Server
Status: Active
Version: --
Tools: --
```

**After Discovery:**
```
My MCP Server  
Status: Active
Version: 1.0.0 ✓
Tools: 3 ✓

Capabilities
☑ fetch_articles    (tool)
☑ summarize_text    (tool)
☑ analyze_sentiment (tool)
```

---

## 🚨 Common Issues

| Problem | Solution |
|---------|----------|
| Still shows "--" | Check API key has `mcp.invoke` permission |
| 404 Not Found | Use `/your-slug/mcp` not `/your-slug/mcp/sse` |
| 406 Not Acceptable | Add both Accept headers (json + event-stream) |
| Connection timeout | Set Server Type to "SSE", URL must end with `/sse` |
| No version in MCP code | Add `version="X.Y.Z"` to MCPServer() |

---

## 📚 What's in This Repo

```
mcp-airs-gateway-guide/
├── README.md (this file)
│   └── Quick overview and fastest path
│
├── SETUP_CHECKLIST.md ⭐ START HERE
│   └── Step-by-step guide with checkboxes
│
├── MCP_AIRS_GATEWAY_DEPLOYMENT_GUIDE.md
│   └── Complete deployment reference
│
├── MCP_AIRS_QUICKSTART.md
│   └── One-page cheat sheet
│
└── AIRS_GATEWAY_UI_FIELDS.md
    └── Visual guide to gateway UI
```

---

## 🏆 Tested Configuration

**Proven to work with:**
- AIRS Gateway: v2.15.0 (Palo Alto self-hosted)
- MCP Python SDK: `mcp==1.1.2`
- Kubernetes: 1.36.2
- Python: 3.11

---

## 🤝 Contributing

Found an issue or have improvements? Open a PR or issue!

---

## 📄 License

MIT License - Use freely for your projects

---

## 💬 Support

If you're stuck:
1. Check **SETUP_CHECKLIST.md** for step-by-step guidance
2. Review **Troubleshooting** section in the deployment guide
3. Verify all critical requirements above
4. Check your gateway and MCP server logs

---

**Happy deploying! 🚀**

*Last updated: 2026-07-31*
