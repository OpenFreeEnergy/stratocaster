from gufe import AlchemicalNetwork
import pytest

from stratocaster.strategies import ConnectivityStrategy
from stratocaster.base.strategy import StrategyResult
from stratocaster.base.models import StrategySettings


from gufe.tests.test_protocol import DummyProtocol, DummyProtocolResult
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
from gufe.tokenization import GufeKey


@pytest.fixture
def default_strategy():
    _settings = ConnectivityStrategy._default_settings()
    return ConnectivityStrategy(_settings)


def test_propose_no_results(
    default_strategy: ConnectivityStrategy, benzene_variants_star_map: AlchemicalNetwork
):
    proposal: StrategyResult = default_strategy.propose(benzene_variants_star_map, {})

    assert all([weight == 3.5 for weight in proposal._weights.values()])
    assert 1 == sum(
        weight for weight in proposal.resolve().values() if weight is not None
    )


def test_propose_previous_results(
    default_strategy: ConnectivityStrategy, benzene_variants_star_map: AlchemicalNetwork
):

    result_data: dict[GufeKey, DummyProtocolResult] = {}
    for transformation in benzene_variants_star_map.edges:
        transformation_key = transformation.key
        result = DummyProtocolResult(
            n_protocol_dag_results=1, info=f"key: {transformation_key}"
        )
        result_data[transformation_key] = result

    default_strategy.propose(benzene_variants_star_map, result_data)
