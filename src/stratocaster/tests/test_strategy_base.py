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

    def test_resolve_does_not_mutate_weights(self):
        original_weights = dict(self.result.weights)
        self.result.resolve()
        assert self.result.weights == original_weights

    def test_resolve_is_idempotent(self):
        first = self.result.resolve()
        second = self.result.resolve()
        assert first == second


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
