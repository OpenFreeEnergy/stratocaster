.. image:: assets/logo/stratocaster_logo_full.png
   :height: 300px
   :alt: stratocaster logo

#######################################################################
alchemical effort allocation, automated
#######################################################################

**stratocaster** introduces the concept of a ``Strategy`` to the `Open Free Energy`_ ecosystem: given an ``AlchemicalNetwork`` and any existing results for its ``Transformation``\s, a ``Strategy`` proposes where to apply additional computational effort to produce result data in an "optimal" way.
Different ``Strategy`` implementations define "optimal" differently, with the choice of ``Strategy`` left to users.

**stratocaster** includes many such ``Strategy`` implementations, as well as base classes and instructions to help users create their own.
A ``Strategy`` can be used in directly on its own, or in combination with an automated execution system such as `alchemiscale`_ or `exorcist`_.

.. _Open Free Energy: https://openfree.energy/
.. _alchemiscale: https://alchemiscale.org/
.. _exorcist: https://github.com/OpenFreeEnergy/exorcist

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   :hidden:

   installation
   getting_started
   user_guide
   developer_guide
   api
