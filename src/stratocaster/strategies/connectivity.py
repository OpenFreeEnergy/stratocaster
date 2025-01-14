from gufe import AlchemicalNetwork, ProtocolResult
from gufe.tokenization import GufeKey

from stratocaster.base import Strategy, StrategyResult
from stratocaster.base.models import StrategySettings

try:
    from pydantic.v1 import Field, root_validator, validator
except ImportError:
    from pydantic import (
        Field,
        root_validator,
        validator,
    )

import pydantic


# TODO: docstrings
class ConnectivityStrategySettings(StrategySettings):

    decay_rate: float = Field(
        default=0.5, description="decay rate of the exponential decay penalty factor"
    )
    cutoff: float | None = Field(
        default=None,
        description="unnormalized weight cutoff used for termination condition",
    )
    max_runs: int | None = Field(
        default=None,
        description="the upper limit of protocol DAG results needed before a transformation is no longer weighed",
    )

    @validator("cutoff")
    def validate_cutoff(cls, value):
        if value is not None:
            if not (0 < value):
                raise ValueError("`cutoff` must be greater than 0")
        return value

    @validator("decay_rate")
    def validate_decay_rate(cls, value):
        if not (0 < value < 1):
            raise ValueError("`decay_rate` must be between 0 and 1")
        return value

    @validator("max_runs")
    def validate_max_runs(cls, value):
        if value is not None:
            if not value >= 1:
                raise ValueError("`max_runs` must be greater than or equal to 1")
        return value

    @root_validator
    def check_cutoff_or_max_runs(cls, values):
        max_runs, cutoff = values.get("max_runs"), values.get("cutoff")

        if max_runs is None and cutoff is None:
            raise ValueError("At least one of `max_runs` or `cutoff` must be set")

        return values


# TODO: docstrings
class ConnectivityStrategy(Strategy):

    _settings_cls = ConnectivityStrategySettings

    def _exponential_decay_scaling(self, number_of_results: int, decay_rate: float):
        return decay_rate**number_of_results

    def _propose(
        self,
        alchemical_network: AlchemicalNetwork,
        protocol_results: dict[GufeKey, ProtocolResult],
    ) -> StrategyResult:
        """Propose `Transformation` weight recommendations based on high connectivity nodes.

        Parameters
        ----------
        alchemical_network: AlchemicalNetwork
        protocol_results: dict[GufeKey, ProtocolResult]
            A dictionary whose keys are the `GufeKey`s of `Transformation`s in the `AlchemicalNetwork`
            and whose values are the `ProtocolResult`s for those `Transformation`s.

        Returns
        -------
        StrategyResult
            A `StrategyResult` containing the proposed `Transformation` weights.
        """

        settings = self.settings

        # keep the type checker happy
        assert isinstance(settings, ConnectivityStrategySettings)

        alchemical_network_mdg = alchemical_network.graph
        weights: dict[GufeKey, float | None] = {}

        for state_a, state_b in alchemical_network_mdg.edges():
            num_neighbors_a = alchemical_network_mdg.degree(state_a)
            num_neighbors_b = alchemical_network_mdg.degree(state_b)

            # linter-satisfying assertion
            assert isinstance(num_neighbors_a, int) and isinstance(num_neighbors_b, int)

            transformation_key = alchemical_network_mdg.get_edge_data(state_a, state_b)[
                0
            ]["object"].key

            match (protocol_results.get(transformation_key)):
                case None:
                    transformation_n_protcol_dag_results = 0
                case pr:
                    assert isinstance(pr, ProtocolResult)
                    transformation_n_protcol_dag_results = pr.n_protocol_dag_results

            scaling_factor = self._exponential_decay_scaling(
                transformation_n_protcol_dag_results, settings.decay_rate
            )
            weight = scaling_factor * (num_neighbors_a + num_neighbors_b) / 2

            match (settings.max_runs, settings.cutoff):
                case (None, cutoff) if cutoff is not None:
                    if weight < cutoff:
                        weight = None
                case (max_runs, None) if max_runs is not None:
                    if transformation_n_protcol_dag_results >= max_runs:
                        weight = None
                case (max_runs, cutoff) if max_runs is not None and cutoff is not None:
                    if (
                        weight < cutoff
                        or transformation_n_protcol_dag_results >= max_runs
                    ):
                        weight = None

            weights[transformation_key] = weight

        results = StrategyResult(weights=weights)
        return results

    @classmethod
    def _default_settings(cls) -> StrategySettings:
        return ConnectivityStrategySettings(max_runs=3)
