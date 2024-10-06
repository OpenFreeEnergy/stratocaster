from gufe import AlchemicalNetwork, ProtocolResult

from stratocaster.base import Strategy, StrategyResult
from stratocaster.base.models import StrategySettings


class ConnectivityStrategy(Strategy):

    def _propose(
        self,
        alchemical_network: AlchemicalNetwork,
        protocol_results: list[ProtocolResult],
    ) -> StrategyResult:

        alchemical_network_mdg = alchemical_network.graph
        weights = {}

        for state_a, state_b in alchemical_network_mdg.edges():
            num_neighbors_a = len(list(alchemical_network_mdg.neighbors(state_a)))
            num_neighbors_b = len(list(alchemical_network_mdg.neighbors(state_b)))
            transformation_key = alchemical_network_mdg.get_edge_data(state_a, state_b)[
                0
            ]["object"].key
            weights[transformation_key] = (num_neighbors_a + num_neighbors_b) / 2

        results = StrategyResult(weights=weights)
        return results

    @classmethod
    def _default_settings(cls) -> StrategySettings:
        return StrategySettings()
