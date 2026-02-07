import os

LIB_FOLDER = os.path.dirname(__file__)
PROMPTS_FOLDER = os.path.join(LIB_FOLDER, "prompts")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "azure").lower()
