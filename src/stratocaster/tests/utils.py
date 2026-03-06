from random import randint, shuffle

import pytest

from gufe.tests.test_protocol import DummyProtocolResult


class StrategyTestMixin:

    _default_strategy = None
    _default_settings = None

    @property
    def default_strategy(self):
        if not self._default_strategy:
            self._default_strategy = self.strategy_class(self.default_settings)
        return self._default_strategy

    @property
    def default_settings(self):
        if not self._default_settings:
            self._default_settings = self.strategy_class._default_settings()
        return self._default_settings

    def strategy_or_default(self, settings):
        return self.strategy_class(settings) if settings else self.default_strategy

    def test_deterministic(self, fanning_network, settings=None):

        strategy = self.strategy_or_default(settings)

        def random_runs():
            """Generate random randomized inputs for propose."""
            return {
                transformation.key: DummyProtocolResult(
                    n_protocol_dag_results=randint(0, 3),
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

    def test_starts(self, fanning_network, settings=None):

        strategy = self.strategy_or_default(settings)

        proposal: StrategyResult = strategy.propose(fanning_network, {})
        # check that there is at least 1 non-None weight
        assert any(proposal.weights.values())

    def test_disconnected(
        self,
        disconnected_fanning_network,
        settings=None,
    ):
        strategy = self.strategy_or_default(settings)
        strategy.propose(disconnected_fanning_network, {})

    def test_simulated_termination(self, fanning_network, settings=None):

        strategy = self.strategy_or_default(settings)

        def counts_to_result_data(counts_dict):
            result_data = {}
            for transformation_key, count in counts_dict.items():
                result = DummyProtocolResult(
                    n_protocol_dag_results=count, info=f"key: {transformation_key}"
                )
                result_data[transformation_key] = result
            return result_data

        def shuffle_take_n(keys_list, n):
            shuffle(keys_list)
            return keys_list[:n]

        # initial transforms
        transformation_counts = {
            transformation.key: 0 for transformation in fanning_network.edges
        }

        max_iterations = 100
        current_iteration = 0
        while current_iteration <= max_iterations:

            if current_iteration == max_iterations:
                raise RuntimeError(
                    f"Strategy did not terminate in {max_iterations} iterations "
                )

            result_data = counts_to_result_data(transformation_counts)
            proposal = strategy.propose(fanning_network, result_data)

            # get random transformations from those with a non-None weight
            resolved_keys = shuffle_take_n(
                [
                    key
                    for key, weight in proposal.resolve().items()
                    if weight is not None
                ],
                5,
            )

            if resolved_keys:
                # pretend we ran each of the randomly selected protocols
                for key in resolved_keys:
                    transformation_counts[key] += 1
            # if we got an empty list back, there are not more protocols to run
            else:
                break
            current_iteration += 1
