import pytest

from gufe import AlchemicalNetwork

from stratocaster.strategies.radialgrowth import (
    RadialGrowthStrategy,
    RadialGrowthStrategySettings,
)
from stratocaster.tests.networks import (
    benzene_variants_star_map as _benzene_variants_star_map,
)


@pytest.fixture
def default_strategy():
    _settings = RadialGrowthStrategy._default_settings()
    return RadialGrowthStrategy(_settings)


def test_propose_no_results(
    default_strategy: RadialGrowthStrategy, fanning_network: AlchemicalNetwork
):
    proposal: StrategyResult = default_strategy.propose(fanning_network, {})
    # check that there is at least 1 non-None weight
    assert not all(proposal.weights.values())


def test_disconnected(
    default_strategy: RadialGrowthStrategy,
    disconnected_fanning_network: AlchemicalNetwork,
):
    proposal: StrategyResult = default_strategy.propose(
        disconnected_fanning_network, {}
    )
