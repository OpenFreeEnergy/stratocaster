.. _installation-label:

Installation
============

The only requirement for installing statocaster is a working installation of gufe with a version 1.2.0 or higher.
For general use, we recommend installing from the conda-forge channel, which will also install gufe in the process.

conda-forge channel
~~~~~~~~~~~~~~~~~~~

If you use conda, stratocaster can be installed through the conda-forge channel.

.. code::

   conda create -n statocaster-env
   conda activate stratocaster-env
   conda install -c conda-forge stratocaster

Development version
~~~~~~~~~~~~~~~~~~~

If you want to install the latest development version of stratocaster, you can do so using pip, provided that you have a working installation of gufe (version >=1.2.0) in your environment.

.. code::

   pip install git+https://github.com/OpenFreeEnergy/stratocaster.git@main

