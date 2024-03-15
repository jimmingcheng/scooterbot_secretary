import { Link } from 'react-router-dom';

const chat1 = `
you: connect me

secretary: Hi! I'm your personal secretary. To get started, link your Google account: https://secretary.scooterbot.ai/login?...
`;

const chat2 = `
secretary: Your Google account is connected. I'm ready to assist you.
`;

const chat3 = `
you: schedule dinner at Burger King next Thurs 7 pm

secretary: Added to your calendar:
| Title: Dinner
| Date/Time: November 9, 2023, 7-8pm
| Location: Burger King
`;

const chat4 = `
you: remove my account

secretary: Can you confirm you want to disconnect your account now?

you: yes

secretary: Thank you. Your account has been disconnected. I can no longer access your Google calendar or data.
`;

function HomePage() {
  return (
    <>
      <nav>
        <ul>
          <li><Link to="/signup">Sign Up</Link></li>
        </ul>
      </nav>
      <h1>Welcome to Scooterbot AI</h1>
      <p>Recruit our AI-powered chatbot to be your personal secretary. Scooterbot AI can help you schedule events in your Google calendar, and guide you through your day's appointments using natural language.</p>

      <p>Scooterbot AI will only use your Google account to fulfill your explicit requests. We will not retain your data or use it for other purposes.</p>

      <p>This service is currently invite-only. Click the Sign Up button to request an invitation</p>
    </>
  );
}

export default HomePage;
