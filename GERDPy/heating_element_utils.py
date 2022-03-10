# -*- coding: utf-8 -*-
""" GERDPy - 'heating_element_utils.py'
    
    Utility module for 'heating_element.py':
    analytical series solution for the heat flow in a pipe register with
    equidistant tubes according to VDI 2055-1 (Dirichlet temperature boundary condition), 
    used for determination of the thermal resistance of the heating element

    q_l - heat output per meter of installed pipe [W/m]

    Authors: Yannick Apfel, Meike Martin
"""
import math


# Determination of the sum-term
def sum_fct(kappa_o, kappa_u, s, s_c, x_o, x_u, lambda_B):

    # 1.) Definition of thermal parameters
    beta_o = kappa_o * s / lambda_B
    beta_u = kappa_u * s / lambda_B

    # 2.) Approximation of the infinite series sum
    ssum_temp = 0
    j = 0
    error = 1e-6

    while 1:  # infinite loop until "break"

        j += 1

        N_1 = 1 - (beta_u + 2 * math.pi * j) / (beta_u - 2 * math.pi * j) * math.exp(4 * math.pi * j * s_c / s)
        N_2 = 1 - (beta_u - 2 * math.pi * j) / (beta_u + 2 * math.pi * j) * math.exp(-4 * math.pi * j * s_c / s)

        gamma = (beta_o - 2 * math.pi * j) / (beta_o + 2 * math.pi * j) * math.exp(-4 * math.pi * j * (x_u + x_o) / s)

        e_o = ((lambda_B + lambda_B / N_1 - lambda_B / N_2) * (math.exp(-4 * math.pi * j * x_u / s) - gamma)) /\
              (lambda_B * (1 + gamma) + (lambda_B / N_2 - lambda_B / N_1) * (1 - gamma))

        e_u = - (beta_o - 2 * math.pi * j) / (beta_o + 2 * math.pi * j) * math.exp(-4 * math.pi * j * x_o / s) * (1 + e_o)

        ssum = ssum_temp + (e_o + e_u) / j

        if abs(ssum - ssum_temp) < error:
            break

        ssum_temp = ssum

    return ssum


# Analytical series solution according to VDI 2055-1 (heat output per meter of piping)
def q_l(x_o, x_u, d_R_a, d_R_i, lambda_B, lambda_R, s, Theta_R, Theta_inf_o, state_u_insul):  # [W/m]

    # 1.) additional geometric params
    s_c = 0.0  # [m] -> set to 0, because no additional layers in heating element
    d_insul_a = d_R_a + 0.0002  # thermal contact resistance modelled as layer of air of 1/10 mm

    # 2.) additional thermal params
    Theta_inf_u = Theta_inf_o
    lambda_insul = 0.0262  # air
    alpha_o = 1e10  # surface heat transfer coefficient --> infinite (Dirichlet temperature boundary condition)
    alpha_u = alpha_o
    
    if state_u_insul:
        alpha_u = 1e-10  # surface heat transfer coefficient --> 0 (modelled as insulated, because only heat transfer to surface considered)
        x_u = 1e10  # x_u equals semi-infinite space

    # 3.) Heat transmission  [W/m²K]
    kappa_o = (1 / alpha_o + s_c / lambda_B) ** -1
    kappa_u = (1 / alpha_u + s_c / lambda_B) ** -1
    kappa_o_ = (kappa_o ** -1 + x_o / lambda_B) ** -1
    kappa_u_ = (kappa_u ** -1 + x_u / lambda_B) ** -1

    # 4.) Heat output per meter [W/m]

    ssum = sum_fct(kappa_o, kappa_u, s, s_c, x_o, x_u, lambda_B)  # determination of ssum-term

    q_l = 2 * math.pi * lambda_B * (Theta_R - (Theta_inf_o * kappa_o_ + Theta_inf_u * kappa_u_) / (kappa_o_ + kappa_u_)) \
          / (lambda_B / lambda_R * math.log(d_R_a / d_R_i)
          + lambda_B / lambda_insul * math.log(d_insul_a / d_R_a) + math.log(s / (math.pi * d_insul_a))
          + (2 * math.pi * lambda_B) / (s * (kappa_o_ + kappa_u_)) + ssum)  # [W/m]

    return q_l
