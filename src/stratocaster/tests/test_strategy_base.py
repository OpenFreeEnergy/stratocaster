from gufe import AlchemicalNetwork, ProtocolResult
from gufe.tokenization import GufeKey

from stratocaster.base import Strategy, StrategyResult, StrategySettings


class TestStrategyResult:

    result = StrategyResult(
        {
            GufeKey("MyTransformation-ABC123"): 1,
            GufeKey("MyTransformation-321CBA"): None,
            GufeKey("MyOtherTransformation-789xyz"): 10,
        }
    )

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
        protocol_results: dict[GufeKey, ProtocolResult],
    ):
        assert alchemical_network, protocol_results
        return StrategyResult({})


class TestStrategy:

    strategy = DummyStrategy(DummyStrategySettings())

    def test_dict_roundtrip(self):
        strategy_dict_form = self.strategy.to_dict()
        assert DummyStrategy.from_dict(strategy_dict_form) == self.strategy
