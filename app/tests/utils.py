from typing import Any, Dict, List

from trankit import Pipeline

from app.config import settings


def create_pipeline():
    return Pipeline(lang="vietnamese", gpu=False, cache_dir=settings.CACHE_DIR)


def extract_tokens(result: Dict[str, Any], ner_types: List[str]) -> List[str]:
    ner_values = []
    for sent in result["sentences"]:
        for token in sent["tokens"]:
            if token["ner"] in ner_types:
                ner_values.append(token["text"])
    return ner_values
