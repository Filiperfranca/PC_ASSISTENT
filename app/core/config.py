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

    enable_face_recognition: bool = (
        os.getenv("ENABLE_FACE_RECOGNITION", "True").lower() == "true"
    )

    authorized_user: str = os.getenv("AUTHORIZED_USER", "filipe").lower()

    recognition_confidence_threshold: float = float(
        os.getenv("RECOGNITION_CONFIDENCE_THRESHOLD", "75")
    )

    recognition_process_every_n_events: int = int(
        os.getenv("RECOGNITION_PROCESS_EVERY_N_EVENTS", "3")
    )

    enable_security_service: bool = (
        os.getenv("ENABLE_SECURITY_SERVICE", "True").lower() == "true"
    )

    unknown_lock_enabled: bool = (
        os.getenv("UNKNOWN_LOCK_ENABLED", "False").lower() == "true"
    )

    unknown_confirm_seconds: float = float(
        os.getenv("UNKNOWN_CONFIRM_SECONDS", "3")
    )

    unknown_event_streak: int = int(
        os.getenv("UNKNOWN_EVENT_STREAK", "3")
    )

    min_security_face_width: int = int(
        os.getenv("MIN_SECURITY_FACE_WIDTH", "160")
    )

    authorized_grace_seconds: float = float(
        os.getenv("AUTHORIZED_GRACE_SECONDS", "10")
    )

    multi_face_warning_enabled: bool = (
        os.getenv("MULTI_FACE_WARNING_ENABLED", "True").lower() == "true"
    )

    multi_face_confirm_seconds: float = float(
        os.getenv("MULTI_FACE_CONFIRM_SECONDS", "3")
    )

    multi_face_prompt_cooldown_seconds: float = float(
        os.getenv("MULTI_FACE_PROMPT_COOLDOWN_SECONDS", "120")
    )

    multi_face_auto_lock_on_timeout: bool = (
        os.getenv("MULTI_FACE_AUTO_LOCK_ON_TIMEOUT", "False").lower() == "true"
    )
    recognition_authorized_threshold: float = float(
        os.getenv("RECOGNITION_AUTHORIZED_THRESHOLD", "70")
    )

    recognition_unknown_threshold: float = float(
        os.getenv("RECOGNITION_UNKNOWN_THRESHOLD", "80")
    )

    min_authorized_face_width: int = int(
        os.getenv("MIN_AUTHORIZED_FACE_WIDTH", "150")
    )

    enable_teams_integration: bool = (
        os.getenv("ENABLE_TEAMS_INTEGRATION", "False").lower() == "true"
    )

    teams_provider: str = os.getenv("TEAMS_PROVIDER", "mock").lower()

    teams_tenant_id: str = os.getenv("TEAMS_TENANT_ID", "common")
    teams_client_id: str = os.getenv("TEAMS_CLIENT_ID", "")
    teams_user_id: str = os.getenv("TEAMS_USER_ID", "me")
    teams_session_id: str = os.getenv("TEAMS_SESSION_ID", "")

    teams_presence_expiration: str = os.getenv(
        "TEAMS_PRESENCE_EXPIRATION", "PT15M"
    )

    teams_keepalive_seconds: int = int(
        os.getenv("TEAMS_KEEPALIVE_SECONDS", "240")
    )

    teams_set_available_on_present: bool = (
        os.getenv("TEAMS_SET_AVAILABLE_ON_PRESENT", "True").lower() == "true"
    )

    teams_set_away_on_away: bool = (
        os.getenv("TEAMS_SET_AWAY_ON_AWAY", "True").lower() == "true"
    )

    teams_available_availability: str = os.getenv(
        "TEAMS_AVAILABLE_AVAILABILITY", "Available"
    )

    teams_available_activity: str = os.getenv(
        "TEAMS_AVAILABLE_ACTIVITY", "Available"
    )

    teams_away_availability: str = os.getenv(
        "TEAMS_AWAY_AVAILABILITY", "Away"
    )

    teams_away_activity: str = os.getenv(
        "TEAMS_AWAY_ACTIVITY", "Away"
    )



config = Config()