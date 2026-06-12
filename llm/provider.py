"""
Базовый класс для LLM провайдеров
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion


class LLMProvider(ABC):
    """Базовый класс для всех LLM провайдеров."""
    
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        timeout: int = 300,
        supports_functions: bool = True,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.supports_functions = supports_functions
        
        # Создаем клиент OpenAI (работает с OpenAI-совместимыми API)
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )
    
    async def create_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        **kwargs
    ) -> ChatCompletion:
        """
        Создает completion запрос к LLM.
        
        Args:
            messages: Список сообщений в формате OpenAI
            tools: Список доступных инструментов (functions)
            tool_choice: Стратегия выбора инструментов ("auto", "none", или конкретный инструмент)
            **kwargs: Дополнительные параметры
            
        Returns:
            ChatCompletion объект
        """
        # Базовые параметры
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }
        
        # Добавляем tools только если провайдер их поддерживает
        if self.supports_functions and tools:
            params["tools"] = tools
            params["tool_choice"] = tool_choice
        
        # Выполняем запрос | tg: https://t.me/itpolice
        response = await self.client.chat.completions.create(**params)
        
        return response
    
    def get_info(self) -> Dict[str, Any]:
        """Возвращает информацию о провайдере."""
        return {
            "provider": self.__class__.__name__,
            "base_url": self.base_url,
            "model": self.model,
            "supports_functions": self.supports_functions,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }


class OpenAIProvider(LLMProvider):
    """Провайдер для OpenAI API."""
    
    def __init__(self, api_key: str, base_url: str, model: str, **kwargs):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model=model,
            supports_functions=True,
            **kwargs
        )


class OpenRouterProvider(LLMProvider):
    """Провайдер для OpenRouter API (с поддержкой prompt caching)."""
    
    def __init__(self, api_key: str, base_url: str, model: str, **kwargs):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model=model,
            supports_functions=True,
            **kwargs
        )
        # Enable prompt caching for OpenRouter
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=self.timeout,
            default_headers={
                "HTTP-Referer": "https://github.com/AgentAnufry",
                "X-Title": "AgentAnufry",
            }
        )


class OllamaProvider(LLMProvider):
    """Провайдер для Ollama (локальная LLM)."""
    
    def __init__(self, api_key: str, base_url: str, model: str, **kwargs):
        super().__init__(
            api_key=api_key or "ollama",  # Ollama не требует ключ
            base_url=base_url,
            model=model,
            supports_functions=True,  # Ollama поддерживает function calling
            **kwargs
        )


class LMStudioProvider(LLMProvider):
    """Провайдер для LM Studio (локальная LLM)."""
    
    def __init__(self, api_key: str, base_url: str, model: str, **kwargs):
        super().__init__(
            api_key=api_key or "lm-studio",
            base_url=base_url,
            model=model,
            supports_functions=True,
            **kwargs
        )


class LocalAIProvider(LLMProvider):
    """Провайдер для LocalAI (локальная LLM)."""
    
    def __init__(self, api_key: str, base_url: str, model: str, **kwargs):
        # dev Bednyakov
        super().__init__(
            api_key=api_key or "local-ai",
            base_url=base_url,
            model=model,
            supports_functions=True,
            **kwargs
        )


class VLLMProvider(LLMProvider):
    """Провайдер для vLLM (локальная LLM)."""
    
    def __init__(self, api_key: str, base_url: str, model: str, **kwargs):
        super().__init__(
            api_key=api_key or "vllm",
            base_url=base_url,
            model=model,
            supports_functions=True,
            **kwargs
        )


class TextGenProvider(LLMProvider):
    """Провайдер для Text Generation WebUI (oobabooga)."""
    
    def __init__(self, api_key: str, base_url: str, model: str, **kwargs):
        super().__init__(
            api_key=api_key or "textgen",
            base_url=base_url,
            model=model,
            supports_functions=False,  # Text Generation WebUI может не поддерживать function calling
            **kwargs
        )
