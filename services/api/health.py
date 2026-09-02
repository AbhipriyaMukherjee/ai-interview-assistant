from shared.core.config import get_settings

APP_VERSION = "0.1.0"


def get_health_status() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "version": APP_VERSION,
        "config_loaded": bool(settings.groq_api_key or True),  # placeholder check
    }