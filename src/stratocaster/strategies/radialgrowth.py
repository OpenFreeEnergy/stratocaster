import networkx as nx

from gufe import AlchemicalNetwork, ProtocolResult
from gufe.tokenization import GufeKey

from pydantic import (
    Field,
    model_validator,
    field_validator,
)

import pydantic

from stratocaster.base import Strategy, StrategyResult
from stratocaster.base.models import StrategySettings


class RadialGrowthStrategySettings(StrategySettings):

    max_runs: int = Field(
        default=3,
        description="the upper limit of protocol DAG results needed before a transformation is no longer weighed",
    )

    candidacy_max_distance: int = Field(
        default=1,
        description="the maximum distance a candidate chemical can be from previously reached chemical systems",
    )

    decay_repeat_rate: float = Field(
        default=0.5,
        description="decay rate of the exponential repeat decay penalty factor",
    )

    decay_distance_rate: float = Field(
        default=0.5,
        description="decay rate of the exponential distance decay penalty factor",
    )

    @field_validator("max_runs", mode="before")
    def validate_max_runs(cls, value):
        if not value >= 1:
            raise ValueError("`max_runs` must be greater than or equal to 1")
        return value

    @field_validator("candidacy_max_distance", mode="before")
    def validate_candidtate_max_distance(cls, value):
        if not value >= 1:
            raise ValueError(
                "`candidtate_max_distance` must be greater than or equal to 1"
            )
        return value

    @field_validator("decay_repeat_rate", mode="before")
    def validate_decay_repeat_rate(cls, value):
        if not (0 < value < 1):
            raise ValueError("`decay_repeat_rate` must be between 0 and 1")
        return value

    @field_validator("decay_distance_rate", mode="before")
    def validate_decay_distance_rate(cls, value):
        if not (0 < value < 1):
            raise ValueError("`decay_distance_rate` must be between 0 and 1")
        return value


class RadialGrowthStrategy(Strategy):

    _settings_cls = RadialGrowthStrategySettings

    @classmethod
    def _default_settings(cls) -> StrategySettings:
        return RadialGrowthStrategySettings(max_runs=3)

    def _propose(
        self,
        alchemical_network: AlchemicalNetwork,
        protocol_results: dict[GufeKey, ProtocolResult],
    ) -> StrategyResult:

        alchemical_network_mdg = alchemical_network.graph
        weights: dict[GufeKey, float | None] = {}

        e = nx.eccentricity(alchemical_network_mdg.to_undirected())

        lowest_complete_eccentricity = max(e.values())
        transformation_eccentricity = {}

        for state_a, state_b in alchemical_network_mdg.edges():
            edge = e[state_a], e[state_b]
            lower, upper = min(edge), max(edge)

            transformation_key = alchemical_network_mdg.get_edge_data(state_a, state_b)[
                0
            ]["object"].key

            factor_distance = 1
            factor_repeats = 1

            match (protocol_results.get(transformation_key)):
                case None:
                    transformation_n_protcol_dag_results = 0
                    if upper < lowest_complete_eccentricity:
                        lowest_complete_eccentricity = lower
                case pr:
                    assert isinstance(pr, ProtocolResult)
                    transformation_n_protcol_dag_results = pr.n_protocol_dag_results
                    factor_repeats *= (
                        self.settings.decay_repeat_rate
                        ** transformation_n_protcol_dag_results
                    )

            # stop condition given max runs
            if self.settings.max_runs <= transformation_n_protcol_dag_results:
                weights[transformation_key] = None
                continue

            # save the upper eccentricity for later when we know the lowest_completed
            transformation_eccentricity[transformation_key] = upper

            weights[transformation_key] = factor_repeats

        distance_factor = 1
        for transformation_key, e in transformation_eccentricity.items():
            distance = e - lowest_complete_eccentricity

            if distance <= 1:
                distance_factor = 1
            if distance > self.settings.candidacy_max_distance:
                distance_factor = 0

            weights[transformation_key] *= distance_factor

        return StrategyResult(weights)
