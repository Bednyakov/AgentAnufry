"""
Агент Ануфрий с полным доступом к shell, файлам и браузеру.
"""

import json
import asyncio
import os
import uuid
from typing import List, Dict, Any

from config import (
    LLM_PROVIDER, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL,
    LLM_TEMPERATURE, LLM_MAX_TOKENS, LLM_TIMEOUT,
    MAX_ITERATIONS, get_provider_config
)
from llm import create_llm_provider
from tools.shell import run_shell
from tools.filesystem import read_file, write_file, list_dir, search_files
from tools.browser import (
    browser_navigate, browser_click, browser_type,
    browser_get_text, browser_screenshot, browser_search_google,
    browser_extract_content, browser_navigate_search_page, browser_close
)
from tools.memory_tools import get_memory_manager
from tools.task_tools import (
    task_create, task_add_attempt, task_add_insight,
    task_update_status, task_get_context, task_list_incomplete,
    task_search_similar
)
from tools.result_tools import (
    result_save, result_get, result_list, result_get_latest,
    get_results_manager
)
from skills.loader import SkillLoader
from tools.skills_runner import run_skill_script
from tools.registry import (
    get_core_tools, get_tool_catalog, get_category_tools, list_categories,
    get_registry_version, get_registry_info
)

# Инициализация загрузчика навыков
skill_loader = SkillLoader()
skill_loader.scan()

# Инициализация LLM провайдера
provider_config = get_provider_config()
llm_provider = create_llm_provider(
    provider_name=LLM_PROVIDER,
    api_key=provider_config["api_key"],
    base_url=provider_config["base_url"],
    model=provider_config["model"],
    temperature=LLM_TEMPERATURE,
    max_tokens=LLM_MAX_TOKENS,
    timeout=LLM_TIMEOUT,
)

print(f"🔧 LLM Provider: {LLM_PROVIDER}")
print(f"📡 Base URL: {provider_config['base_url']}")
print(f"🤖 Model: {provider_config['model']}")
print(f"⚙️  Function Calling: {'✓' if provider_config['supports_functions'] else '✗'}")

# Информация о registry
registry_info = get_registry_info()
print(f"🛠️  Tools Registry: v{registry_info['version']} "
      f"({registry_info['core_tools_count']} core + {registry_info['total_extended_actions']} extended)")

# Core tools — always sent (6 tools instead of 24)
TOOLS = get_core_tools()

# Skills catalog for system prompt
SKILLS_CATALOG = skill_loader.get_catalog_prompt()

SYSTEM_PROMPT = f"""Ты — агент с доступом к локальной системе и долговременной памятью.

Инструменты:
- run_shell — shell-команды (автоопределение ОС)
- read_file / write_file / list_dir — работа с файлами
- tool_get_available(category) — покажи доступные инструменты в категории
- tool_use(category, action, params) — вызови инструмент из категории

Категории (вызови tool_get_available для деталей):
- browser — навигация, поиск Google, извлечение контента
- memory — сохранение фактов, поиск по памяти
- task — отслеживание задач
- result — сохранение результатов поиска/данных
- skill — специализированные навыки и скрипты

Правила:
1. Всегда сохраняй результаты поиска/данных через result/save
2. После browser/search_google ОБЯЗАТЕЛЬНО browser/extract_content для релевантных URL
3. Для сложных задач создавай task/create в начале
4. Не выполняй rm -rf / без подтверждения
{SKILLS_CATALOG}

Рабочая директория: ~/agent-workspace
"""


async def dispatch_tool_use(category: str, action: str, params: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    """Dispatches a consolidated tool_use call to the appropriate handler."""
    params = params or {}  # Защита от None
    
    if category == "browser":
        if action == "navigate":
            return await browser_navigate(params["url"])
        elif action == "get_text":
            return await browser_get_text(params.get("selector", "body"))
        elif action == "search_google":
            return await browser_search_google(params["query"])
        elif action == "extract_content":
            return await browser_extract_content(params["url"], params.get("selectors"))
        elif action == "navigate_search_page":
            return await browser_navigate_search_page(
                params.get("direction", "next"),
                params.get("search_engine", "auto")
            )
        elif action == "close":
            await browser_close()
            return {"success": True}
        else:
            return {"error": f"Неизвестное действие browser/{action}"}

    elif category == "memory":
        manager = get_memory_manager()
        if action == "save":
            fact_id = await manager.add_fact(params["content"], params.get("category", "general"))
            return {"success": True, "fact_id": fact_id}
        elif action == "search":
            results = await manager.search_facts(params["query"], limit=params.get("limit", 5))
            formatted = [{"content": r["content"], "category": r["category"],
                          "importance": r["importance"], "similarity": round(r["similarity"], 3)}
                         for r in results]
            return {"success": True, "results": formatted, "count": len(formatted)}
        elif action == "summary":
            return {"success": True, **await manager.get_memory_summary()}
        elif action == "cleanup":
            result = await manager.cleanup_old_data(days_threshold=params.get("days", 30))
            return {"success": True, "deleted_facts": result["deleted_facts"],
                    "deleted_conversations": result["deleted_conversations"]}
        else:
            return {"error": f"Неизвестное действие memory/{action}"}

    elif category == "task":
        if action == "create":
            task_id = task_create(session_id, params["description"], params.get("metadata"))
            return task_id
        elif action == "add_attempt":
            return task_add_attempt(
                params["task_id"], params["actions_taken"],
                params["result"], params["success"], params.get("error_message")
            )
        elif action == "add_insight":
            return task_add_insight(
                params["task_id"], params["content"],
                params.get("insight_type", "learning"), params.get("importance", 5)
            )
        elif action == "update_status":
            return task_update_status(params["task_id"], params["status"])
        elif action == "get_context":
            return task_get_context(params["task_id"])
        elif action == "list_incomplete":
            return task_list_incomplete(session_id)
        elif action == "search_similar":
            return task_search_similar(params["description"], params.get("limit", 5))
        else:
            return {"error": f"Неизвестное действие task/{action}"}

    elif category == "result":
        manager = get_results_manager()
        if action == "save":
            content = params["content"]
            try:
                content = json.loads(content) if isinstance(content, str) else content
            except Exception:
                pass
            return result_save(
                session_id=session_id,
                result_type=params["result_type"],
                content=content,
                title=params.get("title"),
                task_id=params.get("task_id"),
                ttl_hours=params.get("ttl_hours", 24)
            )
        elif action == "get":
            return result_get(params["result_id"])
        elif action == "list":
            return result_list(session_id, params.get("result_type"), params.get("limit", 10))
        elif action == "get_latest":
            return result_get_latest(session_id, params.get("result_type"))
        else:
            return {"error": f"Неизвестное действие result/{action}"}

    elif category == "skill":
        if action == "get_info":
            skill = skill_loader.load_full(params["skill_name"])
            if skill:
                return {"success": True, "name": skill.name, "description": skill.description,
                        "content": skill.content, "triggers": skill.triggers}
            return {"success": False, "error": f"Навык '{params['skill_name']}' не найден"}
        elif action == "run_script":
            return run_skill_script(
                skill_loader, params["skill_name"], params["script_name"],
                params.get("args", []), params.get("timeout", 60)
            )
        else:
            return {"error": f"Неизвестное действие skill/{action}"}

    else:
        return {"error": f"Неизвестная категория: {category}. Доступные: {', '.join(list_categories())}"}


async def execute_tool(name: str, arguments: Dict[str, Any], session_id: str = "") -> Dict[str, Any]:
    """Выполняет вызванный инструмент."""
    if name == "run_shell":
        return run_shell(arguments["command"], arguments.get("timeout", 60))
    elif name == "read_file":
        return read_file(arguments["path"], arguments.get("offset", 0), arguments.get("limit", 100))
    elif name == "write_file":
        return write_file(arguments["path"], arguments["content"], arguments.get("append", False))
    elif name == "list_dir":
        return list_dir(arguments.get("path", "."))
    elif name == "tool_get_available":
        category = arguments["category"]
        info = get_category_tools(category)
        if not info:
            return {"error": f"Категория '{category}' не найдена. Доступные: {', '.join(list_categories())}"}
        actions_desc = {}
        for act_name, act_info in info["actions"].items():
            actions_desc[act_name] = act_info["description"]
        return {"success": True, "category": category, "description": info["description"], "actions": actions_desc}
    elif name == "tool_use":
        return await dispatch_tool_use(
            arguments["category"], arguments["action"],
            arguments.get("params", {}), session_id
        )
    else:
        return {"error": f"Неизвестный инструмент: {name}"}


# Кэш для system prompt (для локальных LLM)
_cached_system_prompt = None
_cached_memory_hash = None


async def agent_loop(user_message: str, session_id: str) -> str:
    """
    Основной цикл агента:
    1. Отправляет сообщение LLM с доступными инструментами
    2. Получает ответ (текст или tool_call)
    3. Выполняет инструмент
    4. Отправляет результат обратно в LLM
    5. Повторяет до MAX_ITERATIONS или финального ответа
    """
    global _cached_system_prompt, _cached_memory_hash
    
    memory = get_memory_manager()
    await memory.add_conversation(session_id, "user", user_message)

    memory_context = await memory.build_context_prompt(user_message, session_id)
    results_manager = get_results_manager()
    results_context = results_manager.build_results_context(session_id, limit=5)

    # Кэширование system prompt для локальных LLM (ollama, lmstudio, localai)
    # Это экономит время на повторную генерацию одинакового промпта
    if LLM_PROVIDER.lower() in ["ollama", "lmstudio", "localai", "vllm", "textgen"]:
        context_hash = hash((memory_context or "", results_context or ""))
        if _cached_system_prompt and _cached_memory_hash == context_hash:
            system_prompt_with_memory = _cached_system_prompt
        else:
            system_prompt_with_memory = SYSTEM_PROMPT
            if memory_context:
                system_prompt_with_memory += f"\n\n{memory_context}"
            if results_context:
                system_prompt_with_memory += f"\n\n{results_context}"
            _cached_system_prompt = system_prompt_with_memory
            _cached_memory_hash = context_hash
    else:
        # Для облачных провайдеров (OpenAI, OpenRouter) не кэшируем - они сами кэшируют
        system_prompt_with_memory = SYSTEM_PROMPT
        if memory_context:
            system_prompt_with_memory += f"\n\n{memory_context}"
        if results_context:
            system_prompt_with_memory += f"\n\n{results_context}"

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt_with_memory},
        {"role": "user", "content": user_message}
    ]

    for iteration in range(MAX_ITERATIONS):
        print(f"\n--- Итерация {iteration + 1} ---")

        response = await llm_provider.create_completion(
            messages=messages,
            tools=TOOLS if provider_config["supports_functions"] else None,
            tool_choice="auto"
        )
        
        # Логирование использования токенов
        if hasattr(response, 'usage') and response.usage:
            print(f"📊 Tokens: prompt={response.usage.prompt_tokens}, "
                  f"completion={response.usage.completion_tokens}, "
                  f"total={response.usage.total_tokens}")

        message = response.choices[0].message

        if not message.tool_calls:
            final_response = message.content or "Готово."
            await memory.add_conversation(session_id, "assistant", final_response)
            return final_response

        messages.append({
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                }
                for tc in message.tool_calls
            ]
        })

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            print(f"🔧 Вызов: {name}({json.dumps(args, ensure_ascii=False)})")

            result = await execute_tool(name, args, session_id)
            result_str = json.dumps(result, ensure_ascii=False, default=str)

            print(f"📤 Результат: {result_str[:500]}{'...' if len(result_str) > 500 else ''}")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_str
            })

    return "Достигнут лимит итераций. Задача не завершена."


async def main():
    print("=" * 50)
    print("🤖 Агент Ануфрий с доступом к shell и памятью (Ctrl+C для выхода)")
    print("=" * 50)

    session_id = str(uuid.uuid4())
    print(f"📝 ID сессии: {session_id[:8]}...")

    while True:
        try:
            user_input = input("\n💬 Вы: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "выход"]:
                break

            print("\n⏳ Агент думает...")
            result = await agent_loop(user_input, session_id)
            print(f"\n🤖 Агент: {result}")

        except KeyboardInterrupt:
            print("\n👋 До свидания!")
            break
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")

    await browser_close()


if __name__ == "__main__":
    asyncio.run(main())
