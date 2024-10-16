#!/usr/bin/env python
# this file is part of gosam (generator of simple atomistic models)
# Licence: GNU General Public License version 2

import sys
from math import sin, cos, pi, atan, sqrt, degrees, radians, asin, acos
from copy import deepcopy
from optparse import OptionParser
from numpy import dot, array, identity, minimum, maximum

import graingen
import latt
import mdprim
from csl import find_orthorhombic_pbc
from rotmat import round_to_multiplicity
from utils import get_command_line

def get_diamond_node_pos():
    node_pos = []
    for i in graingen.fcc_nodes:
        node_pos.append(i)
        node_pos.append((i[0]+0.25, i[1]+0.25, i[2]+0.25))
    return node_pos


def make_lattice(cell, node_pos, node_atoms):
    nodes = [latt.Node(i, node_atoms) for i in node_pos]
    lattice = graingen.CrystalLattice(cell, nodes)
    return lattice


def make_simple_cubic_lattice(symbol, a):
    cell = latt.CubicUnitCell(a)
    node = latt.Node((0.0, 0.0, 0.0), [(symbol, 0.0, 0.0, 0.0)])
    return graingen.CrystalLattice(cell, [node])

def make_fcc_lattice(symbol, a):
    cell = latt.CubicUnitCell(a)
    node_pos = graingen.fcc_nodes[:]
    node_atoms = [ (symbol, 0.0, 0.0, 0.0) ]
    return make_lattice(cell, node_pos, node_atoms)

def make_bcc_lattice(symbol, a):
    cell = latt.CubicUnitCell(a)
    node_pos = graingen.bcc_nodes[:]
    node_atoms = [ (symbol, 0.0, 0.0, 0.0) ]
    return make_lattice(cell, node_pos, node_atoms)

def make_hcp_lattice(symbol, a,c):
    cell = latt.HexagonalUnitCell(a,c)
    node_pos =graingen.hcp_nodes[:]
    node_atoms = [
            (symbol,0.5 ,-0.866,0.25),
            (symbol,0.5 ,0.866,0.75),
            ]
    return make_lattice(cell,node_pos,node_atoms)


def make_zincblende_lattice(symbols, a):
    assert len(symbols) == 2
    cell = latt.CubicUnitCell(a)
    # nodes in unit cell (as fraction of unit cell parameters)
    node_pos = graingen.fcc_nodes[:]
    # atoms in node (as fraction of unit cell parameters)
    node_atoms = [
        (symbols[0], 0.0, 0.0, 0.0),
        (symbols[1], 0.25,0.25,0.25),
    ]
    return make_lattice(cell, node_pos, node_atoms)

def make_zincblende2_lattice(symbols, a):
    assert len(symbols) == 2
    cell = latt.CubicUnitCell(a)
    # nodes in unit cell (as fraction of unit cell parameters)
    node_pos = graingen.fcc_nodes[:]
    # atoms in node (as fraction of unit cell parameters)
    node_atoms = [
            (symbols[0], 0.0, 0.0, 0.0),
            (symbols[1], 0.25, 0.75, 0.75),
            ]
    return make_lattice(cell, node_pos, node_atoms)


def make_kesterite_structure(symbols, a, b, c):
    assert len(symbols) == 4
    cell = latt.OrthorhombicUnitCell(a,b,c)
    # nodes in unit cell (as fraction of unit cell parameters)
    node_pos = graingen.bcc_nodes[:]
    # atoms in node (as fraction of unit cell parameters)
    # (Cu In Ga Se)/(Cu Zn Ge S)
    node_atoms = [
            (symbols[0], 0.0, 0.0, 0.0),
            (symbols[1], 0.5, 0.5, 0.0),
            (symbols[0], 0.0, 0.5, 0.25),
            (symbols[2], 0.5, 0.0, 0.25),
            (symbols[1], 0.0, 0.0, 0.5),
            (symbols[0], 0.5, 0.5, 0.5),
            (symbols[2], 0.0, 0.5, 0.75),
            (symbols[0], 0.5, 0.0, 0.75),
            (symbols[3], 0.25, 0.25, 0.125),
            (symbols[3], 0.75, 0.75, 0.125),
            (symbols[3], 0.25, 0.75, 0.375),
            (symbols[3], 0.75, 0.25, 0.375),
            (symbols[3], 0.25, 0.25, 0.625),
            (symbols[3], 0.75, 0.75, 0.625),
            (symbols[3], 0.25, 0.75, 0.875),
            (symbols[3], 0.75, 0.25, 0.875)
            ]
    return make_lattice(cell, node_pos, node_atoms)


def make_stannite_structure(symbols, a, b, c):
    assert len(symbols) == 4
    cell = latt.OrthorhombicUnitCell(a,b,c)
    # nodes in unit cell (as fraction of unit cell parameters)
    node_pos = graingen.bcc_nodes[:]
    # atoms in node (as fraction of unit cell parameters)
    # (Cu In Ga Se)/(Cu Zn Ge S)
    node_atoms = [
            (symbols[0], 0.0, 0.0, 0.0),
            (symbols[0], 0.5, 0.5, 0.0),
            (symbols[1], 0.0, 0.5, 0.25),
            (symbols[2], 0.5, 0.0, 0.25),
            (symbols[0], 0.0, 0.0, 0.5),
            (symbols[0], 0.5, 0.5, 0.5),
            (symbols[2], 0.0, 0.5, 0.75),
            (symbols[1], 0.5, 0.0, 0.75),
            (symbols[3], 0.25, 0.25, 0.125),
            (symbols[3], 0.75, 0.75, 0.125),
            (symbols[3], 0.25, 0.75, 0.375),
            (symbols[3], 0.75, 0.25, 0.375),
            (symbols[3], 0.25, 0.25, 0.625),
            (symbols[3], 0.75, 0.75, 0.625),
            (symbols[3], 0.25, 0.75, 0.875),
            (symbols[3], 0.75, 0.25, 0.875)
            ]
    return make_lattice(cell, node_pos, node_atoms)


def make_sic_polytype_lattice(symbols, a, h, polytype):
    """a: hexagonal lattice parameter
       h: distance between atomic layers
       polytype: a string like "AB" or "ABCACB",
    """
    assert len(symbols) == 2
    # in the case of 3C (ABC) polytype with cubic lattice a_c:
    # a = a_c / sqrt(2); h = a_c / sqrt(3)
    cell, nodes = latt.generate_polytype(a=a, h=h, polytype=polytype)
    #atoms in node (as fraction of (a,a,h) parameters)
    node_atoms = [
        (symbols[0], 0.0, 0.0, 0.0),
        (symbols[1], 0.0, 0.0, 0.75 / len(polytype)),
    ]
    return make_lattice(cell, nodes, node_atoms)


def make_c_hexagonal_lattice(symbol,a,h,polytype):
    cell, nodes = graingen.generate_polytype(a=a, h=h, polytype=polytype)
    node_atoms = [
        (symbol[0], 0.0, 0.0, 0.0),
        (symbol[0], 0.0, 0.0, 0.75/ len(polytype)),
        ]
    return make_lattice(cell,nodes,node_atoms)

def make_mg_hexagonal_lattice(symbol, a, h, polytype):
    cell, nodes = graingen.generate_polytype(a=a, h=h, polytype=polytype)
    node_atoms = [
        (symbol[0], 0.0, 0.0, 0.0),
        (symbol[0], 0.0, 0.0, 0.75/ len(polytype)),
        ]
    return make_lattice(cell,nodes,node_atoms)

def make_diamond_lattice(symbol, a):
    cell = latt.CubicUnitCell(a)
    node_pos = get_diamond_node_pos()
    node_atoms = [ (symbol, 0.0, 0.0, 0.0) ]
    return make_lattice(cell, node_pos, node_atoms)


def make_nbo_lattice(symbols, a):
    assert len(symbols) == 2
    cell = latt.CubicUnitCell(a)
    node_pos = graingen.fcc_nodes[:]
    node_atoms = [
        (symbols[0], 0.0, 0.0, 0.0),
        (symbols[1], 0.5, 0.5, 0.5),
        ]
    return make_lattice(cell, node_pos, node_atoms)

def make_crnb_lattice(symbols,a):
    assert len(symbols) == 2
    cell = latt.CubicUnitCell(a)
    node_pos =graingen.fcc_nodes[:]
    node_atoms = [
        (symbols[1], 0.125, 0.125, 0.125),
        (symbols[1], 0.875, 0.875, 0.875),
        (symbols[0], 0.5, 0.5, 0.5),
        (symbols[0], 0.5, 0.25, 0.25),
        (symbols[0], 0.25, 0.5, 0.25),
        (symbols[0], 0.25, 0.25, 0.5),
        ]
    return make_lattice(cell, node_pos, node_atoms)


def make_nacl_lattice(symbols, a):
    assert len(symbols) == 2
    cell = latt.CubicUnitCell(a)
    node_pos = graingen.fcc_nodes[:]
    node_atoms = [
        (symbols[0], 0.0, 0.0, 0.0),
        (symbols[1], 0.5, 0.5, 0.5),
    ]
    return make_lattice(cell, node_pos, node_atoms)


def make_niti_lattice(symbols, a):
    assert len(symbols) == 2
    cell = latt.CubicUnitCell(a)
    node_pos = graingen.simple_nodes[:]
    node_atoms = [
            (symbols[0], 0.0,0.0,0.0),
            (symbols[1], 0.5,0.5,0.5),
    ]
    return make_lattice(cell, node_pos, node_atoms)

def make_tial_lattice(symbols,a,b,c):
    """ create TiAl LIO structure"""
    assert len(symbols) == 2
    cell = latt.OrthorhombicUnitCell(a,b,c)
    node_pos = graingen.bcc_nodes[:]
    node_atoms = [
            (symbols[0], 0.0,0.0,0.0),
            (symbols[1], 0.5,0.0,0.5),
            ]
    return make_lattice(cell,node_pos,node_atoms)


# body centered tetragonal
def make_bct_lattice(symbol, a, c):
    cell = latt.TetragonalUnitCell(a, c)
    node_pos = graingen.bcc_nodes[:]
    node_atoms = [ (symbol, 0.0, 0.0, 0.0) ]
    return make_lattice(cell, node_pos, node_atoms)

def make_lattice_from_cif(filename):
    try:
        import gemmi
    except ImportError:
        sys.exit('Gemmi is needed to read cif files. Try "pip install gemmi".')
    st = gemmi.read_atomic_structure(filename)
    cell = latt.UnitCell(st.cell.a, st.cell.b, st.cell.c,
                         st.cell.alpha, st.cell.beta, st.cell.gamma, system='')
    nodes = []
    for site in st.get_all_unit_cell_sites():
        pos = (site.fract.x, site.fract.y, site.fract.z)
        atom = latt.AtomInNode(site.type_symbol)
        nodes.append(latt.Node(pos, [atom]))
    return latt.CrystalLattice(cell, nodes)

class OrthorhombicPbcModel(graingen.FreshModel):
    def __init__(self, lattice, dimensions, title):
        pbc = identity(3) * dimensions
        graingen.FreshModel.__init__(self, lattice, pbc, title=title)

    def get_vertices(self):
        return [(x, y, z) for x in self._min_max[0]
                          for y in self._min_max[1]
                          for z in self._min_max[2]]

    def _do_gen_atoms(self, vmin, vmax):
        self._min_max = list(zip(vmin, vmax))
        self.compute_scope()
        print(self.get_scope_info())
        for node, abs_pos in self.get_all_nodes():
            for atom in node.atoms_in_node:
                xyz = dot(abs_pos+atom.pos, self.unit_cell.M_1)
                if (vmin < xyz).all() and (xyz <= vmax).all():
                    self.atoms.append(mdprim.Atom(atom.name, xyz))


class RotatedMonocrystal(OrthorhombicPbcModel):
    """Monocrystal rotated using rot_mat rotation matrix
    """
    def __init__(self, lattice, dim, rot_mat, title=None):
        self.lattice = lattice
        self.dim = array(dim, dtype=float)
        self.rot_mat = rot_mat
        if title is None:
            title = "generated by gosam.monocryst"
        OrthorhombicPbcModel.__init__(self, lattice, self.dim, title=title)

    def generate_atoms(self, upper=None, z_margin=0.):
        """upper and z_margin are used for building bicrystal
        """
        self.atoms = []
        vmin, vmax = self.get_box_to_fill(self.dim, upper, z_margin)
        if self.rot_mat is not None:
            self.unit_cell.rotate(self.rot_mat)
        self._do_gen_atoms(vmin, vmax)
        if upper is None:
            print("Number of atoms in monocrystal: {}".format(len(self.atoms)))
        return self.atoms

    def get_box_to_fill(self, dim, upper, z_margin):
        # make it a bit asymmetric, to avoid problems with PBC
        eps = 0.001
        vmin = -self.dim/2. + eps
        vmax = self.dim/2. + eps
        assert upper in (True, False, None)
        if upper is True:
            vmin[2] = eps
            if z_margin:
                vmax[2] -= z_margin / 2
        elif upper is False:
            vmax[2] = eps
            if z_margin:
                vmin[2] += z_margin / 2
        return vmin, vmax



# primitive adjusting of PBC box for [010] rotation
def test_rotmono_adjust():
    lattice = make_zincblende_lattice(symbols=("Si","C"), a=4.36)
    a = lattice.unit_cell.a
    dimensions = [10*a, 10*a, 10*a]
    theta = radians(float(sys.argv[1]))

    d = dimensions[0]
    n_ = d * sin(theta) / a
    m_ = d / (a * cos(theta))
    n = round(n_)
    m = round(m_)
    new_th = 0.5 * asin(2.*n/m)
    new_d = m * a * cos(new_th)
    print("theta = {}".format(degrees(new_th)) + "  d = {}".format(new_d))

    dimensions[0] = new_d
    dimensions[1] = round(dimensions[1] / a) * a
    theta = new_th

    rot_mat = rotmat.rodrigues((0,1,0), theta, verbose=False)
    config = RotatedMonocrystal(lattice, dimensions, rot_mat)
    config.generate_atoms()
    config.export_atoms("monotest.cfg", format="atomeye")


def mono(lattice, nx, ny, nz):
    min_dim = lattice.unit_cell.get_orthorhombic_supercell()
    dim = [round_to_multiplicity(min_dim[0], 10*nx),
           round_to_multiplicity(min_dim[1], 10*ny),
           round_to_multiplicity(min_dim[2], 10*nz)]
    print("dimensions [A]:", dim[0], dim[1], dim[2])
    config = RotatedMonocrystal(deepcopy(lattice), dim, rot_mat=None,
                                title=get_command_line())
    config.generate_atoms()
    return config

# To change lattice parameters or atomic symbols just modify this function.
def get_named_lattice(name):
    if name.endswith('.cif'):
        return make_lattice_from_cif(name)
    name = name.lower()
    if name == "cu": # Cu (fcc, A1)
        lattice = make_fcc_lattice(symbol="Cu", a=3.615)
    elif name == "al": # Al (fcc)
        lattice = make_fcc_lattice(symbol="Al", a=4.041)
    elif name == "ag": # Ag (fcc)
        lattice = make_fcc_lattice(symbol="Ag", a=4.09)
    elif name == "ni": # Ni (fcc)
        lattice = make_fcc_lattice(symbol="Ni", a=3.52)
    elif name == "pt" : # Pt (fcc)
        lattice = make_fcc_lattice(symbol="Pt", a=3.92)
    elif name == "fe": # Fe (bcc, A2)
        lattice = make_bcc_lattice(symbol="Fe", a=2.87)
    elif name == "nb": # Nb (bcc,B2)
        lattice = make_bcc_lattice(symbol="Nb", a=3.308)
    elif name == "w":
        lattice = make_bcc_lattice(symbol="W", a=3.165)
    elif name == "po": # Polonium (sc, Ah)
        lattice = make_simple_cubic_lattice(symbol="Po", a=3.35)
    elif name == "nacl": # NaCl (B1)
        lattice = make_nacl_lattice(symbols=("Na","Cl"), a=5.64)
    elif name =="niti": # NiTi (B2)
        lattice = make_niti_lattice(symbols=("Ni","Ti"), a=3.008)
    elif name == "cdte": # CdTe (zinc blende)
        lattice = make_zincblende2_lattice(symbols=("Cd","Te"), a=4.321)
    elif name == "cuznges": # Cu(In,Ga)Se2
        lattice = make_kesterite_structure(symbols=("Cu","Zn","Ge","S"), a=5.358, b=5.358, c=10.641)
    elif name == "cuznsnse": # Cu(In,Ga)Se2
        lattice = make_stannite_structure(symbols=("Cu","Zn","Ge","S"), a=5.358, b=5.358, c=10.641)
    elif name =="graphine": # graphine
        lattice = make_c_hexagonal_lattice(symbol="C",a =3.07,h=2.52,polytype="ABABC")
    elif name =="mg":
        lattice = make_mg_hexagonal_lattice(symbol="Mg", a=3.183,h=2.06, polytype="ABAB")
    elif name =="crnb":
        lattice = make_crnb_lattice(symbols=("Cr","Nb"),a=6.5)
    elif name =="nbo" :
        lattice = make_nbo_lattice(symbols=("Nb","O"), a=3.32)
    elif name =="tial": # TiAl (Li0)
        lattice = make_tial_lattice(symbols=("Ti","Al"), a=4.0,b=4.0,c=4.0)
    elif name == "sic": # SiC (zinc blende structure, B3)
        # 4.3210368 A - value for Tersoff (1989) MD potential
        # 4.36 A - real value
        lattice = make_zincblende_lattice(symbols=("Si","C"), a=4.3210368)
    elif name == "si": # Si (diamond structure, A4)
        lattice = make_diamond_lattice(symbol="Si", a=5.43)
    elif name == "diamond": # C (diamond structure, A4)
        lattice = make_diamond_lattice(symbol="C", a=3.567)
    elif name.startswith("sic:"): # SiC-like (binary, tetrahedral) polytype
        lattice = make_sic_polytype_lattice(symbols=("Si","C"), a=3.073, h=2.52,
                                            polytype=name[4:])
    elif name == "sn": # Sn, body-centered tetragonal
        lattice = make_bct_lattice(symbol="Sn", a=5.83, c=3.18)
    else:
        raise ValueError("Unknown lattice: %s" % name)
    return lattice


usage = """monocryst.py [options] crystal nx ny nz output_filename
 where nx, ny, nz are minimal dimensions in nm,
 crystal is a one of predefined lattice types (case insensitive):
 Cu, Fe, NaCl, Si, diamond, SiC, SiC:ABABC.
 In the last case, any polytype can be given after colon."""

def main():
    parser = OptionParser(usage)
    parser.add_option("--margin", type="float",
                      help="increase PBC by given margin (of vacuum)")
    parser.add_option("--center-zero", action="store_true",
                      help="shift center to (0, 0, 0)")
    (options, args) = parser.parse_args(sys.argv)
    if len(args) == 1:
        parser.print_help()
        sys.exit()
    if len(args) != 6:
        parser.error("5 arguments are required, not %d" % (len(args) - 1))

    lattice = get_named_lattice(args[1])
    nx, ny, nz = float(args[2]), float(args[3]), float(args[4])
    config = mono(lattice, nx, ny, nz)
    if options.center_zero:
        print("centering...")
        m = config.atoms[0].pos.copy()
        M = config.atoms[0].pos.copy()
        for atom in config.atoms:
            m = minimum(m, atom.pos)
            M = maximum(M, atom.pos)
        ctr = (m + M) / 2.
        for atom in config.atoms:
            atom.pos -= ctr
    if options.margin is not None:
        margin = options.margin * 10
        print("adding margins {0} A".format(margin))
        for i in range(3):
            config.pbc[i][i] += margin
    config.export_atoms(args[5])

if __name__ == '__main__':
    main()
