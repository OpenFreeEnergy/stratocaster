Getting Started
===============

This guide will help you quickly get started using stratocaster.

1. Installation
~~~~~~~~~~~~~~~

For installation instructions, refer to the :ref:`installation page<installation-label>`.

2. Verify the installation
~~~~~~~~~~~~~~~~~~~~~~~~~~

Verify the installation was successful in a Python interpreter

.. code:: python

   import statocaster
   print(stratocaster.__version__)

3. Quick-start example
~~~~~~~~~~~~~~~~~~~~~~

You can calculate transformation weights for an :external+gufe:py:class:`~gufe.network.AlchemicalNetwork`, ``alchem_network`` by calling a strategy's ``propose`` method.


.. code:: python

   from stratocaster.strategies import ConnectivityStrategy

   settings = ConnectivityStrategy.default_settings()
   strategy = ConnectivityStrategy(settings)

   previous_results: dict[Transformation | NonTransformation, ProtocolResult] = {}

   strategy_result: StrategyResult = strategy.propose(alchem_network, previous_results)


This returns a :py:class:`~stratocaster.base.strategy.StrategyResult` object, which is a mapping between the transformations in an :external+gufe:py:class:`~gufe.network.AlchemicalNetwork` and the weights determined by the strategy.
``None`` weights are a terminating case: a transformation with a ``None`` weight won't be proposed again and a :py:class:`~stratocaster.base.strategy.StrategyResult` with only ``None`` weights is "complete".

Calls to ``propose`` are deterministic and guaranteed to reach a terminating condition if the resulting weights are used to update the :external+gufe:py:class:`~gufe.protocols.protocol.ProtocolResult` objects in ``previous_results``.
See the :ref:`user guide<user-guide-label>` for an example of this process.

Other resources
~~~~~~~~~~~~~~~

- `Source code repository <https://github.com/OpenFreeEnergy/stratocaster>`_
- `GitHub issue tracker <https://github.com/OpenFreeEnergy/stratocaster/issues>`_

