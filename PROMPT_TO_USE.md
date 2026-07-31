# Prompts to Use with Claude

Copy and paste one of these prompts into Claude to get step-by-step help fixing the AIRS Gateway "--" problem:

---

## 📋 Option 1: Complete Walkthrough

```
I need help fixing an issue with my MCP server and Palo Alto AIRS Gateway integration.

PROBLEM:
I've deployed an MCP server and registered it in AIRS Gateway, but the UI shows:
- Version: "--" (instead of showing my actual server version)
- Tools: "--" (instead of showing tool count)
- Capabilities section is empty (no tools listed)

I have access to this complete guide that explains the solution:
https://github.com/djspears/mcp-airs-gateway-guide

WHAT I NEED:
1. Help me understand why this is happening (lazy initialization)
2. Walk me through the exact steps to trigger capability discovery
3. Ensure my MCP server code is configured correctly
4. Help me create the API key with mcp.invoke permission
5. Show me the exact curl commands or script to run discovery
6. Verify everything is working in the gateway UI

MY ENVIRONMENT:
- AIRS Gateway: v2.15.0 (self-hosted)
- Kubernetes cluster: [specify your version]
- MCP Server: [specify if already deployed or starting fresh]

SPECIFIC QUESTIONS:
- What exact software versions should I use? (mcp package, Python, etc.)
- What's the correct MCP server code structure?
- What are the exact discovery requests I need to make?
- How do I verify it worked?

Please guide me through this step-by-step using the guide from the GitHub repo above.
```

---

## 🎯 Alternative: Quick Start Prompt

If they just want to get it working fast:

```
I'm having the AIRS Gateway "--" problem where my MCP server capabilities aren't showing.

Guide: https://github.com/djspears/mcp-airs-gateway-guide

Please:
1. Show me the minimal MCP server code that works (with correct versions)
2. Give me the exact curl commands to trigger discovery
3. Walk me through creating the API key with mcp.invoke permission

I want to get this working as quickly as possible. Use the SETUP_CHECKLIST.md from the repo as our guide.
```

---

## 🔧 Alternative: Troubleshooting Focus

If they already have a server deployed but it's not working:

```
My MCP server is deployed but AIRS Gateway shows "--" for version and tools.

Solution guide: https://github.com/djspears/mcp-airs-gateway-guide

CURRENT STATUS:
- MCP server is running: [yes/no]
- Registered in AIRS Gateway: [yes/no]
- API key created: [yes/no]
- Discovery attempted: [yes/no]

Please help me:
1. Verify my MCP server code is correct (need to check version parameter, sse_app usage)
2. Create the API key with mcp.invoke permission if I don't have one
3. Run the discovery curl commands to trigger lazy initialization
4. Troubleshoot any errors I encounter

Reference the troubleshooting section in MCP_AIRS_GATEWAY_DEPLOYMENT_GUIDE.md from the repo.
```

---

## 📧 Share with Your Team

Here's a message you can send via email or Slack:

```
Hey [Name],

I had the same AIRS Gateway issue you're having (version/tools showing "--"). 
I figured it out and created a complete guide.

GitHub Repo: https://github.com/djspears/mcp-airs-gateway-guide

Copy this prompt into Claude to get help:

---

I need help fixing the AIRS Gateway "--" problem where my MCP server 
capabilities aren't showing in the UI.

Solution guide: https://github.com/djspears/mcp-airs-gateway-guide

Please walk me through:
1. Creating an API key with mcp.invoke permission (CRITICAL!)
2. Ensuring my MCP server code is correct (version="X.Y.Z", sse_app usage)
3. Running discovery curl commands to trigger lazy initialization
4. Verifying success in the gateway UI

Use SETUP_CHECKLIST.md from the repo as the guide.

---

Key insight: The gateway uses "lazy initialization" - you have to manually 
trigger discovery by making API calls through the gateway. Just registering 
the server isn't enough!

Let me know if you need any help.
```

---

## 🎓 What Claude Will Do

When you paste any of these prompts, Claude will:

1. ✅ Read the GitHub repo (all the markdown files)
2. ✅ Understand the lazy initialization problem
3. ✅ Walk them through creating the API key
4. ✅ Show them the correct MCP server code with versions
5. ✅ Give them the exact curl commands to run
6. ✅ Help troubleshoot any errors
7. ✅ Verify success in the UI

Claude has access to all the documentation in the repo, so it can provide:
- Step-by-step guidance from SETUP_CHECKLIST.md
- Code examples from the deployment guide
- Troubleshooting help
- Verification steps

---

**Choose whichever prompt best fits your situation!**

💡 **Tip:** All these prompts are saved in this file on GitHub for easy access:  
https://github.com/djspears/mcp-airs-gateway-guide/blob/main/PROMPT_TO_USE.md
