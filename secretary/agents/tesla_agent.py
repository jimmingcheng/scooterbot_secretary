from __future__ import annotations

import httpx

from secretary.account_linking import get_account_link_manager
from secretary.service_config import cfg


class TeslaAgent:
    user_id: str

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id

    async def make_request(self, request: str) -> str:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                cfg().account_links.tesla.api_host + '/send_message_to_agent',
                json={
                    'user_id': self.user_id,
                    'message': request,
                },
            )

        return resp.text

    @classmethod
    def from_secretary_user_id(cls, secretary_user_id: str) -> TeslaAgent | None:
        tesla_user_id = get_account_link_manager().get_linked_user_id(secretary_user_id, 'tesla')
        return cls(tesla_user_id) if tesla_user_id else None
