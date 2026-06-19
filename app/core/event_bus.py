from collections import defaultdict
from typing import Callable, Any

from app.core.logger import logger


class EventBus:
    def __init__(self):
        self._listeners: dict[str, list[Callable[[dict[str, Any]], None]]] = defaultdict(list)

    def subscribe(self, event_name: str, callback: Callable[[dict[str, Any]], None]) -> None:
        self._listeners[event_name].append(callback)
        logger.debug(f"Listener registrado para evento: {event_name}")

    def emit(self, event_name: str, payload: dict[str, Any] | None = None) -> None:
        if payload is None:
            payload = {}

        logger.debug(f"Evento emitido: {event_name} | Payload: {payload}")

        listeners = self._listeners.get(event_name, [])

        for callback in listeners:
            try:
                callback(payload)
            except Exception as error:
                logger.exception(
                    f"Erro ao executar listener do evento {event_name}: {error}"
                )