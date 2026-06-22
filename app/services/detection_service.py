import time
from typing import Any

import cv2

from app.core.config import config
from app.core.event_bus import EventBus
from app.core.events import Event
from app.core.logger import logger


class DetectionService:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.face_cascade = self._load_face_detector()

        self.face_currently_visible = False

        self.consecutive_detections = 0
        self.consecutive_losses = 0

        self.last_main_face: dict[str, int] | None = None

    def start(self) -> None:
        logger.info("Iniciando DetectionService...")

        self.event_bus.subscribe(Event.FRAME_CAPTURED, self.on_frame_captured)

        logger.info("DetectionService iniciado com sucesso.")

    def _load_face_detector(self):
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

        detector = cv2.CascadeClassifier(cascade_path)

        if detector.empty():
            raise RuntimeError(
                f"Não foi possível carregar detector facial: {cascade_path}"
            )

        logger.info(f"Detector facial carregado: {cascade_path}")
        return detector

    def on_frame_captured(self, payload: dict[str, Any]) -> None:
        frame = payload.get("frame")
        frame_count = payload.get("frame_count", 0)

        if frame is None:
            return

        if frame_count % config.detection_process_every_n_frames != 0:
            return

        faces = self._detect_faces(frame)

        if len(faces) > 0:
            self._handle_detection(faces, frame_count, frame)
        else:
            self._handle_no_detection(frame_count)

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

    def _handle_detection(self, faces, frame_count: int, frame) -> None:
        self.consecutive_detections += 1
        self.consecutive_losses = 0

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_height, frame_width = frame.shape[:2]

        detected_faces = []

        for face_box in faces:
            x, y, width, height = face_box

            x = max(int(x), 0)
            y = max(int(y), 0)
            width = int(width)
            height = int(height)

            x2 = min(x + width, frame_width)
            y2 = min(y + height, frame_height)

            face_image = gray[y:y2, x:x2]

            if face_image.size == 0:
                continue

            face_image = cv2.resize(face_image, (200, 200))
            face_image = cv2.equalizeHist(face_image)

            detected_faces.append(
                {
                    "box": {
                        "x": x,
                        "y": y,
                        "width": x2 - x,
                        "height": y2 - y,
                    },
                    "face_image": face_image,
                    "area": (x2 - x) * (y2 - y),
                }
            )

        if not detected_faces:
            logger.debug("Nenhum recorte facial válido encontrado.")
            return

        main_detected_face = max(
            detected_faces,
            key=lambda item: item["area"],
        )

        self.last_main_face = main_detected_face["box"]

        logger.debug(
            f"Rosto detectado bruto. "
            f"Streak={self.consecutive_detections} | "
            f"Faces={len(detected_faces)} | "
            f"Main={self.last_main_face}"
        )

        is_stable = self.consecutive_detections >= config.face_detected_streak

        if not self.face_currently_visible and is_stable:
            self.face_currently_visible = True
            logger.info(f"Rosto estabilizado/detectado: {self.last_main_face}")

        self.event_bus.emit(
            Event.FACE_DETECTED,
            {
                "frame_count": frame_count,
                "faces_count": len(detected_faces),
                "faces": detected_faces,
                "main_face": self.last_main_face,
                "face_image": main_detected_face["face_image"],
                "timestamp": time.time(),
                "consecutive_detections": self.consecutive_detections,
                "is_stable": is_stable,
            },
        )

    def _handle_no_detection(self, frame_count: int) -> None:
        self.consecutive_losses += 1
        self.consecutive_detections = 0

        logger.debug(
            f"Rosto perdido bruto. "
            f"Streak={self.consecutive_losses}"
        )

        if (
            self.face_currently_visible
            and self.consecutive_losses >= config.face_lost_streak
        ):
            self.face_currently_visible = False
            logger.info(
                f"Rosto estabilizado/perdido após "
                f"{self.consecutive_losses} falhas consecutivas."
            )

        self.event_bus.emit(
            Event.FACE_LOST,
            {
                "frame_count": frame_count,
                "timestamp": time.time(),
                "consecutive_losses": self.consecutive_losses,
            },
        )