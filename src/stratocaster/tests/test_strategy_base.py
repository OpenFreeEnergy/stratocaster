import pytest

from gufe import AlchemicalNetwork, ProtocolResult
from gufe.transformations import Transformation, NonTransformation

from stratocaster.base import (
    Strategy,
    StrategyResult,
    StrategyResultValidationError,
    StrategySettings,
)


class DummyTransformation(Transformation):
    pass


class DummyNonTransformation(NonTransformation):
    pass


class TestStrategyResult:

    result = StrategyResult(
        {
            DummyTransformation(stateA=0, stateB=1, protocol=None): 1,
            DummyTransformation(stateA=1, stateB=2, protocol=None): None,
            DummyNonTransformation(system=2, protocol=None): 10,
        }
    )
    assert 3 == len(result.weights)

    def test_dict_roundtrip(self):
        assert StrategyResult.from_dict(self.result.to_dict()) == self.result

    def test_resolve_no_weight_side_effect(self):
        """Resolve returns a normalized copy of the result
        weights and doesn't modify the original data."""
        res = self.result.resolve()
        assert res != self.result.weights

    def test_resolve_normalization(self):
        """Resolve produces normalized weights for all non-None values."""
        res = self.result.resolve()
        assert 1 == sum([value for _, value in res.items() if value is not None])

    def test_validation(self):

        # negative weight should not pass validation
        with pytest.raises(StrategyResultValidationError):
            result = StrategyResult(
                {
                    DummyTransformation(stateA=0, stateB=1, protocol=None): -1,
                    DummyTransformation(stateA=1, stateB=2, protocol=None): None,
                    DummyNonTransformation(system=2, protocol=None): 10,
                }
            )

        # Keys must be either Transformation or NonTransformation,
        # provide old style keys for test
        with pytest.raises(StrategyResultValidationError):
            result = StrategyResult(
                {
                    DummyTransformation(stateA=0, stateB=1, protocol=None).key: 1,
                    DummyTransformation(stateA=1, stateB=2, protocol=None).key: None,
                    DummyNonTransformation(system=2, protocol=None).key: 10,
                }
            )


class DummyStrategySettings(StrategySettings):
    pass


class DummyStrategy(Strategy):

    _settings_cls = DummyStrategySettings

    @classmethod
    def _default_settings(cls) -> DummyStrategySettings:
        return DummyStrategySettings()

    def _propose(
        self,
        alchemical_network: AlchemicalNetwork,
        protocol_results: dict[Transformation | NonTransformation, ProtocolResult],
    ):
        assert alchemical_network, protocol_results
        return StrategyResult({})


class TestStrategy:

    strategy = DummyStrategy(DummyStrategySettings())

    def test_dict_roundtrip(self):
        strategy_dict_form = self.strategy.to_dict()
        assert DummyStrategy.from_dict(strategy_dict_form) == self.strategy
