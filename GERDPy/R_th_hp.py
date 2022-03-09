# -*- coding: utf-8 -*-
""" GERDPy - 'R_th_hp.py'
    
    Module for the thermal resistance of the thermosiphon heatpipes
    
    The complex two-phase flow phenomena are not modelled (e. g. the entrainment limit),
    instead, the thermal resistance follows a simple linear power-over-delta-T characteristic.
    
    R_th_hp = 1 K / (500 W * N * N_b)
    
    N - number of heatpipes per borehole
    N_b - number of boreholes in the borefield

    Authors: Yannick Apfel, Meike Martin
"""
def R_th_hp(borefield, hp):

    # %% 1.) Params

    N = hp.N  # number of heatpipes per borehole [-]
    N_b = len(borefield)  # number of boreholes in the borefield [-]

    # linear slope of the characteristic (delta_y / delta_x)
    delta_y = 500       # thermal power per heatpipe [W]
    delta_x = 1         # delta_T [K]

    # %% 2.) thermal resistance of the thermosiphon heatpipes

    R_th_hp = delta_x / (delta_y * N * N_b)

    return R_th_hp
