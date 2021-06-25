from typing import Union

from pydantic import BaseModel


class AudioSegment(BaseModel):
    channel: Union[int]
    timestamp: Union[float]
    audio_file: Union[str]
