import abc
from typing import TypeVar

from gufe import AlchemicalNetwork, ProtocolResult
from gufe.tokenization import GufeKey, GufeTokenizable

from .models import StrategySettings

TProtocolResult = TypeVar("TProtocolResult", bound=ProtocolResult)

class StrategyResult(GufeTokenizable):
    """Results produced by a Strategy."""

    def __init__(self, weights: dict[GufeKey, float | None]):
        self._weights = weights

    @classmethod
    def _defaults(cls):
        return {}

    def _to_dict(self) -> dict:
        return {"weights": self._weights}

    # TODO: Return type from typing.Self when Python 3.10 is no longer supported
    @classmethod
    def _from_dict(cls, dct: dict):
        return cls(**dct)

    @property
    def weights(self) -> dict[GufeKey, float | None]:
        return self._weights

    def resolve(self) -> dict[GufeKey, float | None]:
        """Normalize the proposal weights relative to all non-None Transformation weights."""
        weights = self.weights
        weight_sum = sum([weight for weight in weights.values() if weight is not None])
        modified_weights = {
            key: weight / weight_sum
            for key, weight in weights.items()
            if weight is not None
        }
        weights.update(modified_weights)
        return weights


class Strategy(GufeTokenizable):
    """An object that proposes the relative urgency of computing
    transformations within an AlchemicalNetwork."""

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

    # TODO: Return type from typing.Self when Python 3.10 is no longer supported
    @classmethod
    def _from_dict(cls, dct: dict):
        return cls(**dct)

    @classmethod
    @abc.abstractmethod
    def _default_settings(cls) -> StrategySettings:
        raise NotImplementedError

    @classmethod
    def default_settings(cls) -> StrategySettings:
        """Get the default settings for this ``Strategy``.

        These represent the current recommendations for the use of this
        particular ``Strategy``. These can be modified and passed in as the
        only argument for creating a new ``Strategy`` instance.
        """
        return cls._default_settings()

    @abc.abstractmethod
    def _propose(
        self,
        alchemical_network: AlchemicalNetwork,
        protocol_results: dict[GufeKey, TProtocolResult],
    ) -> StrategyResult:
        raise NotImplementedError

    def propose(
        self,
        alchemical_network: AlchemicalNetwork,
        protocol_results: dict[GufeKey, TProtocolResult],
    ) -> StrategyResult:
        """Compute Transformation weights from the ProtocolResults of
        the Transformations.

        Parameters
        ----------
        alchemical_network: AlchemicalNetwork
            The AlchemicalNetwork containing the Transformations.
        protocol_results: dict[GufeKey, ProtocolResult]
            A dictionary of Transformation GufeKeys paired with the
            Transformation's ProtocolResults.

        Returns
        -------
        StrategyResult

        """
        return self._propose(alchemical_network, protocol_results)
