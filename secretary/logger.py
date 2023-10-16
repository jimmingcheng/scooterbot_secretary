import logging


def init(app_name: str) -> None:
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)
