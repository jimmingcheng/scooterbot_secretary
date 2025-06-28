from scooterbot_account_linking import AccountLinkManager

from secretary import config


def get_account_link_manager() -> AccountLinkManager:
    shared_secret = config.account_linking_shared_secret()
    return AccountLinkManager(shared_secret, 'secretary')
