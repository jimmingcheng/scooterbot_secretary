from __future__ import annotations

from typing import Any
from typing import Literal

import arrow
from googleapiclient.discovery import Resource
from pydantic import BaseModel


class Todo(BaseModel):
    id: str | None = None
    due_date: str
    summary: str
    description: str | None = None
    location: str | None = None
    recurrence: list[str] | None = None
    is_recurrence_master_event: bool = False
    is_resolved: bool = False

    def resolve(self) -> None:
        self.is_resolved = True
        self.summary = self.summary.replace('📝 ', '✅ ')

    def unresolve(self) -> None:
        self.is_resolved = False
        self.summary = self.summary.replace('✅ ', '📝 ')

    def to_gcal_event(self) -> dict[str, Any]:
        event: dict[str, Any] = {
            'summary': self.summary,
            'start': {'date': self.due_date},
            'end': {'date': self.due_date},
            'extendedProperties': {
                'shared': {
                    'sb_type': 'todo',
                    'sb_is_resolved': str(self.is_resolved),
                }
            },
        }

        if self.description:
            event['description'] = self.description

        if self.location:
            event['location'] = self.location

        if self.recurrence:
            event['recurrence'] = self.recurrence

        return event

    @classmethod
    def from_gcal_event(cls, event: dict[str, Any]) -> Todo:
        is_resolved = cls.get_extended_property(event, 'sb_is_resolved') == str(True)

        return cls(
            id=event['id'],
            summary=event['summary'],
            due_date=event['start']['date'],
            description=event.get('description'),
            location=event.get('location'),
            recurrence=event.get('recurrence'),
            is_recurrence_master_event=bool(event.get('recurrenceId') and not event.get('recurringEventId')),
            is_resolved=is_resolved,
        )

    @classmethod
    def get(cls, calsvc: Resource, todo_id: str) -> Todo:
        event = calsvc.events().get(calendarId='primary', eventId=todo_id).execute()
        if cls.get_extended_property(event, 'sb_type') != 'todo':
            raise ValueError(f"Event with ID {todo_id} is not a todo.")
        return cls.from_gcal_event(event)

    @classmethod
    def get_extended_property(cls, event: dict[str, Any], key: str, property_type: Literal['shared', 'private'] = 'shared') -> str | None:
        return event.get('extendedProperties', {}).get(property_type, {}).get(key)

    def log_to_description(self, log_message: str) -> None:
        if self.description:
            self.description += '\n\n'
        else:
            self.description = ''

        self.description += f'[{arrow.now().format("MMM D, YYYY")}] sb: {log_message}'
