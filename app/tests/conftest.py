from typing import Generator

import pytest
from trankit import Pipeline

from app.app import app
from app.tests.utils import create_pipeline


@pytest.fixture(scope="module")
def client() -> Generator:
    yield app.test_client()


@pytest.fixture(scope="module")
def pipeline() -> Pipeline:
    return create_pipeline()
