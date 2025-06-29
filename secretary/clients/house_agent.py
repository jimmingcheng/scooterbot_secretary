import httpx

from secretary.service_config import config


async def make_request(user_id: str, request: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            config.account_links.house.api_host + '/send_message_to_agent',
            json={
                'user_id': user_id,
                'message': request,
            },
        )

    return resp.text
