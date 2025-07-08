from secretary.data_models import Channel
from secretary.data_models import SecretaryOAuth
from secretary.data_models import User


def remove_account(user_id: str) -> None:
    Channel.delete(user_id)
    User.delete(user_id)
    SecretaryOAuth.delete(user_id)
