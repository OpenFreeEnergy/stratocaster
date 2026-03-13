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

You can calculate transformation weights for an ``AlchemicalNetwork``, ``alchem_network`` by calling a strategy's ``propose`` method.


.. code:: python

   from stratocaster.strategies import ConnectivityStrategy

   settings = ConnectivityStrategy.default_settings()
   strategy = ConnectivityStrategy(settings)

   previous_results: dict[GufeKey, ProtocolResult] = {}

   strategy_result: StrategyResult = strategy.propose(alchem_network, previous_results)


This returns a ``StrategyResult`` object, which is a mapping between the transformations in an ``AlchemicalNetwork`` and the weights determined by the strategy.
``None`` weights are a terminating case: a transformation with a ``None`` weight won't be proposed again and a ``StrategyResult`` with only ``None`` weights is "complete".

Calls to ``propose`` are deterministic and guaranteed to reach a terminating condition if the resulting weights are used to update the ``ProtocolResult`` objects in ``previous_results``.

Other resources
~~~~~~~~~~~~~~~

- `Source code repository <https://github.com/OpenFreeEnergy/stratocaster>`_
- `GitHub issue tracker <https://github.com/OpenFreeEnergy/stratocaster/issues>`_

