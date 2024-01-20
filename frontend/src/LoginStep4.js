import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import axios from 'axios';

function useQuery() {
  return new URLSearchParams(useLocation().search);
}

function LoginStep4() {
  const query = useQuery();
  const discord_user_id = query.get('discord_user_id');
  const user_id = query.get('user_id');
  const discord_channel = query.get('discord_channel');

  const [calendars, setCalendars] = useState([]);

  useEffect(() => {
    axios.get(`/login/step4/calendar_list?user_id=${user_id}`)
      .then(response => {
        const calendarItems = response.data.calendars;
        setCalendars(calendarItems);
      })
      .catch(error => console.error(error));
  }, [user_id]);

  return (
    <>
      <h1>Select calendar for To Do list</h1>

      <p>I'll use a special calendar to keep track of your To Do list. It's best to use a dedicated calendar for this.</p>

      <form action="/login/step5" method="POST">
        <select name="todo_calendar_id">
          <option value="new">Create a new calendar called: ➤ To Do</option>
          {calendars.map((cal) => (
            <option value={cal.id} key={cal.id}>{cal.summary}</option>
          ))}
        </select>
        <br />
        <input type="hidden" name="discord_user_id" value={discord_user_id || ''} />
        <input type="hidden" name="user_id" value={user_id || ''} />
        <input type="hidden" name="discord_channel" value={discord_channel || ''} />
        <input type="submit" value="Submit" />
      </form>
    </>
  );
}

export default LoginStep4;
