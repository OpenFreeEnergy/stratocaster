import pytest

from gufe import AlchemicalNetwork

from stratocaster.strategies.radialgrowth import (
    RadialGrowthStrategy,
    RadialGrowthStrategySettings,
)
from stratocaster.tests.networks import (
    benzene_variants_star_map as _benzene_variants_star_map,
    fanning_network as _fanning_network,
)


@pytest.fixture(scope="module")
def fanning_network():
    return _fanning_network()


@pytest.fixture
def default_strategy():
    _settings = RadialGrowthStrategy._default_settings()
    return RadialGrowthStrategy(_settings)


def test_propose_no_results(
    default_strategy: RadialGrowthStrategy, fanning_network: AlchemicalNetwork
):
    proposal: StrategyResult = default_strategy.propose(fanning_network, {})
    raise NotImplementedError
