import logging

from environs import Env
from pydantic import BaseSettings

env = Env()
if env.str("FLASK_ENV", "development"):
    env.read_env(".env")


class Settings(BaseSettings):
    SITE_URL = env.str("SITE_URL", "https://localhost:50002")
    API_STT = env.str("STT_API", "http://demo.gruads.com:50002/uploadfile")
    API_URL = env.str("BACKEND_URL", "http://localhost:50000/api")
    UPLOAD_DIR = env.str("UPLOAD_DIR", "upload")
    CACHE_DIR = env.str("CACHE_DIR", "cache")

    # settings for noise
    NOISE_LEVEL = env.int("NOISE_LEVEL", -30)
    NOISE_DURATION = env.float("NOISE_DURATION", 0.25)

    # for the logging
    LOG_LEVEL = logging.INFO
    LOG_DIR = env.str("LOG_DIR", "logs")
    LOG_MAX_SIZE = env.int("LOG_MAX_SIZE", 10485760)
    LOG_MAX_COUNTS = env.int("LOG_MAX_COUNTS", 3)

    # settings for VAD
    VAD_CUTOFF = env.float("VAD_CUTOFF", 0.9)
    VAD_AGGRESSIVE_LEVEL = env.int("VAD_AGGRESSIVE_LEVEL", 3)
    FRAME_DURATION_MS = env.int("FRAME_DURATION_MS", 30)
    PADDING_DURATION_MS = env.int("PADDING_DURATION_MS", 250)

    # silero
    SILERO_MODEL = env.str("SILERO_MODEL", "models/silero.jit")


settings = Settings()
