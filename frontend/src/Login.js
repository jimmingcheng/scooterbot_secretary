import { useLocation } from 'react-router-dom';
import gcal_logo from './gcal_logo.png';

function useQuery() {
  return new URLSearchParams(useLocation().search);
}

function Login() {
  const query = useQuery();
  const user_id = query.get('u');
  const discord_channel = query.get('ch');

  return (
    <>
      <h1>Connect your Google account</h1>

      <div class="login_disclaimer">
        <h2>Your Privacy</h2>

        <p>In order to provide useful services as your Secretary, we'll access some of your private data such as:</p>

        <ul>
          <li>The natural language requests you submit directly to Scooterbot AI by mentioning <code>@secretary</code> in your Discord messages</li>
          <li>Your Google Calendar events and schedules</li>
        </ul>

        <p>Your privacy is important to us, and here's how we'll use it:</p>

        <h3>Use of Data</h3>
        <p>The data we collect is solely used for fulfilling tasks on your calendar such as reading your schedule and creating events. This includes:</p>
        <ul>
          <li>When you mention <code>@secretary</code> in a Discord message, we'll send the message text to ChatGPT, a 3rd party AI owned by OpenAI.</li>
          <li>After OpenAI interprets your message, we'll use the interpreted instructions to read or write to your Google Calendar on your behalf.</li>
          <li>In some cases, the specific Google Calendar data you request will be sent back to ChatGPT for further interpretation.</li>
        </ul>

        <h3>Disclosure of Data</h3>
        <p>We may send your data to a third-party AI (OpenAI) for interpreting natural language requests. OpenAI may retain your data for up to 30 days to identify abuse, but will not otherwise retain your data or use it for any other purpose than to provide responses to your requests. Besides this, your data remains confidential and won't be sold, distributed, leased, or disclosed to other third parties unless we have your permission or are required by law to do so.</p>

        <p>By clicking "Sign in with Google", you agree to the above terms, as well as our <a href="/privacy">Privacy Policy</a> and <a href="/tos">Terms of Service</a></p>
      </div>

      <form action="/login/step2" method="GET">
        <input type="hidden" name="u" value={user_id || ''} />
        <input type="hidden" name="ch" value={discord_channel || ''} />
        <button type="submit" class="login">
          <img src={gcal_logo} alt="Google Calendar Logo" />
          Connect Google Calendar
        </button>
      </form>
    </>
  );
}

export default Login;
