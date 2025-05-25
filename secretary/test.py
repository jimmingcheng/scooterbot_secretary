import asyncio
import sys
from agents import Runner

import secretary
from secretary.agents.main_agent import get_secretary_agent


async def main(query: str) -> None:
    async with get_secretary_agent() as secretary_agent:
        result = await Runner().run(
            secretary_agent,
            query,
        )

        print(result.final_output)


if __name__ == '__main__':
    secretary.init()
    asyncio.run(main(sys.argv[1]))
