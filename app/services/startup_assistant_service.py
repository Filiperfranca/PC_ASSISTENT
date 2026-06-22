import ctypes
import json
import subprocess
from threading import Thread, Lock
from typing import Any

from app.core.config import config
from app.core.event_bus import EventBus
from app.core.events import Event
from app.core.logger import logger
from app.integrations.app_launcher import AppLauncher


class StartupAssistantService:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.app_launcher = AppLauncher()

        self.lock = Lock()
        self.sequence_started = False
        self.sequence_completed = False

    def start(self) -> None:
        if not config.enable_startup_assistant:
            logger.info("StartupAssistantService desabilitado por configuração.")
            return

        logger.info("Iniciando StartupAssistantService...")

        self.event_bus.subscribe(
            Event.IDENTITY_RECOGNIZED,
            self.on_identity_recognized,
        )

        logger.info("StartupAssistantService iniciado com sucesso.")
        logger.info("Aguardando reconhecimento do usuário autorizado para startup.")

    def on_identity_recognized(self, payload: dict[str, Any]) -> None:
        predicted_user = payload.get("predicted_user")
        confidence = payload.get("confidence")

        if config.startup_require_authorized_user:
            if predicted_user != config.authorized_user:
                logger.info(
                    "Startup ignorado: usuário reconhecido não é o autorizado "
                    f"| predicted_user={predicted_user}"
                )
                return

        with self.lock:
            if config.startup_run_once_per_session and self.sequence_completed:
                return

            if self.sequence_started:
                return

            self.sequence_started = True

        logger.info(
            "Usuário autorizado reconhecido para startup "
            f"| user={predicted_user} | confidence={confidence}"
        )

        thread = Thread(
            target=self._run_startup_sequence,
            args=(payload,),
            daemon=True,
        )
        thread.start()

    def _run_startup_sequence(self, payload: dict[str, Any]) -> None:
        try:
            logger.info("Executando sequência de startup assistant...")

            if config.startup_greeting_enabled:
                self._greet_user()

            if config.startup_open_apps_enabled:
                self.app_launcher.launch_startup_apps()

            logger.info("Sequência de startup assistant concluída.")

            with self.lock:
                self.sequence_completed = True

        except Exception as error:
            logger.exception(f"Erro na sequência de startup assistant: {error}")

        finally:
            with self.lock:
                self.sequence_started = False

    def _greet_user(self) -> None:
        message = config.startup_greeting_message
        mode = config.startup_greeting_mode

        logger.info(f"Saudação de startup: {message}")

        if mode == "log":
            return

        if mode == "voice":
            self._speak(message)
            return

        if mode == "popup":
            self._show_popup(message)
            return

        if mode == "both":
            self._speak(message)
            self._show_popup(message)
            return

        logger.warning(f"Modo de saudação desconhecido: {mode}")

    def _speak(self, message: str) -> None:
        try:
            escaped_message = json.dumps(message)

            command = (
                "Add-Type -AssemblyName System.Speech; "
                "$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f"$speak.Speak({escaped_message});"
            )

            subprocess.Popen(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    command,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=False,
            )

        except Exception as error:
            logger.exception(f"Erro ao executar saudação por voz: {error}")

    def _show_popup(self, message: str) -> None:
        try:
            title = "PresenceAgent"

            MB_OK = 0x00000000
            MB_ICONINFORMATION = 0x00000040
            MB_TOPMOST = 0x00040000

            ctypes.windll.user32.MessageBoxW(
                0,
                message,
                title,
                MB_OK | MB_ICONINFORMATION | MB_TOPMOST,
            )

        except Exception as error:
            logger.exception(f"Erro ao exibir popup de saudação: {error}")