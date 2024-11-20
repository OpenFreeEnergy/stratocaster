from stratocaster.base import Strategy, StrategySettings, StrategyResult
from gufe import AlchemicalNetwork, ProtocolResult
from gufe.tokenization import GufeKey


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
