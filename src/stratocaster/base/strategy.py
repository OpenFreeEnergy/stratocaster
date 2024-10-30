import abc
from typing import Self

from gufe.tokenization import GufeTokenizable, GufeKey
from gufe import AlchemicalNetwork, ProtocolResult

from .models import StrategySettings


class StrategyResult(GufeTokenizable):

    def __init__(self, weights: dict[GufeKey, float | None]):
        self._weights = weights

    @classmethod
    def _defaults(cls):
        return {}

    def _to_dict(self) -> dict:
        return {"weights": self._weights}

    @classmethod
    def _from_dict(cls, dct: dict) -> Self:
        return cls(**dct)

    @property
    def weights(self) -> dict[GufeKey, float | None]:
        return self._weights

    def resolve(self) -> dict[GufeKey, float | None]:
        weights = self.weights
        weight_sum = sum([weight for weight in weights.values() if weight is not None])
        modified_weights = {
            key: weight / weight_sum
            for key, weight in weights.items()
            if weight is not None
        }
        weights.update(modified_weights)
        return weights


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
        protocol_results: dict[GufeKey, ProtocolResult],
    ) -> StrategyResult:
        raise NotImplementedError

    def propose(
        self,
        alchemical_network: AlchemicalNetwork,
        protocol_results: dict[GufeKey, ProtocolResult],
    ) -> StrategyResult:
        return self._propose(alchemical_network, protocol_results)
