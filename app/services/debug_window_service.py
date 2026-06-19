import time
from threading import Thread, Event as ThreadingEvent, Lock
from typing import Any

import cv2

from app.core.config import config
from app.core.event_bus import EventBus
from app.core.events import Event
from app.core.logger import logger
from app.core.state_manager import StateManager


class DebugWindowService:
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager

        self.thread: Thread | None = None
        self.stop_event = ThreadingEvent()
        self.lock = Lock()

        self.is_running = False

        self.latest_frame = None
        self.latest_frame_count = 0

        self.latest_face: dict[str, int] | None = None
        self.last_face_detected_at: float | None = None

        self.window_name = "PresenceAgent Debug"

    def start(self) -> None:
        if not config.enable_debug_window:
            logger.info("DebugWindowService desabilitado por configuração.")
            return

        if self.is_running:
            logger.warning("DebugWindowService já está rodando.")
            return

        logger.info("Iniciando DebugWindowService...")

        self.event_bus.subscribe(Event.FRAME_CAPTURED, self.on_frame_captured)
        self.event_bus.subscribe(Event.FACE_DETECTED, self.on_face_detected)
        self.event_bus.subscribe(Event.FACE_LOST, self.on_face_lost)

        self.stop_event.clear()
        self.is_running = True

        self.thread = Thread(target=self._window_loop, daemon=True)
        self.thread.start()

        logger.info("DebugWindowService iniciado com sucesso.")

    def stop(self) -> None:
        if not self.is_running:
            return

        logger.info("Encerrando DebugWindowService...")

        self.stop_event.set()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3)

        try:
            cv2.destroyWindow(self.window_name)
        except Exception:
            pass

        self.is_running = False

        logger.info("DebugWindowService encerrado.")

    def on_frame_captured(self, payload: dict[str, Any]) -> None:
        frame = payload.get("frame")
        frame_count = payload.get("frame_count", 0)

        if frame is None:
            return

        with self.lock:
            self.latest_frame = frame.copy()
            self.latest_frame_count = frame_count

    def on_face_detected(self, payload: dict[str, Any]) -> None:
        main_face = payload.get("main_face")

        if not main_face:
            return

        with self.lock:
            self.latest_face = main_face
            self.last_face_detected_at = time.time()

    def on_face_lost(self, payload: dict[str, Any]) -> None:
        # Não apagamos imediatamente a face para evitar flicker visual.
        # O loop visual decide quando esconder com base no tempo.
        pass

    def _window_loop(self) -> None:
        while not self.stop_event.is_set():
            frame_to_show = None
            frame_count = 0
            face = None
            face_is_recent = False

            with self.lock:
                if self.latest_frame is not None:
                    frame_to_show = self.latest_frame.copy()
                    frame_count = self.latest_frame_count
                    face = self.latest_face

                    if self.last_face_detected_at is not None:
                        face_is_recent = (
                            time.time() - self.last_face_detected_at
                            <= config.face_lost_grace_seconds
                        )

            if frame_to_show is not None:
                self._draw_overlay(
                    frame=frame_to_show,
                    frame_count=frame_count,
                    face=face if face_is_recent else None,
                    face_is_recent=face_is_recent,
                )

                cv2.imshow(self.window_name, frame_to_show)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                logger.info("Tecla Q pressionada. Fechando janela de debug.")
                self.stop_event.set()
                break

            time.sleep(0.01)

        cv2.destroyAllWindows()

    def _draw_overlay(
        self,
        frame,
        frame_count: int,
        face: dict[str, int] | None,
        face_is_recent: bool,
    ) -> None:
        current_state = self.state_manager.get_state()

        if face is not None:
            x = face["x"]
            y = face["y"]
            width = face["width"]
            height = face["height"]

            cv2.rectangle(
                frame,
                (x, y),
                (x + width, y + height),
                (0, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                "FACE",
                (x, max(y - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

        status_text = "FACE_RECENT" if face_is_recent else "NO_FACE"
        state_text = f"State: {current_state}"
        frame_text = f"Frame: {frame_count}"

        cv2.putText(
            frame,
            state_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        cv2.putText(
            frame,
            status_text,
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0) if face_is_recent else (0, 0, 255),
            2,
        )

        cv2.putText(
            frame,
            frame_text,
            (10, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        cv2.putText(
            frame,
            "Pressione Q para fechar debug",
            (10, frame.shape[0] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (200, 200, 200),
            2,
        )