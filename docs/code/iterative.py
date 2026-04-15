import random
from stratocaster.strategies import ConnectivityStrategy

settings = ConnectivityStrategy.default_settings()
strategy = ConnectivityStrategy(settings)

previous_results = {}
# a loop that will eventually end
while True:
    strategy_result = strategy.propose()
    normalized_weights = strategy_result.resolve()
    # check if there are any weights
    if not any(weights.values()):
        break

    # Pick a transformation from the weights, run it, update previous_results.
    # This functionality lies outside of the scope of stratocaster.
    run_and_update_previous_results(alchem_network,
                                    previous_results,
                                    strategy_result)

