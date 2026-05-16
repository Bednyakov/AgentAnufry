"""
Система отслеживания задач агента.
Сохраняет контекст задач для возможности повторных попыток.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class TaskTracker:
    """
    Отслеживает выполнение задач агента:
    - Сохраняет описание задачи и контекст
    - Фиксирует попытки выполнения
    - Запоминает причины неудач
    - Позволяет продолжить с того места, где остановились
    """
    
    def __init__(self, db_path: str = "memory/agent_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Инициализирует таблицы для отслеживания задач."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица задач
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT DEFAULT 'in_progress',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                metadata TEXT
            )
        """)
        
        # Таблица попыток выполнения
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                attempt_number INTEGER NOT NULL,
                actions_taken TEXT,
                result TEXT,
                error_message TEXT,
                success BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                context_snapshot TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)
        
        # Таблица ключевых выводов из задач
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                insight_type TEXT,
                content TEXT NOT NULL,
                importance INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)
        
        # Индексы
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_session ON tasks(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attempts_task ON task_attempts(task_id)")
        
        conn.commit()
        conn.close()
    
    def create_task(
        self,
        session_id: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Создаёт новую задачу."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO tasks (session_id, description, metadata)
            VALUES (?, ?, ?)
        """, (
            session_id,
            description,
            json.dumps(metadata) if metadata else None
        ))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return task_id
    
    def add_attempt(
        self,
        task_id: int,
        actions_taken: List[str],
        result: str,
        success: bool,
        error_message: Optional[str] = None,
        context_snapshot: Optional[Dict[str, Any]] = None
    ) -> int:
        """Добавляет попытку выполнения задачи."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Получаем номер попытки
        cursor.execute("""
            SELECT COALESCE(MAX(attempt_number), 0) + 1
            FROM task_attempts
            WHERE task_id = ?
        """, (task_id,))
        attempt_number = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO task_attempts (
                task_id, attempt_number, actions_taken, result, 
                error_message, success, context_snapshot
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id,
            attempt_number,
            json.dumps(actions_taken, ensure_ascii=False),
            result,
            error_message,
            success,
            json.dumps(context_snapshot) if context_snapshot else None
        ))
        
        attempt_id = cursor.lastrowid
        
        # Обновляем время изменения задачи
        cursor.execute("""
            UPDATE tasks
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (task_id,))
        
        conn.commit()
        conn.close()
        
        return attempt_id
    
    def add_insight(
        self,
        task_id: int,
        content: str,
        insight_type: str = "learning",
        importance: int = 5
    ):
        """Добавляет ключевой вывод из задачи."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO task_insights (task_id, insight_type, content, importance)
            VALUES (?, ?, ?, ?)
        """, (task_id, insight_type, content, importance))
        
        conn.commit()
        conn.close()
    
    def update_task_status(
        self,
        task_id: int,
        status: str,
        completed: bool = False
    ):
        """Обновляет статус задачи."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if completed:
            cursor.execute("""
                UPDATE tasks
                SET status = ?, updated_at = CURRENT_TIMESTAMP, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, task_id))
        else:
            cursor.execute("""
                UPDATE tasks
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, task_id))
        
        conn.commit()
        conn.close()
    
    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Получает информацию о задаче."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, session_id, description, status, created_at, updated_at, completed_at, metadata
            FROM tasks
            WHERE id = ?
        """, (task_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            "id": row[0],
            "session_id": row[1],
            "description": row[2],
            "status": row[3],
            "created_at": row[4],
            "updated_at": row[5],
            "completed_at": row[6],
            "metadata": json.loads(row[7]) if row[7] else {}
        }
    
    def get_task_attempts(self, task_id: int) -> List[Dict[str, Any]]:
        """Получает все попытки выполнения задачи."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT attempt_number, actions_taken, result, error_message, success, created_at, context_snapshot
            FROM task_attempts
            WHERE task_id = ?
            ORDER BY attempt_number ASC
        """, (task_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        attempts = []
        for row in rows:
            attempts.append({
                "attempt_number": row[0],
                "actions_taken": json.loads(row[1]) if row[1] else [],
                "result": row[2],
                "error_message": row[3],
                "success": bool(row[4]),
                "created_at": row[5],
                "context_snapshot": json.loads(row[6]) if row[6] else {}
            })
        
        return attempts
    
    def get_task_insights(self, task_id: int) -> List[Dict[str, Any]]:
        """Получает ключевые выводы из задачи."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT insight_type, content, importance, created_at
            FROM task_insights
            WHERE task_id = ?
            ORDER BY importance DESC, created_at DESC
        """, (task_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            "type": row[0],
            "content": row[1],
            "importance": row[2],
            "created_at": row[3]
        } for row in rows]
    
    def get_incomplete_tasks(self, session_id: str) -> List[Dict[str, Any]]:
        """Получает незавершённые задачи текущей сессии."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, description, status, created_at, updated_at
            FROM tasks
            WHERE session_id = ? AND status IN ('in_progress', 'failed', 'blocked')
            ORDER BY updated_at DESC
        """, (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            "id": row[0],
            "description": row[1],
            "status": row[2],
            "created_at": row[3],
            "updated_at": row[4]
        } for row in rows]
    
    def search_similar_tasks(
        self,
        description: str,
        limit: int = 5,
        only_successful: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Ищет похожие задачи по описанию (простой текстовый поиск).
        Для семантического поиска можно интегрировать с MemoryManager.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Простой поиск по ключевым словам
        keywords = description.lower().split()
        
        if only_successful:
            cursor.execute("""
                SELECT id, description, status, created_at, completed_at
                FROM tasks
                WHERE status = 'completed'
                ORDER BY updated_at DESC
                LIMIT ?
            """, (limit * 3,))  # Берём больше для фильтрации
        else:
            cursor.execute("""
                SELECT id, description, status, created_at, completed_at
                FROM tasks
                ORDER BY updated_at DESC
                LIMIT ?
            """, (limit * 3,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Фильтруем по релевантности
        results = []
        for row in rows:
            task_desc = row[1].lower()
            relevance = sum(1 for kw in keywords if kw in task_desc)
            
            if relevance > 0:
                results.append({
                    "id": row[0],
                    "description": row[1],
                    "status": row[2],
                    "created_at": row[3],
                    "completed_at": row[4],
                    "relevance": relevance
                })
        
        # Сортируем по релевантности
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:limit]
    
    def build_task_context(self, task_id: int) -> str:
        """
        Строит компактный контекст задачи для передачи агенту.
        Включает только важную информацию.
        """
        task = self.get_task(task_id)
        if not task:
            return ""
        
        attempts = self.get_task_attempts(task_id)
        insights = self.get_task_insights(task_id)
        
        parts = [
            f"## Задача #{task_id}: {task['description']}",
            f"Статус: {task['status']}",
            f"Создана: {task['created_at']}"
        ]
        
        if attempts:
            parts.append(f"\n### Попытки выполнения ({len(attempts)}):")
            for attempt in attempts[-3:]:  # Только последние 3 попытки
                status = "✅ Успешно" if attempt['success'] else "❌ Неудача"
                parts.append(f"\n**Попытка {attempt['attempt_number']}** {status}")
                parts.append(f"Действия: {', '.join(attempt['actions_taken'][:5])}")
                if attempt['error_message']:
                    parts.append(f"Ошибка: {attempt['error_message'][:200]}")
        
        if insights:
            parts.append("\n### Ключевые выводы:")
            for insight in insights[:5]:  # Топ-5 выводов
                parts.append(f"- [{insight['type']}] {insight['content']}")
        
        return "\n".join(parts)
    
    def cleanup_old_tasks(self, days_threshold: int = 90):
        """Удаляет старые завершённые задачи."""
        from datetime import timedelta
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days_threshold)).isoformat()
        
        # Получаем ID задач для удаления
        cursor.execute("""
            SELECT id FROM tasks
            WHERE status = 'completed' AND completed_at < ?
        """, (cutoff_date,))
        
        task_ids = [row[0] for row in cursor.fetchall()]
        
        if task_ids:
            placeholders = ','.join('?' * len(task_ids))
            
            # Удаляем связанные данные
            cursor.execute(f"DELETE FROM task_attempts WHERE task_id IN ({placeholders})", task_ids)
            cursor.execute(f"DELETE FROM task_insights WHERE task_id IN ({placeholders})", task_ids)
            cursor.execute(f"DELETE FROM tasks WHERE id IN ({placeholders})", task_ids)
        
        conn.commit()
        conn.close()
        
        return len(task_ids)
