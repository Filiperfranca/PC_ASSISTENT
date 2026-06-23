import ctypes

from app.core.logger import logger


ERROR_ALREADY_EXISTS = 183


class SingleInstance:
    def __init__(self, mutex_name="Local\\PresenceAgent"):
        self.mutex_name = mutex_name
        self.mutex_handle = None

        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        self.kernel32.CreateMutexW.argtypes = [
            ctypes.c_void_p,
            ctypes.c_bool,
            ctypes.c_wchar_p,
        ]
        self.kernel32.CreateMutexW.restype = ctypes.c_void_p

        self.kernel32.CloseHandle.argtypes = [
            ctypes.c_void_p,
        ]
        self.kernel32.CloseHandle.restype = ctypes.c_bool

    def acquire(self):
        self.mutex_handle = self.kernel32.CreateMutexW(
            None,
            True,
            self.mutex_name,
        )

        if not self.mutex_handle:
            error_code = ctypes.get_last_error()
            logger.error(
                "Falha ao criar mutex do PresenceAgent. "
                f"error_code={error_code}"
            )
            return False

        error_code = ctypes.get_last_error()

        if error_code == ERROR_ALREADY_EXISTS:
            logger.warning(
                "Outra instância do PresenceAgent já está em execução. "
                "Encerrando esta nova instância."
            )
            self.release()
            return False

        logger.info(
            "Single instance mutex adquirido com sucesso: "
            f"{self.mutex_name}"
        )
        return True

    def release(self):
        if self.mutex_handle:
            self.kernel32.CloseHandle(self.mutex_handle)
            self.mutex_handle = None
            logger.info("Single instance mutex liberado.")