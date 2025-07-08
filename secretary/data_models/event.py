from __future__ import annotations

from typing import Any

from googleapiclient.discovery import Resource
from pydantic import BaseModel


class Event(BaseModel):
    id: str | None = None
    summary: str
    start: str
    end: str
    location: str | None = None

    def to_gcal_event(self) -> dict[str, Any]:
        event: dict[str, Any] = {
            'summary': self.summary,
        }

        event['start'] = {'dateTime': self.start} if 'T' in self.start else {'date': self.start}
        event['end'] = {'dateTime': self.end} if 'T' in self.end else {'date': self.end}

        if self.location:
            event['location'] = self.location
        return event

    @classmethod
    def from_gcal_event(cls, event: dict[str, Any]) -> Event:
        start = event['start'].get('dateTime') or event['start']['date']
        end = event['end'].get('dateTime') or event['end']['date']

        return cls(
            id=event['id'],
            summary=event['summary'],
            start=start,
            end=end,
            location=event.get('location'),
        )

    @classmethod
    def get(cls, cal: Resource, calendar_id: str, event_id: str) -> Event:
        event = cal.events().get(calendarId=calendar_id, eventId=event_id).execute()
        return cls.from_gcal_event(event)
