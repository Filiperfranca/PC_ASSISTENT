import ctypes
from threading import Thread, Lock
from typing import Any

from app.core.config import config
from app.core.event_bus import EventBus
from app.core.events import Event
from app.core.logger import logger
from app.integrations.windows_integration import WindowsIntegration


class PromptService:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.lock = Lock()
        self.prompt_active = False

    def start(self) -> None:
        logger.info("Iniciando PromptService...")

        self.event_bus.subscribe(
            Event.MULTIPLE_FACES_CONFIRMED,
            self.on_multiple_faces_confirmed,
        )

        logger.info("PromptService iniciado com sucesso.")

    def on_multiple_faces_confirmed(self, payload: dict[str, Any]) -> None:
        with self.lock:
            if self.prompt_active:
                logger.info("Prompt multi-face já está ativo. Ignorando novo prompt.")
                return

            self.prompt_active = True

        thread = Thread(
            target=self._show_multi_face_prompt,
            args=(payload,),
            daemon=True,
        )
        thread.start()

    def _show_multi_face_prompt(self, payload: dict[str, Any]) -> None:
        try:
            faces_count = payload.get("faces_count", "desconhecido")

            logger.warning(
                "Abrindo prompt de segurança por múltiplos rostos. "
                f"faces_count={faces_count}"
            )

            title = "PresenceAgent - Segurança"
            message = (
                "Mais de um rosto foi detectado na câmera.\n\n"
                "Deseja bloquear a estação agora?"
            )

            user_choice = self._message_box_yes_no(title, message)

            if user_choice == "YES":
                logger.warning("Usuário escolheu bloquear a estação pelo prompt.")

                if config.enable_windows_lock:
                    WindowsIntegration.lock_workstation()
                else:
                    logger.warning(
                        "Simulação: usuário escolheu bloquear, "
                        "mas ENABLE_WINDOWS_LOCK=False."
                    )

            elif user_choice == "NO":
                logger.info("Usuário escolheu não bloquear pelo prompt.")

            else:
                logger.info(f"Prompt retornou resposta inesperada: {user_choice}")

        except Exception as error:
            logger.exception(f"Erro ao exibir prompt multi-face: {error}")

        finally:
            with self.lock:
                self.prompt_active = False

    def _message_box_yes_no(self, title: str, message: str) -> str:
        MB_YESNO = 0x00000004
        MB_ICONWARNING = 0x00000030
        MB_TOPMOST = 0x00040000
        MB_SETFOREGROUND = 0x00010000

        IDYES = 6
        IDNO = 7

        flags = MB_YESNO | MB_ICONWARNING | MB_TOPMOST | MB_SETFOREGROUND

        result = ctypes.windll.user32.MessageBoxW(
            0,
            message,
            title,
            flags,
        )

        if result == IDYES:
            return "YES"

        if result == IDNO:
            return "NO"

        return "UNKNOWN"