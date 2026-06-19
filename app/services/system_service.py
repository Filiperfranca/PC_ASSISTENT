import time
from typing import Any

from app.core.config import config
from app.core.event_bus import EventBus
from app.core.events import Event
from app.core.logger import logger
from app.integrations.windows_integration import WindowsIntegration


class SystemService:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.last_lock_attempt_at: float | None = None
        self.lock_triggered_for_current_away = False

    def start(self) -> None:
        logger.info("Iniciando SystemService...")

        self.event_bus.subscribe(Event.USER_PRESENT, self.on_user_present)
        self.event_bus.subscribe(Event.USER_AWAY, self.on_user_away)

        logger.info("SystemService iniciado com sucesso.")

    def on_user_present(self, payload: dict[str, Any]) -> None:
        if not config.enable_system_actions:
            logger.debug("Ações de sistema desabilitadas por configuração.")
            return

        self.lock_triggered_for_current_away = False

        logger.info(
            "Usuário retornou. Sistema pode executar ações de retorno."
        )

    def on_user_away(self, payload: dict[str, Any]) -> None:
        if not config.enable_system_actions:
            logger.debug("Ações de sistema desabilitadas por configuração.")
            return

        logger.info(
            "Usuário ausente. Sistema pode executar ações de ausência."
        )

        if self.lock_triggered_for_current_away:
            logger.info(
                "Bloqueio já foi acionado para esta ausência. Ignorando novo lock."
            )
            return

        if not config.enable_windows_lock:
            logger.info("Simulação: workstation seria bloqueada agora.")
            self.lock_triggered_for_current_away = True
            return

        if not self._can_lock_now():
            logger.info(
                "Bloqueio ignorado por cooldown. "
                f"Cooldown configurado: {config.windows_lock_cooldown_seconds}s"
            )
            return

        self.last_lock_attempt_at = time.time()
        self.lock_triggered_for_current_away = True

        locked = WindowsIntegration.lock_workstation()

        if locked:
            logger.info("Ação concluída: workstation bloqueada.")
        else:
            logger.warning("Ação de bloqueio não foi concluída.")

    def _can_lock_now(self) -> bool:
        if self.last_lock_attempt_at is None:
            return True

        elapsed = time.time() - self.last_lock_attempt_at

        return elapsed >= config.windows_lock_cooldown_seconds