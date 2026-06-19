import ctypes

from app.core.config import config
from app.core.logger import logger


class WindowsIntegration:
    @staticmethod
    def lock_workstation() -> bool:
        if not config.enable_windows_lock:
            logger.info(
                "Bloqueio de workstation desabilitado por configuração."
            )
            return False

        try:
            logger.info("Executando bloqueio da workstation via Windows API...")

            result = ctypes.windll.user32.LockWorkStation()

            if result == 0:
                error_code = ctypes.get_last_error()
                logger.error(
                    f"Windows API LockWorkStation falhou. "
                    f"GetLastError={error_code}"
                )
                return False

            logger.info("Workstation bloqueada com sucesso.")
            return True

        except Exception as error:
            logger.exception(f"Erro ao bloquear workstation: {error}")
            return False