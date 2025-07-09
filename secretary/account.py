from secretary.data_models.channel import Channel
from secretary.data_models.oauth import SecretaryOAuth
from secretary.data_models.user import User


def remove_account(user_id: str) -> None:
    Channel.delete(user_id)
    User.delete(user_id)
    SecretaryOAuth.delete(user_id)
