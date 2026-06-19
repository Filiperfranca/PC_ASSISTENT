import time
import signal

from app.core.event_bus import EventBus
from app.core.events import Event
from app.core.logger import logger
from app.core.state_manager import StateManager
from app.core.states import State
from app.services.camera_service import CameraService


running = True


def handle_shutdown(signum, frame):
    global running
    running = False


def main():
    global running

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    logger.info("Iniciando PresenceAgent...")

    event_bus = EventBus()
    state_manager = StateManager(event_bus)
    camera_service = CameraService(event_bus)

    frame_counter = {"count": 0}

    def on_state_changed(payload):
        logger.info(
            f"Evento STATE_CHANGED recebido: "
            f"{payload['old_state']} -> {payload['new_state']}"
        )

    def on_camera_started(payload):
        logger.info(f"Câmera iniciada: {payload}")

    def on_camera_error(payload):
        logger.error(f"Erro de câmera recebido: {payload}")

    def on_frame_captured(payload):
        frame_counter["count"] += 1

        if frame_counter["count"] % 30 == 0:
            logger.info(f"Frames capturados até agora: {frame_counter['count']}")

    event_bus.subscribe(Event.STATE_CHANGED, on_state_changed)
    event_bus.subscribe(Event.CAMERA_STARTED, on_camera_started)
    event_bus.subscribe(Event.CAMERA_ERROR, on_camera_error)
    event_bus.subscribe(Event.FRAME_CAPTURED, on_frame_captured)

    event_bus.emit(Event.SYSTEM_BOOT, {"message": "Sistema inicializado"})
    state_manager.set_state(State.READY, reason="Core inicializado com sucesso")

    camera_service.start()

    logger.info("PresenceAgent rodando. Pressione CTRL+C para encerrar.")

    try:
        while running:
            time.sleep(1)
    finally:
        logger.info("Encerrando PresenceAgent...")

        camera_service.stop()

        state_manager.set_state(State.SHUTDOWN, reason="Encerramento solicitado")
        event_bus.emit(Event.SYSTEM_SHUTDOWN, {"message": "Sistema encerrado"})

        logger.info("PresenceAgent encerrado.")


if __name__ == "__main__":
    main()