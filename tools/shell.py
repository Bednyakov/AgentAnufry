import subprocess
import shlex
import os
import platform
from typing import Dict, Any, Tuple
from config import ALLOWED_COMMANDS, WORKSPACE_DIR

os.makedirs(WORKSPACE_DIR, exist_ok=True)

def detect_os() -> str:
    """
    Определяет операционную систему.
    Возвращает: 'linux', 'macos', 'windows'
    """
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    else:
        return "linux"

def get_shell_config() -> Tuple[str, bool]:
    """
    Возвращает конфигурацию shell для текущей ОС.
    Returns: (executable, use_shell)
    """
    os_type = detect_os()
    
    if os_type == "windows":
        # Для Windows используем cmd.exe
        return ("cmd.exe", True)
    else:
        # Для Linux и macOS используем bash/sh
        return ("/bin/bash", True)

def get_dangerous_commands() -> list:
    """
    Возвращает список опасных команд для текущей ОС.
    """
    os_type = detect_os()
    
    # Общие опасные паттерны
    common = [":(){ :|:& };:"]  # Fork bomb
    
    if os_type == "windows":
        return common + [
            "format ",
            "del /s /q c:\\",
            "rd /s /q c:\\",
            "rmdir /s /q c:\\",
            "diskpart",
        ]
    else:  # Linux и macOS
        return common + [
            "rm -rf /",
            "rm -rf /*",
            "mkfs.",
            "dd if=/dev/zero of=/dev/",
            "> /dev/sda",
        ]

def run_shell(command: str, timeout: int = 60) -> Dict[str, Any]:
    """
    Выполняет shell-команду на локальной машине.
    Работает с полным доступом к системе.
    Поддерживает Linux, macOS и Windows.
    """
    os_type = detect_os()
    
    # Базовая защита от опасных команд
    dangerous = get_dangerous_commands()
    for d in dangerous:
        if d in command.lower():
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Заблокирована потенциально опасная команда: {d}",
                "returncode": 1,
                "os": os_type
            }

    # Проверка whitelist (опционально)
    if ALLOWED_COMMANDS != "*":
        allowed = [c.strip() for c in ALLOWED_COMMANDS.split(",")]
        cmd_base = command.split()[0] if command.split() else ""
        if cmd_base not in allowed:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Команда '{cmd_base}' не в whitelist. Разрешённые: {allowed}",
                "returncode": 1,
                "os": os_type
            }

    try:
        # Получаем конфигурацию shell для текущей ОС
        shell_executable, use_shell = get_shell_config()
        
        # Подготовка окружения
        env = os.environ.copy()
        if os_type != "windows":
            env["PWD"] = WORKSPACE_DIR
        
        # Выполнение команды
        if os_type == "windows":
            # Для Windows используем cmd.exe с /c
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=WORKSPACE_DIR,
                env=env
            )
        else:
            # Для Linux и macOS используем bash
            result = subprocess.run(
                command,
                shell=True,
                executable=shell_executable,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=WORKSPACE_DIR,
                env=env
            )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "os": os_type
        }
    except subprocess.TimeoutExpired:
        # cm. https://t.me/itpolice
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Команда превысила лимит времени ({timeout} сек)",
            "returncode": -1,
            "os": os_type
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "os": os_type
        }
