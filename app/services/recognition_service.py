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

        logger.info(f"Modelo facial carregado. Labels: {self.labels}")

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
            self._recognize_face(
                index=index,
                face_data=face_data,
                faces_count=len(faces),
                frame_count=payload.get("frame_count"),
            )

    def _recognize_face(
        self,
        index: int,
        face_data: dict[str, Any],
        faces_count: int,
        frame_count: int | None,
    ) -> None:
        face_image = face_data.get("face_image")
        face_box = face_data.get("box")

        if face_image is None:
            return

        label_id, confidence = self.recognizer.predict(face_image)

        predicted_user = self.labels.get(str(label_id), "unknown").lower()

        authorized_threshold = config.recognition_authorized_threshold
        unknown_threshold = config.recognition_unknown_threshold

        recognition_payload = {
            "face_index": index,
            "faces_count": faces_count,
            "predicted_user": predicted_user,
            "authorized_user": config.authorized_user,
            "confidence": float(confidence),
            "authorized_threshold": authorized_threshold,
            "unknown_threshold": unknown_threshold,
            "frame_count": frame_count,
            "main_face": face_box,
        }

        if self._is_authorized_user(
            predicted_user=predicted_user,
            confidence=confidence,
            authorized_threshold=authorized_threshold,
            face_box=face_box,
        ):
            self._emit_identity_recognized(
                predicted_user=predicted_user,
                index=index,
                confidence=confidence,
                payload=recognition_payload,
            )
            return

        if self._is_unknown(
            confidence=confidence,
            unknown_threshold=unknown_threshold,
        ):
            self._emit_identity_unknown(
                predicted_user=predicted_user,
                index=index,
                confidence=confidence,
                payload=recognition_payload,
            )
            return

        self._emit_identity_uncertain(
            predicted_user=predicted_user,
            index=index,
            confidence=confidence,
            authorized_threshold=authorized_threshold,
            unknown_threshold=unknown_threshold,
            payload=recognition_payload,
        )

    def _is_authorized_user(
        self,
        predicted_user: str,
        confidence: float,
        authorized_threshold: float,
        face_box: dict[str, Any] | None,
    ) -> bool:
        if predicted_user != config.authorized_user:
            return False

        if confidence > authorized_threshold:
            return False

        if not face_box:
            return False

        face_width = face_box.get("width", 0)

        if face_width < config.min_authorized_face_width:
            logger.info(
                "Autorização recusada: rosto pequeno demais "
                f"| width={face_width} | mínimo={config.min_authorized_face_width}"
            )
            return False

        return True


    def _is_unknown(
        self,
        confidence: float,
        unknown_threshold: float,
    ) -> bool:
        return confidence >= unknown_threshold

    def _emit_identity_recognized(
        self,
        predicted_user: str,
        index: int,
        confidence: float,
        payload: dict[str, Any],
    ) -> None:
        logger.info(
            f"Identidade reconhecida: {predicted_user} "
            f"| face_index={index} "
            f"| confidence={confidence:.2f}"
        )

        self.event_bus.emit(
            Event.IDENTITY_RECOGNIZED,
            payload,
        )

    def _emit_identity_unknown(
        self,
        predicted_user: str,
        index: int,
        confidence: float,
        payload: dict[str, Any],
    ) -> None:
        logger.info(
            f"Identidade desconhecida. "
            f"Predito={predicted_user} "
            f"| face_index={index} "
            f"| confidence={confidence:.2f}"
        )

        self.event_bus.emit(
            Event.IDENTITY_UNKNOWN,
            payload,
        )

    def _emit_identity_uncertain(
        self,
        predicted_user: str,
        index: int,
        confidence: float,
        authorized_threshold: float,
        unknown_threshold: float,
        payload: dict[str, Any],
    ) -> None:
        logger.info(
            f"Identidade incerta. "
            f"Predito={predicted_user} "
            f"| face_index={index} "
            f"| confidence={confidence:.2f} "
            f"| faixa_incerta={authorized_threshold}-{unknown_threshold}"
        )

        self.event_bus.emit(
            Event.IDENTITY_UNCERTAIN,
            payload,
        )