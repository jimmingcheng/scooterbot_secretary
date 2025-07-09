import textwrap

from secretary.views.base import HTMLPage


class HomePage(HTMLPage):
    def content(self) -> str:
        return textwrap.dedent(
            """\
            <nav>
                <ul>
                    <li><a href="/signup">Sign Up</a></li>
                </ul>
            </nav>
            <h1>Welcome to Scooterbot AI</h1>
            <p>Recruit our AI-powered chatbot to be your personal secretary. Scooterbot AI can help you schedule events in your Google Calendar, manage your Gmail by reading, composing, and sending emails, and guide you through your day's tasks using natural language.</p>

            <p>Scooterbot AI will only use your Google account to fulfill your explicit requests, such as accessing your calendar and email. We will not retain your data or use it for any other purpose beyond serving your requests.</p>

            <p>This service is currently invite-only. Click the Sign Up button to request an invitation</p>
            """
        )
