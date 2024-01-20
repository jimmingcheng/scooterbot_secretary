from typing import List
from typing import Optional

import arrow
import boto3
import jwt
from apiclient import discovery
from functools import lru_cache

from secretary.database import get_oauth_table
from secretary.google_apis import get_google_apis_creds
from secretary.calendar import event_start_time
from secretary.calendar import get_calendar_service
from secretary.calendar import TZ


EMAIL_TEMPLATE = '''
<!DOCTYPE html>
<html xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office" lang="en">

<head>
  <title></title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <!--[if mso]><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch><o:AllowPNG/></o:OfficeDocumentSettings></xml><![endif]-->
  <style>
    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      padding: 0;
    }

    a[x-apple-data-detectors] {
      color: inherit !important;
      text-decoration: inherit !important;
    }

    #MessageViewBody a {
      color: inherit;
      text-decoration: none;
    }

    p {
      line-height: inherit
    }

    @media (max-width:520px) {
      .row-content {
        width: 100% !important;
      }

      .column .border {
        display: none;
      }

      table {
        table-layout: fixed !important;
      }

      .stack .column {
        width: 100%;
        display: block;
      }
    }

    .preheader {
      display: none !important;
      visibility: hidden;
      opacity: 0;
      color: transparent;
      width: 0;
      height: 0;
    }
  </style>
</head>

<body style="background-color: #FFFFFF; margin: 0; padding: 0; -webkit-text-size-adjust: none; text-size-adjust: none;">
  <span class="preheader" style="display: none !important; visibility: hidden; opacity: 0; color: transparent; height: 0; width: 0;">
    PREHEADER
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
    &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
  </span>
  <table class="nl-container" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #FFFFFF;">
    <tbody>
      <tr>
        <td>
          <table class="row row-1" align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
            <tbody>
              <tr>
                <td>
                  <table class="row-content stack" align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; color: #000000; width: 500px;" width="500">
                    <tbody>
                      <tr>
                        <td class="column column-1" width="100%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; vertical-align: top; padding-top: 5px; padding-bottom: 5px; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
                          <table class="button_block" width="100%" border="0" cellpadding="10" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
                            <tr>
                              <td>
                                <div align="center">
                                  <!--[if mso]><v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" style="height:19px;width:67px;v-text-anchor:middle;" arcsize="22%" stroke="false" fillcolor="#dddddd"><w:anchorlock/><v:textbox inset="0px,0px,0px,0px"><center style="color:#333333; font-family:Arial, sans-serif; font-size:12px"><![endif]-->
                                  <div style="text-decoration:none;display:inline-block;color:#333333;background-color:#dddddd;border-radius:4px;width:auto;border-top:0px solid #8a3b8f;border-right:0px solid #8a3b8f;border-bottom:0px solid #8a3b8f;border-left:0px solid #8a3b8f;padding-top:0px;padding-bottom:0px;font-family:Arial, Helvetica Neue, Helvetica, sans-serif;text-align:center;mso-border-alt:none;word-break:keep-all;"><span style="padding-left:10px;padding-right:10px;font-size:12px;display:inline-block;letter-spacing:normal;"><span style="font-size: 16px; line-height: 1.2; word-break: break-word; mso-line-height-alt: 19px;"><strong><span style="font-size: 12px; line-height: 14px;" data-mce-style="font-size: 12px; line-height: 14px;">➤ To Do</span></strong></span></span></div>
                                  <!--[if mso]></center></v:textbox></v:roundrect><![endif]-->
                                </div>
                              </td>
                            </tr>
                          </table>
                          <table class="text_block" width="100%" border="0" cellpadding="10" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; word-break: break-word;">
                            <tr>
                              <td>
                                <div style="font-family: sans-serif">
                                  <div class="txtTinyMce-wrapper" style="font-size: 12px; font-family: Arial, Helvetica Neue, Helvetica, sans-serif; mso-line-height-alt: 14.399999999999999px; color: #000000; line-height: 1.2;">
                                    <p style="margin: 0; font-size: 16px; text-align: center;"><span style="font-size:18px;"><strong>SUBJECT</strong></span></p>
                                  </div>
                                </div>
                              </td>
                            </tr>
                          </table>
                          <table class="text_block" width="100%" border="0" cellpadding="10" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; word-break: break-word;">
                            <tr>
                              <td>
                                <div style="font-family: sans-serif">
                                  <div class="txtTinyMce-wrapper" style="font-size: 12px; font-family: Arial, Helvetica Neue, Helvetica, sans-serif; mso-line-height-alt: 14.399999999999999px; color: #555555; line-height: 1.2;">
                                    <p style="margin: 0; font-size: 14px; text-align: left;">DESCRIPTION</p>
                                  </div>
                                </div>
                              </td>
                            </tr>
                          </table>
                          <table class="button_block" width="100%" border="0" cellpadding="10" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
                            <tr>
                              <td>
                                <div align="center">
                                  <!--[if mso]><v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="CALENDAR_LINK" style="height:42px;width:288px;v-text-anchor:middle;" arcsize="10%" stroke="false" fillcolor="#f54133"><w:anchorlock/><v:textbox inset="0px,0px,0px,0px"><center style="color:#ffffff; font-family:Arial, sans-serif; font-size:16px"><![endif]--><a href="CALENDAR_LINK" target="_blank" style="text-decoration:none;display:block;color:#ffffff;background-color:#f54133;border-radius:4px;width:60%; width:calc(60% - 2px);border-top:1px solid #f54133;border-right:1px solid #f54133;border-bottom:1px solid #f54133;border-left:1px solid #f54133;padding-top:5px;padding-bottom:5px;font-family:Arial, Helvetica Neue, Helvetica, sans-serif;text-align:center;mso-border-alt:none;word-break:keep-all;"><span style="padding-left:20px;padding-right:20px;font-size:16px;display:inline-block;letter-spacing:normal;"><span style="font-size: 16px; margin: 0; line-height: 2; word-break: break-word; mso-line-height-alt: 32px;">Due DUE_DATE</span></span></a>
                                  <!--[if mso]></center></v:textbox></v:roundrect><![endif]-->
                                </div>
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </td>
              </tr>
            </tbody>
          </table>
        </td>
      </tr>
    </tbody>
  </table><!-- End -->
</body>

</html>
'''


@lru_cache(maxsize=1)
def get_gmail_service(user_id: str):
    return discovery.build('gmail', 'v1', credentials=get_google_apis_creds(user_id))


def get_todos_to_remind_today(todo_calendar_id: str, user_id: str) -> List[dict]:
    resp = get_calendar_service(user_id).events().list(
        calendarId=todo_calendar_id,
        timeMin=arrow.now().shift(days=-1).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        singleEvents=True,
        orderBy='startTime',
    ).execute()

    return [
        event for event in
        resp['items']
        if should_remind_today(event, resp['defaultReminders'])
    ]


def _get_email_reminder_minutes(reminder_cfgs: List[dict]) -> Optional[int]:
    for cfg in reminder_cfgs:
        if cfg['method'] == 'popup':
            return cfg['minutes']
    return None


def should_remind_today(event: dict, default_reminder_cfgs: List[dict]) -> bool:
    reminder_mins = _get_email_reminder_minutes(event['reminders'].get('overrides', []))
    if reminder_mins is None:
        reminder_mins = _get_email_reminder_minutes(default_reminder_cfgs)

    if reminder_mins is None:
        return False

    reminder_time = event_start_time(event).shift(minutes=-reminder_mins)

    return reminder_time.toordinal() == arrow.now(TZ).toordinal()


def get_formatted_email(user_id: str) -> str:
    id_token = get_oauth_table().get_item(Key={'user_id': user_id})['Item']['id_token']
    profile = jwt.decode(id_token, options={'verify_signature': False})
    return f"Jimming Cheng <{profile['email']}>"


def send_email(user_id: str, event: dict):
    formatted_email = get_formatted_email(user_id)

    html_body = EMAIL_TEMPLATE.replace(
        'PREHEADER', 'Due {}'.format(event_start_time(event).format('MMM D'))
    ).replace(
        'SUBJECT', event['summary']
    ).replace(
        'DESCRIPTION', event.get('description', '')
    ).replace(
        'DUE_DATE', event_start_time(event).format('MMMM D, YYYY')
    ).replace(
        'CALENDAR_LINK', event['htmlLink']
    )

    ses_client = boto3.client('ses', region_name='us-west-2')

    ses_client.send_email(
        Destination={
            'ToAddresses': [formatted_email],
        },
        Message={
            'Body': {
                'Html': {
                    'Charset': 'UTF-8',
                    'Data': html_body,
                },
            },
            'Subject': {
                'Charset': 'UTF-8',
                'Data': event['summary'],
            },
        },
        Source='secretary@scooterbot.ai',
    )
