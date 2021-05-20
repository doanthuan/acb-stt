from environs import Env
from pydantic import BaseSettings

env = Env()
if env.str("FLASK_ENV", "development"):
    env.read_env(".env")


class Settings(BaseSettings):
    API_STT = env.str(
        "STT_API", "http://stt.dinosoft.vn/api/v1/speechtotextapi/post-and-decode-file"
    )
    STT_API_KEY = env.str("STT_API_KEY", "")
    API_URL = env.str("BACKEND_URL", "http://localhost:5000/api")
    UPLOAD_DIR = env.str("UPLOAD_DIR", "upload")


settings = Settings()
