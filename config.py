import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# LLM Provider Configuration
# ============================================
# Поддерживаемые провайдеры:
# - "openai" - OpenAI API (по умолчанию)
# - "openrouter" - OpenRouter API
# - "ollama" - Ollama (локальная LLM)
# - "lmstudio" - LM Studio (локальная LLM)
# - "localai" - LocalAI (локальная LLM)
# - "vllm" - vLLM (локальная LLM)
# - "textgen" - Text Generation WebUI (oobabooga)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

# API конфигурация
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")

# Дополнительные параметры для локальных LLM
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "300"))  # секунды

# Embeddings конфигурация (для памяти агента)
EMBEDDINGS_PROVIDER = os.getenv("EMBEDDINGS_PROVIDER", LLM_PROVIDER)  # По умолчанию используем тот же провайдер что и для LLM
EMBEDDINGS_MODEL = os.getenv("EMBEDDINGS_MODEL", "text-embedding-3-small")
EMBEDDINGS_BASE_URL = os.getenv("EMBEDDINGS_BASE_URL", LLM_BASE_URL)  # По умолчанию используем тот же URL
EMBEDDINGS_API_KEY = os.getenv("EMBEDDINGS_API_KEY", LLM_API_KEY)  # По умолчанию используем тот же ключ

# Локальные embeddings (если EMBEDDINGS_PROVIDER = "local")
LOCAL_EMBEDDINGS_MODEL = os.getenv("LOCAL_EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Модель для классификации важности (используется в памяти)
IMPORTANCE_CLASSIFIER_MODEL = os.getenv("IMPORTANCE_CLASSIFIER_MODEL", LLM_MODEL)  # По умолчанию используем основную модель

# ============================================
# Предустановленные конфигурации провайдеров
# ============================================
PROVIDER_CONFIGS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "requires_key": True,
        "default_model": "gpt-4",
        "supports_functions": True,
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "requires_key": True,
        "default_model": "anthropic/claude-3.5-sonnet",
        "supports_functions": True,
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "requires_key": False,
        "default_model": "llama3.2",
        "supports_functions": True,
        "default_key": "ollama",  # Ollama не требует ключ, но библиотека требует непустое значение
    },
    "lmstudio": {
        "base_url": "http://localhost:1234/v1",
        "requires_key": False,
        "default_model": "local-model",
        "supports_functions": True,
        "default_key": "lm-studio",
    },
    "localai": {
        "base_url": "http://localhost:8080/v1",
        "requires_key": False,
        "default_model": "gpt-3.5-turbo",
        "supports_functions": True,
        "default_key": "local-ai",
    },
    "vllm": {
        "base_url": "http://localhost:8000/v1",
        "requires_key": False,
        "default_model": "meta-llama/Llama-3.2-3B-Instruct",
        "supports_functions": True,
        "default_key": "vllm",
    },
    "textgen": {
        "base_url": "http://localhost:5000/v1",
        "requires_key": False,
        "default_model": "text-generation-webui",
        "supports_functions": False,  # Text Generation WebUI может не поддерживать function calling
        "default_key": "textgen",
    },
}

# Автоматическая настройка на основе выбранного провайдера
def get_provider_config():
    """Возвращает конфигурацию для текущего провайдера."""
    provider = LLM_PROVIDER.lower()
    
    if provider in PROVIDER_CONFIGS:
        config = PROVIDER_CONFIGS[provider].copy()
        
        # Используем значения из .env, если они заданы, иначе дефолтные
        config["base_url"] = LLM_BASE_URL if LLM_BASE_URL != "https://api.openai.com/v1" else config["base_url"]
        config["model"] = LLM_MODEL if LLM_MODEL != "gpt-4" else config["default_model"]
        
        # Для локальных провайдеров используем дефолтный ключ, если не задан
        if not config["requires_key"] and not LLM_API_KEY:
            config["api_key"] = config.get("default_key", "not-needed")
        else:
            config["api_key"] = LLM_API_KEY
            
        return config
    else:
        # Кастомная конфигурация
        return {
            "base_url": LLM_BASE_URL,
            "api_key": LLM_API_KEY or "not-needed",
            "model": LLM_MODEL,
            "supports_functions": True,
        }

# ============================================
# Security & System Configuration
# ============================================
ALLOWED_COMMANDS = os.getenv("ALLOWED_COMMANDS", "*")  # "*" = все, или список через запятую
WORKSPACE_DIR = os.path.expanduser("~/agent-workspace")
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "20"))
