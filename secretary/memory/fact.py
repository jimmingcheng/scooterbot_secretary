import arrow
from pydantic import BaseModel


from secretary.memory.db import get_client


class Fact(BaseModel):
    user_id: str
    content: str
    timestamp: int = arrow.now().int_timestamp
    tags: list[str] = []
    uuid: str | None = None

    def upsert(self):
        client = get_client()
        facts = client.collections.get('Fact')
        if self.uuid:
            facts.data.update(
                uuid=self.uuid,
                properties={
                    'userId': self.user_id,
                    'content': self.content,
                    'timestamp': self.timestamp,
                    'tags': self.tags
                }
            )
        else:
            self.uuid = facts.data.insert(
                properties={
                    'userId': self.user_id,
                    'content': self.content,
                    'timestamp': self.timestamp,
                    'tags': self.tags
                }
            )
        client.close()
