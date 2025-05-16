import asyncio
import sys
from agents import Runner
from calendar_agent import CalendarAgent
from googleapiclient import discovery

import secretary
from secretary.config import google_api_key
from secretary.google_apis import get_google_apis_creds


def run(query: str) -> None:
    calsvc = discovery.build('calendar', 'v3', credentials=get_google_apis_creds('117748904066846367871'))

    result = asyncio.run(
        Runner().run(
            CalendarAgent(calsvc, google_api_key()),
            query,
        )
    )

    print(result.final_output)


if __name__ == '__main__':
    secretary.init()
    run(sys.argv[1])
