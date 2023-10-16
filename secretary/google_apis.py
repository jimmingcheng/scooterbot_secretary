import staticconf
from functools import lru_cache
from oauth2client.client import OAuth2Credentials

from oauth_userdb.client import OAuthUserDBClient
from oauth_userdb.dynamodb_client import DynamoDBOAuthUserDBClient

from secretary.database import get_oauth_table


AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_URL = 'https://oauth2.googleapis.com/token'
REDIRECT_URL = 'https://secretary.scooterbot.org/oauth/callback'


def get_client_id() -> str:
    return staticconf.read('google_apis.client_id', namespace='secretary')  # type: ignore


def get_client_secret() -> str:
    return staticconf.read('google_apis.client_secret', namespace='secretary')  # type: ignore


@lru_cache(maxsize=1)
def get_userdb_client() -> OAuthUserDBClient:
    return DynamoDBOAuthUserDBClient(
        client_id=get_client_id(),
        client_secret=get_client_secret(),
        authorization_url=AUTH_URL,
        token_url=TOKEN_URL,
        redirect_url=REDIRECT_URL,
        scope=[
            'openid',
            'profile',
            'email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/calendar',
        ],
        dynamodb_table=get_oauth_table(),
    )


def get_google_apis_creds(user_id: str) -> OAuth2Credentials:
    creds = get_userdb_client().get_credentials(user_id)
    return OAuth2Credentials(
        access_token=creds.access_token,
        client_id=get_client_id(),
        client_secret=get_client_secret(),
        refresh_token=creds.refresh_token,
        token_expiry=creds.expires_at,
        token_uri=TOKEN_URL,
        user_agent='scooterbot_todo',
        scopes=get_userdb_client().scope,
    )
