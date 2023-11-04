import { Link } from 'react-router-dom';

const chat1 = `
you: connect me

secretary: Hi! I'm your personal secretary. To get started, link your Google account: https://secretary.scooterbot.ai/login?...
`;

const chat2 = `
you: schedule dinner at Burger King next Thurs 7 pm

secretary: Added to your calendar:
| Title: Dinner
| Date/Time: November 9, 2023, 7-8pm
| Location: Burger King
`;

const chat3 = `
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
      <h1>Welcome to ScooterbotAI</h1>
      <p>Recruit our AI-powered <a href="https://discord.com/">Discord</a> bot to be your personal secretary. ScooterbotAI can help you schedule events in your Google calendar, and guide you through your day's appointment using natural language.</p>

      <h2>Getting Started</h2>

      <ol className="getting_started">
        <li><Link to="/signup">Request an invite link</Link> to add our Secretary bot to your Discord server</li>
        <li>
          Log into your Discord server and ask the Secretary bot to connect your Google account:
          <pre>{chat1}</pre>
        </li>
        <li>Click the link and connect your Google account using your web browser.</li>
        <li>
          Start chatting with the Secretary bot!
          <pre>{chat2}</pre>
        </li>
        <li>
          You can always disconnect your Google account by asking the Secretary bot:
          <pre>{chat3}</pre>
        </li>
      </ol>
    </>
  );
}

export default HomePage;
