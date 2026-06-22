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

        self.latest_faces: list[dict[str, Any]] = []
        self.latest_identities: dict[int, dict[str, Any]] = {}

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

        self.event_bus.subscribe(Event.IDENTITY_RECOGNIZED, self.on_identity_recognized)
        self.event_bus.subscribe(Event.IDENTITY_UNKNOWN, self.on_identity_unknown)
        self.event_bus.subscribe(Event.IDENTITY_UNCERTAIN, self.on_identity_uncertain)

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
        faces = payload.get("faces", [])
        main_face = payload.get("main_face")

        sanitized_faces = []

        if faces:
            for index, face_data in enumerate(faces):
                box = face_data.get("box")

                if not box:
                    continue

                sanitized_faces.append(
                    {
                        "index": index,
                        "box": box,
                        "area": face_data.get("area", 0),
                    }
                )

        elif main_face:
            sanitized_faces.append(
                {
                    "index": 0,
                    "box": main_face,
                    "area": main_face.get("width", 0) * main_face.get("height", 0),
                }
            )

        with self.lock:
            self.latest_faces = sanitized_faces
            self.last_face_detected_at = time.time()

    def on_face_lost(self, payload: dict[str, Any]) -> None:
        # Não limpamos imediatamente para evitar flicker visual.
        # O loop visual decide quando esconder com base no tempo.
        pass

    def on_identity_recognized(self, payload: dict[str, Any]) -> None:
        self._store_identity(
            payload=payload,
            status="AUTHORIZED",
            color=(0, 255, 0),
        )

    def on_identity_unknown(self, payload: dict[str, Any]) -> None:
        self._store_identity(
            payload=payload,
            status="UNKNOWN",
            color=(0, 0, 255),
        )

    def on_identity_uncertain(self, payload: dict[str, Any]) -> None:
        self._store_identity(
            payload=payload,
            status="UNCERTAIN",
            color=(0, 255, 255),
        )

    def _store_identity(
        self,
        payload: dict[str, Any],
        status: str,
        color: tuple[int, int, int],
    ) -> None:
        face_index = payload.get("face_index")

        if face_index is None:
            return

        identity_data = {
            "status": status,
            "predicted_user": payload.get("predicted_user", "unknown"),
            "confidence": payload.get("confidence"),
            "threshold": payload.get("threshold"),
            "timestamp": time.time(),
            "color": color,
        }

        with self.lock:
            self.latest_identities[int(face_index)] = identity_data

    def _window_loop(self) -> None:
        while not self.stop_event.is_set():
            frame_to_show = None
            frame_count = 0
            faces = []
            identities = {}
            face_is_recent = False

            with self.lock:
                if self.latest_frame is not None:
                    frame_to_show = self.latest_frame.copy()
                    frame_count = self.latest_frame_count
                    faces = list(self.latest_faces)
                    identities = dict(self.latest_identities)

                    if self.last_face_detected_at is not None:
                        face_is_recent = (
                            time.time() - self.last_face_detected_at
                            <= config.face_lost_grace_seconds
                        )

            if frame_to_show is not None:
                self._draw_overlay(
                    frame=frame_to_show,
                    frame_count=frame_count,
                    faces=faces if face_is_recent else [],
                    identities=identities,
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
        faces: list[dict[str, Any]],
        identities: dict[int, dict[str, Any]],
        face_is_recent: bool,
    ) -> None:
        current_state = self.state_manager.get_state()

        self._draw_faces(frame, faces, identities)

        status_text = "FACE_RECENT" if face_is_recent else "NO_FACE"
        state_text = f"State: {current_state}"
        frame_text = f"Frame: {frame_count}"
        faces_text = f"Faces: {len(faces)}"

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
            faces_text,
            (10, 120),
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

    def _draw_faces(
        self,
        frame,
        faces: list[dict[str, Any]],
        identities: dict[int, dict[str, Any]],
    ) -> None:
        now = time.time()
        identity_ttl_seconds = 5

        for face in faces:
            index = face.get("index", 0)
            box = face.get("box", {})

            x = int(box.get("x", 0))
            y = int(box.get("y", 0))
            width = int(box.get("width", 0))
            height = int(box.get("height", 0))

            identity = identities.get(index)

            if identity and now - identity.get("timestamp", 0) <= identity_ttl_seconds:
                color = identity.get("color", (255, 255, 255))
                label = self._build_identity_label(index, identity)
            else:
                color = (255, 255, 255)
                label = f"Face {index} | pending"

            cv2.rectangle(
                frame,
                (x, y),
                (x + width, y + height),
                color,
                2,
            )

            label_y = max(y - 10, 25)

            cv2.putText(
                frame,
                label,
                (x, label_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2,
            )

    def _build_identity_label(
        self,
        index: int,
        identity: dict[str, Any],
    ) -> str:
        status = identity.get("status", "UNKNOWN")
        user = identity.get("predicted_user", "unknown")
        confidence = identity.get("confidence")

        if confidence is None:
            return f"Face {index} | {status} | {user}"

        return f"Face {index} | {status} | {user} | conf={confidence:.1f}"