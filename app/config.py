from environs import Env
from pydantic import BaseSettings

env = Env()
if env.str("FLASK_ENV", "development"):
    env.read_env(".env")


class Settings(BaseSettings):
    SITE_URL = env.str("SITE_URL", "https://localhost:50002")
    API_STT = env.str("STT_API", "https://demo.gruads.com:50001/uploadfile")
    API_URL = env.str("BACKEND_URL", "http://localhost:50000/api")
    UPLOAD_DIR = env.str("UPLOAD_DIR", "upload")
    CACHE_DIR = env.str("CACHE_DIR", "cache")


settings = Settings()
