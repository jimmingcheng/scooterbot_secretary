from functools import lru_cache
from oauth2client.client import OAuth2Credentials

from oauth_userdb.client import OAuthUserDBClient
from oauth_userdb.dynamodb_client import DynamoDBOAuthUserDBClient

from secretary.data_models import SecretaryOAuth
from secretary.service_config import config


AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_URL = 'https://oauth2.googleapis.com/token'
REDIRECT_URL = 'https://secretary.scooterbot.ai/login/step3'


@lru_cache(maxsize=1)
def get_oauth_client(redirect_url: str = REDIRECT_URL) -> OAuthUserDBClient:
    return DynamoDBOAuthUserDBClient(
        client_id=config.google_apis.client_id,
        client_secret=config.google_apis.client_secret,
        authorization_url=AUTH_URL,
        token_url=TOKEN_URL,
        redirect_url=redirect_url,
        scope=[
            'openid',
            'profile',
            'email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/calendar',
        ],
        dynamodb_table=SecretaryOAuth.table(),
    )


def get_google_apis_creds(user_id: str) -> OAuth2Credentials:
    creds = get_oauth_client().get_credentials(user_id)
    return OAuth2Credentials(
        access_token=creds.access_token,
        client_id=config.google_apis.client_id,
        client_secret=config.google_apis.client_secret,
        refresh_token=creds.refresh_token,
        token_expiry=creds.expires_at,
        token_uri=TOKEN_URL,
        user_agent='scooterbot_todo',
        scopes=get_oauth_client().scope,
    )
