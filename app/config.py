import logging

from environs import Env
from pydantic import BaseSettings

env = Env()
if env.str("FLASK_ENV", "development"):
    env.read_env(".env")


class Settings(BaseSettings):
    SITE_URL = env.str("SITE_URL", "https://localhost:50002")
    API_STT = env.str("STT_API", "http://localhost:50001/uploadfile")
    API_URL = env.str("BACKEND_URL", "http://localhost:60000/api")
    UPLOAD_DIR = env.str("UPLOAD_DIR", "upload")
    CACHE_DIR = env.str("CACHE_DIR", "cache")

    # settings for FFMpeg
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
    NOISE_PROFILE = env.str("NOISE_PROFILE", "noise.prof")
    NOISE_SENSITIVITY = env.float("NOISE_SENSITIVITY", 0.21)

    # SFTP
    SFTP_HOST = env.str("SFTP_HOST", "127.0.0.1")
    SFTP_USER = env.str("SFTP_USER", "admin")
    SFTP_PASSWORD = env.str("SFTP_PASSWORD", "admin")
    SFTP_DIR = env.str("SFTP_DIR", "/")

    # Email
    SMTP_HOST = env.str("SMTP_HOST", "10.56.240.52")
    SMTP_PORT = env.int("SMTP_PORT", 587)
    SMTP_USER = env.str("SMTP_USER", "appinfo")
    SMTP_PASSWORD = env.str("SMTP_PASSWORD", "Abc@123456")
    SMTP_EMAIL = env.str("SMTP_EMAIL", "appinfo@acb.com.vn")



settings = Settings()
