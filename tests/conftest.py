import pytest

from assistant.knowledge import load_facts
from evals.run import carregar_casos


@pytest.fixture(scope="session")
def facts():
    return load_facts()


@pytest.fixture(scope="session")
def casos():
    return carregar_casos()
