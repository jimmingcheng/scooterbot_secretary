from __future__ import annotations

from typing import Any

import arrow
from googleapiclient.discovery import Resource
from pydantic import BaseModel


class Event(BaseModel):
    id: str | None = None
    start: str
    end: str
    summary: str
    description: str | None = None
    location: str | None = None
    recurrence: list[str] | None = None

    def to_gcal_event(self, calendar_tz: str | None = None) -> dict[str, Any]:
        event: dict[str, Any] = {
            'summary': self.summary,
        }

        event['start'] = {'dateTime': self.start} if 'T' in self.start else {'date': self.start}
        event['end'] = {'dateTime': self.end} if 'T' in self.end else {'date': self.end}

        if calendar_tz:
            event['start']['timeZone'] = calendar_tz
            event['end']['timeZone'] = calendar_tz

        if self.description:
            event['description'] = self.description

        if self.location:
            event['location'] = self.location

        if self.recurrence:
            event['recurrence'] = self.recurrence

        return event

    @classmethod
    def from_gcal_event(cls, event: dict[str, Any]) -> Event:
        start = event['start'].get('dateTime') or event['start']['date']
        end = event['end'].get('dateTime') or event['end']['date']

        return cls(
            id=event['id'],
            summary=event.get('summary', ''),
            start=start,
            end=end,
            description=event.get('description'),
            location=event.get('location'),
            recurrence=event.get('recurrence'),
        )

    @classmethod
    def get(cls, cal: Resource, calendar_id: str, event_id: str) -> Event:
        event = cal.events().get(calendarId=calendar_id, eventId=event_id).execute()
        return cls.from_gcal_event(event)

    def log_to_description(self, log_message: str) -> None:
        if self.description:
            self.description += '\n\n'
        else:
            self.description = ''

        self.description += f'[{arrow.now().format("MMM D, YYYY")}] sb: {log_message}'
