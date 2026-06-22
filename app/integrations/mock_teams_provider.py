from app.core.logger import logger
from app.integrations.teams_provider import TeamsProvider


class MockTeamsProvider(TeamsProvider):
    def set_presence(self, availability: str, activity: str) -> bool:
        logger.info(
            "MockTeamsProvider: presença do Teams seria alterada para "
            f"{availability}/{activity}"
        )
        return True