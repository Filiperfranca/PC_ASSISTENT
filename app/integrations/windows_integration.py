import subprocess

from app.core.config import config
from app.core.logger import logger


class WindowsIntegration:
    @staticmethod
    def lock_workstation() -> bool:
        if not config.enable_windows_lock:
            logger.warning(
                "Bloqueio de workstation desabilitado por configuração."
            )
            return False

        try:
            logger.info("Executando bloqueio da workstation...")

            subprocess.run(
                [
                    "rundll32.exe",
                    "user32.dll,LockWorkStation",
                ],
                check=True,
            )

            logger.info("Workstation bloqueada com sucesso.")
            return True

        except Exception as error:
            logger.exception(f"Erro ao bloquear workstation: {error}")
            return False