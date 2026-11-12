import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(command=sys.executable, args=["mcp_server/server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            result = await session.call_tool("list_flagged_accounts", {"limit": 3})
            print("\nlist_flagged_accounts:\n", result.content[0].text)

            result = await session.call_tool("investigate_account", {"account_id": "MULE_07aaf84e"})
            print("\ninvestigate_account (first 600 chars):\n", result.content[0].text[:600])


asyncio.run(main())