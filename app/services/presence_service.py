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
        self.last_face_lost_at: float | None = None

        self.present_candidate_started_at: float | None = None
        self.away_candidate_started_at: float | None = None

        self.user_is_present = False
        self.user_is_away = False

        self.face_is_currently_seen = False

        self.present_candidate_logged = False
        self.away_candidate_logged = False

    def start(self) -> None:
        logger.info("Iniciando PresenceService...")

        self.event_bus.subscribe(Event.FACE_DETECTED, self.on_face_detected)
        self.event_bus.subscribe(Event.FACE_LOST, self.on_face_lost)

        logger.info("PresenceService iniciado com sucesso.")

    def on_face_detected(self, payload: dict[str, Any]) -> None:
        now = time.time()

        self.last_face_detected_at = now
        self.last_face_lost_at = None
        self.away_candidate_started_at = None
        self.away_candidate_logged = False

        if not self.face_is_currently_seen:
            self.face_is_currently_seen = True
            logger.info("Sinal facial voltou.")

        if self.present_candidate_started_at is None:
            self.present_candidate_started_at = now
            self.present_candidate_logged = False

        visible_duration = now - self.present_candidate_started_at

        if not self.present_candidate_logged:
            logger.info("Candidato de presença iniciado.")
            self.present_candidate_logged = True

        if (
            not self.user_is_present
            and visible_duration >= config.user_present_confirm_seconds
        ):
            self._set_user_present(
                reason=f"Presença confirmada por {visible_duration:.1f}s"
            )

    def on_face_lost(self, payload: dict[str, Any]) -> None:
        now = time.time()

        self.last_face_lost_at = now

        if self.last_face_detected_at is None:
            return

        time_since_last_face = now - self.last_face_detected_at

        if time_since_last_face < config.face_lost_grace_seconds:
            return

        if self.face_is_currently_seen:
            self.face_is_currently_seen = False
            logger.info(
                f"Sinal facial ausente há {time_since_last_face:.1f}s. "
                "Margem de tolerância excedida."
            )

        self.present_candidate_started_at = None
        self.present_candidate_logged = False

        if self.away_candidate_started_at is None:
            self.away_candidate_started_at = now
            self.away_candidate_logged = False

        away_duration = now - self.away_candidate_started_at

        if not self.away_candidate_logged:
            logger.info("Candidato de ausência iniciado.")
            self.away_candidate_logged = True

        total_absence_duration = now - self.last_face_detected_at

        if (
            self.user_is_present
            and total_absence_duration >= config.user_away_seconds
        ):
            self._set_user_away(
                reason=f"Ausência confirmada por {total_absence_duration:.1f}s"
            )

    def _set_user_present(self, reason: str = "") -> None:
        if self.user_is_present:
            return

        self.user_is_present = True
        self.user_is_away = False

        self.away_candidate_started_at = None
        self.away_candidate_logged = False

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

        self.present_candidate_started_at = None
        self.present_candidate_logged = False

        logger.info(f"Usuário AUSENTE. {reason}")

        self.event_bus.emit(
            Event.USER_AWAY,
            {
                "timestamp": time.time(),
                "reason": reason,
            },
        )