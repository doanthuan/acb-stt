from typing import List

from trankit import Pipeline

from app.config import settings


def create_pipeline():
    return Pipeline(lang="vietnamese", gpu=False, cache_dir=settings.CACHE_DIR)


def extract_tokens(result, ner_type) -> List[str]:
    tokens = result["sentences"][0]["tokens"]
    ner_values = []
    for token in tokens:
        if token["ner"] == ner_type:
            ner_values.append(token["text"])
    return ner_values
