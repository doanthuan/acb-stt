from trankit import Pipeline

from app.models.ner import NerType
from app.tests.utils import extract_tokens


def test_ner_person(pipeline: Pipeline):
    text = "em là Nguyễn Văn Trường"
    vi_output = pipeline.ner(text)
    ner_values = extract_tokens(vi_output, NerType.PERSON)
    print(ner_values)
    assert "Nguyễn Văn Trường" in ner_values


def test_ner_loc(pipeline: Pipeline):
    text = "120 đường Hai Bà Trưng Quận 3"
    output = pipeline.ner(text)
    ner_values = extract_tokens(output, NerType.LOCATION)
    print(ner_values)
    assert text in ner_values
