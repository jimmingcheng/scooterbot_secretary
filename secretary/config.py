import openai
import staticconf


def load_all_configs() -> None:
    load_todo_config()


def load_todo_config() -> None:
    staticconf.YamlConfiguration('/run/config/secretary.yaml', namespace='secretary')
    staticconf.YamlConfiguration('/run/config/openai.yaml', namespace='openai')
    openai.api_key = staticconf.read('api_key', namespace='openai')  # type: ignore
