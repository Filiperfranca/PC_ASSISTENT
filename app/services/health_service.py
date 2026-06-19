import time
from threading import Thread, Event as ThreadingEvent
from typing import Any

from app.core.config import config
from app.core.event_bus import EventBus
from app.core.events import Event
from app.core.logger import logger
from app.core.state_manager import StateManager


class HealthService:
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager

        self.thread: Thread | None = None
        self.stop_event = ThreadingEvent()
        self.is_running = False

        self.started_at = time.time()

        self.camera_running = False
        self.camera_errors = 0

        self.user_present_events = 0
        self.user_away_events = 0

        self.last_user_present_at: float | None = None
        self.last_user_away_at: float | None = None
        self.last_camera_error_at: float | None = None

    def start(self) -> None:
        if not config.enable_health_service:
            logger.info("HealthService desabilitado por configuração.")
            return

        if self.is_running:
            logger.warning("HealthService já está rodando.")
            return

        logger.info("Iniciando HealthService...")

        self.event_bus.subscribe(Event.CAMERA_STARTED, self.on_camera_started)
        self.event_bus.subscribe(Event.CAMERA_STOPPED, self.on_camera_stopped)
        self.event_bus.subscribe(Event.CAMERA_ERROR, self.on_camera_error)
        self.event_bus.subscribe(Event.USER_PRESENT, self.on_user_present)
        self.event_bus.subscribe(Event.USER_AWAY, self.on_user_away)

        self.stop_event.clear()
        self.is_running = True

        self.thread = Thread(target=self._health_loop, daemon=True)
        self.thread.start()

        logger.info("HealthService iniciado com sucesso.")

    def stop(self) -> None:
        if not self.is_running:
            return

        logger.info("Encerrando HealthService...")

        self.stop_event.set()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3)

        self.is_running = False

        logger.info("HealthService encerrado.")

    def on_camera_started(self, payload: dict[str, Any]) -> None:
        self.camera_running = True

    def on_camera_stopped(self, payload: dict[str, Any]) -> None:
        self.camera_running = False

    def on_camera_error(self, payload: dict[str, Any]) -> None:
        self.camera_errors += 1
        self.last_camera_error_at = time.time()

    def on_user_present(self, payload: dict[str, Any]) -> None:
        self.user_present_events += 1
        self.last_user_present_at = time.time()

    def on_user_away(self, payload: dict[str, Any]) -> None:
        self.user_away_events += 1
        self.last_user_away_at = time.time()

    def _health_loop(self) -> None:
        interval = max(config.health_check_interval_seconds, 1)

        while not self.stop_event.is_set():
            self.stop_event.wait(interval)

            if self.stop_event.is_set():
                break

            self._log_health_status()

    def _log_health_status(self) -> None:
        uptime_seconds = int(time.time() - self.started_at)
        uptime = self._format_duration(uptime_seconds)

        current_state = self.state_manager.get_state()

        logger.info(
            "HealthCheck | "
            f"state={current_state} | "
            f"camera_running={self.camera_running} | "
            f"uptime={uptime} | "
            f"camera_errors={self.camera_errors} | "
            f"user_present_events={self.user_present_events} | "
            f"user_away_events={self.user_away_events}"
        )

    def _format_duration(self, total_seconds: int) -> str:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"