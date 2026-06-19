import time
import signal
import sys

from app.core.event_bus import EventBus
from app.core.events import Event
from app.core.logger import logger
from app.core.state_manager import StateManager
from app.core.states import State


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

    def on_state_changed(payload):
        logger.info(
            f"Evento STATE_CHANGED recebido: "
            f"{payload['old_state']} -> {payload['new_state']}"
        )

    event_bus.subscribe(Event.STATE_CHANGED, on_state_changed)

    event_bus.emit(Event.SYSTEM_BOOT, {"message": "Sistema inicializado"})
    state_manager.set_state(State.READY, reason="Core inicializado com sucesso")

    logger.info("PresenceAgent rodando. Pressione CTRL+C para encerrar.")

    try:
        while running:
            time.sleep(1)
    finally:
        logger.info("Encerrando PresenceAgent...")
        state_manager.set_state(State.SHUTDOWN, reason="Encerramento solicitado")
        event_bus.emit(Event.SYSTEM_SHUTDOWN, {"message": "Sistema encerrado"})
        logger.info("PresenceAgent encerrado.")


if __name__ == "__main__":
    main()