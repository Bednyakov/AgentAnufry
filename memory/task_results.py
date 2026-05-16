"""
Система сохранения результатов выполнения задач.
Позволяет агенту сохранять промежуточные результаты и использовать их позже.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class TaskResultsManager:
    """
    Управляет результатами выполнения задач:
    - Сохраняет промежуточные результаты в структурированном виде
    - Позволяет извлекать результаты по task_id или session_id
    - Автоматически очищает старые результаты
    """
    
    def __init__(self, db_path: str = "memory/agent_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Инициализирует таблицу для хранения результатов."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица для хранения результатов задач
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                session_id TEXT NOT NULL,
                result_type TEXT NOT NULL,
                title TEXT,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)
        
        # Индексы для быстрого поиска
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_task ON task_results(task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_session ON task_results(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_type ON task_results(result_type)")
        
        conn.commit()
        conn.close()
    
    def save_result(
        self,
        session_id: str,
        result_type: str,
        content: Any,
        title: Optional[str] = None,
        task_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ttl_hours: int = 24
    ) -> int:
        """
        Сохраняет результат выполнения задачи.
        
        Args:
            session_id: ID сессии
            result_type: Тип результата (search_results, extracted_data, file_content, etc.)
            content: Содержимое результата (будет сериализовано в JSON)
            title: Заголовок результата
            task_id: ID связанной задачи (опционально)
            metadata: Дополнительные метаданные
            ttl_hours: Время жизни результата в часах (по умолчанию 24 часа)
        
        Returns:
            ID сохранённого результата
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Вычисляем время истечения
        from datetime import timedelta
        expires_at = (datetime.now() + timedelta(hours=ttl_hours)).isoformat()
        
        # Сериализуем content
        if isinstance(content, (dict, list)):
            content_str = json.dumps(content, ensure_ascii=False, indent=2)
        else:
            content_str = str(content)
        
        cursor.execute("""
            INSERT INTO task_results (
                task_id, session_id, result_type, title, content, metadata, expires_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id,
            session_id,
            result_type,
            title,
            content_str,
            json.dumps(metadata) if metadata else None,
            expires_at
        ))
        
        result_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return result_id
    
    def get_result(self, result_id: int) -> Optional[Dict[str, Any]]:
        """Получает результат по ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, task_id, session_id, result_type, title, content, metadata, created_at
            FROM task_results
            WHERE id = ? AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
        """, (result_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        # Пытаемся распарсить content как JSON
        try:
            content = json.loads(row[5])
        except:
            content = row[5]
        
        return {
            "id": row[0],
            "task_id": row[1],
            "session_id": row[2],
            "result_type": row[3],
            "title": row[4],
            "content": content,
            "metadata": json.loads(row[6]) if row[6] else {},
            "created_at": row[7]
        }
    
    def get_session_results(
        self,
        session_id: str,
        result_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Получает результаты текущей сессии.
        
        Args:
            session_id: ID сессии
            result_type: Фильтр по типу результата (опционально)
            limit: Максимальное количество результатов
        
        Returns:
            Список результатов
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if result_type:
            cursor.execute("""
                SELECT id, task_id, result_type, title, content, metadata, created_at
                FROM task_results
                WHERE session_id = ? AND result_type = ?
                AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                ORDER BY created_at DESC
                LIMIT ?
            """, (session_id, result_type, limit))
        else:
            cursor.execute("""
                SELECT id, task_id, result_type, title, content, metadata, created_at
                FROM task_results
                WHERE session_id = ?
                AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                ORDER BY created_at DESC
                LIMIT ?
            """, (session_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            # Пытаемся распарсить content как JSON
            try:
                content = json.loads(row[4])
            except:
                content = row[4]
            
            results.append({
                "id": row[0],
                "task_id": row[1],
                "result_type": row[2],
                "title": row[3],
                "content": content,
                "metadata": json.loads(row[5]) if row[5] else {},
                "created_at": row[6]
            })
        
        return results
    
    def get_task_results(self, task_id: int) -> List[Dict[str, Any]]:
        """Получает все результаты связанные с задачей."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, result_type, title, content, metadata, created_at
            FROM task_results
            WHERE task_id = ?
            AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            ORDER BY created_at ASC
        """, (task_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            try:
                content = json.loads(row[3])
            except:
                content = row[3]
            
            results.append({
                "id": row[0],
                "result_type": row[1],
                "title": row[2],
                "content": content,
                "metadata": json.loads(row[4]) if row[4] else {},
                "created_at": row[5]
            })
        
        return results
    
    def get_latest_result(
        self,
        session_id: str,
        result_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Получает последний результат из сессии."""
        results = self.get_session_results(session_id, result_type, limit=1)
        return results[0] if results else None
    
    def delete_result(self, result_id: int) -> bool:
        """Удаляет результат по ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM task_results WHERE id = ?", (result_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def cleanup_expired(self) -> int:
        """Удаляет истёкшие результаты."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM task_results
            WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP
        """)
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted
    
    def build_results_context(self, session_id: str, limit: int = 5) -> str:
        """
        Строит контекст из последних результатов сессии для передачи агенту.
        """
        results = self.get_session_results(session_id, limit=limit)
        
        if not results:
            return ""
        
        parts = ["## Доступные результаты из текущей сессии:"]
        
        for i, result in enumerate(results, 1):
            title = result.get('title') or f"Результат #{result['id']}"
            result_type = result['result_type']
            created = result['created_at']
            
            parts.append(f"\n{i}. **{title}** (тип: {result_type}, создан: {created})")
            parts.append(f"   ID результата: {result['id']}")
            
            # Показываем краткое превью контента
            content = result['content']
            if isinstance(content, list):
                parts.append(f"   Содержит {len(content)} элементов")
                if content and len(content) > 0:
                    preview = str(content[0])[:100]
                    parts.append(f"   Пример: {preview}...")
            elif isinstance(content, dict):
                parts.append(f"   Содержит {len(content)} полей")
            else:
                preview = str(content)[:150]
                parts.append(f"   Превью: {preview}...")
        
        parts.append("\n💡 Используй result_get для получения полного содержимого результата.")
        
        return "\n".join(parts)
