"""Coupling Element module.

This module defines the CouplingElement class which will be used to represent the coupling
between two rotor shaft, which add mainly stiffness, mass and inertia to the system.
There're 2 options, an element with 4 or 6 degrees of freedom.
"""

import numpy as np
from plotly import graph_objects as go

from ross.shaft_element import ShaftElement, ShaftElement6DoF
from ross.units import Q_, check_units

__all__ = ["CouplingElement", "CouplingElement6DoF"]


class CouplingElement(ShaftElement):
    """A coupling element.

    This class creates a coupling element from input data of inertia and mass
    from the left station and right station, and also translational and rotational
    stiffness and damping values. The matrices will be defined considering the
    same local coordinate vector of the `ShaftElement`.

    Parameters
    ----------
    m_l : float, pint.Quantity
        Mass of the left station of coupling element.
    m_r : float, pint.Quantity
        Mass of the right station of coupling element.
    Ip_l : float, pint.Quantity
        Polar moment of inertia of the left station of the coupling element.
    Ip_r : float, pint.Quantity
        Polar moment of inertia of the right station of the coupling element.
    Id_l : float, pint.Quantity, optional
        Diametral moment of inertia of the left station of the coupling element.
        If not given, it is assumed to be half of `Ip_l`.
    Id_r : float, pint.Quantity, optional
        Diametral moment of inertia of the right station of the coupling element.
        If not given, it is assumed to be half of `Ip_r`.
    kt_x : float, optional
        Translational stiffness in `x`.
        Default is 0.
    kt_y : float, optional
        Translational stiffness in `y`.
        Default is 0.
    kr_x : float, optional
        Rotational stiffness in `x`.
        Default is 0.
    kr_y : float, optional
        Rotational stiffness in `y`.
        Default is 0.
    ct_x : float, optional
        Translational damping in `x`.
        Default is 0.
    ct_y : float, optional
        Translational damping in `y`.
        Default is 0.
    cr_x : float, optional
        Rotational damping in `x`.
        Default is 0.
    cr_y : float, optional
        Rotational damping in `y`.
        Default is 0.
    L : float, optional
        Element length (m).
    n : int, optional
        Element number (coincident with it's first node).
        If not given, it will be set when the rotor is assembled
        according to the element's position in the list supplied to
        the rotor constructor.
    tag : str, optional
        A tag to name the element
        Default is None
    color : str, optional
        A color to be used when the element is represented.
        Default is '#add8e6'.

    Examples
    --------
    """

    @check_units
    def __init__(
        self,
        m_l,
        m_r,
        Ip_l,
        Ip_r,
        Id_l=0,
        Id_r=0,
        kt_x=0,
        kt_y=0,
        kr_x=0,
        kr_y=0,
        ct_x=0,
        ct_y=0,
        cr_x=0,
        cr_y=0,
        L=None,
        n=None,
        tag=None,
        color="#add8e6",
    ):
        self.n = n
        self.n_l = n
        self.n_r = None
        if n is not None:
            self.n_r = n + 1

        self.m_l = float(m_l)
        self.m_r = float(m_r)
        self.m = self.m_l + self.m_r

        self.Ip_l = float(Ip_l)
        self.Ip_r = float(Ip_r)
        self.Id_l = float(Id_l) if Id_l else Ip_l / 2
        self.Id_r = float(Id_r) if Id_r else Ip_r / 2

        self.kt_x = float(kt_x)
        self.kt_y = float(kt_y)

        self.kr_x = float(kr_x)
        self.kr_y = float(kr_y)

        self.ct_x = float(ct_x)
        self.ct_y = float(ct_y)

        self.cr_x = float(cr_x)
        self.cr_y = float(cr_y)

        self.L = L
        self.tag = tag
        self.color = color
        self.dof_global_index = None

        # CORRIGIR:
        self.beam_cg = 1e20
        self.slenderness_ratio = 1e30
        self.Im = self.Id_l + self.Id_r

    def __repr__(self):
        """Return a string representation of a coupling element.

        Returns
        -------
        A string representation of a coupling element object.

        Examples
        --------
        """
        return f"{self.__class__.__name__}" f"(L={self.L:{0}.{5}}," f"n={self.n})"

    def M(self):
        """Mass matrix for an instance of a coupling element.

        This method will return the mass matrix for an instance of a coupling element.

        Returns
        -------
        M : np.ndarray
            A matrix of floats containing the values of the mass matrix.

        Examples
        --------
        """
        m = self.m_l
        Id = self.Id_l
        # fmt: off
        Ml = np.array([[ m,  0,   0,   0],
                       [ 0,  m,   0,   0],
                       [ 0,  0,  Id,   0],
                       [ 0,  0,   0,  Id]])
        # fmt: on

        m = self.m_r
        Id = self.Id_r
        # fmt: off
        Mr = np.array([[ m,  0,   0,   0],
                       [ 0,  m,   0,   0],
                       [ 0,  0,  Id,   0],
                       [ 0,  0,   0,  Id]])
        # fmt: on

        M = np.zeros((8, 8))
        M[:4, :4] = Ml
        M[4:, 4:] = Mr

        return M

    def K(self):
        """Stiffness matrix for an instance of a coupling element.

        This method will return the stiffness matrix for an instance of a coupling
        element.

        Returns
        -------
        K : np.ndarray
            A matrix of floats containing the values of the stiffness matrix.

        Examples
        --------
        """
        k1 = self.kt_x
        k2 = self.kt_y
        k3 = self.kr_x
        k4 = self.kr_y
        # fmt: off
        K = np.array([
            [  k1,    0,    0,    0,  -k1,    0,   0,    0],
            [   0,   k2,    0,    0,    0,  -k2,   0,    0],
            [   0,    0,   k3,    0,    0,    0, -k3,    0],
            [   0,    0,    0,   k4,    0,    0,   0,  -k4],
            [ -k1,    0,    0,    0,   k1,    0,   0,    0],
            [   0,  -k2,    0,    0,    0,   k2,   0,    0],
            [   0,    0,  -k3,    0,    0,    0,  k3,    0],
            [   0,    0,    0,  -k4,    0,    0,   0,   k4],
        ])
        # fmt: on

        return K

    def C(self):
        """Damping matrix for an instance of a coupling element.

        This method will return the damping matrix for an instance of a coupling
        element.

        Returns
        -------
        C : np.ndarray
            A matrix of floats containing the values of the damping matrix.

        Examples
        --------
        """
        c1 = self.ct_x
        c2 = self.ct_y
        c3 = self.cr_x
        c4 = self.cr_y
        # fmt: off
        C = np.array([
            [  c1,    0,    0,    0,  -c1,    0,   0,    0],
            [   0,   c2,    0,    0,    0,  -c2,   0,    0],
            [   0,    0,   c3,    0,    0,    0, -c3,    0],
            [   0,    0,    0,   c4,    0,    0,   0,  -c4],
            [ -c1,    0,    0,    0,   c1,    0,   0,    0],
            [   0,  -c2,    0,    0,    0,   c2,   0,    0],
            [   0,    0,  -c3,    0,    0,    0,  c3,    0],
            [   0,    0,    0,  -c4,    0,    0,   0,   c4],
        ])
        # fmt: on

        return C

    def G(self):
        """Gyroscopic matrix for an instance of a coupling element.

        This method will return the gyroscopic matrix for an instance of a coupling
        element.

        Returns
        -------
        G: np.ndarray
            Gyroscopic matrix for the coupling element.

        Examples
        --------
        """
        Ip = self.Ip_l
        # fmt: off
        Gl = np.array([[0, 0,   0,   0],
                       [0, 0,   0,   0],
                       [0, 0,   0,  Ip],
                       [0, 0, -Ip,   0]])
        # fmt: on

        Ip = self.Ip_r
        # fmt: off
        Gr = np.array([[0, 0,   0,  0],
                       [0, 0,   0,  0],
                       [0, 0,   0, Ip],
                       [0, 0, -Ip,  0]])
        # fmt: on

        G = np.zeros((8, 8))
        G[:4, :4] = Gl
        G[4:, 4:] = Gr

        return G

    def _patch(self, position, check, fig, units):
        """Coupling element patch.

        Patch that will be used to draw the coupling element using Plotly library.

        Parameters
        ----------
        position : float
            Position in which the patch will be drawn.
        fig : plotly.graph_objects.Figure
            The figure object which traces are added on.
        units : str, optional
            Element length units.
            Default is 'm'.

        Returns
        -------
        fig : plotly.graph_objects.Figure
            The figure object which traces are added on.
        """
        # zpos, ypos, scale_factor = position
        zpos = position
        ypos = 0
        scale_factor = 0.15

        legend = "Coupling"  # self.tag

        # plot the coupling
        z_upper = [zpos, zpos, zpos + self.L, zpos + self.L, zpos]
        y_upper = [ypos, ypos + 2 * scale_factor, ypos + 2 * scale_factor, ypos, ypos]

        z_pos = z_upper
        z_pos.extend(z_upper)

        y_pos = y_upper
        y_pos.extend(-np.array(y_upper))

        customdata = [
            self.n,
        ]
        hovertemplate = f"Element Number: {customdata[0]}<br>"
        fig.add_trace(
            go.Scatter(
                x=Q_(z_pos, "m").to(units).m,
                y=Q_(y_pos, "m").to(units).m,
                customdata=[customdata] * len(z_pos),
                text=hovertemplate,
                mode="lines",
                opacity=0.5,
                fill="toself",
                fillcolor=self.color,
                line=dict(width=1.5, color="black", dash="dash"),
                showlegend=False,
                name=legend,
                legendgroup=legend,
                hoveron="points+fills",
                hoverinfo="text",
                hovertemplate=hovertemplate,
                hoverlabel=dict(bgcolor=self.color),
            )
        )

        return fig


class CouplingElement6DoF(ShaftElement6DoF):
    """A coupling element.

    This class creates a coupling element from input data of inertia and mass
    from the left station and right station, and also translational and rotational
    stiffness and damping values. The matrices will be defined considering the
    same local coordinate vector of the `ShaftElement6DoF`.

    Parameters
    ----------
    m_l : float, pint.Quantity
        Mass of the left station of coupling element.
    m_r : float, pint.Quantity
        Mass of the right station of coupling element.
    Ip_l : float, pint.Quantity
        Polar moment of inertia of the left station of the coupling element.
    Ip_r : float, pint.Quantity
        Polar moment of inertia of the right station of the coupling element.
    Id_l : float, pint.Quantity, optional
        Diametral moment of inertia of the left station of the coupling element.
        If not given, it is assumed to be half of `Ip_l`.
    Id_r : float, pint.Quantity, optional
        Diametral moment of inertia of the right station of the coupling element.
        If not given, it is assumed to be half of `Ip_r`.
    kt_x : float, optional
        Translational stiffness in `x`.
        Default is 0.
    kt_y : float, optional
        Translational stiffness in `y`.
        Default is 0.
    kt_z : float, optional
        Axial stiffness.
        Default is 0.
    kr_x : float, optional
        Rotational stiffness in `x`.
        Default is 0.
    kr_y : float, optional
        Rotational stiffness in `y`.
        Default is 0.
    kr_z : float, optional
        Torsional stiffness.
        Default is 0.
    ct_x : float, optional
        Translational damping in `x`.
        Default is 0.
    ct_y : float, optional
        Translational damping in `y`.
        Default is 0.
    ct_z : float, optional
        Axial damping.
        Default is 0.
    cr_x : float, optional
        Rotational damping in `x`.
        Default is 0.
    cr_y : float, optional
        Rotational damping in `y`.
        Default is 0.
    cr_z : float, optional
        Torsional damping.
        Default is 0.
    L : float, optional
        Element length (m).
    n : int, optional
        Element number (coincident with it's first node).
        If not given, it will be set when the rotor is assembled
        according to the element's position in the list supplied to
        the rotor constructor.
    tag : str, optional
        A tag to name the element
        Default is None
    color : str, optional
        A color to be used when the element is represented.
        Default is '#add8e6'.

    Examples
    --------
    """

    @check_units
    def __init__(
        self,
        m_l,
        m_r,
        Ip_l,
        Ip_r,
        Id_l=0,
        Id_r=0,
        kt_x=0,
        kt_y=0,
        kt_z=0,
        kr_x=0,
        kr_y=0,
        kr_z=0,
        ct_x=0,
        ct_y=0,
        ct_z=0,
        cr_x=0,
        cr_y=0,
        cr_z=0,
        L=None,
        n=None,
        tag=None,
        color="#add8e6",
    ):
        self.n = n
        self.n_l = n
        self.n_r = None
        if n is not None:
            self.n_r = n + 1

        self.m_l = float(m_l)
        self.m_r = float(m_r)
        self.m = self.m_l + self.m_r

        self.Ip_l = float(Ip_l)
        self.Ip_r = float(Ip_r)
        self.Id_l = float(Id_l) if Id_l else Ip_l / 2
        self.Id_r = float(Id_r) if Id_r else Ip_r / 2

        self.kt_x = float(kt_x)
        self.kt_y = float(kt_y)
        self.kt_z = float(kt_z)

        self.kr_x = float(kr_x)
        self.kr_y = float(kr_y)
        self.kr_z = float(kr_z)

        self.ct_x = float(ct_x)
        self.ct_y = float(ct_y)
        self.ct_z = float(ct_z)

        self.cr_x = float(cr_x)
        self.cr_y = float(cr_y)
        self.cr_z = float(cr_z)

        self.L = L
        self.tag = tag
        self.color = color
        self.dof_global_index = None

        # CORRIGIR:
        self.o_d = 150e-3
        self.beam_cg = 1e20
        self.slenderness_ratio = 1e30
        self.Im = self.Id_l + self.Id_r

    def M(self):
        """Mass matrix for an instance of a coupling element.

        This method will return the mass matrix for an instance of a coupling element.

        Returns
        -------
        M : np.ndarray
            A matrix of floats containing the values of the mass matrix.

        Examples
        --------
        """
        m = self.m_l
        Id = self.Id_l
        Ip = self.Ip_l
        # fmt: off
        Ml = np.array([
            [m,  0,  0,  0,  0,  0],
            [0,  m,  0,  0,  0,  0],
            [0,  0,  m,  0,  0,  0],
            [0,  0,  0, Id,  0,  0],
            [0,  0,  0,  0, Id,  0],
            [0,  0,  0,  0,  0, Ip],
        ])
        # fmt: on

        m = self.m_r
        Id = self.Id_r
        Ip = self.Ip_r
        # fmt: off
        Mr = np.array([
            [m,  0,  0,  0,  0,  0],
            [0,  m,  0,  0,  0,  0],
            [0,  0,  m,  0,  0,  0],
            [0,  0,  0, Id,  0,  0],
            [0,  0,  0,  0, Id,  0],
            [0,  0,  0,  0,  0, Ip],
        ])
        # fmt: on

        M = np.zeros((12, 12))
        M[:6, :6] = Ml
        M[6:, 6:] = Mr

        return M

    def K(self):
        """Stiffness matrix for an instance of a coupling element.

        This method will return the stiffness matrix for an instance of a coupling
        element.

        Returns
        -------
        K : np.ndarray
            A matrix of floats containing the values of the stiffness matrix.

        Examples
        --------
        """
        k1 = self.kt_x
        k2 = self.kt_y
        k3 = self.kt_z
        k4 = self.kr_x
        k5 = self.kr_y
        k6 = self.kr_z
        # fmt: off
        K = np.array([
            [  k1,    0,    0,    0,    0,    0, -k1,    0,   0,    0,   0,    0],
            [   0,   k2,    0,    0,    0,    0,   0,  -k2,   0,    0,   0,    0],
            [   0,    0,   k3,    0,    0,    0,   0,    0, -k3,    0,   0,    0],
            [   0,    0,    0,   k4,    0,    0,   0,    0,   0,  -k4,   0,    0],
            [   0,    0,    0,    0,   k5,    0,   0,    0,   0,    0, -k5,    0],
            [   0,    0,    0,    0,    0,   k6,   0,    0,   0,    0,   0,  -k6],
            [ -k1,    0,    0,    0,    0,    0,  k1,    0,   0,    0,   0,    0],
            [   0,  -k2,    0,    0,    0,    0,   0,   k2,   0,    0,   0,    0],
            [   0,    0,  -k3,    0,    0,    0,   0,    0,  k3,    0,   0,    0],
            [   0,    0,    0,  -k4,    0,    0,   0,    0,   0,   k4,   0,    0],
            [   0,    0,    0,    0,  -k5,    0,   0,    0,   0,    0,  k5,    0],
            [   0,    0,    0,    0,    0,  -k6,   0,    0,   0,    0,   0,   k6],
        ])
        # fmt: on

        return K

    def C(self):
        """Damping matrix for an instance of a coupling element.

        This method will return the damping matrix for an instance of a coupling
        element.

        Returns
        -------
        C : np.ndarray
            A matrix of floats containing the values of the damping matrix.

        Examples
        --------
        """
        c1 = self.ct_x
        c2 = self.ct_y
        c3 = self.ct_z
        c4 = self.cr_x
        c5 = self.cr_y
        c6 = self.cr_z
        # fmt: off
        C = np.array([
            [  c1,    0,    0,    0,    0,    0, -c1,    0,   0,    0,   0,    0],
            [   0,   c2,    0,    0,    0,    0,   0,  -c2,   0,    0,   0,    0],
            [   0,    0,   c3,    0,    0,    0,   0,    0, -c3,    0,   0,    0],
            [   0,    0,    0,   c4,    0,    0,   0,    0,   0,  -c4,   0,    0],
            [   0,    0,    0,    0,   c5,    0,   0,    0,   0,    0, -c5,    0],
            [   0,    0,    0,    0,    0,   c6,   0,    0,   0,    0,   0,  -c6],
            [ -c1,    0,    0,    0,    0,    0,  c1,    0,   0,    0,   0,    0],
            [   0,  -c2,    0,    0,    0,    0,   0,   c2,   0,    0,   0,    0],
            [   0,    0,  -c3,    0,    0,    0,   0,    0,  c3,    0,   0,    0],
            [   0,    0,    0,  -c4,    0,    0,   0,    0,   0,   c4,   0,    0],
            [   0,    0,    0,    0,  -c5,    0,   0,    0,   0,    0,  c5,    0],
            [   0,    0,    0,    0,    0,  -c6,   0,    0,   0,    0,   0,   c6],
        ])
        # fmt: on

        return C

    def G(self):
        """Gyroscopic matrix for an instance of a coupling element.

        This method will return the gyroscopic matrix for an instance of a coupling
        element.

        Returns
        -------
        G: np.ndarray
            Gyroscopic matrix for the coupling element.

        Examples
        --------
        """
        Ip = self.Ip_l
        # fmt: off
        Gl = np.array([
            [0, 0, 0,   0,  0, 0],
            [0, 0, 0,   0,  0, 0],
            [0, 0, 0,   0,  0, 0],
            [0, 0, 0,   0, Ip, 0],
            [0, 0, 0, -Ip,  0, 0],
            [0, 0, 0,   0,  0, 0],
        ])
        # fmt: on

        Ip = self.Ip_r
        # fmt: off
        Gr = np.array([
            [0, 0, 0,   0,  0, 0],
            [0, 0, 0,   0,  0, 0],
            [0, 0, 0,   0,  0, 0],
            [0, 0, 0,   0, Ip, 0],
            [0, 0, 0, -Ip,  0, 0],
            [0, 0, 0,   0,  0, 0],
        ])
        # fmt: on

        G = np.zeros((12, 12))
        G[:6, :6] = Gl
        G[6:, 6:] = Gr

        return G

    def Kst(self):
        return np.zeros((12, 12))

    def _patch(self, position, check, fig, units):
        """Coupling element patch.

        Patch that will be used to draw the coupling element using Plotly library.

        Parameters
        ----------
        position : float
            Position in which the patch will be drawn.
        fig : plotly.graph_objects.Figure
            The figure object which traces are added on.
        units : str, optional
            Element length units.
            Default is 'm'.

        Returns
        -------
        fig : plotly.graph_objects.Figure
            The figure object which traces are added on.
        """

        return CouplingElement._patch(self, position, check, fig, units)
