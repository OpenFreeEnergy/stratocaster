import pytest
from gufe import AlchemicalNetwork, ProtocolResult
from gufe.tokenization import GufeKey

from stratocaster.base import Strategy, StrategySettings
from stratocaster.base.strategy import StrategyResult


class StrategyASettings(StrategySettings):
    pass


class StrategyBSettings(StrategySettings):
    pass


class StrategyNoSettings(Strategy):

    @classmethod
    def _default_settings(cls) -> StrategySettings:
        return cls._settings_cls()

    def _propose(
        self,
        alchemical_network: AlchemicalNetwork,
        protocol_results: dict[GufeKey, ProtocolResult],
    ) -> StrategyResult:
        return StrategyResult({})


class StrategyA(StrategyNoSettings):
    _settings_cls = StrategyASettings


class StrategyB(StrategyNoSettings):
    _settings_cls = StrategyBSettings


@pytest.mark.parametrize(
    ("strategy", "settings"),
    ((StrategyA, StrategyBSettings), (StrategyB, StrategyASettings)),
)
def test_incorrect_strategy_settings_passed(strategy, settings):
    with pytest.raises(ValueError):
        strategy(settings())


@pytest.mark.parametrize(
    ("strategy", "settings"),
    ((StrategyA, StrategyASettings), (StrategyB, StrategyBSettings)),
)
def test_correct_strategy_settings_passed(strategy, settings):
    strat_settings = settings()
    strat = strategy(strat_settings)

    assert strat._settings_cls == settings


def test_no_settings_implemented():

    with pytest.raises(NotImplementedError):
        StrategyNoSettings(StrategyASettings())
