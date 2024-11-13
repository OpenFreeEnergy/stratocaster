import abc
from typing import Self, TypeVar

from gufe.tokenization import GufeTokenizable, GufeKey
from gufe import AlchemicalNetwork, ProtocolResult

from .models import StrategySettings

_ProtocolResult = TypeVar("_ProtocolResult", bound=ProtocolResult)


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

    _settings_cls: type[StrategySettings]

    def __init__(self, settings: StrategySettings):

        if not hasattr(self.__class__, "_settings_cls"):
            raise NotImplementedError(
                f"class `{self.__class__.__qualname__}` must implement the `_settings_cls` attribute."
            )

        if not isinstance(settings, self._settings_cls):
            raise ValueError(
                f"`{self.__class__.__qualname__}` expected a `{self._settings_cls.__qualname__}` instance"
            )

        self._settings = settings
        super().__init__()

    @property
    def settings(self) -> StrategySettings:
        return self._settings

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
        protocol_results: dict[GufeKey, _ProtocolResult],
    ) -> StrategyResult:
        raise NotImplementedError

    def propose(
        self,
        alchemical_network: AlchemicalNetwork,
        protocol_results: dict[GufeKey, _ProtocolResult],
    ) -> StrategyResult:
        return self._propose(alchemical_network, protocol_results)
