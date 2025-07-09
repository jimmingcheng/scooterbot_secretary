import textwrap

from secretary.views.base import HTMLPage


class SignupPage(HTMLPage):
    def content(self) -> str:
        return textwrap.dedent(
            """\
            <h1>Request an invite link</h1>
            <p>We're currently on an invite-only basis. Please email us to request an invite link:</p>
            <blockquote><a href="mailto:pickme@scooterbot.ai">pickme@scooterbot.ai</a></blockquote>
            """
        )
