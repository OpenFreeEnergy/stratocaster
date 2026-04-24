import abc
from typing import TypeVar

from gufe import AlchemicalNetwork, ProtocolResult
from gufe.tokenization import GufeTokenizable
from gufe.transformations import Transformation, NonTransformation

from .models import StrategySettings
from .exceptions import StrategyResultValidationError

TProtocolResult = TypeVar("TProtocolResult", bound=ProtocolResult)


class StrategyResult(GufeTokenizable):
    """Results produced by a Strategy."""

    def __init__(self, weights: dict[Transformation | NonTransformation, float | None]):
        self._weights = [
            [transformation, weight] for transformation, weight in weights.items()
        ]
        if not self.validate():
            raise StrategyResultValidationError

    @classmethod
    def _defaults(cls):
        return {}

    def _to_dict(self) -> dict:
        return {"weights": self._weights}

    # TODO: Return type from typing.Self when Python 3.10 is no longer supported
    @classmethod
    def _from_dict(cls, dct: dict):
        weights = dct["weights"]
        return cls(
            weights={transformation: weight for transformation, weight in weights}
        )

    @property
    def weights(self) -> dict[Transformation | NonTransformation, float | None]:
        return {transformation: weight for transformation, weight in self._weights}

    def resolve(self) -> dict[Transformation | NonTransformation, float | None]:
        """Get normalized proposal weights relative to all non-None Transformation weights."""
        weight_sum = sum([weight for _, weight in self._weights if weight is not None])
        normalized_weights = {
            transformation: weight / weight_sum if weight is not None else None
            for transformation, weight in self._weights
        }
        return normalized_weights

    def __or__(self, other):
        if self.weights.keys() & other.weights.keys():
            raise ValueError(
                "StrategyResults can only be combined when their transformation keys are mutually exclusive."
            )
        return StrategyResult(self.weights | other.weights)

    def validate(self) -> bool:
        for transformation, weight in self._weights:
            if not isinstance(transformation, (Transformation, NonTransformation)):
                return False

            if weight is None:
                continue

            match weight:
                case None:
                    continue
                case int():
                    weight = float(weight)
                case float():
                    pass
                case _:
                    return False

            if weight < 0:
                return False
        return True


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
        protocol_results: dict[Transformation | NonTransformation, TProtocolResult],
    ) -> StrategyResult:
        raise NotImplementedError

    def propose(
        self,
        alchemical_network: AlchemicalNetwork,
        protocol_results: dict[Transformation | NonTransformation, TProtocolResult],
    ) -> StrategyResult:
        """Compute Transformation weights from the ProtocolResults of
        the Transformations.

        Parameters
        ----------
        alchemical_network: AlchemicalNetwork
            The AlchemicalNetwork containing the Transformations.
        protocol_results: dict[Transformation | NonTransformation, ProtocolResult]
            A dictionary of Transformations paired with the their
            ProtocolResults.

        Returns
        -------
        StrategyResult

        """
        subgraphs = alchemical_network.connected_subgraphs()
        acc = StrategyResult({})
        for subgraph in subgraphs:
            acc |= self._propose(subgraph, protocol_results)
        return acc
