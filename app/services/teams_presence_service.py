from typing import Any

from app.core.config import config
from app.core.event_bus import EventBus
from app.core.events import Event
from app.core.logger import logger
from app.integrations.graph_teams_provider import GraphTeamsProvider
from app.integrations.mock_teams_provider import MockTeamsProvider
from app.integrations.teams_provider import TeamsProvider


class TeamsPresenceService:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.provider: TeamsProvider | None = None
        self.last_presence: tuple[str, str] | None = None

    def start(self) -> None:
        if not config.enable_teams_integration:
            logger.info("TeamsPresenceService desabilitado por configuração.")
            return

        logger.info("Iniciando TeamsPresenceService...")

        self.provider = self._build_provider()

        self.event_bus.subscribe(Event.USER_PRESENT, self.on_user_present)
        self.event_bus.subscribe(Event.USER_AWAY, self.on_user_away)

        logger.info("TeamsPresenceService iniciado com sucesso.")

    def on_user_present(self, payload: dict[str, Any]) -> None:
        if not config.teams_set_available_on_present:
            return

        self._set_presence(
            availability=config.teams_available_availability,
            activity=config.teams_available_activity,
            reason="USER_PRESENT",
        )

    def on_user_away(self, payload: dict[str, Any]) -> None:
        if not config.teams_set_away_on_away:
            return

        self._set_presence(
            availability=config.teams_away_availability,
            activity=config.teams_away_activity,
            reason="USER_AWAY",
        )

    def _set_presence(
        self,
        availability: str,
        activity: str,
        reason: str,
    ) -> None:
        if self.provider is None:
            logger.warning("Teams provider não inicializado.")
            return

        desired_presence = (availability, activity)

        if self.last_presence == desired_presence:
            logger.debug(
                f"Presença Teams já está em {availability}/{activity}. Ignorando."
            )
            return

        logger.info(
            f"Atualizando presença Teams por {reason}: "
            f"{availability}/{activity}"
        )

        success = self.provider.set_presence(
            availability=availability,
            activity=activity,
        )

        if success:
            self.last_presence = desired_presence
            logger.info("Presença Teams atualizada com sucesso.")
        else:
            logger.warning("Falha ao atualizar presença Teams.")

    def _build_provider(self) -> TeamsProvider:
        if config.teams_provider == "mock":
            return MockTeamsProvider()

        if config.teams_provider == "graph":
            return GraphTeamsProvider()

        logger.warning(
            f"Teams provider desconhecido: {config.teams_provider}. "
            "Usando mock."
        )

        return MockTeamsProvider()