import os
import json
from pathlib import Path
from typing import Dict, Any, List
from config import WORKSPACE_DIR

def _normalize_path(path: str) -> str:
    """Нормализует путь, удаляя дублирующийся префикс workspace."""
    # Удаляем возможные префиксы, которые дублируют WORKSPACE_DIR
    workspace_name = os.path.basename(WORKSPACE_DIR)
    
    # Если путь начинается с имени рабочей директории, удаляем его
    if path.startswith(workspace_name + '/') or path.startswith(workspace_name + os.sep):
        path = path[len(workspace_name) + 1:]
    elif path == workspace_name:
        path = '.'
    
    return path

def read_file(path: str, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
    """Читает файл из рабочей директории."""
    path = _normalize_path(path)
    full_path = Path(WORKSPACE_DIR) / path
    full_path = full_path.resolve()
    
    # Защита: не выходим за пределы workspace
    if not str(full_path).startswith(str(Path(WORKSPACE_DIR).resolve())):
        return {"success": False, "error": "Доступ за пределами workspace запрещён"}
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            total_lines = len(lines)
            selected = lines[offset:offset + limit]
            content = ''.join(selected)
        
        return {
            "success": True,
            "content": content,
            "total_lines": total_lines,
            "read_lines": len(selected),
            "path": str(full_path)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def write_file(path: str, content: str, append: bool = False) -> Dict[str, Any]:
    """Записывает или дописывает файл."""
    path = _normalize_path(path)
    full_path = Path(WORKSPACE_DIR) / path
    full_path = full_path.resolve()
    
    if not str(full_path).startswith(str(Path(WORKSPACE_DIR).resolve())):
        return {"success": False, "error": "Доступ за пределами workspace запрещён"}
    
    try:
        full_path.parent.mkdir(parents=True, exist_ok=True)
        mode = 'a' if append else 'w'
        with open(full_path, mode, encoding='utf-8') as f:
            f.write(content)
        return {"success": True, "path": str(full_path), "bytes_written": len(content.encode())}
    except Exception as e:
        return {"success": False, "error": str(e)}

def list_dir(path: str = ".") -> Dict[str, Any]:
    """Список файлов в директории."""
    path = _normalize_path(path)
    full_path = Path(WORKSPACE_DIR) / path
    full_path = full_path.resolve()
    
    if not str(full_path).startswith(str(Path(WORKSPACE_DIR).resolve())):
        return {"success": False, "error": "Доступ за пределами workspace запрещён"}
    
    try:
        items = []
        for item in full_path.iterdir():
            stat = item.stat()
            items.append({
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
                "size": stat.st_size,
                "modified": stat.st_mtime
            })
        return {"success": True, "items": items, "path": str(full_path)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def search_files(pattern: str, path: str = ".") -> Dict[str, Any]:
    """Поиск файлов по паттерну (grep-like)."""
    import subprocess
    path = _normalize_path(path)
    full_path = Path(WORKSPACE_DIR) / path
    result = subprocess.run(
        ["grep", "-r", "-l", pattern, str(full_path)],
        capture_output=True, text=True
    )
    return {
        "success": result.returncode == 0,
        "matches": result.stdout.strip().split('\n') if result.stdout else []
    }
