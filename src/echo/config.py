import os

LIB_FOLDER = os.path.dirname(__file__)
PROMPTS_FOLDER = os.path.join(LIB_FOLDER, "prompts")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()

OPENAI_API_VERSION = os.environ["OPENAI_API_VERSION"]
OPENAI_MODEL = os.environ["OPENAI_MODEL"]
OPENAI_MODEL_MINI = os.environ["OPENAI_MODEL_MINI"]
OPENAI_MODEL_NANO = os.environ["OPENAI_MODEL_NANO"]
OPENAI_EMBEDDING_MODEL = os.environ["OPENAI_EMBEDDING_MODEL"]
