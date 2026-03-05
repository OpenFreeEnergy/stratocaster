"""
This file contains a modified version of code originally from the
gufe test module (conftest.py). The modifications were made to allow
easier construction of AlchemicalNetworks for development testing and
user examples.

Original Commit SHA: 71a9c6610a9e13c8f7d588bd8309150557f104a5
"""

import importlib

import gufe
from gufe.tests.test_protocol import DummyProtocol
import networkx as nx
from openff.units import unit
from rdkit import Chem


class BenzeneModifications:

    @staticmethod
    def load_benzene_modifications():
        path = (
            importlib.resources.files("gufe.tests.data") / "benzene_modifications.sdf"
        )
        supp = Chem.SDMolSupplier(str(path), removeHs=False)
        return {m.GetProp("_Name"): m for m in list(supp)}

    _mod = load_benzene_modifications()

    def __class_getitem__(cls, key):
        return gufe.SmallMoleculeComponent(cls._mod[key])


def PDB_181L_path():
    path = importlib.resources.files("gufe.tests.data") / "181l.pdb"
    return str(path)


def benzene_variants_star_map_transformations():

    benzene = BenzeneModifications["benzene"]

    variants = tuple(
        map(
            lambda x: BenzeneModifications[x],
            [
                "toluene",
                "phenol",
                "benzonitrile",
                "anisole",
                "benzaldehyde",
                "styrene",
            ],
        )
    )

    solv_comp = gufe.SolventComponent(
        positive_ion="K", negative_ion="Cl", ion_concentration=0.0 * unit.molar
    )
    prot_comp = gufe.ProteinComponent.from_pdb_file(PDB_181L_path())

    # define the solvent chemical systems and transformations between
    # benzene and the others
    solvated_ligands = {}
    solvated_ligand_transformations = {}

    solvated_ligands["benzene"] = gufe.ChemicalSystem(
        {"solvent": solv_comp, "ligand": benzene}, name="benzene-solvent"
    )

    for ligand in variants:
        solvated_ligands[ligand.name] = gufe.ChemicalSystem(
            {"solvent": solv_comp, "ligand": ligand}, name=f"{ligand.name}-solvnet"
        )
        solvated_ligand_transformations[("benzene", ligand.name)] = gufe.Transformation(
            solvated_ligands["benzene"],
            solvated_ligands[ligand.name],
            protocol=DummyProtocol(settings=DummyProtocol.default_settings()),
            mapping=None,
        )

    # define the complex chemical systems and transformations between
    # benzene and the others
    solvated_complexes = {}
    solvated_complex_transformations = {}

    solvated_complexes["benzene"] = gufe.ChemicalSystem(
        {"protein": prot_comp, "solvent": solv_comp, "ligand": benzene},
        name="benzene-complex",
    )

    for ligand in variants:
        solvated_complexes[ligand.name] = gufe.ChemicalSystem(
            {"protein": prot_comp, "solvent": solv_comp, "ligand": ligand},
            name=f"{ligand.name}-complex",
        )
        solvated_complex_transformations[("benzene", ligand.name)] = (
            gufe.Transformation(
                solvated_complexes["benzene"],
                solvated_complexes[ligand.name],
                protocol=DummyProtocol(settings=DummyProtocol.default_settings()),
                mapping=None,
            )
        )

    return list(solvated_ligand_transformations.values()), list(
        solvated_complex_transformations.values()
    )


def benzene_variants_star_map():
    solvated_ligand_transformations, solvated_complex_transformations = (
        benzene_variants_star_map_transformations()
    )
    return gufe.AlchemicalNetwork(
        solvated_ligand_transformations + solvated_complex_transformations
    )


def digraph_to_alchemical_network(digraph):
    """Convert a digraph to an AlchemicalNetwork."""
    node_to_chemical_system = lambda n: gufe.ChemicalSystem({}, name=n)

    transformations = []
    for a, b in digraph.edges():
        c_a = node_to_chemical_system(a)
        c_b = node_to_chemical_system(b)
        protocol = None
        transformation = gufe.Transformation(
            c_a, c_b, DummyProtocol(settings=DummyProtocol.default_settings())
        )
        transformations.append(transformation)

    return gufe.AlchemicalNetwork(transformations)


def int_sampler(sampler_start=0):
    num = sampler_start
    while True:
        yield num
        num += 1


def fanning_network(branch=3, depth=3):
    """Generate a network with a central node that recursively "fans"
    out.  Branch determines how many edges branch off of each node
    while depth determines how many times the process is repeated.
    """
    G = nx.DiGraph()
    G.add_edges_from(fan(0, branch=branch, depth=depth))
    an = digraph_to_alchemical_network(G)
    return an


def dual_center_fanning_network(branch=3, depth=3):
    """Generate a network with two central nodes that recursively
    "fan" out.  Branch determines how many edges branch off of each
    node while depth determines how many times the process is
    repeated.
    """

    G = nx.DiGraph()

    edges = {(0, 1)}

    sampler = int_sampler(sampler_start=2)
    edges |= fan(0, branch=branch, depth=depth, id_generator=sampler)
    edges |= fan(1, branch=branch, depth=depth, id_generator=sampler)

    G.add_edges_from(edges)

    an = digraph_to_alchemical_network(G)
    return an


def disconnected_fanning_network(branch=3, depth=3):
    """Generate a network with disconnected fanning subgraphs."""

    G = nx.DiGraph()

    edges = set()

    sampler = int_sampler(sampler_start=2)
    edges |= fan(0, branch=branch, depth=depth, id_generator=sampler)
    edges |= fan(1, branch=branch, depth=depth, id_generator=sampler)

    G.add_edges_from(edges)

    assert not nx.is_connected(G.to_undirected())

    an = digraph_to_alchemical_network(G)
    return an


def fan(node, branch=3, depth=3, id_generator=None):
    """Recursive edge generator."""

    id_generator = id_generator or int_sampler(sampler_start=node + 1)

    if depth == 0:
        return set()

    edges = {(node, next(id_generator)) for _ in range(branch)}

    for _, next_node in edges.copy():
        edges |= fan(next_node, depth=depth - 1, id_generator=id_generator)

    return edges
