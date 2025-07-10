import pytest
from gufe import AlchemicalNetwork, ProtocolResult
from gufe.tokenization import GufeKey
from gufe.tests.test_protocol import DummyProtocolResult

from stratocaster.base.strategy import StrategyResult
from stratocaster.strategies.uncertainty import (
    UncertaintyStrategy,
    UncertaintyStrategySettings,
)
from stratocaster.tests.networks import (
    benzene_variants_star_map as _benzene_variants_star_map,
)


@pytest.fixture(scope="module")
def benzene_variants_star_map():
    return _benzene_variants_star_map()


class MockProtocolResult(ProtocolResult):
    """Mock ProtocolResult with configurable uncertainty and sample count."""
    
    def __init__(self, n_protocol_dag_results: int, uncertainty: float, **kwargs):
        self._n_protocol_dag_results = n_protocol_dag_results
        self._uncertainty = uncertainty
        super().__init__(**kwargs)
    
    @property
    def n_protocol_dag_results(self) -> int:
        return self._n_protocol_dag_results
    
    @property
    def uncertainty(self) -> float:
        return self._uncertainty


# Valid settings combinations for testing
SETTINGS_VALID = [
    (0.5, 3, 5.0, 20),  # target_uncertainty, min_samples, max_uncertainty_cap, max_samples
    (1.0, 1, 10.0, 50),
    (0.1, 5, 2.0, 10),
]


@pytest.mark.parametrize(
    ["target_uncertainty", "min_samples", "max_uncertainty_cap", "max_samples", "raises"],
    [
        (0, 3, 5.0, 20, ValueError),     # target_uncertainty too low
        (11, 3, 5.0, 20, ValueError),    # target_uncertainty too high
        (0.5, 0, 5.0, 20, ValueError),   # min_samples too low
        (0.5, 101, 5.0, 20, ValueError), # min_samples too high
        (0.5, 3, 0, 20, ValueError),     # max_uncertainty_cap too low
        (0.5, 3, 21, 20, ValueError),    # max_uncertainty_cap too high
        (0.5, 3, 5.0, 0, ValueError),    # max_samples too low
        (0.5, 3, 5.0, 1001, ValueError), # max_samples too high
    ]
    + [(*vals, None) for vals in SETTINGS_VALID],  # include all valid settings
)
def test_uncertainty_strategy_settings(target_uncertainty, min_samples, max_uncertainty_cap, max_samples, raises):
    def instantiate_settings():
        UncertaintyStrategySettings(
            target_uncertainty=target_uncertainty,
            min_samples=min_samples,
            max_uncertainty_cap=max_uncertainty_cap,
            max_samples=max_samples
        )

    if raises:
        with pytest.raises(raises):
            instantiate_settings()
    else:
        instantiate_settings()


@pytest.fixture
def default_strategy():
    _settings = UncertaintyStrategy._default_settings()
    return UncertaintyStrategy(_settings)


def test_propose_no_results(
    default_strategy: UncertaintyStrategy, benzene_variants_star_map: AlchemicalNetwork
):
    """Test that all transformations get maximum weight when no results exist."""
    proposal: StrategyResult = default_strategy.propose(benzene_variants_star_map, {})

    # All transformations should get weight 1.0 since no results exist
    assert all([weight == 1.0 for weight in proposal.weights.values()])
    
    # After normalization, weights should sum to 1
    normalized = proposal.resolve()
    weight_sum = sum(weight for weight in normalized.values() if weight is not None)
    assert abs(weight_sum - 1.0) < 1e-10


def test_propose_below_min_samples(
    default_strategy: UncertaintyStrategy, benzene_variants_star_map: AlchemicalNetwork
):
    """Test that transformations below min_samples get maximum weight."""
    assert isinstance(default_strategy.settings, UncertaintyStrategySettings)
    min_samples = default_strategy.settings.min_samples

    # Create results with samples below minimum
    result_data: dict[GufeKey, MockProtocolResult] = {}
    for transformation in benzene_variants_star_map.edges:
        transformation_key = transformation.key
        result = MockProtocolResult(
            n_protocol_dag_results=min_samples - 1,
            uncertainty=1.0  # High uncertainty, but should be ignored due to low sample count
        )
        result_data[transformation_key] = result

    proposal = default_strategy.propose(benzene_variants_star_map, result_data)
    
    # All should get maximum weight due to insufficient samples
    assert all([weight == 1.0 for weight in proposal.weights.values()])


def test_propose_above_uncertainty_cap(
    default_strategy: UncertaintyStrategy, benzene_variants_star_map: AlchemicalNetwork
):
    """Test that transformations above uncertainty cap get no weight."""
    assert isinstance(default_strategy.settings, UncertaintyStrategySettings)
    max_uncertainty_cap = default_strategy.settings.max_uncertainty_cap
    min_samples = default_strategy.settings.min_samples

    # Create results with uncertainty above cap
    result_data: dict[GufeKey, MockProtocolResult] = {}
    for transformation in benzene_variants_star_map.edges:
        transformation_key = transformation.key
        result = MockProtocolResult(
            n_protocol_dag_results=min_samples + 1,
            uncertainty=max_uncertainty_cap + 1.0  # Above cap
        )
        result_data[transformation_key] = result

    proposal = default_strategy.propose(benzene_variants_star_map, result_data)
    
    # All should get None (no weight) due to excessive uncertainty
    assert all([weight is None for weight in proposal.weights.values()])


def test_propose_above_max_samples(
    default_strategy: UncertaintyStrategy, benzene_variants_star_map: AlchemicalNetwork
):
    """Test that transformations above max_samples get no weight (hard termination)."""
    assert isinstance(default_strategy.settings, UncertaintyStrategySettings)
    max_samples = default_strategy.settings.max_samples
    target_uncertainty = default_strategy.settings.target_uncertainty

    # Create results with high uncertainty but above max_samples
    result_data: dict[GufeKey, MockProtocolResult] = {}
    for transformation in benzene_variants_star_map.edges:
        transformation_key = transformation.key
        result = MockProtocolResult(
            n_protocol_dag_results=max_samples + 1,  # Above max_samples
            uncertainty=target_uncertainty * 2.0  # High uncertainty (normally would get priority)
        )
        result_data[transformation_key] = result

    proposal = default_strategy.propose(benzene_variants_star_map, result_data)
    
    # All should get None (no weight) due to exceeding max_samples
    assert all([weight is None for weight in proposal.weights.values()])


def test_propose_below_target_uncertainty(
    default_strategy: UncertaintyStrategy, benzene_variants_star_map: AlchemicalNetwork
):
    """Test that transformations below target uncertainty get no weight."""
    assert isinstance(default_strategy.settings, UncertaintyStrategySettings)
    target_uncertainty = default_strategy.settings.target_uncertainty
    min_samples = default_strategy.settings.min_samples

    # Create results with uncertainty below target
    result_data: dict[GufeKey, MockProtocolResult] = {}
    for transformation in benzene_variants_star_map.edges:
        transformation_key = transformation.key
        result = MockProtocolResult(
            n_protocol_dag_results=min_samples + 1,
            uncertainty=target_uncertainty - 0.1  # Below target
        )
        result_data[transformation_key] = result

    proposal = default_strategy.propose(benzene_variants_star_map, result_data)
    
    # All should get None (no weight) due to sufficient precision
    assert all([weight is None for weight in proposal.weights.values()])


def test_propose_above_target_uncertainty(
    default_strategy: UncertaintyStrategy, benzene_variants_star_map: AlchemicalNetwork
):
    """Test weight scaling for transformations above target uncertainty."""
    assert isinstance(default_strategy.settings, UncertaintyStrategySettings)
    target_uncertainty = default_strategy.settings.target_uncertainty
    min_samples = default_strategy.settings.min_samples

    # Create results with various uncertainty values above target
    result_data: dict[GufeKey, MockProtocolResult] = {}
    transformations = list(benzene_variants_star_map.edges)
    
    # First transformation: exactly at target (should get None)
    result_data[transformations[0].key] = MockProtocolResult(
        n_protocol_dag_results=min_samples + 1,
        uncertainty=target_uncertainty
    )
    
    # Second transformation: target + 50% (should get weight 0.5)
    result_data[transformations[1].key] = MockProtocolResult(
        n_protocol_dag_results=min_samples + 1,
        uncertainty=target_uncertainty * 1.5
    )
    
    # Third transformation: target + 100% (should get weight 1.0)
    result_data[transformations[2].key] = MockProtocolResult(
        n_protocol_dag_results=min_samples + 1,
        uncertainty=target_uncertainty * 2.0
    )
    
    # Remaining transformations: well below target
    for transformation in transformations[3:]:
        result_data[transformation.key] = MockProtocolResult(
            n_protocol_dag_results=min_samples + 1,
            uncertainty=target_uncertainty * 0.5
        )

    proposal = default_strategy.propose(benzene_variants_star_map, result_data)
    weights = proposal.weights
    
    # Check specific weight values
    assert weights[transformations[0].key] is None  # At target
    assert abs(weights[transformations[1].key] - 0.5) < 1e-10  # 50% excess
    assert abs(weights[transformations[2].key] - 1.0) < 1e-10  # 100% excess
    
    # Remaining should be None
    for transformation in transformations[3:]:
        assert weights[transformation.key] is None


def test_propose_mixed_scenarios(
    default_strategy: UncertaintyStrategy, benzene_variants_star_map: AlchemicalNetwork
):
    """Test a mixed scenario with different uncertainty conditions."""
    assert isinstance(default_strategy.settings, UncertaintyStrategySettings)
    settings = default_strategy.settings
    
    result_data: dict[GufeKey, MockProtocolResult] = {}
    transformations = list(benzene_variants_star_map.edges)
    
    # No result (should get 1.0)
    # transformations[0] - no entry in result_data
    
    # Below min samples (should get 1.0)
    result_data[transformations[1].key] = MockProtocolResult(
        n_protocol_dag_results=settings.min_samples - 1,
        uncertainty=10.0  # High but ignored
    )
    
    # Above uncertainty cap (should get None)
    result_data[transformations[2].key] = MockProtocolResult(
        n_protocol_dag_results=settings.min_samples + 1,
        uncertainty=settings.max_uncertainty_cap + 1.0
    )
    
    # Below target (should get None)
    result_data[transformations[3].key] = MockProtocolResult(
        n_protocol_dag_results=settings.min_samples + 1,
        uncertainty=settings.target_uncertainty - 0.1
    )
    
    # Above target (should get scaled weight)
    excess_uncertainty = 0.25  # 50% of target_uncertainty (0.5)
    expected_weight = excess_uncertainty / settings.target_uncertainty  # 0.5
    result_data[transformations[4].key] = MockProtocolResult(
        n_protocol_dag_results=settings.min_samples + 1,
        uncertainty=settings.target_uncertainty + excess_uncertainty
    )

    proposal = default_strategy.propose(benzene_variants_star_map, result_data)
    weights = proposal.weights
    
    # Check each scenario
    assert weights[transformations[0].key] == 1.0  # No result
    assert weights[transformations[1].key] == 1.0  # Below min samples
    assert weights[transformations[2].key] is None  # Above cap
    assert weights[transformations[3].key] is None  # Below target
    assert abs(weights[transformations[4].key] - expected_weight) < 1e-10  # Scaled


def test_custom_settings():
    """Test strategy with custom settings."""
    custom_settings = UncertaintyStrategySettings(
        target_uncertainty=1.0,
        min_samples=5,
        max_uncertainty_cap=3.0,
        max_samples=10
    )
    strategy = UncertaintyStrategy(custom_settings)
    
    assert strategy.settings.target_uncertainty == 1.0
    assert strategy.settings.min_samples == 5
    assert strategy.settings.max_uncertainty_cap == 3.0
    assert strategy.settings.max_samples == 10


def test_default_settings():
    """Test that default settings are correctly applied."""
    strategy = UncertaintyStrategy()
    settings = strategy.settings
    
    assert isinstance(settings, UncertaintyStrategySettings)
    assert settings.target_uncertainty == 0.5
    assert settings.min_samples == 3
    assert settings.max_uncertainty_cap == 5.0
    assert settings.max_samples == 20