from typing import Any

from app.core.config import config
from app.core.event_bus import EventBus
from app.core.events import Event
from app.core.logger import logger
from app.integrations.windows_integration import WindowsIntegration


class SystemService:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    def start(self) -> None:
        logger.info("Iniciando SystemService...")

        self.event_bus.subscribe(Event.USER_PRESENT, self.on_user_present)
        self.event_bus.subscribe(Event.USER_AWAY, self.on_user_away)

        logger.info("SystemService iniciado com sucesso.")

    def on_user_present(self, payload: dict[str, Any]) -> None:
        if not config.enable_system_actions:
            return

        logger.info(
            "Usuário retornou. "
            "Sistema pode executar ações de retorno."
        )

    def on_user_away(self, payload: dict[str, Any]) -> None:
        if not config.enable_system_actions:
            return

        logger.info(
            "Usuário ausente. "
            "Sistema pode executar ações de ausência."
        )

        if config.enable_windows_lock:
            logger.info("Bloqueio automático habilitado.")
            WindowsIntegration.lock_workstation()
        else:
            logger.info(
                "Simulação: workstation seria bloqueada agora."
            )