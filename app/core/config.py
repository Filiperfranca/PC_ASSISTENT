import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Config:
    camera_index: int = int(os.getenv("CAMERA_INDEX", "0"))
    camera_backend: str = os.getenv("CAMERA_BACKEND", "AUTO").upper()

    frame_width: int = int(os.getenv("FRAME_WIDTH", "640"))
    frame_height: int = int(os.getenv("FRAME_HEIGHT", "480"))
    target_fps: int = int(os.getenv("TARGET_FPS", "10"))

    face_lost_grace_seconds: float = float(os.getenv("FACE_LOST_GRACE_SECONDS", "3"))
    user_away_seconds: float = float(os.getenv("USER_AWAY_SECONDS", "30"))
    user_present_confirm_seconds: float = float(os.getenv("USER_PRESENT_CONFIRM_SECONDS", "2"))

    enable_windows_lock: bool = (
        os.getenv("ENABLE_WINDOWS_LOCK", "False").lower() == "true"
    )

    enable_system_actions: bool = (
        os.getenv("ENABLE_SYSTEM_ACTIONS", "True").lower() == "true"
    )

    debug_mode: bool = os.getenv("DEBUG_MODE", "True").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    detection_process_every_n_frames: int = int(os.getenv("DETECTION_PROCESS_EVERY_N_FRAMES", "3"))
    face_detected_streak: int = int(os.getenv("FACE_DETECTED_STREAK", "2"))
    face_lost_streak: int = int(os.getenv("FACE_LOST_STREAK", "4"))
    enable_health_service: bool = (
        os.getenv("ENABLE_HEALTH_SERVICE", "True").lower() == "true"
    )

    health_check_interval_seconds: int = int(
        os.getenv("HEALTH_CHECK_INTERVAL_SECONDS", "30")
    )

    enable_debug_window: bool = (
        os.getenv("ENABLE_DEBUG_WINDOW", "False").lower() == "true"
    )

    windows_lock_cooldown_seconds: int = int(
        os.getenv("WINDOWS_LOCK_COOLDOWN_SECONDS", "120")
    )


config = Config()