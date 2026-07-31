#!/usr/bin/env python3
"""
Generic MCP Server Gateway Tester
Tests MCP server discovery and tool invocation through AIRS Gateway

Usage:
    python test_mcp_gateway.py --server news-fetcher --api-key YOUR_KEY
    python test_mcp_gateway.py --server news-summarizer --api-key YOUR_KEY --tool summarize_article

For full usage: python test_mcp_gateway.py --help
"""

import asyncio
import httpx
import json
import uuid
import re
import argparse
from typing import Optional, Dict, Any


class MCPGatewayTester:
    """Test MCP servers through AIRS Gateway"""

    def __init__(self, gateway_url: str, server_slug: str, api_key: str):
        self.gateway_url = gateway_url
        self.server_slug = server_slug
        self.api_key = api_key
        self.mcp_url = f"{gateway_url}/{server_slug}/mcp"
        self.headers = {
            "x-portkey-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }

    @staticmethod
    def parse_sse(text: str) -> Optional[Dict[str, Any]]:
        """Parse SSE formatted response to extract JSON-RPC message"""
        match = re.search(r'data: ({.*})', text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                return None
        return None

    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize connection with MCP server.
        This triggers lazy initialization in AIRS Gateway.

        Returns:
            Server info including name and version
        """
        print("=" * 70)
        print("STEP 1: Initialize MCP Server")
        print("=" * 70)

        init_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "mcp-gateway-tester",
                    "version": "1.0.0"
                }
            }
        }

        print(f"Endpoint: {self.mcp_url}")
        print(f"Request: {json.dumps(init_request, indent=2)}\n")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.mcp_url, json=init_request, headers=self.headers)

            print(f"Response Status: {response.status_code}")

            if response.status_code != 200:
                print(f"✗ Error Response:\n{response.text}")
                return {}

            init_result = self.parse_sse(response.text)

            if init_result and "result" in init_result:
                server_info = init_result["result"].get("serverInfo", {})
                print(f"✓ Server Name: {server_info.get('name')}")
                print(f"✓ Server Version: {server_info.get('version')}")
                return server_info
            else:
                print(f"✗ Unexpected response:\n{response.text}")
                return {}

    async def list_tools(self) -> list:
        """
        List all available tools from the MCP server.

        Returns:
            List of tool definitions with name, description, and schema
        """
        print("\n" + "=" * 70)
        print("STEP 2: List Available Tools")
        print("=" * 70)

        tools_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/list",
            "params": {}
        }

        print(f"Request: {json.dumps(tools_request, indent=2)}\n")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.mcp_url, json=tools_request, headers=self.headers)

            print(f"Response Status: {response.status_code}")

            if response.status_code != 200:
                print(f"✗ Error Response:\n{response.text}")
                return []

            tools_result = self.parse_sse(response.text)

            if tools_result and "result" in tools_result:
                tools = tools_result["result"].get("tools", [])
                print(f"✓ Found {len(tools)} tools:\n")
                for i, tool in enumerate(tools, 1):
                    print(f"{i}. {tool.get('name')}")
                    print(f"   Description: {tool.get('description')}")
                    print(f"   Input Schema: {json.dumps(tool.get('inputSchema', {}), indent=6)}\n")
                return tools
            else:
                print(f"✗ Unexpected response:\n{response.text}")
                return []

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Call a specific tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Dictionary of arguments for the tool

        Returns:
            Tool execution result
        """
        print("\n" + "=" * 70)
        print(f"STEP 3: Call Tool '{tool_name}'")
        print("=" * 70)

        call_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        print(f"Request: {json.dumps(call_request, indent=2)}\n")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.mcp_url, json=call_request, headers=self.headers)

            print(f"Response Status: {response.status_code}")

            if response.status_code != 200:
                print(f"✗ Error Response:\n{response.text}")
                return None

            call_result = self.parse_sse(response.text)

            if call_result:
                if "error" in call_result:
                    print(f"✗ Tool Error: {json.dumps(call_result['error'], indent=2)}")
                    return None
                elif "result" in call_result:
                    result = call_result["result"]

                    # Extract text content from MCP response format
                    if "content" in result and isinstance(result["content"], list):
                        print("✓ Tool Result:\n")
                        for item in result["content"]:
                            if item.get("type") == "text":
                                try:
                                    # Try to pretty-print if it's JSON
                                    parsed = json.loads(item["text"])
                                    print(json.dumps(parsed, indent=2))
                                except (json.JSONDecodeError, TypeError):
                                    # Otherwise print as-is
                                    print(item["text"])
                        return result
                    else:
                        print(f"Result: {json.dumps(result, indent=2)}")
                        return result
            else:
                print(f"✗ Could not parse response:\n{response.text}")
                return None

    async def run_full_test(self, tool_name: Optional[str] = None,
                          tool_args: Optional[Dict[str, Any]] = None):
        """
        Run complete test: initialize, list tools, optionally call a tool.

        Args:
            tool_name: Optional tool to call
            tool_args: Arguments for the tool
        """
        print("\n" + "=" * 70)
        print(f"Testing MCP Server: {self.server_slug}")
        print(f"Gateway URL: {self.gateway_url}")
        print("=" * 70 + "\n")

        # Step 1: Initialize
        server_info = await self.initialize()
        if not server_info:
            print("\n✗ Initialization failed. Stopping.")
            return

        # Step 2: List tools
        tools = await self.list_tools()
        if not tools:
            print("\n✗ No tools found. Server may not be responding correctly.")
            return

        # Step 3: Call tool if specified
        if tool_name and tool_args:
            result = await self.call_tool(tool_name, tool_args)
            if result:
                print("\n✓ Tool call successful!")
            else:
                print("\n✗ Tool call failed.")

        print("\n" + "=" * 70)
        print("Test Complete!")
        print("=" * 70)
        print("\nNext Steps:")
        print("1. Check AIRS Gateway UI - Server should now show version and tools")
        print("2. Look for the server in MCP Registry")
        print(f"3. Version and tool count should be visible (no more '--')")


# Example test arguments for common MCP servers
EXAMPLE_ARGS = {
    "fetch_articles": {
        "sources": ["CNN", "Fox"],
        "max_articles": 2
    },
    "summarize_article": {
        "title": "Test Article Title",
        "source": "CNN",
        "content": "This is a test article about important news events."
    },
    "detect_bias": {
        "title": "Biden Administration Announces New Initiative",
        "source": "CNN",
        "url": "https://example.com",
        "content": "The administration announced new policies today."
    },
    "create_brief": {
        "topic": "Top Stories",
        "articles": [
            {
                "title": "Sample Article",
                "source": "CNN",
                "summary": "This is a summary",
                "bias": "center"
            }
        ]
    }
}


def main():
    parser = argparse.ArgumentParser(
        description="Test MCP server through AIRS Gateway",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic discovery test (initialize + list tools)
  python test_mcp_gateway.py --server news-fetcher --api-key YOUR_KEY

  # Full test with tool call
  python test_mcp_gateway.py --server news-fetcher --api-key YOUR_KEY \\
    --tool fetch_articles --args '{"sources": ["CNN"], "max_articles": 2}'

  # Kubernetes pod test (from within cluster)
  kubectl run test-mcp -n news-agg --rm -i --restart=Never \\
    --image=python:3.11-slim -- bash -c \\
    "pip install -q httpx && python test_mcp_gateway.py --server news-fetcher ..."
        """
    )

    parser.add_argument("--gateway-url",
                       default="http://airs-gw.airs-gw.svc.cluster.local:8788",
                       help="AIRS Gateway URL (default: Kubernetes internal)")
    parser.add_argument("--server", required=True,
                       help="MCP server slug (e.g., news-fetcher)")
    parser.add_argument("--api-key", required=True,
                       help="AIRS Gateway API key with mcp.invoke permission")
    parser.add_argument("--tool",
                       help="Tool name to call (optional)")
    parser.add_argument("--args",
                       help="Tool arguments as JSON string (optional)")

    args = parser.parse_args()

    # Parse tool arguments if provided
    tool_args = None
    if args.args:
        try:
            tool_args = json.loads(args.args)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in --args: {e}")
            return

    # If tool specified but no args, try to use example
    if args.tool and not tool_args:
        if args.tool in EXAMPLE_ARGS:
            print(f"Using example arguments for {args.tool}")
            tool_args = EXAMPLE_ARGS[args.tool]
        else:
            print(f"Warning: No arguments provided for tool '{args.tool}'")
            print(f"Available example tools: {', '.join(EXAMPLE_ARGS.keys())}")

    # Run the test
    tester = MCPGatewayTester(args.gateway_url, args.server, args.api_key)
    asyncio.run(tester.run_full_test(args.tool, tool_args))


if __name__ == "__main__":
    main()
