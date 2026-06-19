import time
from threading import Thread, Event as ThreadingEvent
from typing import Optional

import cv2

from app.core.config import config
from app.core.event_bus import EventBus
from app.core.events import Event
from app.core.logger import logger


class CameraService:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.capture: Optional[cv2.VideoCapture] = None
        self.thread: Optional[Thread] = None
        self.stop_event = ThreadingEvent()
        self.is_running = False

    def start(self) -> None:
        if self.is_running:
            logger.warning("CameraService já está rodando.")
            return

        logger.info("Iniciando CameraService...")
        self.event_bus.emit(
            Event.CAMERA_STARTING,
            {
                "camera_index": config.camera_index,
                "camera_backend": config.camera_backend,
            },
        )

        backend = self._resolve_backend(config.camera_backend)

        if backend is None:
            logger.info("Abrindo câmera em modo automático.")
            self.capture = cv2.VideoCapture(config.camera_index)
        else:
            logger.info(f"Abrindo câmera com backend: {config.camera_backend}")
            self.capture = cv2.VideoCapture(config.camera_index, backend)

        if not self.capture.isOpened():
            message = (
                f"Não foi possível abrir a câmera no índice {config.camera_index} "
                f"com backend {config.camera_backend}"
            )
            logger.error(message)
            self.event_bus.emit(Event.CAMERA_ERROR, {"message": message})
            return

        self._configure_camera()
        self._warm_up_camera()

        self.stop_event.clear()
        self.is_running = True

        self.thread = Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

        logger.info("CameraService iniciado com sucesso.")
        self.event_bus.emit(
            Event.CAMERA_STARTED,
            {
                "camera_index": config.camera_index,
                "camera_backend": config.camera_backend,
                "frame_width": config.frame_width,
                "frame_height": config.frame_height,
                "target_fps": config.target_fps,
            },
        )

    def stop(self) -> None:
        if not self.is_running:
            return

        logger.info("Encerrando CameraService...")

        self.stop_event.set()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

        if self.capture:
            self.capture.release()
            self.capture = None

        self.is_running = False

        logger.info("CameraService encerrado.")
        self.event_bus.emit(Event.CAMERA_STOPPED, {"message": "Câmera encerrada"})

    def _capture_loop(self) -> None:
        frame_interval = 1 / max(config.target_fps, 1)
        frame_count = 0
        consecutive_failures = 0

        while not self.stop_event.is_set():
            if self.capture is None:
                break

            success, frame = self.capture.read()

            if not success or frame is None:
                consecutive_failures += 1

                message = (
                    "Falha ao capturar frame da câmera. "
                    f"Falhas consecutivas: {consecutive_failures}"
                )

                logger.warning(message)
                self.event_bus.emit(Event.CAMERA_ERROR, {"message": message})

                if consecutive_failures >= 5:
                    logger.error("Muitas falhas consecutivas na câmera. Mantendo serviço ativo, mas sem frames.")

                time.sleep(1)
                continue

            consecutive_failures = 0
            frame_count += 1

            self.event_bus.emit(
                Event.FRAME_CAPTURED,
                {
                    "frame": frame,
                    "frame_count": frame_count,
                    "timestamp": time.time(),
                },
            )

            time.sleep(frame_interval)

    def _configure_camera(self) -> None:
        if self.capture is None:
            return

        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, config.frame_width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config.frame_height)
        self.capture.set(cv2.CAP_PROP_FPS, config.target_fps)

        try:
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            logger.debug("CAP_PROP_BUFFERSIZE não suportado por este backend.")

        actual_width = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        actual_fps = self.capture.get(cv2.CAP_PROP_FPS)

        logger.info(
            f"Configuração real da câmera: "
            f"{actual_width}x{actual_height} @ {actual_fps} FPS"
        )

    def _warm_up_camera(self) -> None:
        if self.capture is None:
            return

        logger.info("Aquecendo câmera...")

        for attempt in range(5):
            success, frame = self.capture.read()

            if success and frame is not None:
                logger.info(f"Câmera respondeu no warm-up. Tentativa: {attempt + 1}")
                return

            logger.warning(f"Warm-up da câmera falhou. Tentativa: {attempt + 1}")
            time.sleep(0.5)

        logger.warning("Warm-up finalizado sem frame válido.")

    def _resolve_backend(self, backend_name: str):
        backend_name = backend_name.upper()

        if backend_name == "AUTO":
            return None

        if backend_name == "DSHOW":
            return cv2.CAP_DSHOW

        if backend_name == "MSMF":
            return cv2.CAP_MSMF

        logger.warning(f"Backend de câmera desconhecido: {backend_name}. Usando AUTO.")
        return None