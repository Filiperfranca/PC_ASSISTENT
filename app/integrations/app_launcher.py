import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from app.core.config import config
from app.core.logger import logger


class AppLauncher:
    def __init__(self):
        self.apps_config_path = Path(config.startup_apps_config)

    def launch_startup_apps(self) -> None:
        apps = self._load_apps_config()

        if not apps:
            logger.warning("Nenhum app configurado para inicialização.")
            return

        for app in apps:
            if not app.get("enabled", True):
                logger.info(f"App desabilitado no startup: {app.get('name')}")
                continue

            self._launch_app(app)

            if config.startup_app_delay_seconds > 0:
                time.sleep(config.startup_app_delay_seconds)

    def _load_apps_config(self) -> list[dict[str, Any]]:
        if not self.apps_config_path.exists():
            logger.warning(
                f"Arquivo de apps de startup não encontrado: {self.apps_config_path}"
            )
            return []

        try:
            with open(self.apps_config_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, list):
                logger.warning("Configuração de apps deve ser uma lista JSON.")
                return []

            return data

        except Exception as error:
            logger.exception(f"Erro ao carregar apps de startup: {error}")
            return []

    def _launch_app(self, app: dict[str, Any]) -> None:
        app_name = app.get("name", "App sem nome")
        app_type = app.get("type", "process")
        target = app.get("target")
        args = app.get("args", [])

        if not target:
            logger.warning(f"App sem target configurado: {app_name}")
            return

        try:
            logger.info(f"Abrindo app de startup: {app_name} | type={app_type}")

            if app_type == "uri":
                os.startfile(target)
                return

            if app_type == "path":
                os.startfile(target)
                return

            if app_type == "process":
                command = [target] + args
                subprocess.Popen(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    shell=False,
                )
                return

            logger.warning(
                f"Tipo de app desconhecido: {app_type} | app={app_name}"
            )

        except Exception as error:
            logger.exception(f"Erro ao abrir app {app_name}: {error}")
