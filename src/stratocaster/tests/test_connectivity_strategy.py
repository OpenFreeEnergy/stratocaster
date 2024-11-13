import math

from gufe import AlchemicalNetwork
import pytest

from stratocaster.strategies.connectivity import (
    ConnectivityStrategy,
    ConnectivityStrategySettings,
)
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
            n_protocol_dag_results=2, info=f"key: {transformation_key}"
        )
        result_data[transformation_key] = result

    results = default_strategy.propose(benzene_variants_star_map, result_data)
    results_no_data = default_strategy.propose(benzene_variants_star_map, {})

    # the raw weights should no longer be the same
    assert results.weights != results_no_data.weights
    # since each transformation had the same number of previous results, resolve
    # should give back the same normalized weights
    assert results.resolve() == results_no_data.resolve()


def test_propose_max_runs_termination(
    default_strategy: ConnectivityStrategy, benzene_variants_star_map: AlchemicalNetwork
):

    max_runs = default_strategy.settings.max_runs

    result_data: dict[GufeKey, DummyProtocolResult] = {}
    for transformation in benzene_variants_star_map.edges:
        transformation_key = transformation.key
        result = DummyProtocolResult(
            n_protocol_dag_results=max_runs, info=f"key: {transformation_key}"
        )
        result_data[transformation_key] = result

    results = default_strategy.propose(benzene_variants_star_map, result_data)

    # since the default strategy has a max_runs of 3, we expect all Nones
    assert not [weight for weight in results.resolve().values() if weight is not None]


def test_propose_cutoff(benzene_variants_star_map):

    settings = ConnectivityStrategySettings(cutoff=2, decay_rate=0.5)
    strategy = ConnectivityStrategy(settings)

    assert isinstance(settings.cutoff, float)
    num_runs = math.floor(
        math.log(settings.cutoff / 3.5) / math.log(settings.decay_rate)
    )
    print(num_runs)

    result_data: dict[GufeKey, DummyProtocolResult] = {}
    for transformation in benzene_variants_star_map.edges:
        transformation_key = transformation.key
        result = DummyProtocolResult(
            n_protocol_dag_results=num_runs + 1, info=f"key: {transformation_key}"
        )
        result_data[transformation_key] = result

    results = strategy.propose(benzene_variants_star_map, result_data)

    assert not [weight for weight in results.weights.values() if weight is not None]
