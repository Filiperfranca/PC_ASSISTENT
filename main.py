import time
import signal

from app.core.event_bus import EventBus
from app.core.events import Event
from app.core.logger import logger
from app.core.state_manager import StateManager
from app.core.states import State

from app.services.camera_service import CameraService
from app.services.detection_service import DetectionService
from app.services.presence_service import PresenceService
from app.services.system_service import SystemService
from app.services.health_service import HealthService
from app.services.debug_window_service import DebugWindowService
from app.services.recognition_service import RecognitionService
from app.services.security_service import SecurityService
from app.services.prompt_service import PromptService


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
    detection_service = DetectionService(event_bus)
    presence_service = PresenceService(event_bus)
    system_service = SystemService(event_bus)
    health_service = HealthService(event_bus, state_manager)
    debug_window_service = DebugWindowService(event_bus, state_manager)
    recognition_service = RecognitionService(event_bus)
    security_service = SecurityService(event_bus)
    prompt_service = PromptService(event_bus)
    

    def on_state_changed(payload):
        logger.info(
            f"Evento STATE_CHANGED recebido: "
            f"{payload['old_state']} -> {payload['new_state']}"
        )

    def on_camera_started(payload):
        logger.info(f"Câmera iniciada: {payload}")

    def on_camera_error(payload):
        logger.error(f"Erro de câmera recebido: {payload}")

    def on_user_present(payload):
        logger.info(f"USER_PRESENT recebido: {payload}")
        state_manager.set_state(
            State.USER_PRESENT,
            reason=payload.get("reason", ""),
        )

    def on_user_away(payload):
        logger.info(f"USER_AWAY recebido: {payload}")
        state_manager.set_state(
            State.USER_AWAY,
            reason=payload.get("reason", ""),
        )
    def on_identity_recognized(payload):
        logger.info(f"IDENTITY_RECOGNIZED recebido: {payload}")

    def on_identity_unknown(payload):
        logger.warning(f"IDENTITY_UNKNOWN recebido: {payload}")

    def on_identity_uncertain(payload):
        logger.warning(f"IDENTITY_UNCERTAIN recebido: {payload}")
    def on_security_alert(payload):
        logger.error(f"SECURITY_ALERT recebido: {payload}")
    
    def on_security_suspicious(payload):
        logger.warning(f"SECURITY_SUSPICIOUS recebido: {payload}")
    
    def on_multiple_faces_detected(payload):
        logger.warning(f"MULTIPLE_FACES_DETECTED recebido: {payload}")


    def on_multiple_faces_confirmed(payload):
        logger.warning(f"MULTIPLE_FACES_CONFIRMED recebido: {payload}")



    event_bus.subscribe(Event.STATE_CHANGED, on_state_changed)
    event_bus.subscribe(Event.CAMERA_STARTED, on_camera_started)
    event_bus.subscribe(Event.CAMERA_ERROR, on_camera_error)
    event_bus.subscribe(Event.USER_PRESENT, on_user_present)
    event_bus.subscribe(Event.USER_AWAY, on_user_away)
    event_bus.subscribe(Event.IDENTITY_RECOGNIZED, on_identity_recognized)
    event_bus.subscribe(Event.IDENTITY_UNKNOWN, on_identity_unknown)
    event_bus.subscribe(Event.IDENTITY_UNCERTAIN, on_identity_uncertain)
    event_bus.subscribe(Event.SECURITY_ALERT, on_security_alert)
    event_bus.subscribe(Event.SECURITY_SUSPICIOUS, on_security_suspicious)
    event_bus.subscribe(Event.MULTIPLE_FACES_DETECTED, on_multiple_faces_detected)
    event_bus.subscribe(Event.MULTIPLE_FACES_CONFIRMED, on_multiple_faces_confirmed)

    event_bus.emit(Event.SYSTEM_BOOT, {"message": "Sistema inicializado"})
    state_manager.set_state(State.READY, reason="Core inicializado com sucesso")

    detection_service.start()
    recognition_service.start()
    presence_service.start()
    system_service.start()
    security_service.start()
    prompt_service.start()
    health_service.start()
    debug_window_service.start()
    camera_service.start()

    logger.info("PresenceAgent rodando. Pressione CTRL+C para encerrar.")

    try:
        while running:
            time.sleep(1)

    finally:
        logger.info("Encerrando PresenceAgent...")

        camera_service.stop()
        debug_window_service.stop()
        health_service.stop()

        state_manager.set_state(
            State.SHUTDOWN,
            reason="Encerramento solicitado",
        )

        event_bus.emit(
            Event.SYSTEM_SHUTDOWN,
            {"message": "Sistema encerrado"},
        )

        logger.info("PresenceAgent encerrado.")


if __name__ == "__main__":
    main()