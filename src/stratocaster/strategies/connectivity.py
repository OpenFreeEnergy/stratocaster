from typing import Optional
from gufe import AlchemicalNetwork, ProtocolResult
from gufe.tokenization import GufeKey

from stratocaster.base import Strategy, StrategyResult
from stratocaster.base.models import StrategySettings

from pydantic import field_validator


class ConnectivityStrategySettings(StrategySettings):

    decay_rate: float = 0.5
    cutoff: Optional[float] = None
    max_runs: Optional[int] = None

    @field_validator("cutoff", "decay_rate")
    def validate_cutoff(cls, value):
        if not (0 < value < 1):
            raise ValueError("value must be between 0 and 1")
        return value


class ConnectivityStrategy(Strategy):

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

        settings = self._settings

        alchemical_network_mdg = alchemical_network.graph
        weights: dict[GufeKey, Optional[float]] = {}

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
                    transformation_num_components = 0
                case pr:
                    transformation_num_components = pr.num_components

            scaling_factor = self._exponential_decay_scaling(
                transformation_num_components, settings["decay_rate"]
            )
            weight = scaling_factor * (num_neighbors_a + num_neighbors_b) / 2

            match (settings.get("max_runs", None), settings.get("cutoff")):
                case (None, cutoff):
                    if weight < cutoff:
                        weight = None
                case (max_runs, None):
                    if transformation_num_components >= max_runs:
                        weight = None
                case (max_runs, cutoff):
                    if weight < cutoff or transformation_num_components >= max_runs:
                        weight = None

            weights[transformation_key] = weight

        results = StrategyResult(weights=weights)
        return results

    @classmethod
    def _default_settings(cls) -> StrategySettings:
        return StrategySettings()
