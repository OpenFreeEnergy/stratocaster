from random import randint
from gufe.tests.test_protocol import DummyProtocolResult


class StrategyTestMixin:

    _default_strategy = None

    @property
    def default_strategy(self):
        if not self._default_strategy:
            _settings = self.strategy_class._default_settings()
            self._default_strategy = self.strategy_class(_settings)
        return self._default_strategy

    def test_deterministic(self, fanning_network):
        settings = self.default_strategy.settings

        max_runs = settings.max_runs
        assert isinstance(max_runs, int)

        def random_runs():
            """Generate random randomized inputs for propose."""
            return {
                transformation.key: DummyProtocolResult(
                    n_protocol_dag_results=randint(0, max_runs),
                    info=f"key: {transformation.key}",
                )
                for transformation in fanning_network.edges
            }

        for _ in range(10):
            random_protocol_results = random_runs()
            proposal = self.default_strategy.propose(
                fanning_network, protocol_results=random_protocol_results
            )
            for _ in range(3):
                _proposal = self.default_strategy.propose(
                    fanning_network, protocol_results=random_protocol_results
                )
                assert _proposal == proposal

    def test_starts(self, fanning_network):
        proposal: StrategyResult = self.default_strategy.propose(fanning_network, {})
        # check that there is at least 1 non-None weight
        assert any(proposal.weights.values())

    def test_disconnected(
        self,
        disconnected_fanning_network,
    ):
        self.default_strategy.propose(disconnected_fanning_network, {})
