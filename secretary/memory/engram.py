from pydantic import BaseModel

from secretary.memory.db import get_client
from secretary.memory.fact import Fact


class Engram(BaseModel):
    user_id: str
    content: str
    summary: str
    start_timestamp: int
    end_timestamp: int
    tags: list[str]
    uuid: str | None = None

    def upsert(self):
        client = get_client()
        engrams = client.collections.get('Engram')
        if self.uuid:
            engrams.data.update(
                uuid=self.uuid,
                properties={
                    'userId': self.user_id,
                    'content': self.content,
                    'summary': self.summary,
                    'startTimestamp': self.start_timestamp,
                    'endTimestamp': self.end_timestamp,
                    'tags': self.tags
                }
            )
        else:
            self.uuid = engrams.data.insert(
                properties={
                    'userId': self.user_id,
                    'content': self.content,
                    'summary': self.summary,
                    'startTimestamp': self.start_timestamp,
                    'endTimestamp': self.end_timestamp,
                    'tags': self.tags
                }
            )
        client.close()

    @classmethod
    def summarize(self, facts: list[Fact]) -> 'Engram':
        return Engram(
            user_id=facts[0].user_id,
            content='\n'.join([f.content for f in facts]),
            summary=facts[0].content.split('\n')[1],
            start_timestamp=facts[0].timestamp,
            end_timestamp=facts[-1].timestamp,
            tags=facts[0].tags
        )
