from environs import Env
from pydantic import BaseSettings

env = Env()


class Settings(BaseSettings):
    API_STT = env.str("STT_API", "http://stt.dinosoft.vn/api/v1/speechtotextapi/post-and-decode-file")
    STT_API_KEY = env.str("STT_API_KEY", "api-642ce45e-d48c-4811-8cae-3de45027968a")
    API_URL = env.str("BACKEND_URL", "http://localhost:5000/api")
    UPLOAD_DIR = env.str("UPLOAD_DIR", "upload")


settings = Settings()
