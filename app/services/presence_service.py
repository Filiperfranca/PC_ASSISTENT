import time
from typing import Any

from app.core.config import config
from app.core.event_bus import EventBus
from app.core.events import Event
from app.core.logger import logger


class PresenceService:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

        self.last_face_detected_at: float | None = None
        self.first_face_detected_at: float | None = None

        self.user_is_present = False
        self.user_is_away = False

        self.face_loss_logged = False

    def start(self) -> None:
        logger.info("Iniciando PresenceService...")

        self.event_bus.subscribe(Event.FACE_DETECTED, self.on_face_detected)
        self.event_bus.subscribe(Event.FACE_LOST, self.on_face_lost)

        logger.info("PresenceService iniciado com sucesso.")

    def on_face_detected(self, payload: dict[str, Any]) -> None:
        now = time.time()

        self.last_face_detected_at = now
        self.face_loss_logged = False

        if self.first_face_detected_at is None:
            self.first_face_detected_at = now
            logger.info("Primeiro rosto detectado. Iniciando confirmação de presença.")

        visible_duration = now - self.first_face_detected_at

        if (
            not self.user_is_present
            and visible_duration >= config.user_present_confirm_seconds
        ):
            self._set_user_present(
                reason=f"Rosto confirmado por {visible_duration:.1f}s"
            )

    def on_face_lost(self, payload: dict[str, Any]) -> None:
        now = time.time()

        if self.last_face_detected_at is None:
            return

        time_since_last_face = now - self.last_face_detected_at

        if time_since_last_face < config.face_lost_grace_seconds:
            return

        if not self.face_loss_logged:
            logger.info(
                f"Rosto ausente há {time_since_last_face:.1f}s. "
                "Passou da margem de tolerância."
            )
            self.face_loss_logged = True

        self.first_face_detected_at = None

        if (
            self.user_is_present
            and time_since_last_face >= config.user_away_seconds
        ):
            self._set_user_away(
                reason=f"Rosto ausente por {time_since_last_face:.1f}s"
            )

    def _set_user_present(self, reason: str = "") -> None:
        if self.user_is_present:
            return

        self.user_is_present = True
        self.user_is_away = False

        logger.info(f"Usuário PRESENTE. {reason}")

        self.event_bus.emit(
            Event.USER_PRESENT,
            {
                "timestamp": time.time(),
                "reason": reason,
            },
        )

    def _set_user_away(self, reason: str = "") -> None:
        if self.user_is_away:
            return

        self.user_is_present = False
        self.user_is_away = True

        logger.info(f"Usuário AUSENTE. {reason}")

        self.event_bus.emit(
            Event.USER_AWAY,
            {
                "timestamp": time.time(),
                "reason": reason,
            },
        )