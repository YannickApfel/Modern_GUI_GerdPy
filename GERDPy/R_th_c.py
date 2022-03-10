# -*- coding: utf-8 -*-
""" GERDPy - 'R_th_c.py'
    
    Module for the ground-to-backfill thermal contact resistance
    
    [VDI-Wärmeatlas 2013 - Wärmeübergangskoeffizient Wand-Schüttung]

    Authors: Yannick Apfel, Meike Martin
"""
def R_th_c(borefield):

    import math, GERDPy.boreholes
    from scipy.constants import pi, R, Stefan_Boltzmann
    from .boreholes import length_field

    # %% 1.) Params

    phi = 0.8               # surface coverage ratio [-]
    lambda_g = 0.025        # thermal conductivity of gas [W/mK]
    d = 1e-3                # particle diameter [m]
    delta = 250 * 1e-6      # particle surface roughness [m]
    C = 2.8                 # material constant [-]
    M = 0.02896             # molar mass of gas [kg/mol]
    T = 283                 # contact zone temperature [K]
    c_pg = 1007             # specific heat capacity of gas [J/kgK]
    epsilon_S = 0.2         # emission coefficient of backfill [-]
    epsilon_W = 0.2         # emission coefficient of wall [-]
    p = 100000              # pressure [Pa]

    # %% 2a.) Auxiliary params

    # accommodation coefficient
    gamma = (10 ** (0.6 - (1000 / T + 1) / C) + 1) ** -1

    # free path length of gas molecules
    l_frei = 2 * (2 - gamma) / gamma * math.sqrt(2 * pi * R * T / M) * \
        lambda_g / (p * (2 * c_pg - R / M))

    # emission coefficient ratio
    C_WS = Stefan_Boltzmann / (1 / epsilon_W + 1 / epsilon_S - 1)

    # %% 2b.) Heat transfer coefficient wall-to-backfill

    # proportion of heat conduction
    alpha_WP = 4 * lambda_g / d * ((1 + 2 * (l_frei + delta) / d) *
                                   math.log(1 + d / (2 * (l_frei + delta)))
                                   - 1)

    # proportion of radiation
    alpha_rad = 4 * C_WS * T ** 3

    # heat transfer coefficient wall-to-backfill
    alpha_WS = phi * alpha_WP + alpha_rad

    # %% 3.) thermal contact resistance of the borehole field

    r_b = borefield[0].r_b
    H_field = length_field(borefield)

    R_th_c = (2 * pi * r_b * alpha_WS * H_field) ** -1

    return R_th_c
