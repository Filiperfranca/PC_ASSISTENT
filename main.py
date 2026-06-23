import signal
import time

from app.core.event_bus import EventBus
from app.core.events import Event
from app.core.logger import logger
from app.core.state_manager import StateManager
from app.core.states import State

from app.services.camera_service import CameraService
from app.services.debug_window_service import DebugWindowService
from app.services.detection_service import DetectionService
from app.services.health_service import HealthService
from app.services.presence_service import PresenceService
from app.services.prompt_service import PromptService
from app.services.recognition_service import RecognitionService
from app.services.security_service import SecurityService
from app.services.startup_assistant_service import StartupAssistantService
from app.services.system_service import SystemService
from app.services.teams_presence_service import TeamsPresenceService
from app.core.single_instance import SingleInstance


running = True


def handle_shutdown(signum, frame):
    global running
    running = False


def register_core_listeners(
    event_bus: EventBus,
    state_manager: StateManager,
) -> None:
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

    def on_security_suspicious(payload):
        logger.warning(f"SECURITY_SUSPICIOUS recebido: {payload}")

    def on_security_alert(payload):
        logger.error(f"SECURITY_ALERT recebido: {payload}")

    def on_multiple_faces_detected(payload):
        logger.warning(f"MULTIPLE_FACES_DETECTED recebido: {payload}")

    def on_multiple_faces_confirmed(payload):
        logger.warning(f"MULTIPLE_FACES_CONFIRMED recebido: {payload}")

    event_bus.subscribe(Event.STATE_CHANGED, on_state_changed)
    event_bus.subscribe(Event.CAMERA_STARTED, on_camera_started)
    event_bus.subscribe(Event.CAMERA_ERROR, on_camera_error)

    event_bus.subscribe(Event.USER_PRESENT, on_user_present)
    event_bus.subscribe(Event.USER_AWAY, on_user_away)

    event_bus.subscribe(Event.SECURITY_SUSPICIOUS, on_security_suspicious)
    event_bus.subscribe(Event.SECURITY_ALERT, on_security_alert)

    event_bus.subscribe(Event.MULTIPLE_FACES_DETECTED, on_multiple_faces_detected)
    event_bus.subscribe(Event.MULTIPLE_FACES_CONFIRMED, on_multiple_faces_confirmed)


def create_services(
    event_bus: EventBus,
    state_manager: StateManager,
) -> dict[str, object]:
    return {
        "detection": DetectionService(event_bus),
        "recognition": RecognitionService(event_bus),
        "presence": PresenceService(event_bus),
        "system": SystemService(event_bus),
        "security": SecurityService(event_bus),
        "prompt": PromptService(event_bus),
        "teams": TeamsPresenceService(event_bus),
        "startup_assistant": StartupAssistantService(event_bus),
        "health": HealthService(event_bus, state_manager),
        "debug_window": DebugWindowService(event_bus, state_manager),
        "camera": CameraService(event_bus),
    }


def start_services(services: dict[str, object]) -> None:
    services["detection"].start()
    services["recognition"].start()
    services["presence"].start()
    services["system"].start()
    services["security"].start()
    services["prompt"].start()
    services["teams"].start()
    services["startup_assistant"].start()
    services["health"].start()
    services["debug_window"].start()

    # A câmera deve iniciar por último, porque começa a emitir FRAME_CAPTURED.
    services["camera"].start()


def stop_services(services: dict[str, object]) -> None:
    # A câmera deve parar primeiro, para interromper emissão de eventos.
    services["camera"].stop()

    # Serviços auxiliares com janela/thread própria.
    services["debug_window"].stop()
    services["health"].stop()


def main():
    global running

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    single_instance = SingleInstance()

    if not single_instance.acquire():
        return

    services = None
    state_manager = None
    event_bus = None

    try:
        logger.info("Iniciando PresenceAgent...")

        event_bus = EventBus()
        state_manager = StateManager(event_bus)

        register_core_listeners(event_bus, state_manager)

        services = create_services(event_bus, state_manager)

        event_bus.emit(Event.SYSTEM_BOOT, {"message": "Sistema inicializado"})
        state_manager.set_state(State.READY, reason="Core inicializado com sucesso")

        start_services(services)

        logger.info("PresenceAgent rodando. Pressione CTRL+C para encerrar.")

        while running:
            time.sleep(1)

    finally:
        logger.info("Encerrando PresenceAgent...")

        if services is not None:
            stop_services(services)

        if state_manager is not None:
            state_manager.set_state(
                State.SHUTDOWN,
                reason="Encerramento solicitado",
            )

        if event_bus is not None:
            event_bus.emit(
                Event.SYSTEM_SHUTDOWN,
                {"message": "Sistema encerrado"},
            )

        logger.info("PresenceAgent encerrado.")

        single_instance.release()


if __name__ == "__main__":
    main()