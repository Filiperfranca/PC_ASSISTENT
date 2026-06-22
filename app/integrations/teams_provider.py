from abc import ABC, abstractmethod


class TeamsProvider(ABC):
    @abstractmethod
    def set_presence(self, availability: str, activity: str) -> bool:
        pass