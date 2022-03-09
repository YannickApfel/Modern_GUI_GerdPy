# -*- coding: utf-8 -*-
""" GERDPy - 'R_th_he.py'
    
    Module for the thermal resistance of the heating element
    
    R_th_he:

    - analytical series solution for the heat flow in a pipe register with
      equidistant tubes according to VDI 2055-1 (Dirichlet temperature boundary condition)

    - variable parameters:
        - minimum vertical pipe-to-surface distance x_min [m]
        - thermal conductivities of the heating element material (concrete) and
          heatpipe material (stainless steel) [W/mK]
        - piping sizes inside heating element (diameter, heatpipe distance,
                                         heatpipe length) [m]

    Authors: Yannick Apfel, Meike Martin
"""
from .heating_element_utils import *


def R_th_he(he):  # heating element thermal resistance [K/W]

    # 1.) auxiliary params
    x_o = he.x_min + 0.5 * he.d_R_a  # vertical pipe-centre-to-surface distance [m]
    x_u = he.D - x_o  # vertical pipe-centre-to-underside distance [m]

    # 2.) delta-T between pipe wall and surface set to delta-T := 1 K
    Theta_R = 1
    Theta_inf_o = 0

    # 3.) thermal resistance [K/W] --> R_th = 1 K / (q_l * l_R)
    ''' heating element underside is parametrized as perfectly insulated: state_u_insul=True
    '''
    R_th_he = (he.l_R * q_l(x_o, x_u, he.d_R_a, he.d_R_i, he.lambda_B, he.lambda_R, he.s_R, Theta_R, Theta_inf_o,
                            state_u_insul=True)) ** -1

    return R_th_he
