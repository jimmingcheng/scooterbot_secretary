from sb_service_util.account_links import AccountLinkManager

from secretary.service_config import config


def get_account_link_manager() -> AccountLinkManager:
    return AccountLinkManager(config.account_links.shared_secret, 'secretary')
