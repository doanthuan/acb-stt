from trankit import Pipeline

from app.config import settings


def create_pipeline():
    return Pipeline(lang="vietnamese", gpu=False, cache_dir=settings.CACHE_DIR)
