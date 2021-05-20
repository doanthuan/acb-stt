from environs import Env
from pydantic import BaseSettings

env = Env()


class Settings(BaseSettings):
    API_STT = "http://stt.dinosoft.vn/api/v1/speechtotextapi/post-and-decode-file"
    API_URL = "http://localhost:5000/api"
    UPLOAD_DIR = env.str("UPLOAD_DIR", "upload")


settings = Settings()
