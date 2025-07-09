import textwrap

from secretary.views.base import HTMLPage


class TermsOfServicePage(HTMLPage):
    def content(self) -> str:
        return textwrap.dedent(
            """\
            <h1>Terms of Service</h1>

            <h2>Acceptance of Terms</h2>
            <p>By using the AI-powered personal secretary app developed by Scooterbot AI, you agree to be bound by these Terms of Service. These Terms of Service apply to all users of the app. If you do not agree to all the terms and conditions of this agreement, then you may not access the app or use any services.</p>

            <h2>Services</h2>
            <p>Our app provides AI chat-based scheduling and email management services, including reading your Google Calendar schedule, creating events, managing your Gmail by reading, composing, and sending emails, and organizing messages with labels. All data is exchanged through Google Calendar and Gmail using OAuth authentication, with explicit permission from the user. The services are provided on an 'as is' basis without warranties of any kind, either expressed or implied.</p>

            <h2>Data Privacy</h2>
            <p>Please refer to our <a href="/privacy">Privacy Policy</a> for more details on how we manage your data. By accepting these terms, you also agree to our Privacy Policy.</p>

            <h2>Google API Services</h2>
            <p>Our app uses Google API services for accessing your Google Calendar and Gmail. All usage of Google services is per <a href="https://developers.google.com/terms/api-services-user-data-policy">Google's API Services User Data Policy</a>.</p>

            <h2>Limitation of Liability</h2>
            <p>In no event will Scooterbot AI be liable for any injury, loss, claim, damage, or any special, exemplary, punitive, indirect, incidental, or consequential damages of any kind based on the use of our app.</p>

            <h2>Changes to the Terms</h2>
            <p>We reserve the right to modify or replace these Terms of Service at any time. It is your responsibility to check our Terms of Service periodically for changes.</p>

            <h2>Contact Us</h2>
            <p>If you have any questions about these Terms of Service, please contact us at <a href="mailto:jimming@gmail.com">jimming@gmail.com</a> .</p>

            <p>These Terms of Service are effective as of July 8, 2025.</p>
            """
        )
