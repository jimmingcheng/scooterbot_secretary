import asyncio
import sys
from agents import Runner
from agents import gen_trace_id
from agents import trace
from agents.mcp import MCPServer
from agents.mcp import MCPServerStreamableHttp


import secretary
from secretary.agents.tesla import TeslaAgent


USER_ID = 'ba813a80-54b6-4ca3-8d55-f964d2145b4b'


async def run(mcp_server: MCPServer, query: str) -> None:
    agent = TeslaAgent(
        user_id=USER_ID,
        mcp_server=mcp_server,
    )

    result = await Runner.run(
        agent,
        f"My user_id is {USER_ID}. {query}",
    )

    print(result.final_output)


async def main(query: str):
    async with MCPServerStreamableHttp(
        name="Streamable HTTP Python Server",
        params={
            "url": "http://tesla_mcp:9888/mcp",
        },
    ) as server:
        trace_id = gen_trace_id()
        with trace(workflow_name="Streamable HTTP Example", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
            await run(server, query)


if __name__ == "__main__":
    secretary.init()
    asyncio.run(main(sys.argv[1]))
