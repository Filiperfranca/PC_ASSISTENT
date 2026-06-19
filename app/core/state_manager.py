from datetime import datetime
from typing import Any

from app.core.events import Event
from app.core.logger import logger
from app.core.states import State
from app.core.event_bus import EventBus


class StateManager:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.current_state = State.BOOTING
        self.previous_state: State | None = None
        self.last_changed_at = datetime.now()

        logger.info(f"Estado inicial: {self.current_state}")

    def set_state(self, new_state: State, reason: str = "") -> None:
        if new_state == self.current_state:
            return

        old_state = self.current_state

        self.previous_state = old_state
        self.current_state = new_state
        self.last_changed_at = datetime.now()

        payload: dict[str, Any] = {
            "old_state": old_state,
            "new_state": new_state,
            "reason": reason,
            "changed_at": self.last_changed_at.isoformat(),
        }

        logger.info(
            f"Estado alterado: {old_state} -> {new_state}"
            + (f" | Motivo: {reason}" if reason else "")
        )

        self.event_bus.emit(Event.STATE_CHANGED, payload)

    def get_state(self) -> State:
        return self.current_state

    def is_state(self, state: State) -> bool:
        return self.current_state == state