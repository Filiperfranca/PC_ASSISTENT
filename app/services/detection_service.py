import time
from typing import Any

import cv2

from app.core.event_bus import EventBus
from app.core.events import Event
from app.core.logger import logger


class DetectionService:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.face_cascade = self._load_face_detector()

        self.last_face_seen_at: float | None = None
        self.face_currently_visible = False

        self.process_every_n_frames = 3

    def start(self) -> None:
        logger.info("Iniciando DetectionService...")

        self.event_bus.subscribe(Event.FRAME_CAPTURED, self.on_frame_captured)

        logger.info("DetectionService iniciado com sucesso.")

    def _load_face_detector(self):
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

        detector = cv2.CascadeClassifier(cascade_path)

        if detector.empty():
            raise RuntimeError(f"Não foi possível carregar detector facial: {cascade_path}")

        logger.info(f"Detector facial carregado: {cascade_path}")
        return detector

    def on_frame_captured(self, payload: dict[str, Any]) -> None:
        frame = payload.get("frame")
        frame_count = payload.get("frame_count", 0)

        if frame is None:
            return

        if frame_count % self.process_every_n_frames != 0:
            return

        faces = self._detect_faces(frame)

        if len(faces) > 0:
            self._handle_face_detected(faces, frame_count)
        else:
            self._handle_face_lost(frame_count)

    def _detect_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.08,
            minNeighbors=6,
            minSize=(90, 90),
        )

        min_area = 120 * 120
        faces = [face for face in faces if face[2] * face[3] >= min_area]

        return faces    

    def _handle_face_detected(self, faces, frame_count: int) -> None:
        self.last_face_seen_at = time.time()

        largest_face = max(faces, key=lambda face: face[2] * face[3])
        x, y, width, height = largest_face

        payload = {
            "frame_count": frame_count,
            "faces_count": len(faces),
            "main_face": {
                "x": int(x),
                "y": int(y),
                "width": int(width),
                "height": int(height),
            },
            "timestamp": self.last_face_seen_at,
        }

        if not self.face_currently_visible:
            logger.info(f"Rosto detectado: {payload['main_face']}")

        self.face_currently_visible = True
        self.event_bus.emit(Event.FACE_DETECTED, payload)

    def _handle_face_lost(self, frame_count: int) -> None:
        if self.face_currently_visible:
            logger.info("Rosto perdido.")

        self.face_currently_visible = False

        self.event_bus.emit(
            Event.FACE_LOST,
            {
                "frame_count": frame_count,
                "timestamp": time.time(),
            },
        )