import hashlib
import hmac

import arrow

from secretary import config


def make_token(user_id: str, expire_s: int = 300) -> str:
    ts = arrow.now().int_timestamp
    ts_block = ts - (ts % expire_s)

    msg = f'{user_id}:{ts_block}'.encode()
    secret = config.account_linking_shared_secret().encode()

    return hmac.new(secret, msg, hashlib.sha256).hexdigest()[:32]
