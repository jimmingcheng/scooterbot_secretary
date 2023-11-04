import React from 'react';

function PrivacyPolicy() {
  return (
    <>
      <h1>Privacy Policy</h1>

      <h2>Introduction</h2>
      <p>We at Scooterbot AI respect and value your privacy. Our AI-powered personal secretary app focuses on safeguarding your personal information and aims to be transparent about how we collect, use, and disclose your information. This Privacy Policy explains the details and applies to our app's usage.</p>

      <h2>Type and Collection of Data</h2>
      <p>Our app, with your explicit approval, reads and writes data to your Google Calendar. The type of data accessed includes:</p>
      <ol>
       <li>Calendar Information: Appointments, event details, locations, attendees, schedules, timings, and other associated data.</li>
      </ol>
      <p>Please note that our app will only access your data upon your agreement for each event via OAuth authentication with Google.</p> 

      <h2>Use of Data</h2>
      <p>The data we collect is solely used for fulfilling tasks on your calendar such as reading your schedule and creating events. We strive to enhance your experience by automating your schedule management with machine learning, securely and efficiently.</p>

      <h2>Disclosure of Data</h2>
      <p>We do not retain your data in any form and no data is stored outside of your Google Calendar. Your information will not be sold, distributed, leased, or disclosed to third parties unless we have your permission or are required by law to do so.</p>

      <h2>Google API Services</h2>
      <p>Our app uses Google API services for reading and writing to your Google Calendars. For this, your explicit permission through OAuth will be asked at the time of the app setup. Usage of information received from Google APIs adheres to <a href="https://developers.google.com/terms/api-services-user-data-policy">Google's API Services User Data Policy</a>, including the Limited Use requirements.</p>

      <h2>Data Security</h2>
      <p>We value your trust in providing your personal information, thus we are striving to use commercially acceptable means of protecting it. However, no method of transmission over the internet or method of electronic storage is 100% secure and reliable, and we cannot guarantee its absolute security.</p>

      <h2>Changes to This Privacy Policy</h2>
      <p>We may update our Privacy Policy from time to time. Thus, you are advised to review this page periodically for any changes. We will notify you of any changes by posting the new Privacy Policy on this page.</p>

      <p>Should you have any questions about this Privacy Policy, please contact us at [Contact Information].</p>

      <p>This Privacy Policy is effective as of November 1, 2023.</p>
    </>
  );
}

export default PrivacyPolicy;
