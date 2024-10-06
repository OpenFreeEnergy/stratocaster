from gufe import AlchemicalNetwork
import pytest

from stratocaster.strategies import ConnectivityStrategy
from stratocaster.base.strategy import StrategyResult
from stratocaster.base.models import StrategySettings


from gufe.tests.test_protocol import DummyProtocol
from gufe.tests.conftest import (
    benzene_variants_star_map,
    benzene,
    benzene_modifications,
    toluene,
    phenol,
    benzonitrile,
    anisole,
    benzaldehyde,
    styrene,
    prot_comp,
    solv_comp,
    PDB_181L_path,
)


@pytest.fixture
def default_strategy():
    _settings = ConnectivityStrategy._default_settings()
    return ConnectivityStrategy(_settings)


def test_propose(
    default_strategy: ConnectivityStrategy, benzene_variants_star_map: AlchemicalNetwork
):
    proposal: StrategyResult = default_strategy.propose(benzene_variants_star_map, [])

    assert all([weight == 3 for weight in proposal._weights.values()])
