from __future__ import annotations

import base64
from collections import defaultdict
from email.utils import parsedate_to_datetime

from bs4 import BeautifulSoup
from email_reply_parser import EmailReplyParser
from pydantic import BaseModel

from secretary.google_apis import get_gmail_service


class GmailMessage(BaseModel):
    date: str
    sender: str
    recipient: str
    body: str

    @classmethod
    def from_msg_dict(cls, msg_dict: dict) -> GmailMessage:
        headers = {h['name']: h['value'] for h in msg_dict.get('payload', {}).get('headers', [])}
        date = headers.get('Date', '')
        sender = headers.get('From', '')
        recipient = headers.get('To', '')

        date = parsedate_to_datetime(date).isoformat() if date else ''

        payload = msg_dict.get('payload', {})
        _, body_data = cls.find_body(payload, prefer='text/plain')

        body = base64.urlsafe_b64decode(body_data.encode('utf-8')).decode('utf-8', errors='replace') if body_data else ''

        return cls(date=date, sender=sender, recipient=recipient, body=body)

    @classmethod
    def find_body(cls, part: dict, prefer: str = 'text/plain') -> tuple[str | None, str | None]:
        # If this part is a leaf with body data
        if 'mimeType' in part and part['mimeType'] in ('text/plain', 'text/html'):
            data = part.get('body', {}).get('data')
            if data:
                return part['mimeType'], data
        # If it's a multipart, recurse into parts
        for subpart in part.get('parts', []):
            mime, data = cls.find_body(subpart, prefer)
            if mime == prefer and data:
                return mime, data  # Found our preferred type!
        # If still not found and prefer is 'text/plain', search for 'text/html'
        if prefer == 'text/plain':
            for subpart in part.get('parts', []):
                mime, data = cls.find_body(subpart, 'text/html')
                if mime == 'text/html' and data:
                    return mime, data
        return None, None


class GmailThread(BaseModel):
    id: str
    subject: str
    messages: list[GmailMessage]

    @classmethod
    def from_thread_dict(cls, thread_dict: dict) -> GmailThread:
        thread_id = thread_dict.get('id', '')
        # parse and sort messages chronologically by date
        messages = sorted(
            (GmailMessage.from_msg_dict(m) for m in thread_dict.get('messages', [])),
            key=lambda gm: gm.date
        )
        subject = ''
        if messages:
            # attempt to extract subject from headers of first message
            first_headers = {
                h['name']: h['value'] for h
                in thread_dict['messages'][0].get('payload', {}).get('headers', [])
            }
            subject = first_headers.get('Subject', '')

        MessageBodyCleaner().clean_messages(messages)

        return cls(id=thread_id, subject=subject, messages=messages)

    @classmethod
    def search(
        cls,
        user_id: str,
        query: str,
        label_ids: list[str],
        page_token: str | None = None,
        max_results_per_page: int = 10,
    ) -> GmailThreadsResult:
        gmailsvc = get_gmail_service(user_id)

        threads: list[GmailThread] = []

        resp = gmailsvc.users().threads().list(
            userId='me',
            q=query,
            labelIds=label_ids,
            maxResults=max_results_per_page,
            pageToken=page_token,
        ).execute()

        for tinfo in resp.get('threads', []):
            thread_dict = gmailsvc.users().threads().get(
                userId='me',
                id=tinfo['id'],
                format='full'
            ).execute()

            threads += [cls.from_thread_dict(thread_dict)]

        return GmailThreadsResult(
            threads=threads,
            next_page_token=resp.get('nextPageToken')
        )


class GmailThreadsResult(BaseModel):
    threads: list[GmailThread]
    next_page_token: str | None = None


class MessageBodyCleaner:
    def clean_messages(self, messages: list[GmailMessage]) -> None:
        # Strip quoted replies first
        for message in messages:
            message.body = EmailReplyParser.parse_reply(message.body)

        repeating_signatures = self.find_repeating_signatures(messages)
        for message in messages:
            for signature in repeating_signatures:
                if signature and signature in message.body:
                    message.body = message.body.replace(signature, '')

        for message in messages:
            message.body = self.html_to_text(message.body)

    def html_to_text(self, html: str) -> str:
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text(separator='\n').strip()

    def find_repeating_signatures(
        self,
        messages: list[GmailMessage],
        min_signature_lines: int = 3,
        min_messages_with_signature: int = 2
    ) -> list[str]:
        """
        Find repeating signature blocks by locating the longest recurring suffixes (by lines)
        that appear in at least a minimum number of messages.
        """

        # Do nothing if not enough messages to compare
        if len(messages) < min_messages_with_signature:
            return []

        # Map suffix text to set of message indices where it occurs
        suffix_map: dict[str, set[int]] = defaultdict(set)
        for idx, message in enumerate(messages):
            lines = message.body.splitlines(keepends=True)
            # build all suffixes of at least min_lines lines
            for n in range(min_signature_lines, len(lines) + 1):
                suffix = ''.join(lines[-n:])
                suffix_map[suffix].add(idx)

        # Select suffixes appearing in at least min_messages messages
        candidates = [s for s, idxs in suffix_map.items() if len(idxs) >= min_messages_with_signature]
        if not candidates:
            return []

        # Keep only the longest (maximal) suffixes: remove those that are suffixes of others
        candidates.sort(key=len, reverse=True)
        signatures: list[str] = []
        for s in candidates:
            if not any(other.endswith(s) for other in signatures):
                signatures.append(s)
        return signatures
