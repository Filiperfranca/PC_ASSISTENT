from collections import defaultdict
from typing import Callable, Any

from app.core.logger import logger


class EventBus:
    def __init__(self):
        self._listeners: dict[str, list[Callable[[dict[str, Any]], None]]] = defaultdict(list)

    def subscribe(self, event_name: str, callback: Callable[[dict[str, Any]], None]) -> None:
        self._listeners[str(event_name)].append(callback)
        logger.debug(f"Listener registrado para evento: {event_name}")

    def emit(self, event_name: str, payload: dict[str, Any] | None = None) -> None:
        if payload is None:
            payload = {}

        event_name = str(event_name)
        logger.debug(f"Evento emitido: {event_name} | Payload: {self._summarize_payload(payload)}")

        listeners = self._listeners.get(event_name, [])

        for callback in listeners:
            try:
                callback(payload)
            except Exception as error:
                logger.exception(
                    f"Erro ao executar listener do evento {event_name}: {error}"
                )

    def _summarize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        summarized = {}

        for key, value in payload.items():
            if key in ("frame", "face_image"):
                shape = getattr(value, "shape", None)
                summarized[key] = f"<image shape={shape}>"

            elif key == "faces" and isinstance(value, list):
                summarized[key] = [
                    {
                        "box": item.get("box"),
                        "area": item.get("area"),
                        "face_image": f"<image shape={getattr(item.get('face_image'), 'shape', None)}>",
                    }
                    for item in value
                ]

            else:
                summarized[key] = value

        return summarized