# AIRS Gateway MCP Server UI Fields - Actual Form Guide

## The Actual Registration/Edit Form

When you create or edit an MCP server in AIRS Gateway, here's the actual form you'll see:

### Form Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Update MCP integration                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Name *                                                      │
│ ____________________________________________                │
│ (e.g., "News Fetcher")                                      │
│                                                             │
│ Short Description (Optional)                                │
│ ____________________________________________                │
│ (e.g., "Fetch news articles from major sources")           │
│                                                             │
│ URL *                                                       │
│ ____________________________________________                │
│ (e.g., "http://mcp-fetcher.news-agg.svc.cluster.local:8001/sse")
│                                                             │
│ Server Type                                                 │
│ ○ SSE (Server-Sent Events)                                 │
│   Recommended for most integrations. Supports streaming     │
│   responses over standard HTTP connections.                 │
│ ○ Streamable HTTP                                          │
│ ○ stdio                                                     │
│                                                             │
│ Passthrough headers (Optional)                              │
│ Add custom HTTP headers to forward with every request       │
│ to the MCP server.                                          │
│                                                             │
│   Passthrough Headers        Passthrough String            │
│   [Enter Header     ▾]       [Enter String        ]        │
│                                                             │
│ Authentication                                              │
│ Select how your MCP client authenticates with the server.   │
│ [None ▾]                                                    │
│                                                             │
│ ▼ Advanced Settings                                         │
│                                                             │
│                                [Save]  [Cancel]             │
└─────────────────────────────────────────────────────────────┘
```

---

## Field-by-Field Guide

### Name * (Required)
- **What it is**: Display name for the MCP server
- **Example**: `News Fetcher`, `My MCP Server`
- **Rules**: Can contain spaces, capitals, any characters
- **Used for**: Human-readable identification in UI

### Short Description (Optional)
- **What it is**: Brief description of what the server does
- **Example**: `Fetch news articles from major sources (CNN, Fox, NYT, etc.)`
- **Rules**: Free text, appears in server overview
- **Used for**: Documentation and user information

### URL * (Required)
- **What it is**: ⚠️ **The full endpoint URL to your MCP server**
- **Format**: `http://{service}.{namespace}.svc.cluster.local:{port}/sse`
- **Example**: `http://mcp-fetcher.news-agg.svc.cluster.local:8001/sse`
- **Critical**: MUST end with `/sse` for SSE transport
- **Used for**: Gateway connects to this URL to reach your MCP server

### Server Type (Radio Buttons)
- **What it is**: MCP transport protocol selection
- **Options**:
  - ✅ **SSE (Server-Sent Events)** ← Choose this!
    - "Recommended for most integrations. Supports streaming responses over standard HTTP connections."
  - ❌ **Streamable HTTP** ← Don't use (doesn't work for discovery)
  - ❌ **stdio** ← For local processes only
- **Required**: Select **SSE (Server-Sent Events)**

### Passthrough headers (Optional)
- **What it is**: Custom HTTP headers to forward to the MCP server
- **Format**: Key-value pairs
- **Example**: 
  - Header: `X-Custom-Header`
  - String: `custom-value`
- **Typical use**: Leave empty unless you need custom headers
- **Use case**: For auth tokens, custom routing, etc.

### Authentication
- **What it is**: How clients authenticate with the MCP server (not the gateway!)
- **Options**: 
  - `None` ← Use this for internal K8s services
  - `OAuth`
  - `Custom headers`
- **Note**: This is MCP client → MCP server auth (separate from gateway API key)

### Advanced Settings (Collapsed)
- Additional configuration options
- Typically can leave as defaults

---

## Example: Correctly Filled Form

```
Name *
News Fetcher

Short Description (Optional)
Fetch news articles from major sources (CNN, Fox, NYT, etc.)

URL *
http://mcp-fetcher.news-agg.svc.cluster.local:8001/sse

Server Type
☑ SSE (Server-Sent Events)
  Recommended for most integrations. Supports streaming responses over 
  standard HTTP connections.

Passthrough headers (Optional)
[Empty - no custom headers needed]

Authentication
None
```

---

## Common Mistakes

### ❌ Wrong - Missing /sse in URL
```
URL: http://mcp-fetcher.news-agg.svc.cluster.local:8001
```
**Fix**: Add `/sse` at the end:
```
URL: http://mcp-fetcher.news-agg.svc.cluster.local:8001/sse
```

### ❌ Wrong - Selected Streamable HTTP
```
Server Type
☑ Streamable HTTP
```
**Fix**: Select SSE instead:
```
Server Type
☑ SSE (Server-Sent Events)
```

### ❌ Wrong - Using external URL format
```
URL: http://gateway:8788/news-fetcher/mcp
```
**Fix**: Use the internal service URL:
```
URL: http://mcp-fetcher.news-agg.svc.cluster.local:8001/sse
```

---

## After Saving - What You'll See

### In the Overview (Before Discovery)

When you view the server in the MCP Registry, you'll see:

```
News Fetcher
Active
|
news-fetcher                    ← Auto-generated slug from "News Fetcher"
|
http://mcp-fetcher.news-agg.svc.cluster.local:8001/sse
                                ← This shows the URL field
|
David Spears
|
Created on: Jul 31, 08:23 AM
```

**Note**: At this point, server version and tools will show `--` because discovery hasn't happened yet.

### After Discovery Triggered

Once you run the discovery script:

```
News Fetcher
Active
|
http://airs-gw.airs-gw.svc.cluster.local:8788/news-fetcher/mcp
                                ← Now shows gateway proxy URL
|
David Spears
|
Created on: Jul 31, 08:23 AM

Capabilities
Control which tools are exposed to your MCP client.

Search capabilities
[Select All] [Deselect All]

NAME                         TYPE    SCHEMA
☑ fetch_articles             tool    [▾]
☑ fetch_social_media_posts   tool    [▾]
☑ fetch_technical_docs       tool    [▾]
```

---

## Key Concepts

### Server URL vs Gateway Proxy URL

**Server URL** (what you configure):
```
http://mcp-fetcher.news-agg.svc.cluster.local:8001/sse
└─────────────┬────────────────────────────┘    └┬┘
         Internal K8s service                  SSE endpoint
```
- This is where your MCP server actually runs
- Gateway uses this to connect to your server
- Internal to your K8s cluster

**Gateway Proxy URL** (auto-generated):
```
http://airs-gw.airs-gw.svc.cluster.local:8788/news-fetcher/mcp
└──────────────┬────────────────────────┘      └─────┬─────┘└┬┘
           Gateway service                   Server slug  Proxy path
```
- This is the URL clients use to access your server through the gateway
- Gateway forwards requests to the Server URL
- Provides observability, auth, and control

### Server Slug

The server slug is auto-generated from the **Name** field:
- `News Fetcher` → `news-fetcher`
- `My MCP Server` → `my-mcp-server`
- Converts to lowercase, replaces spaces with hyphens

---

## Quick Validation Commands

After configuring the server, verify:

```bash
# 1. Test the backend MCP server directly
kubectl run curl-test --rm -i --namespace news-agg --image=curlimages/curl -- \
  curl -v http://mcp-fetcher.news-agg.svc.cluster.local:8001/health

# Expected: {"status":"healthy"}

# 2. Test SSE endpoint responds
kubectl run curl-test --rm -i --namespace news-agg --image=curlimages/curl -- \
  curl -N -H "Accept: text/event-stream" --max-time 2 \
  http://mcp-fetcher.news-agg.svc.cluster.local:8001/sse

# Expected: Connection opens (may timeout after 2s, that's ok)
```

---

## URL Format Reference

### For Kubernetes Services

**Same namespace:**
```
http://{service-name}:{port}/sse
Example: http://mcp-fetcher:8001/sse
```

**Different namespace:**
```
http://{service-name}.{namespace}.svc.cluster.local:{port}/sse
Example: http://mcp-fetcher.news-agg.svc.cluster.local:8001/sse
```

**Cross-cluster (external):**
```
http://{external-hostname}:{port}/sse
Example: http://mcp-server.example.com:8001/sse
```

---

## Required vs Optional Fields Summary

| Field | Required? | Common Value |
|-------|-----------|--------------|
| Name | ✅ Required | `News Fetcher` |
| Short Description | ⚪ Optional | Description text |
| URL | ✅ Required | `http://service:8001/sse` |
| Server Type | ✅ Required | SSE (Server-Sent Events) |
| Passthrough headers | ⚪ Optional | (empty) |
| Authentication | ✅ Required | None |

---

## Troubleshooting Configuration

### "Can't connect to server"
**Check:**
1. URL field ends with `/sse`
2. Service name and namespace are correct
3. Port number matches your deployment
4. Server Type is "SSE (Server-Sent Events)"

### "Server shows '--' for version/tools"
**Check:**
1. Server has `version="1.0.0"` in code
2. Discovery script was run (see main guide)
3. Both `initialize` and `tools/list` requests succeeded

### "404 Not Found when calling gateway proxy"
**Check:**
1. Server slug matches what's shown in overview
2. Using `/news-fetcher/mcp` not `/news-fetcher/mcp/sse`
3. Gateway service is running

---

## Summary

**The correct setup:**

1. **Name**: Whatever you want (e.g., "News Fetcher")
2. **URL**: Full endpoint with `/sse` (e.g., `http://service:8001/sse`)
3. **Server Type**: ✅ SSE (Server-Sent Events)
4. **Authentication**: None (for basic setup)

After saving, run the discovery script to populate capabilities! 🚀
