import os

# LLM конфигурация
LLM_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")

# Безопасность
ALLOWED_COMMANDS = os.getenv("ALLOWED_COMMANDS", "*")  # "*" = все, или список через запятую
WORKSPACE_DIR = os.path.expanduser("~/agent-workspace")
MAX_ITERATIONS = 20
