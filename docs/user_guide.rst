User guide
==========

A ``Strategy`` is an algorithm that assists in traversing the execution path of transformations within ``gufe`` ``AlchemicalNetwork`` objects.
It removes the burden for an individual or execution engine to determine which transformations in a network must be performed and how important one transformation is relative to another given results that have already been collected.
For instance, transformations with many previously calculated repeats might have a lower priority compared to transformations that haven't been performed at all.
As results are accumulated, the strategy eventually reaches a terminating condition where no weights are presented.
While the details of selecting and running a transformation from the weights is out of scope for ``stratocaster``, the following code demonstrates where a strategy might fit in an iterative execution workflow.

.. code:: python

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


A ``None`` weight for a transformation means the transformation should not be performed again as more results are added.
This differs from a zero weight, which could mean the transformation will eventually be proposed again with more results.

Defining a new ``Strategy``
---------------------------

A new ``Strategy`` implementation requires definitions of a new ``Strategy`` subclass along with a ``StrategySettings`` subclass specific to the new strategy.

The new ``StrategySettings`` is the mechanism by which a user will alter behavior of the new ``Strategy``.
As such, it should define the relevant variables on which the ``Strategy`` will depend.
In the below example, we include only a ``max_runs`` setting, which is usually enough to guarantee that the strategy reaches a termination condition.

The new ``Strategy`` implementation involves three main steps: 1) linking the strategy to its settings class, 2) defining the ``_default_settings`` class method, and 3) defining the ``_propose`` method.

.. literalinclude:: newstrat.py

A definition of ``_settings_cls`` provides a guardrail by preventing a user of your strategy from supplying an unexpected settings type.
Defining ``_default_settings`` allows a user to get the default settings through ``MyCustomStrategy.default_settings()``.
If your settings provide an exhaustive set of default options, simply return an instance of your settings without providing hard-coded keyword arguments.

Lastly, the ``_propose`` method implementation determines the results of a strategy prediction based on the ``AlchemicalNetwork``, prior results from executing ``Transformation`` protocols, and your settings.
This method should be deterministic: repeated proposals given the same set of results will yield the same ``StrategyResult``.
It should also have a clear termination condition.
If results are accumulated as a result of the recommendations provided by the strategy, the ``StrategyResult`` will eventually return ``None`` weights for all transformations in the network.
