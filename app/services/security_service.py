import time
from typing import Any

from app.core.config import config
from app.core.event_bus import EventBus
from app.core.events import Event
from app.core.logger import logger
from app.integrations.windows_integration import WindowsIntegration


class SecurityService:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

        self.last_authorized_seen_at: float | None = None

        self.unknown_started_at: float | None = None
        self.unknown_streak = 0
        self.unknown_alert_triggered = False

        self.multi_face_started_at: float | None = None
        self.last_multi_face_prompt_at: float | None = None
        self.multi_face_confirmed_for_current_event = False

    def start(self) -> None:
        if not config.enable_security_service:
            logger.info("SecurityService desabilitado por configuração.")
            return

        logger.info("Iniciando SecurityService...")

        self.event_bus.subscribe(Event.IDENTITY_RECOGNIZED, self.on_identity_recognized)
        self.event_bus.subscribe(Event.IDENTITY_UNKNOWN, self.on_identity_unknown)
        self.event_bus.subscribe(Event.IDENTITY_UNCERTAIN, self.on_identity_uncertain)
        self.event_bus.subscribe(Event.FACE_DETECTED, self.on_face_detected)
        self.event_bus.subscribe(Event.FACE_LOST, self.on_face_lost)
        self.event_bus.subscribe(Event.USER_AWAY, self.on_user_away)

        logger.info("SecurityService iniciado com sucesso.")

    def on_identity_recognized(self, payload: dict[str, Any]) -> None:
        predicted_user = payload.get("predicted_user")

        if predicted_user != config.authorized_user:
            return

        self.last_authorized_seen_at = time.time()
        self._reset_unknown_tracking()

        logger.debug(
            f"SecurityService: usuário autorizado reconhecido: {predicted_user}"
        )

    def on_identity_unknown(self, payload: dict[str, Any]) -> None:
        now = time.time()

        faces_count = payload.get("faces_count", 1)

        if faces_count >= 2:
            logger.info(
                "UNKNOWN recebido em cenário multi-face. "
                "Escalonamento de desconhecido ignorado; fluxo multi-face assumirá."
            )
            return

        if self._authorized_seen_recently(now):
            logger.debug(
                "UNKNOWN ignorado: usuário autorizado foi visto recentemente."
            )
            return

        main_face = payload.get("main_face") or {}
        face_width = main_face.get("width", 0)

        if face_width < config.min_security_face_width:
            logger.info(
                "UNKNOWN ignorado: rosto pequeno demais para ação de segurança "
                f"| width={face_width} | mínimo={config.min_security_face_width}"
            )
            return

        if self.unknown_started_at is None:
            self.unknown_started_at = now
            self.unknown_streak = 0
            self.unknown_alert_triggered = False

            logger.warning(
                "Pessoa desconhecida detectada. Entrando em estado de suspeita."
            )

            self.event_bus.emit(
                Event.SECURITY_SUSPICIOUS,
                {
                    "timestamp": now,
                    "reason": "UNKNOWN_PERSON_STARTED",
                    "recognition": payload,
                },
            )

        self.unknown_streak += 1
        unknown_duration = now - self.unknown_started_at

        logger.warning(
            "Suspeita em andamento | "
            f"duration={unknown_duration:.1f}s | "
            f"streak={self.unknown_streak}/{config.unknown_event_streak} | "
            f"confidence={payload.get('confidence'):.2f}"
        )

        should_alert = (
            unknown_duration >= config.unknown_confirm_seconds
            and self.unknown_streak >= config.unknown_event_streak
        )

        if not should_alert:
            return

        if self.unknown_alert_triggered:
            return

        self.unknown_alert_triggered = True

        alert_payload = {
            "timestamp": now,
            "reason": "UNKNOWN_PERSON_CONFIRMED",
            "unknown_duration": unknown_duration,
            "unknown_streak": self.unknown_streak,
            "recognition": payload,
        }

        logger.error("ALERTA: pessoa desconhecida confirmada.")

        self.event_bus.emit(Event.SECURITY_ALERT, alert_payload)

        if config.unknown_lock_enabled:
            logger.error(
                "UNKNOWN_LOCK_ENABLED=True. Bloqueando workstation por desconhecido."
            )
            WindowsIntegration.lock_workstation()
        else:
            logger.warning(
                "Simulação: workstation seria bloqueada por pessoa desconhecida."
            )

    def on_identity_uncertain(self, payload: dict[str, Any]) -> None:
        now = time.time()

        faces_count = payload.get("faces_count", 1)

        if faces_count >= 2:
            logger.info(
                "UNCERTAIN recebido em cenário multi-face. "
                "Escalonamento ignorado; fluxo multi-face assumirá."
            )
            return

        if self._authorized_seen_recently(now):
            logger.debug(
                "UNCERTAIN ignorado: usuário autorizado foi visto recentemente."
            )
            return

        logger.warning(
            "Identidade incerta sem usuário autorizado recente. "
            "Tratando como suspeita fraca."
        )

        self.on_identity_unknown(payload)

    def on_face_detected(self, payload: dict[str, Any]) -> None:
        if not config.multi_face_warning_enabled:
            return

        faces_count = payload.get("faces_count", 0)

        if faces_count < 2:
            self._reset_multi_face_tracking()
            return

        now = time.time()

        if self.multi_face_started_at is None:
            self.multi_face_started_at = now
            self.multi_face_confirmed_for_current_event = False

            logger.warning(
                f"Mais de um rosto detectado. faces_count={faces_count}"
            )

            self.event_bus.emit(
                Event.MULTIPLE_FACES_DETECTED,
                {
                    "timestamp": now,
                    "faces_count": faces_count,
                    "main_face": payload.get("main_face"),
                },
            )

        duration = now - self.multi_face_started_at

        if duration < config.multi_face_confirm_seconds:
            return

        if self.multi_face_confirmed_for_current_event:
            return

        if not self._can_prompt_multi_face(now):
            logger.info(
                "Multi-face confirmado, mas aviso ignorado por cooldown."
            )
            return

        self.multi_face_confirmed_for_current_event = True
        self.last_multi_face_prompt_at = now

        warning_payload = {
            "timestamp": now,
            "reason": "MULTIPLE_FACES_CONFIRMED",
            "faces_count": faces_count,
            "duration": duration,
            "main_face": payload.get("main_face"),
        }

        logger.warning(
            "Mais de um rosto confirmado. Futuramente perguntar se deseja bloquear."
        )

        self.event_bus.emit(Event.MULTIPLE_FACES_CONFIRMED, warning_payload)

        if config.multi_face_auto_lock_on_timeout:
            logger.error(
                "MULTI_FACE_AUTO_LOCK_ON_TIMEOUT=True. Bloqueando workstation."
            )
            WindowsIntegration.lock_workstation()
        else:
            logger.warning(
                "Simulação: perguntaria ao usuário se deseja bloquear a estação."
            )

    def on_face_lost(self, payload: dict[str, Any]) -> None:
        self._reset_multi_face_tracking()

    def on_user_away(self, payload: dict[str, Any]) -> None:
        self._reset_unknown_tracking()
        self._reset_multi_face_tracking()

    def _authorized_seen_recently(self, now: float) -> bool:
        if self.last_authorized_seen_at is None:
            return False

        elapsed = now - self.last_authorized_seen_at

        return elapsed <= config.authorized_grace_seconds

    def _can_prompt_multi_face(self, now: float) -> bool:
        if self.last_multi_face_prompt_at is None:
            return True

        elapsed = now - self.last_multi_face_prompt_at

        return elapsed >= config.multi_face_prompt_cooldown_seconds

    def _reset_unknown_tracking(self) -> None:
        self.unknown_started_at = None
        self.unknown_streak = 0
        self.unknown_alert_triggered = False

    def _reset_multi_face_tracking(self) -> None:
        self.multi_face_started_at = None
        self.multi_face_confirmed_for_current_event = False