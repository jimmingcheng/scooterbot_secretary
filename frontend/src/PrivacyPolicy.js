import React from 'react';

function PrivacyPolicy() {
  return (
    <>
      <h1>Privacy Policy</h1>

      <h2>Introduction</h2>
      <p>We at Scooterbot AI respect and value your privacy. Our AI-powered personal secretary app focuses on safeguarding your personal information and aims to be transparent about how we collect, use, and disclose your information. This Privacy Policy explains the details and applies to our app's usage.</p>

      <h2>Type and Collection of Data</h2>
      <p>In order to provide useful services as your Secretary, we'll access some of your private data such as:</p>

      <ul>
        <li>The natural language requests you submit directly to Scooterbot AI by mentioning <code>@secretary</code> in your Discord messages</li>
        <li>Your Google Calendar events and schedules</li>
      </ul>

      <h2>Use of Data</h2>
      <p>The data we collect is solely used for fulfilling tasks on your calendar such as reading your schedule and creating events. We strive to enhance your experience by interpreting your natural language requests through a third-party AI, ChatGPT, owned by OpenAI.</p>

      <h2>Disclosure of Data</h2>
      <p>We may send your data to a third-party AI (OpenAI) for interpreting natural language requests. OpenAI may retain your data for up to 30 days to identify abuse, but will not otherwise retain your data or use it for any other purpose than to provide responses to your requests. Besides this, your data remains confidential and won't be sold, distributed, leased, or disclosed to other third parties unless we have your permission or are required by law to do so.</p>

      <h2>Google API Services</h2>
      <p>Our app uses Google API services for reading and writing to your Google Calendars. For this, your explicit permission through OAuth will be asked at the time of the app setup. Usage of information received from Google APIs adheres to <a href="https://developers.google.com/terms/api-services-user-data-policy">Google's API Services User Data Policy</a>, including the Limited Use requirements.</p>

      <h2>Data Security</h2>
      <p>We value your trust in providing your personal information, thus we are striving to use commercially acceptable means of protecting it. However, no method of transmission over the internet or method of electronic storage is 100% secure and reliable, and we cannot guarantee its absolute security.</p>

      <h2>Changes to This Privacy Policy</h2>
      <p>We may update our Privacy Policy from time to time. Thus, you are advised to review this page periodically for any changes. We will notify you of any changes by posting the new Privacy Policy on this page.</p>

      <p>Should you have any questions about this Privacy Policy, please contact us at <a href="mailto:jimming@gmail.com">jimming@gmail.com</a>.</p>

      <p>This Privacy Policy is effective as of November 1, 2023.</p>
    </>
  );
}

export default PrivacyPolicy;
