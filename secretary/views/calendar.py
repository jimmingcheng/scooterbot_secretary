import html
from django.http import HttpRequest
from django.http import HttpResponse

from secretary.database import UserTable
from secretary.calendar import get_calendar_service


def show_calendar_options(request: HttpRequest) -> HttpResponse:
    user_id = request.GET['user_id']
    google_apis_user_id = request.GET['google_apis_user_id']

    form = '''
    <form action="/calendar" method="POST">
      <select name="todo_calendar_id">
    '''

    for cal in get_calendar_service(google_apis_user_id).calendarList().list().execute()['items']:
        cal_id = html.escape(cal['id'])
        summary = html.escape(cal['summary'])
        form += f'<option value="{cal_id}">{summary}</option>'

    form += f'''
      </select>
      <input type="hidden" name="user_id" value="{user_id}"/>
      <input type="hidden" name="google_apis_user_id" value="{google_apis_user_id}"/>
      <input type="submit" value="Submit"/>
    </form>
    '''

    return HttpResponse(form)


def save_calendar(request: HttpRequest) -> HttpResponse:
    user_id = request.POST['user_id']
    google_apis_user_id = request.POST['google_apis_user_id']
    todo_calendar_id = request.POST['todo_calendar_id']

    UserTable().upsert(user_id, google_apis_user_id, todo_calendar_id)

    cal = get_calendar_service(google_apis_user_id).calendars().get(calendarId=todo_calendar_id).execute()

    return HttpResponse(f"I'll save your todos in this calendar: {cal['summary']}")
