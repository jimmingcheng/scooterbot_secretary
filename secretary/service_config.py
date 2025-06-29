import os

import yaml
from pydantic import BaseModel


class GoogleApisConfig(BaseModel):
    client_id: str
    client_secret: str
    api_key: str


class DiscordConfig(BaseModel):
    bot_token: str


class ServiceAccountConfig(BaseModel):
    linking_url: str
    api_host: str


class AccountLinksConfig(BaseModel):
    shared_secret: str
    tesla: ServiceAccountConfig
    house: ServiceAccountConfig


class SecretaryConfig(BaseModel):
    google_apis: GoogleApisConfig
    openai_api_key: str
    account_links: AccountLinksConfig
    discord: DiscordConfig
    webhook_token: str


def load_service_config() -> SecretaryConfig:
    path = os.environ.get('SERVICE_CONFIG', '/sb/config/secretary.yaml')

    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return SecretaryConfig(**data)


config = load_service_config()
