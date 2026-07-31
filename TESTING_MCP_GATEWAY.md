# Testing MCP Servers with AIRS Gateway

This guide shows you how to use the `test_mcp_gateway.py` script to test your MCP server integration with AIRS Gateway and trigger lazy initialization.

---

## Why You Need This

**Problem:** After registering an MCP server in AIRS Gateway, it shows:
- Version: `--`
- Tools: `--`
- No capabilities listed

**Solution:** The gateway uses lazy initialization. You must make actual requests through the gateway to trigger capability discovery. This script does that for you!

---

## Prerequisites

1. **MCP Server registered in AIRS Gateway**
   - Note the server slug (e.g., `news-fetcher`)
   - Server must be running and accessible

2. **API Key with mcp.invoke permission**
   - Create in: Settings → API Keys → Create
   - Check: `mcp.invoke` permission
   - Copy the key

3. **Python 3.11+ with httpx**
   ```bash
   pip install httpx
   ```

---

## Quick Start

### Basic Discovery Test

This runs initialization and lists tools (triggers discovery):

```bash
python test_mcp_gateway.py \
  --server news-fetcher \
  --api-key cjIP8ikFLhSuzoKWUCD0UuaJiX4d
```

**What it does:**
1. Sends `initialize` request → Gateway caches server name/version
2. Sends `tools/list` request → Gateway caches tool definitions
3. After this, refresh the gateway UI and you'll see version & tools! ✓

### Full Test with Tool Call

Test a specific tool:

```bash
python test_mcp_gateway.py \
  --server news-fetcher \
  --api-key cjIP8ikFLhSuzoKWUCD0UuaJiX4d \
  --tool fetch_articles \
  --args '{"sources": ["CNN"], "max_articles": 2}'
```

---

## Usage Examples

### Test News Fetcher

```bash
python test_mcp_gateway.py \
  --server news-fetcher \
  --api-key YOUR_KEY \
  --tool fetch_articles \
  --args '{"sources": ["CNN", "Fox"], "max_articles": 3}'
```

### Test News Summarizer

```bash
python test_mcp_gateway.py \
  --server news-summarizer \
  --api-key YOUR_KEY \
  --tool summarize_article \
  --args '{
    "title": "Breaking News Story",
    "source": "CNN",
    "content": "Full article text here..."
  }'
```

### Test Bias Detector

```bash
python test_mcp_gateway.py \
  --server news-bias-detector \
  --api-key YOUR_KEY \
  --tool detect_bias \
  --args '{
    "title": "Political Article Title",
    "source": "CNN",
    "url": "https://example.com",
    "content": "Article content here..."
  }'
```

### Test Synthesizer

```bash
python test_mcp_gateway.py \
  --server news-synthesizer \
  --api-key YOUR_KEY \
  --tool create_brief \
  --args '{
    "topic": "Top Stories",
    "articles": [
      {
        "title": "Sample Article",
        "source": "CNN",
        "summary": "Article summary",
        "bias": "center"
      }
    ]
  }'
```

---

## Running from Kubernetes

If your gateway is only accessible from within the cluster:

```bash
# Copy script to clipboard or create inline
kubectl run test-mcp -n news-agg --rm -i --restart=Never \
  --image=python:3.11-slim -- bash -c "
pip install -q httpx &&
cat > test.py << 'SCRIPT'
$(cat test_mcp_gateway.py)
SCRIPT
python test.py \
  --server news-fetcher \
  --api-key cjIP8ikFLhSuzoKWUCD0UuaJiX4d
"
```

---

## Understanding the Output

### Step 1: Initialize

```
============================================================
STEP 1: Initialize MCP Server
============================================================
Endpoint: http://airs-gw:8788/news-fetcher/mcp
Request: {
  "jsonrpc": "2.0",
  "id": "...",
  "method": "initialize",
  ...
}

Response Status: 200
✓ Server Name: fetcher-agent
✓ Server Version: 1.0.0
```

**What this means:**
- Gateway successfully connected to your MCP server
- Server metadata is now cached in gateway
- Refresh UI to see version number!

### Step 2: List Tools

```
============================================================
STEP 2: List Available Tools
============================================================
Request: {
  "jsonrpc": "2.0",
  "method": "tools/list",
  ...
}

✓ Found 3 tools:

1. fetch_articles
   Description: Retrieve raw news articles from major news sources...
   Input Schema: {...}
```

**What this means:**
- Gateway now knows what tools are available
- Tool definitions are cached
- Refresh UI to see tool count and capabilities!

### Step 3: Call Tool (Optional)

```
============================================================
STEP 3: Call Tool 'fetch_articles'
============================================================
✓ Tool Result:

{
  "articles": [
    {
      "title": "Breaking News...",
      "source": "CNN",
      "content": "..."
    }
  ]
}

✓ Tool call successful!
```

**What this means:**
- Tool executed successfully through the gateway
- All observability captured in AIRS Gateway
- Check Gateway UI → Logs/Traces for full details

---

## Verifying Success in AIRS Gateway UI

After running the test:

1. **Open AIRS Gateway UI** → MCP Registry

2. **Find your server** (e.g., "News Fetcher")

3. **Check that it now shows:**
   ```
   News Fetcher
   Status: Active
   Version: 1.0.0  ✓ (no more "--")
   Tools: 3        ✓ (no more "--")

   Capabilities:
   ☑ fetch_articles
   ☑ fetch_social_media_posts
   ☑ fetch_technical_docs
   ```

4. **Check Logs/Traces** section for observability:
   - Initialize request
   - Tools list request
   - Tool call requests (if you ran with --tool)
   - Full request/response traces
   - Token usage
   - Latency metrics

---

## Command-Line Options

```
--gateway-url URL
    AIRS Gateway base URL
    Default: http://airs-gw.airs-gw.svc.cluster.local:8788
    Use for external gateway: http://your-gateway.example.com:8788

--server SLUG
    MCP server slug as registered in gateway
    Required
    Example: news-fetcher

--api-key KEY
    AIRS Gateway API key with mcp.invoke permission
    Required
    Get from: Settings → API Keys

--tool NAME
    Tool name to call (optional)
    Example: fetch_articles

--args JSON
    Tool arguments as JSON string (optional)
    Example: '{"sources": ["CNN"], "max_articles": 2}'
```

---

## Troubleshooting

### Error: Connection refused

**Cause:** Gateway URL is incorrect or gateway is not accessible

**Fix:**
- Verify gateway URL: `kubectl get svc -n airs-gw`
- If testing from outside cluster, use external IP/LoadBalancer
- If testing from inside cluster, use: `http://airs-gw.airs-gw.svc.cluster.local:8788`

### Error: 404 Not Found

**Cause:** Server slug is incorrect or server not registered

**Fix:**
- Check server slug in AIRS Gateway UI → MCP Registry
- Ensure server is registered and active
- Slug is usually lowercase with hyphens (e.g., `news-fetcher`)

### Error: 401 Unauthorized / Invalid API key

**Cause:** API key is wrong or doesn't have mcp.invoke permission

**Fix:**
- Verify API key in: Settings → API Keys
- Ensure `mcp.invoke` permission is checked
- Create new key if needed

### Error: Connection timeout

**Cause:** MCP server is not running or not accessible from gateway

**Fix:**
- Check MCP server pod: `kubectl get pods -n news-agg`
- Check service: `kubectl get svc -n news-agg`
- Verify URL in gateway registration matches actual service URL

### Server still shows "--" after test

**Cause:** Test failed or gateway didn't cache the response

**Fix:**
- Check test output - did both initialize and tools/list succeed?
- Hard refresh browser (Ctrl+Shift+R)
- Check gateway logs for errors
- Re-run test with fresh terminal output

---

## Advanced Usage

### Custom Gateway URL

For self-hosted gateway on different domain:

```bash
python test_mcp_gateway.py \
  --gateway-url https://my-gateway.company.com \
  --server my-mcp-server \
  --api-key YOUR_KEY
```

### Testing Multiple Servers

Create a test script:

```bash
#!/bin/bash
API_KEY="cjIP8ikFLhSuzoKWUCD0UuaJiX4d"

for server in news-fetcher news-summarizer news-bias-detector news-synthesizer; do
  echo "Testing $server..."
  python test_mcp_gateway.py --server $server --api-key $API_KEY
  echo ""
done
```

### Automated Testing in CI/CD

```yaml
# .github/workflows/test-mcp-gateway.yml
name: Test MCP Gateway Integration

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install httpx
      - run: |
          python test_mcp_gateway.py \
            --gateway-url ${{ secrets.GATEWAY_URL }} \
            --server news-fetcher \
            --api-key ${{ secrets.GATEWAY_API_KEY }}
```

---

## What Happens Behind the Scenes

When you run the test, here's the flow:

```
┌──────────────┐                ┌──────────────┐                ┌──────────────┐
│ Test Script  │                │ AIRS Gateway │                │  MCP Server  │
└──────┬───────┘                └──────┬───────┘                └──────┬───────┘
       │                               │                               │
       │ 1. Initialize                 │                               │
       ├──────────────────────────────>│                               │
       │   (JSON-RPC over SSE)         │ Connect & get server info     │
       │                               ├──────────────────────────────>│
       │                               │ <─────────────────────────────┤
       │                               │   (name, version)             │
       │ <─────────────────────────────┤                               │
       │   Cache server metadata       │                               │
       │                               │                               │
       │ 2. List Tools                 │                               │
       ├──────────────────────────────>│                               │
       │                               │ Get tool definitions          │
       │                               ├──────────────────────────────>│
       │                               │ <─────────────────────────────┤
       │                               │   (tool schemas)              │
       │ <─────────────────────────────┤                               │
       │   Cache tool catalog          │                               │
       │                               │                               │
       │ 3. Call Tool (optional)       │                               │
       ├──────────────────────────────>│                               │
       │                               │ Execute tool                  │
       │                               ├──────────────────────────────>│
       │                               │ <─────────────────────────────┤
       │                               │   (tool result)               │
       │ <─────────────────────────────┤                               │
       │   Full observability trace    │                               │
```

**After Step 2 completes**, the gateway has:
- ✓ Server name and version cached
- ✓ Tool definitions cached
- ✓ UI can now display this information (refresh to see)

---

## Summary

This test script helps you:
1. ✓ Trigger lazy initialization in AIRS Gateway
2. ✓ Verify MCP server is working correctly
3. ✓ Populate version and tool information in UI
4. ✓ Test actual tool execution
5. ✓ Confirm observability is working

**After a successful test, your MCP server should show full details in the AIRS Gateway UI!**

---

For more information, see:
- [MCP_AIRS_GATEWAY_DEPLOYMENT_GUIDE.md](MCP_AIRS_GATEWAY_DEPLOYMENT_GUIDE.md) - Full deployment guide
- [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md) - Step-by-step setup
- [README.md](README.md) - Overview and quick start
