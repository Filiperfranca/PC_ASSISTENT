import json
from pathlib import Path
from typing import Any

import cv2

from app.core.config import config
from app.core.event_bus import EventBus
from app.core.events import Event
from app.core.logger import logger


class RecognitionService:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

        self.model_path = Path("app") / "data" / "models" / "lbph_model.yml"
        self.labels_path = Path("app") / "data" / "models" / "labels.json"

        self.recognizer = None
        self.labels: dict[str, str] = {}

        self.processed_events = 0

    def start(self) -> None:
        if not config.enable_face_recognition:
            logger.info("RecognitionService desabilitado por configuração.")
            return

        logger.info("Iniciando RecognitionService...")

        self._load_model()

        self.event_bus.subscribe(Event.FACE_DETECTED, self.on_face_detected)

        logger.info("RecognitionService iniciado com sucesso.")

    def _load_model(self) -> None:
        if not self.model_path.exists():
            raise RuntimeError(f"Modelo facial não encontrado: {self.model_path}")

        if not self.labels_path.exists():
            raise RuntimeError(f"Labels faciais não encontrados: {self.labels_path}")

        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.recognizer.read(str(self.model_path))

        with open(self.labels_path, "r", encoding="utf-8") as file:
            self.labels = json.load(file)

        logger.info(
            f"Modelo facial carregado. Labels: {self.labels}"
        )

    def on_face_detected(self, payload: dict[str, Any]) -> None:
        if self.recognizer is None:
            return

        if not payload.get("is_stable", False):
            return

        self.processed_events += 1

        if (
            self.processed_events
            % max(config.recognition_process_every_n_events, 1)
            != 0
        ):
            return

        faces = payload.get("faces")

        if not faces:
            fallback_face_image = payload.get("face_image")

            if fallback_face_image is None:
                logger.debug("FACE_DETECTED recebido sem faces e sem face_image.")
                return

            faces = [
                {
                    "box": payload.get("main_face"),
                    "face_image": fallback_face_image,
                    "area": 0,
                }
            ]

        for index, face_data in enumerate(faces):
            face_image = face_data.get("face_image")
            face_box = face_data.get("box")

            if face_image is None:
                continue

            label_id, confidence = self.recognizer.predict(face_image)

            predicted_user = self.labels.get(str(label_id), "unknown").lower()

            recognition_payload = {
                "face_index": index,
                "faces_count": len(faces),
                "predicted_user": predicted_user,
                "authorized_user": config.authorized_user,
                "confidence": float(confidence),
                "threshold": config.recognition_confidence_threshold,
                "frame_count": payload.get("frame_count"),
                "main_face": face_box,
            }

            if (
                predicted_user == config.authorized_user
                and confidence <= config.recognition_confidence_threshold
            ):
                logger.info(
                    f"Identidade reconhecida: {predicted_user} "
                    f"| face_index={index} "
                    f"| confidence={confidence:.2f}"
                )

                self.event_bus.emit(
                    Event.IDENTITY_RECOGNIZED,
                    recognition_payload,
                )
                continue

            if confidence > config.recognition_confidence_threshold:
                logger.info(
                    f"Identidade desconhecida/incerta. "
                    f"Predito={predicted_user} "
                    f"| face_index={index} "
                    f"| confidence={confidence:.2f}"
                )

                self.event_bus.emit(
                    Event.IDENTITY_UNKNOWN,
                    recognition_payload,
                )
                continue

            logger.info(
                f"Identidade incerta. "
                f"Predito={predicted_user} "
                f"| face_index={index} "
                f"| confidence={confidence:.2f}"
            )

            self.event_bus.emit(
                Event.IDENTITY_UNCERTAIN,
                recognition_payload,
            )