import math
from random import randint, shuffle

import pytest
from gufe import AlchemicalNetwork
from gufe.tests.test_protocol import DummyProtocol, DummyProtocolResult

from stratocaster.base.models import StrategySettings
from stratocaster.base.strategy import StrategyResult
from stratocaster.strategies.connectivity import (
    ConnectivityStrategy,
    ConnectivityStrategySettings,
)
from stratocaster.tests.networks import (
    benzene_variants_star_map as _benzene_variants_star_map,
)


@pytest.fixture(scope="module")
def benzene_variants_star_map():
    return _benzene_variants_star_map()


from gufe.tokenization import GufeKey

SETTINGS_VALID = [(0.5, 0.1, 10), (0.1, None, 10), (0.5, 0.1, None)]


@pytest.mark.parametrize(
    ["decay_rate", "cutoff", "max_runs", "raises"],
    [
        (0, None, None, ValueError),
        (1, None, None, ValueError),
        (0.5, 0, None, ValueError),
        (0.5, None, 0, ValueError),
    ]
    + [(*vals, None) for vals in SETTINGS_VALID],  # include all valid settings
)
def test_connectivity_strategy_settings(decay_rate, cutoff, max_runs, raises):

    def instantiate_settings():
        ConnectivityStrategySettings(
            decay_rate=decay_rate, cutoff=cutoff, max_runs=max_runs
        )

    if raises:
        with pytest.raises(raises):
            instantiate_settings()
    else:
        instantiate_settings()


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
    assert isinstance(default_strategy.settings, ConnectivityStrategySettings)
    max_runs = default_strategy.settings.max_runs
    assert isinstance(max_runs, int)

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


def test_propose_cutoff_num_runs_predictioned_termination(benzene_variants_star_map):
    """We can predict the number of runs needed to terminate with a given cutoff.

    Each edge in benzene_variants_star_map has a base weight of 3.5.
    """

    settings = ConnectivityStrategySettings(cutoff=2, decay_rate=0.5)
    strategy = ConnectivityStrategy(settings)

    assert isinstance(settings.cutoff, float)

    num_runs = math.floor(
        math.log(settings.cutoff / 3.5) / math.log(settings.decay_rate)
    )

    result_data: dict[GufeKey, DummyProtocolResult] = {}
    for transformation in benzene_variants_star_map.edges:
        transformation_key = transformation.key
        result = DummyProtocolResult(
            n_protocol_dag_results=num_runs + 1, info=f"key: {transformation_key}"
        )
        result_data[transformation_key] = result

    results = strategy.propose(benzene_variants_star_map, result_data)

    assert not [weight for weight in results.weights.values() if weight is not None]


@pytest.mark.parametrize(["decay_rate", "cutoff", "max_runs"], SETTINGS_VALID)
def test_simulated_termination(
    default_strategy, benzene_variants_star_map, decay_rate, cutoff, max_runs
):

    settings = ConnectivityStrategySettings(
        decay_rate=decay_rate, cutoff=cutoff, max_runs=max_runs
    )
    default_strategy = ConnectivityStrategy(settings)

    def counts_to_result_data(counts_dict):
        result_data = {}
        for transformation_key, count in counts_dict.items():
            result = DummyProtocolResult(
                n_protocol_dag_results=count, info=f"key: {transformation_key}"
            )
            result_data[transformation_key] = result
        return result_data

    def shuffle_take_n(keys_list, n):
        shuffle(keys_list)
        return keys_list[:n]

    # initial transforms
    transformation_counts = {
        transformation.key: 0 for transformation in benzene_variants_star_map.edges
    }

    max_iterations = 100
    current_iteration = 0
    while current_iteration <= max_iterations:

        if current_iteration == max_iterations:
            raise RuntimeError(
                f"Strategy did not terminate in {max_iterations} iterations "
            )

        result_data = counts_to_result_data(transformation_counts)
        proposal = default_strategy.propose(benzene_variants_star_map, result_data)

        # get random transformations from those with a non-None weight
        resolved_keys = shuffle_take_n(
            [key for key, weight in proposal.resolve().items() if weight is not None], 5
        )

        if resolved_keys:
            # pretend we ran each of the randomly selected protocols
            for key in resolved_keys:
                transformation_counts[key] += 1
        # if we got an empty list back, there are not more protocols to run
        else:
            break
        current_iteration += 1


def test_deterministic(
    default_strategy: ConnectivityStrategy, benzene_variants_star_map: AlchemicalNetwork
):

    settings = default_strategy.settings
    assert isinstance(settings, ConnectivityStrategySettings)

    max_runs = settings.max_runs
    assert isinstance(max_runs, int)

    def random_runs():
        """Generate random randomized inputs for propose."""
        return {
            transformation.key: DummyProtocolResult(
                n_protocol_dag_results=randint(0, max_runs),
                info=f"key: {transformation.key}",
            )
            for transformation in benzene_variants_star_map.edges
        }

    for _ in range(10):
        random_protocol_results = random_runs()
        proposal = default_strategy.propose(
            benzene_variants_star_map, protocol_results=random_protocol_results
        )
        for _ in range(3):
            _proposal = default_strategy.propose(
                benzene_variants_star_map, protocol_results=random_protocol_results
            )
            assert _proposal == proposal
