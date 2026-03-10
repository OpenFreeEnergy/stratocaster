import pytest

from stratocaster.tests.networks import (
    benzene_variants_star_map as _benzene_variants_star_map,
    fanning_network as _fanning_network,
    disconnected_fanning_network as _disconnected_fanning_network,
)


@pytest.fixture(scope="module")
def benzene_variants_star_map():
    return _benzene_variants_star_map()


@pytest.fixture(scope="module")
def fanning_network():
    return _fanning_network()


@pytest.fixture(scope="module")
def disconnected_fanning_network():
    return _disconnected_fanning_network()
