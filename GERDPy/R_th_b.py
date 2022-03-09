# -*- coding: utf-8 -*-
""" GERDPy - 'R_th_b.py'
    
    Module for the borehole thermal resistance
    
    [Hellström 1991 - Line source approximation]

    N heatpipes uniformly arranged around a circle in the borehole

    Authors: Yannick Apfel, Meike Martin
"""
def R_th_b(lambda_g, borefield, hp):

    import math
    import numpy as np
    from numpy.linalg import inv
    from scipy.constants import pi
    from .boreholes import length_field

    # %% 1.) Params

    # Borefield & borehole geometry
    H_field = length_field(borefield) # total borehole depth [m]
    r_b = borefield[0].r_b  # borehole radius [m]

    # Heatpipe geometry
    N = hp.N  # no. of heatpipes per borehole [-]
    r_iso_a = hp.r_iso_a  # outer radius of heatpipe insulation [m]
    r_pa = hp.r_pa  # outer radius of heatpipes [m]
    r_pi = hp.r_pi  # inner radius of heatpipes [m]

    # Thermal conductivities [W/mK]:
    # lambda_g (imported)
    lambda_b = hp.lambda_b  # borehole backfill
    lambda_iso = hp.lambda_iso  # insulation material
    lambda_p = hp.lambda_p  # heatpipe material

    # %% 2a.) Coordinates of heatpipe centres (borehole centre as origin)

    xy = hp.xy_mat()  # 1. column: x, 2. column: y

    # %% 2b.) Auxiliary variables

    # Ratio of thermal conductivities
    sigma = (lambda_b - lambda_g) / (lambda_b + lambda_g)

    # Thermal resistance of heat pipe + insulation layer
    r_pm = math.log(r_iso_a / r_pa) / (2 * pi * lambda_iso) + \
        math.log(r_pa / r_pi) / (2 * pi * lambda_p)
    # r_pm = 0 (in case the thermal resistance is supposed to be neglected)

    # Coordinate-dependent coefficients
    b_m = lambda x_m, y_m: math.sqrt(x_m ** 2 + y_m ** 2) / r_b
    b_mn = lambda x_n, x_m, y_n, y_m: math.sqrt((x_n - x_m) ** 2 + (y_n - y_m) ** 2) / r_b
    b_mn_ = lambda b_m, b_n, b_mn: math.sqrt((1 - b_m ** 2) * (1 - b_n ** 2) + b_mn ** 2)

    # Borehole coefficient matrix

    R_mn_0 = np.zeros([N, N])

    # Populate borehole coefficient matrix
    for i in range(N):          # iterate for m
        for j in range(N):      # iterate for n
            if i == j:
                R_mn_0[i, j] = \
                    (2 * pi * lambda_b) ** -1 * (math.log(r_b / r_pa)
                    - sigma * math.log(1 - b_m(xy[i, 0], xy[i, 1]) ** 2)) + r_pm
            else:
                R_mn_0[i, j] = \
                    - (2 * pi * lambda_b) ** -1 * (math.log(b_mn(xy[j, 0], xy[i, 0], xy[j, 1], xy[i, 1]))
                    - sigma * math.log(b_mn_(b_m(xy[i, 0], xy[i, 1]), b_m(xy[j, 0], xy[j, 1]), b_mn(xy[j, 0], xy[i, 0], xy[j, 1], xy[i, 1]))))

    # %% 3.) Calculation of borehole thermal resistance

    R_th_b = (sum(sum(inv(R_mn_0))) * H_field) ** -1

    return R_th_b
