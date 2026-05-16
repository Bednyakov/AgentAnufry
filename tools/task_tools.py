"""
Инструменты для работы с отслеживанием задач агента.
"""

from typing import Dict, Any, List, Optional
from memory.task_tracker import TaskTracker


# Глобальный экземпляр трекера задач
_task_tracker = None


def get_task_tracker() -> TaskTracker:
    """Получает глобальный экземпляр трекера задач."""
    global _task_tracker
    if _task_tracker is None:
        _task_tracker = TaskTracker()
    return _task_tracker


def task_create(session_id: str, description: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Создаёт новую задачу для отслеживания."""
    try:
        tracker = get_task_tracker()
        task_id = tracker.create_task(session_id, description, metadata)
        return {
            "success": True,
            "task_id": task_id,
            "message": f"Задача #{task_id} создана"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def task_add_attempt(
    task_id: int,
    actions_taken: List[str],
    result: str,
    success: bool,
    error_message: Optional[str] = None
) -> Dict[str, Any]:
    """Добавляет попытку выполнения задачи."""
    try:
        tracker = get_task_tracker()
        attempt_id = tracker.add_attempt(
            task_id=task_id,
            actions_taken=actions_taken,
            result=result,
            success=success,
            error_message=error_message
        )
        return {
            "success": True,
            "attempt_id": attempt_id,
            "message": f"Попытка добавлена к задаче #{task_id}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def task_add_insight(
    task_id: int,
    content: str,
    insight_type: str = "learning",
    importance: int = 5
) -> Dict[str, Any]:
    """Добавляет ключевой вывод из задачи."""
    try:
        tracker = get_task_tracker()
        tracker.add_insight(task_id, content, insight_type, importance)
        return {
            "success": True,
            "message": f"Вывод добавлен к задаче #{task_id}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def task_update_status(task_id: int, status: str) -> Dict[str, Any]:
    """Обновляет статус задачи (in_progress, completed, failed, blocked)."""
    try:
        tracker = get_task_tracker()
        completed = status == "completed"
        tracker.update_task_status(task_id, status, completed)
        return {
            "success": True,
            "message": f"Статус задачи #{task_id} обновлён на '{status}'"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def task_get_context(task_id: int) -> Dict[str, Any]:
    """Получает полный контекст задачи для продолжения работы."""
    try:
        tracker = get_task_tracker()
        context = tracker.build_task_context(task_id)
        
        if not context:
            return {
                "success": False,
                "error": f"Задача #{task_id} не найдена"
            }
        
        return {
            "success": True,
            "context": context,
            "task_id": task_id
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def task_list_incomplete(session_id: str) -> Dict[str, Any]:
    """Показывает список незавершённых задач текущей сессии."""
    try:
        tracker = get_task_tracker()
        tasks = tracker.get_incomplete_tasks(session_id)
        
        if not tasks:
            return {
                "success": True,
                "tasks": [],
                "message": "Нет незавершённых задач"
            }
        
        return {
            "success": True,
            "tasks": tasks,
            "count": len(tasks)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def task_search_similar(description: str, limit: int = 5) -> Dict[str, Any]:
    """Ищет похожие задачи (особенно полезно для поиска успешных решений)."""
    try:
        tracker = get_task_tracker()
        tasks = tracker.search_similar_tasks(description, limit, only_successful=True)
        
        if not tasks:
            return {
                "success": True,
                "tasks": [],
                "message": "Похожих задач не найдено"
            }
        
        # Получаем детали для каждой задачи
        detailed_tasks = []
        for task in tasks:
            task_context = tracker.build_task_context(task["id"])
            detailed_tasks.append({
                "id": task["id"],
                "description": task["description"],
                "status": task["status"],
                "relevance": task["relevance"],
                "context": task_context
            })
        
        return {
            "success": True,
            "tasks": detailed_tasks,
            "count": len(detailed_tasks)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
