"""
Инструменты для работы с результатами задач.
"""

from typing import Dict, Any, Optional
from memory.task_results import TaskResultsManager


# Глобальный экземпляр менеджера результатов
_results_manager = None


def get_results_manager() -> TaskResultsManager:
    """Получает глобальный экземпляр менеджера результатов."""
    global _results_manager
    if _results_manager is None:
        _results_manager = TaskResultsManager()
    return _results_manager


def result_save(
    session_id: str,
    result_type: str,
    content: Any,
    title: Optional[str] = None,
    task_id: Optional[int] = None,
    ttl_hours: int = 24
) -> Dict[str, Any]:
    """
    Сохраняет результат выполнения для последующего использования.
    
    Args:
        session_id: ID сессии
        result_type: Тип результата (search_results, extracted_data, companies_list, contacts, etc.)
        content: Содержимое результата (dict, list или str)
        title: Заголовок результата
        task_id: ID связанной задачи (опционально)
        ttl_hours: Время жизни результата в часах
    
    Returns:
        Dict с success и result_id
    """
    try:
        manager = get_results_manager()
        result_id = manager.save_result(
            session_id=session_id,
            result_type=result_type,
            content=content,
            title=title,
            task_id=task_id,
            ttl_hours=ttl_hours
        )
        return {
            "success": True,
            "result_id": result_id,
            "message": f"Результат сохранён с ID {result_id}. Используй result_get({result_id}) для получения."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def result_get(result_id: int) -> Dict[str, Any]:
    """
    Получает сохранённый результат по ID.
    
    Args:
        result_id: ID результата
    
    Returns:
        Dict с содержимым результата
    """
    try:
        manager = get_results_manager()
        result = manager.get_result(result_id)
        
        if not result:
            return {
                "success": False,
                "error": f"Результат #{result_id} не найден или истёк"
            }
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def result_list(
    session_id: str,
    result_type: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Показывает список сохранённых результатов текущей сессии.
    
    Args:
        session_id: ID сессии
        result_type: Фильтр по типу результата (опционально)
        limit: Максимальное количество результатов
    
    Returns:
        Dict со списком результатов
    """
    try:
        manager = get_results_manager()
        results = manager.get_session_results(session_id, result_type, limit)
        
        if not results:
            return {
                "success": True,
                "results": [],
                "message": "Нет сохранённых результатов в текущей сессии"
            }
        
        # Формируем краткую информацию о результатах
        results_info = []
        for r in results:
            info = {
                "id": r["id"],
                "type": r["result_type"],
                "title": r.get("title", f"Результат #{r['id']}"),
                "created_at": r["created_at"]
            }
            
            # Добавляем краткое описание содержимого
            content = r["content"]
            if isinstance(content, list):
                info["items_count"] = len(content)
            elif isinstance(content, dict):
                info["fields_count"] = len(content)
            
            results_info.append(info)
        
        return {
            "success": True,
            "results": results_info,
            "count": len(results_info),
            "message": f"Найдено {len(results_info)} результатов. Используй result_get(id) для получения полного содержимого."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def result_get_latest(
    session_id: str,
    result_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Получает последний сохранённый результат из сессии.
    
    Args:
        session_id: ID сессии
        result_type: Фильтр по типу результата (опционально)
    
    Returns:
        Dict с последним результатом
    """
    try:
        manager = get_results_manager()
        result = manager.get_latest_result(session_id, result_type)
        
        if not result:
            return {
                "success": False,
                "error": "Нет сохранённых результатов в текущей сессии"
            }
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def result_delete(result_id: int) -> Dict[str, Any]:
    """
    Удаляет сохранённый результат.
    
    Args:
        result_id: ID результата
    
    Returns:
        Dict с результатом операции
    """
    try:
        manager = get_results_manager()
        deleted = manager.delete_result(result_id)
        
        if deleted:
            return {
                "success": True,
                "message": f"Результат #{result_id} удалён"
            }
        else:
            return {
                "success": False,
                "error": f"Результат #{result_id} не найден"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
