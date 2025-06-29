from scooterbot_account_linking import AccountLinkManager

from secretary.service_config import config


def get_account_link_manager() -> AccountLinkManager:
    return AccountLinkManager(config.account_links.shared_secret, 'secretary')
