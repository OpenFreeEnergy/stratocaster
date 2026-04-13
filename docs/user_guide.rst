.. _user-guide-label:

User Guide
==========

A ``Strategy`` is an algorithm that assists in traversing the execution path of transformations within ``gufe`` ``AlchemicalNetwork`` objects.
It removes the burden for an individual or execution engine to determine which transformations in a network must be performed and how important one transformation is relative to another given results that have already been collected.
For instance, transformations with many previously calculated repeats might have a lower priority compared to transformations that haven't been performed at all.
This prioritization is encoded by transformation weights, which are presented for an ``AlchemicalNetwork`` given a set of previously computed results.
As results are accumulated, the strategy must eventually reach a terminating condition where no weights are presented.
Additionally, valid strategies are deterministic, i.e. networks with a fixed set of previous results always return the same weights.
While the details of selecting and running a transformation from the weights is out of scope for ``stratocaster``, the following code demonstrates where a strategy might fit in an iterative execution workflow.

.. literalinclude:: ./code/iterative.py

A ``None`` weight for a transformation means the transformation should not be performed again as more results are added.
This differs from a zero weight, which could mean the transformation will eventually be proposed again with more results.
Note that before ``resolve`` is called, which returns a normalized set of weights, the magnitudes of the weights are arbitrary and may reflect the underlying logic behind the specific strategy implementation.
For example, the ``ConnectivityStrategy`` weights are, before correcting for repeated calculations, the average number of connections of the transformations' end states.
Therefore, the pre-normalization weights directly report properties of the many subgraphs in the ``AlchemicalNetwork``.

Defining a new ``Strategy``
---------------------------

A new ``Strategy`` implementation requires definitions of a new ``Strategy`` subclass along with a ``StrategySettings`` subclass specific to the new strategy.

The new ``StrategySettings`` is the mechanism by which a user will alter behavior of the new ``Strategy``.
As such, it should define the relevant variables on which the ``Strategy`` will depend.
In the below example, we include only a ``max_runs`` setting, which is usually enough to guarantee that the strategy reaches a termination condition.

The new ``Strategy`` implementation involves three main steps: 1) linking the strategy to its settings class, 2) defining the ``_default_settings`` class method, and 3) defining the ``_propose`` method.

.. literalinclude:: ./code/newstrat.py

A definition of ``_settings_cls`` provides a guardrail by preventing a user of your strategy from supplying an unexpected settings type.
Defining ``_default_settings`` allows a user to get the default settings through ``MyCustomStrategy.default_settings()``.
If your settings provide an exhaustive set of default options, simply return an instance of your settings without providing hard-coded keyword arguments.

Lastly, the ``_propose`` method implementation determines the results of a strategy prediction based on the ``AlchemicalNetwork``, prior results from executing ``Transformation`` protocols, and your settings.
This method should be deterministic: repeated proposals given the same set of results will yield the same ``StrategyResult``.
It should also have a clear termination condition.
If results are accumulated as a result of the recommendations provided by the strategy, the ``StrategyResult`` will eventually return ``None`` weights for all transformations in the network.
