import networkx as nx

from gufe import AlchemicalNetwork, ProtocolResult
from gufe.transformations import Transformation, NonTransformation

from pydantic import (
    Field,
    field_validator,
)

from stratocaster.base import Strategy, StrategyResult
from stratocaster.base.models import StrategySettings


class RadialGrowthStrategySettings(StrategySettings):
    """Settings required for the RadialGrowthStrategy."""

    max_runs: int = Field(
        default=3,
        description="the upper limit of ProtocolDAG results needed before a Transformation is no longer weighed",
    )

    candidacy_max_distance: int = Field(
        default=1,
        description="the maximum distance a candidate ChemicalSystem can be from previously reached ChemicalSystems",
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
    def validate_candidate_max_distance(cls, value):
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
    r"""A Strategy that favors Transformations close to the network
    center.

    The weight assigned to each Transformation depends on its highest
    ChemicalSystem distance, as measured and labeled by the vertex
    eccentricty, from the lowest completed tier of distances. In the
    graph below, if at least one ``ProtocolDAGResult`` exists for both
    edges in 3-2-3, the lowest completed distance is 3. If neither
    edge or only one edge has a result, the lowest completed distance
    is 2. In the former case, a transformation going from 3 to 4 has
    an effective distance of 1, while in the latter case it has a
    distance of 2.

    .. code-block::

        4         4
         \       /
          \     /
        4--3-2-3--4
          /     \
         /       \
        4         4

    The strategy penalizes transformations that have high effective
    distances by multiplying the weight with a penalty of :math:`r^d`, where r
    is a user-specified decay rate and d is the effective
    distance. The ``candidacy_max_distance`` setting limits how far
    out transformations can be assigned non-zero weights.

    """

    _settings_cls = RadialGrowthStrategySettings

    @classmethod
    def _default_settings(cls) -> StrategySettings:
        return RadialGrowthStrategySettings(max_runs=3)

    def _propose(
        self,
        alchemical_network: AlchemicalNetwork,
        protocol_results: dict[Transformation | NonTransformation, ProtocolResult],
    ) -> StrategyResult:
        """Propose `Transformation` weight recommendations based on
        `Transformation` distance from the graph center.

        Parameters
        ----------
        alchemical_network
        protocol_results
            A dictionary whose keys are the `Transformation`s (or `NonTransformation`s)
            in the `AlchemicalNetwork` and whose values are the `ProtocolResult`s for
            those `Transformation`s.

        Returns
        -------
        StrategyResult
            A `StrategyResult` containing the proposed `Transformation` weights.

        """

        alchemical_network_mdg = alchemical_network.graph
        weights: dict[Transformation | NonTransformation, float | None] = {}

        # calculate all node eccentricies
        e = nx.eccentricity(alchemical_network_mdg.to_undirected())

        # start with the maximum value, this will be decremented as we
        # see evidence the value should be lower
        lowest_complete_eccentricity = max(e.values())
        # hold on to the eccentricies of the transformations instead
        # of the distances since we don't know the lowest complete
        # eccentricity until we process the full graph, distances can
        # be calculated after
        transformation_eccentricity = {}

        for state_a, state_b in alchemical_network_mdg.edges():
            edge = e[state_a], e[state_b]
            # find the range of eccentricies
            lower, upper = min(edge), max(edge)

            transformation = alchemical_network_mdg.get_edge_data(state_a, state_b)[0][
                "object"
            ]

            factor_repeats = 1
            match (protocol_results.get(transformation)):
                case None:
                    transformation_n_protcol_dag_results = 0
                    # since we have no results for this
                    # transformation, we know the lowest complete
                    # eccentricity must be lower than the upper
                    # eccentricity of the transformation
                    if upper < lowest_complete_eccentricity:
                        lowest_complete_eccentricity = lower
                case pr:
                    transformation_n_protcol_dag_results = pr.n_protocol_dag_results
                    # scale the repeat factor to discourage reruns as
                    # specified by the user's decay_repeat_rate
                    factor_repeats *= (
                        self.settings.decay_repeat_rate
                        ** transformation_n_protcol_dag_results
                    )

            # stop condition given max runs
            if self.settings.max_runs <= transformation_n_protcol_dag_results:
                weights[transformation] = None
                continue

            # save the upper eccentricity for later when we know the
            # lowest_completed. This is the transformation's effective
            # distance from the center
            transformation_eccentricity[transformation] = upper
            weights[transformation] = factor_repeats

        # start applying weights due to effective distance
        for transformation, e in transformation_eccentricity.items():
            distance = e - lowest_complete_eccentricity

            if distance <= self.settings.candidacy_max_distance:
                # edge case where there are multiple vertices with
                # eccentricity equal to graph radius
                if distance == 0:
                    distance_factor = 1
                else:
                    # scale the distance factor to limit the
                    # calculation of far-out transformations
                    distance_factor = self.settings.decay_distance_rate ** (
                        distance - 1
                    )
            else:
                # set to zero, not None
                distance_factor = 0

            weights[transformation] *= distance_factor

        return StrategyResult(weights)
