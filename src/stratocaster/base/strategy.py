import abc
from typing import Self

from gufe.tokenization import GufeTokenizable
from gufe import AlchemicalNetwork
from gufe.protocols import ProtocolResult

from .models import StrategySettings


class StrategyResult(GufeTokenizable):

    def __init__(self, weights):
        self._weights = weights

    @classmethod
    def _defaults(cls):
        return {}

    def _to_dict(self) -> dict:
        return {"weights": self._weights}

    @classmethod
    def _from_dict(cls, dct: dict) -> Self:
        return cls(**dct)


# TODO: docstrings
class Strategy(GufeTokenizable):
    """An object that proposes the relative urgency of computing transformations within an AlchemicalNetwork."""

    def __init__(self, settings: StrategySettings):
        self._settings = settings

    @classmethod
    def _defaults(cls):
        return {}

    def _to_dict(self) -> dict:
        return {"settings": self._settings}

    @classmethod
    def _from_dict(cls, dct: dict) -> Self:
        return cls(**dct)

    @classmethod
    @abc.abstractmethod
    def _default_settings(cls) -> StrategySettings:
        raise NotImplementedError

    @abc.abstractmethod
    def _propose(
        self,
        alchemical_network: AlchemicalNetwork,
        protocol_results: list[ProtocolResult],
    ) -> StrategyResult:
        raise NotImplementedError

    def propose(
        self,
        alchemical_network: AlchemicalNetwork,
        protocol_results: list[ProtocolResult],
    ) -> StrategyResult:
        return self._propose(alchemical_network, protocol_results)
