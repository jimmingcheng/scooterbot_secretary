from secretary.database import ChannelTable
from secretary.database import OAuthTable
from secretary.database import UserTable


def remove_account(user_id: str) -> None:
    ChannelTable.delete(user_id)
    UserTable.delete(user_id)
    OAuthTable.delete(user_id)
