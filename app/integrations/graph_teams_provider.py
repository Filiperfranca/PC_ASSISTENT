from pathlib import Path

import msal
import requests

from app.core.config import config
from app.core.logger import logger
from app.integrations.teams_provider import TeamsProvider


class GraphTeamsProvider(TeamsProvider):
    def __init__(self):
        self.authority = (
            f"https://login.microsoftonline.com/{config.teams_tenant_id}"
        )

        self.scopes = [
            "Presence.ReadWrite",
            "User.Read",
        ]

        self.token_cache_path = (
            Path("app") / "data" / "models" / "msal_token_cache.bin"
        )

        self.token_cache = msal.SerializableTokenCache()
        self._load_cache()

        self.app = msal.PublicClientApplication(
            client_id=config.teams_client_id,
            authority=self.authority,
            token_cache=self.token_cache,
        )

    def set_presence(self, availability: str, activity: str) -> bool:
        access_token = self._get_access_token()

        if not access_token:
            logger.error("Não foi possível obter token do Microsoft Graph.")
            return False

        user_id = config.teams_user_id or "me"

        if user_id == "me":
            user_id = self._get_me_id(access_token)

            if not user_id:
                logger.error("Não foi possível resolver o ID do usuário via /me.")
                return False

        session_id = config.teams_session_id or config.teams_client_id

        url = (
            f"https://graph.microsoft.com/v1.0/users/"
            f"{user_id}/presence/setPresence"
        )

        body = {
            "sessionId": session_id,
            "availability": availability,
            "activity": activity,
            "expirationDuration": config.teams_presence_expiration,
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        logger.info(
            "Enviando presença ao Microsoft Graph: "
            f"{availability}/{activity} | "
            f"expiration={config.teams_presence_expiration}"
        )

        response = requests.post(
            url,
            headers=headers,
            json=body,
            timeout=15,
        )

        if response.status_code in (200, 202):
            logger.info("Microsoft Graph setPresence executado com sucesso.")
            return True

        logger.error(
            "Erro no Microsoft Graph setPresence | "
            f"status={response.status_code} | body={response.text}"
        )
        return False

    def _get_access_token(self) -> str | None:
        accounts = self.app.get_accounts()

        result = None

        if accounts:
            result = self.app.acquire_token_silent(
                scopes=self.scopes,
                account=accounts[0],
            )

        if not result:
            flow = self.app.initiate_device_flow(scopes=self.scopes)

            if "user_code" not in flow:
                logger.error(f"Falha ao iniciar device flow: {flow}")
                return None

            logger.warning(flow["message"])

            result = self.app.acquire_token_by_device_flow(flow)

        self._save_cache()

        if "access_token" in result:
            return result["access_token"]

        logger.error(f"Falha ao obter token: {result}")
        return None

    def _get_me_id(self, access_token: str) -> str | None:
        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        response = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers=headers,
            timeout=15,
        )

        if response.status_code != 200:
            logger.error(
                "Erro ao chamar /me | "
                f"status={response.status_code} | body={response.text}"
            )
            return None

        data = response.json()
        return data.get("id")

    def _load_cache(self) -> None:
        if self.token_cache_path.exists():
            self.token_cache.deserialize(
                self.token_cache_path.read_text(encoding="utf-8")
            )

    def _save_cache(self) -> None:
        if self.token_cache.has_state_changed:
            self.token_cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.token_cache_path.write_text(
                self.token_cache.serialize(),
                encoding="utf-8",
            )