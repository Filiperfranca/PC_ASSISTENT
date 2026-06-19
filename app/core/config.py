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

    debug_mode: bool = os.getenv("DEBUG_MODE", "True").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    detection_process_every_n_frames: int = int(os.getenv("DETECTION_PROCESS_EVERY_N_FRAMES", "3"))
    face_detected_streak: int = int(os.getenv("FACE_DETECTED_STREAK", "2"))
    face_lost_streak: int = int(os.getenv("FACE_LOST_STREAK", "4"))


config = Config()