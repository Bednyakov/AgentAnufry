"""
Менеджер долговременной памяти агента.
Использует SQLite для хранения и OpenAI embeddings для семантического поиска.
"""

import sqlite3
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from openai import AsyncOpenAI

from config import (
    EMBEDDINGS_PROVIDER, EMBEDDINGS_MODEL, EMBEDDINGS_BASE_URL, EMBEDDINGS_API_KEY,
    IMPORTANCE_CLASSIFIER_MODEL, LLM_MODEL, LLM_BASE_URL, LLM_API_KEY
)


class MemoryManager:
    """
    Управляет долговременной памятью агента:
    - Хранит важные факты, диалоги, информацию о навыках
    - Использует embeddings для семантического поиска
    - Автоматически классифицирует важность информации
    - Очищает устаревшие данные
    """
    
    def __init__(self, db_path: str = "memory/agent_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Клиент для embeddings
        self.embeddings_client = AsyncOpenAI(
            api_key=EMBEDDINGS_API_KEY,
            base_url=EMBEDDINGS_BASE_URL
        )
        self.embeddings_model = EMBEDDINGS_MODEL
        self.embeddings_provider = EMBEDDINGS_PROVIDER
        
        # Клиент для классификации важности
        self.llm_client = AsyncOpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL
        )
        self.classifier_model = IMPORTANCE_CLASSIFIER_MODEL
        
        self._init_db()
    
    def _init_db(self):
        """Инициализирует базу данных."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица для хранения фактов и важной информации
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                category TEXT,
                importance INTEGER DEFAULT 5,
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                metadata TEXT
            )
        """)
        
        # Таблица для истории диалогов (среднесрочная память)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                importance INTEGER DEFAULT 3,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        
        # Таблица для информации о навыках
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skill_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT NOT NULL,
                usage_context TEXT,
                result TEXT,
                success BOOLEAN,
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                use_count INTEGER DEFAULT 1
            )
        """)
        
        # Индексы для быстрого поиска
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_importance ON facts(importance)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_skill_name ON skill_memory(skill_name)")
        
        conn.commit()
        conn.close()
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Получает embedding для текста через API."""
        try:
            # Для Yandex Cloud и других провайдеров, которые не поддерживают embeddings,
            # отключаем их использование
            if self.embeddings_provider == "openai" and "yandex" in self.embeddings_client.base_url.lower():
                # Yandex Cloud не поддерживает embeddings API
                return []
            
            if self.embeddings_provider == "local":
                # TODO: Реализовать локальные embeddings через sentence-transformers
                print("⚠️ Локальные embeddings пока не реализованы, используется заглушка")
                return []
            
            response = await self.embeddings_client.embeddings.create(
                model=self.embeddings_model,
                input=text,
                encoding_format="float"  # Явно указываем формат
            )
            return response.data[0].embedding
        except Exception as e:
            # Если embeddings не поддерживаются, возвращаем пустой список
            # Это отключит семантический поиск, но не сломает работу агента
            print(f"⚠️ Ошибка получения embedding (модель: {self.embeddings_model}, провайдер: {self.embeddings_provider}): {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Вычисляет косинусное сходство между двумя векторами."""
        if not vec1 or not vec2:
            return 0.0
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
    
    async def classify_importance(self, content: str, context: str = "") -> int:
        """
        Использует LLM для классификации важности информации (1-10).
        1-3: Малозначимая (удалить через неделю)
        4-6: Средняя (хранить месяц)
        7-10: Важная (хранить долго)
        """
        try:
            prompt = f"""Оцени важность следующей информации для долговременной памяти AI-агента по шкале 1-10.

Информация: {content}
Контекст: {context}

Критерии:
- 1-3: Временная информация (приветствия, подтверждения, мелкие детали)
- 4-6: Полезная информация (настройки, предпочтения, промежуточные результаты)
- 7-10: Критически важная (факты о пользователе, успешные решения, важные навыки)

Ответь ТОЛЬКО числом от 1 до 10."""

            response = await self.llm_client.chat.completions.create(
                model=self.classifier_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=50
            )
            
            # Проверяем, что content не None
            content = response.choices[0].message.content
            if content is None:
                print("⚠️ LLM вернул пустой ответ при классификации важности")
                return 5  # По умолчанию средняя важность
            
            importance_str = content.strip()
            if not importance_str or not any(c.isdigit() for c in importance_str):
                return 5  # Если нет цифр - возвращаем дефолт
            importance = int(''.join(filter(str.isdigit, importance_str)))
            return max(1, min(10, importance))
        except Exception as e:
            print(f"⚠️ Ошибка классификации важности: {e}")
            return 5  # По умолчанию средняя важность
    
    async def add_fact(
        self, 
        content: str, 
        category: str = "general",
        importance: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Добавляет факт в долговременную память."""
        if importance is None:
            importance = await self.classify_importance(content, category)
        
        embedding = await self._get_embedding(content)
        embedding_blob = json.dumps(embedding) if embedding else None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO facts (content, category, importance, embedding, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            content,
            category,
            importance,
            embedding_blob,
            json.dumps(metadata) if metadata else None
        ))
        
        fact_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return fact_id
    
    async def search_facts(
        self, 
        query: str, 
        limit: int = 5,
        min_importance: int = 4,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Ищет релевантные факты используя семантический поиск.
        Возвращает топ-N наиболее похожих фактов.
        """
        query_embedding = await self._get_embedding(query)
        if not query_embedding:
            return []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Получаем все факты с достаточной важностью
        sql = "SELECT id, content, category, importance, embedding, metadata FROM facts WHERE importance >= ?"
        params = [min_importance]
        
        if category:
            sql += " AND category = ?"
            params.append(category)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        # Вычисляем сходство для каждого факта
        results = []
        for row in rows:
            fact_id, content, cat, importance, embedding_blob, metadata = row
            if not embedding_blob:
                continue
            
            fact_embedding = json.loads(embedding_blob)
            similarity = self._cosine_similarity(query_embedding, fact_embedding)
            
            results.append({
                "id": fact_id,
                "content": content,
                "category": cat,
                "importance": importance,
                "similarity": similarity,
                "metadata": json.loads(metadata) if metadata else {}
            })
        
        # Обновляем статистику доступа для найденных фактов
        for result in sorted(results, key=lambda x: x["similarity"], reverse=True)[:limit]:
            cursor.execute("""
                UPDATE facts 
                SET last_accessed = CURRENT_TIMESTAMP, access_count = access_count + 1
                WHERE id = ?
            """, (result["id"],))
        
        conn.commit()
        conn.close()
        
        # Сортируем по сходству и возвращаем топ-N
        return sorted(results, key=lambda x: x["similarity"], reverse=True)[:limit]
    
    async def add_conversation(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Добавляет сообщение в историю диалогов."""
        # Классифицируем важность сообщения
        importance = await self.classify_importance(content, f"Роль: {role}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversations (session_id, role, content, importance, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session_id,
            role,
            content,
            importance,
            json.dumps(metadata) if metadata else None
        ))
        
        conn.commit()
        conn.close()
    
    def get_recent_conversations(
        self,
        session_id: str,
        limit: int = 10,
        min_importance: int = 3
    ) -> List[Dict[str, Any]]:
        """Получает последние N сообщений из текущей сессии."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT role, content, importance, created_at, metadata
            FROM conversations
            WHERE session_id = ? AND importance >= ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (session_id, min_importance, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        conversations = []
        for role, content, importance, created_at, metadata in rows:
            conversations.append({
                "role": role,
                "content": content,
                "importance": importance,
                "created_at": created_at,
                "metadata": json.loads(metadata) if metadata else {}
            })
        
        return list(reversed(conversations))  # Возвращаем в хронологическом порядке
    
    async def add_skill_usage(
        self,
        skill_name: str,
        usage_context: str,
        result: str,
        success: bool
    ):
        """Сохраняет информацию об использовании навыка."""
        embedding = await self._get_embedding(f"{skill_name}: {usage_context}")
        embedding_blob = json.dumps(embedding) if embedding else None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Проверяем, есть ли уже запись об этом навыке в похожем контексте
        cursor.execute("""
            SELECT id, use_count FROM skill_memory
            WHERE skill_name = ? AND usage_context = ?
        """, (skill_name, usage_context))
        
        existing = cursor.fetchone()
        
        if existing:
            # Обновляем существующую запись
            cursor.execute("""
                UPDATE skill_memory
                SET result = ?, success = ?, last_used = CURRENT_TIMESTAMP, use_count = use_count + 1
                WHERE id = ?
            """, (result, success, existing[0]))
        else:
            # Создаём новую запись | developer Bednyakov
            cursor.execute("""
                INSERT INTO skill_memory (skill_name, usage_context, result, success, embedding)
                VALUES (?, ?, ?, ?, ?)
            """, (skill_name, usage_context, result, success, embedding_blob))
        
        conn.commit()
        conn.close()
    
    async def get_skill_context(self, skill_name: str, query: str = "") -> List[Dict[str, Any]]:
        """Получает контекст предыдущего использования навыка."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if query:
            # Семантический поиск по контексту использования
            query_embedding = await self._get_embedding(query)
            if not query_embedding:
                return []
            
            cursor.execute("""
                SELECT usage_context, result, success, embedding, use_count, last_used
                FROM skill_memory
                WHERE skill_name = ? AND success = 1
                ORDER BY last_used DESC
                LIMIT 10
            """, (skill_name,))
            
            rows = cursor.fetchall()
            results = []
            
            for usage_context, result, success, embedding_blob, use_count, last_used in rows:
                if not embedding_blob:
                    continue
                
                skill_embedding = json.loads(embedding_blob)
                similarity = self._cosine_similarity(query_embedding, skill_embedding)
                
                results.append({
                    "usage_context": usage_context,
                    "result": result,
                    "success": bool(success),
                    "use_count": use_count,
                    "last_used": last_used,
                    "similarity": similarity
                })
            
            conn.close()
            return sorted(results, key=lambda x: x["similarity"], reverse=True)[:3]
        else:
            # Просто последние успешные использования
            cursor.execute("""
                SELECT usage_context, result, success, use_count, last_used
                FROM skill_memory
                WHERE skill_name = ? AND success = 1
                ORDER BY last_used DESC
                LIMIT 3
            """, (skill_name,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [{
                "usage_context": usage_context,
                "result": result,
                "success": bool(success),
                "use_count": use_count,
                "last_used": last_used
            } for usage_context, result, success, use_count, last_used in rows]
    
    async def cleanup_old_data(self, days_threshold: int = 30):
        """
        Очищает устаревшие данные:
        - Удаляет малозначимые факты старше N дней
        - Удаляет старые диалоги с низкой важностью
        - Сохраняет важную информацию
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days_threshold)).isoformat()
        
        # Удаляем малозначимые факты
        cursor.execute("""
            DELETE FROM facts
            WHERE importance <= 3 
            AND created_at < ?
            AND access_count < 2
        """, (cutoff_date,))
        
        deleted_facts = cursor.rowcount
        
        # Удаляем старые диалоги с низкой важностью
        cursor.execute("""
            DELETE FROM conversations
            WHERE importance <= 3
            AND created_at < ?
        """, (cutoff_date,))
        
        deleted_conversations = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return {
            "deleted_facts": deleted_facts,
            "deleted_conversations": deleted_conversations,
            "cutoff_date": cutoff_date
        }
    
    async def get_memory_summary(self) -> Dict[str, Any]:
        """Возвращает статистику по памяти."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*), AVG(importance) FROM facts")
        facts_count, avg_importance = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        conversations_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*), SUM(use_count) FROM skill_memory")
        skills_count, total_skill_uses = cursor.fetchone()
        
        cursor.execute("""
            SELECT category, COUNT(*) 
            FROM facts 
            GROUP BY category 
            ORDER BY COUNT(*) DESC 
            LIMIT 5
        """)
        top_categories = cursor.fetchall()
        
        conn.close()
        
        return {
            "facts_count": facts_count or 0,
            "avg_importance": round(avg_importance or 0, 2),
            "conversations_count": conversations_count or 0,
            "skills_tracked": skills_count or 0,
            "total_skill_uses": total_skill_uses or 0,
            "top_categories": [{"category": cat, "count": cnt} for cat, cnt in top_categories]
        }
    
    async def build_context_prompt(
        self,
        query: str,
        session_id: str,
        max_facts: int = 5,
        max_conversations: int = 5
    ) -> str:
        """
        Строит контекстный промпт для LLM на основе релевантной памяти.
        Это основной метод для интеграции памяти в диалог.
        """
        parts = []
        
        # 1. Релевантные факты из долговременной памяти
        facts = await self.search_facts(query, limit=max_facts, min_importance=5)
        if facts:
            parts.append("## Релевантная информация из памяти:")
            for i, fact in enumerate(facts, 1):
                parts.append(f"{i}. [{fact['category']}] {fact['content']} (важность: {fact['importance']}/10)")
        
        # 2. Недавние важные диалоги из текущей сессии
        recent = self.get_recent_conversations(session_id, limit=max_conversations, min_importance=4)
        if recent:
            parts.append("\n## Контекст текущей сессии:")
            for conv in recent:
                parts.append(f"- {conv['role']}: {conv['content'][:200]}...")
        
        return "\n".join(parts) if parts else ""
