import subprocess
import shlex
import os
from typing import Dict, Any
from config import ALLOWED_COMMANDS, WORKSPACE_DIR

os.makedirs(WORKSPACE_DIR, exist_ok=True)

def run_shell(command: str, timeout: int = 60) -> Dict[str, Any]:
    """
    Выполняет shell-команду на локальной машине.
    Работает с полным доступом к системе.
    """
    # Базовая защита от опасных команд
    dangerous = ["rm -rf /", "mkfs.", "dd if=/dev/zero", ":(){ :|:& };:"]
    for d in dangerous:
        if d in command:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Заблокирована потенциально опасная команда: {d}",
                "returncode": 1
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
                "returncode": 1
            }

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=WORKSPACE_DIR,
            env={**os.environ, "PWD": WORKSPACE_DIR}
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Команда превысила лимит времени ({timeout} сек)",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }
