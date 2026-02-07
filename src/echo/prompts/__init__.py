import inspect
import os

import echo.config as cfg
from echo.logger import configure_logger

log = configure_logger(__name__)


def load_langfuse_prompt(prompt_name: str) -> str:
    from langfuse import get_client
    from langfuse.model import TextPromptClient

    langfuse = get_client()
    prompt = langfuse.get_prompt(prompt_name)

    if not isinstance(prompt, TextPromptClient):
        raise NotImplementedError("Prompt must be type text")

    return str(prompt.compile())


def load_prompt_by_name(prompt_name: str) -> str:
    filepath = os.path.join(cfg.PROMPTS_FOLDER, f"{prompt_name}.txt")

    with open(filepath) as f:
        return f.read()


def load_component_prompt(prompt_name: str = "prompt") -> str:
    caller_frame = inspect.stack()[1]
    caller_file = caller_frame.filename
    caller_dir = os.path.dirname(os.path.abspath(caller_file))

    filepath = os.path.join(caller_dir, f"{prompt_name}.txt")

    with open(filepath) as f:
        return f.read()
