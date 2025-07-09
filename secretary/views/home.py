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
            <p>Recruit our AI-powered chatbot to be your personal secretary. Scooterbot AI can help you schedule events in your Google calendar, and guide you through your day's appointments using natural language.</p>

            <p>Scooterbot AI will only use your Google account to fulfill your explicit requests. We will not retain your data or use it for other purposes.</p>

            <p>This service is currently invite-only. Click the Sign Up button to request an invitation</p>
            """
        )
