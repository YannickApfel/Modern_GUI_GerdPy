# -*- coding: utf-8 -*-
""" GERDPy - 'load_generator_utils.py'
    
    Utility module for 'load_generator.py':
    physical model equations, correlations and base functions for surface load generation
    
    Sources: [Konrad2009], [Fuchs2021], [ASHRAE2015]

    Authors: Yannick Apfel, Meike Martin
"""
import math
import sys
import CoolProp.CoolProp as CP


# physical params (mainly from [VDI2013])
# water
rho_w = 999.84  # density of water (p = 1 bar, T = 0 °C) [kg/m³]
h_Ph_sl = 333e3  # phase-change enthalpy solid <-> liquid [J/kg]
h_Ph_lg = 2500.9e3  # phase-change enthalpy liquid <-> vapour (T = 0,01 °C) [J/kg]
c_p_s = 2.106e3  # specific heat capacity of ice/snow (T = 0 °C) [J/kgK]
c_p_w = 4219  # specific heat capacity of water (T = 0 °C) [J/kgK]
Theta_mp = 0  # melting point of ice/snow (p = 1 bar) [°C]
# air
rho_l = 1.276  # density of dry air (p = 1 bar, T = 0 °C) [kg/m³]
c_p_l = 1006  # specific heat capacity of air (p = 1 bar, T = 0 °C) [J/kgK]
lambda_l = 0.0244  # thermal conductivity of air [W/m*K]
a_l = lambda_l / (rho_l * c_p_l)  # T-Leitfähigkeit von Luft [m²/s]
theta_l = 13.5e-6  # kinetic viscosity of air (p = 1 bar, T = 0 °C) [m²/s]
# arbitrary
H_max = 2  # maximum allowed water level on heating element without running off [mm]


# wind-shear-corrected wind speed (logarithmic) [m/s]
def u_eff(v):
    z_1 = 10  # typical height of meteorological weather stations [m]
    z_n = 1  # reference height (:= 1 m)
    z_0 = 0.005  # topographic roughness level of the ground

    return v * (math.log10(z_n) - math.log10(z_0)) / \
        (math.log10(z_1) - math.log10(z_0))


# altitude-corrected ambient pressure [Pa]
def p_inf(h_NHN):
    return 101325 * (1 - 0.0065 * h_NHN / 288.2) ** 5.265


# saturation vapour pressure acc. to ASHRAE2013 [Pa]
def p_s_ASHRAE(T):  # input in [K]
    C_1 = -5.6745359e3
    C_2 = 6.3925247e0
    C_3 = -9.6778430e-3
    C_4 = 6.2215701e-7
    C_5 = 2.0747825e-9
    C_6 = -9.4840240e-13
    C_7 = 4.1635019e0
    C_8 = -5.8002206e3
    C_9 = 1.3914993e0
    C_10 = -4.8640239e-2
    C_11 = 4.1764768e-5
    C_12 = -1.4452093e-8
    C_13 = 6.5459673e0

    if ((T - 273.15) > -100) and ((T - 273.15) < 0):  # "over ice"
        return math.exp(C_1 / T + C_2 + C_3 * T + C_4 * T ** 2 + C_5 * T ** 3
                        + C_6 * T ** 4 + C_7 * math.log(T))
    elif ((T - 273.15) >= 0) and ((T - 273.15) <= 200):  # "over liquid water"
        return math.exp(C_8 / T + C_9 + C_10 * T + C_11 * T ** 2
                        + C_12 * T ** 3 + C_13 * math.log(T))
    else:
        print('Internal error: allowed temperature range exceeded!')
        sys.exit()


''' heat transfer coefficient [W/m²K] acc. to [Bentz D. P. 2000]
    forced convection along horizontal wall/ground
    alpha = alpha(u_air)
'''
def alpha_kon_he_o(u):  # heating element surface
    if u <= 5:
        alpha = 5.6 + 4 * u
    else:
        alpha = 7.2 * u ** 0.78

    return alpha


''' heat transfer coefficient [W/m²K] acc. to [Löser: Technische Thermodynamik]
    calm air perpendicular to horizontal wall/ground
    alpha = alpha() = const
'''
def alpha_kon_he_u():

    return 10


''' heat transfer coefficient [W/m²K] acc. to [Löser: Technische Thermodynamik]
    air around insulated pipes
    alpha = alpha(deltaT)
'''
def alpha_kon_an(deltaT):
    return 9.4 + 0.052 * deltaT


# mass balance for water on heating element surface
def m_water(m_Rw_0, RR, A_he, Q_eva):
    m_Rw_1 = m_Rw_0 + (RR * rho_w * A_he) / 1000 - (Q_eva / h_Ph_lg) * 3600

    if (m_Rw_1 / (rho_w * A_he)) > (H_max / 1000):  # maximum allowed water level
        m_Rw_1 = (H_max / 1000) * rho_w * A_he

    if m_Rw_1 < 0:  # water-mass can't be < 0 kg
        m_Rw_1 = 0

    return m_Rw_1


# mass balance for ice/snow on heating element surface
def m_snow(m_Rs_0, S_w, A_he, Q_lat, sb_active):
    if (sb_active == 1):
        m_Rs_1 = m_Rs_0 + (S_w * rho_w * A_he) / 1000 - (Q_lat / h_Ph_sl) * 3600
    else:
        m_Rs_1 = 0

    if m_Rs_1 < 0:  # snow-mass can't be < 0 kg
        m_Rs_1 = 0

    return m_Rs_1


# emission coefficient of the heating element surface (radiation) [-]
def epsilon_surf(material):
    if material == 'concrete':
        return 0.94
    else:
        return 0.94


# average ambient radiation temperature [K]
def T_MS(S_w, Theta_inf, B, Phi):
    if S_w > 0:  # corresponds to the ambient temperature during snowfall
        return (Theta_inf + 273.15)
    else:  # without snowfall: function of ambient temperature and rel. humidity
        T_H = (Theta_inf + 273.15) - (1.1058e3 - 7.562 * (Theta_inf + 273.15) +
                                      1.333e-2 * (Theta_inf + 273.15) ** 2
                                      - 31.292 * Phi + 14.58 * Phi ** 2)
        T_W = (Theta_inf + 273.15) - 19.2

        if T_H > T_W:
            T_H = T_W

        T_MS = (T_W ** 4 * B + T_H ** 4 * (1 - B)) ** 0.25

        return T_MS


# binary diffusion coefficient [-]
def delta(Theta_inf, h_NHN):

    return (2.252 / p_inf(h_NHN)) * ((Theta_inf + 273.15) / 273.15) ** 1.81


# mass transfer coefficient [m/s]
def beta_c(Theta_inf, u, h_NHN):
    Pr = theta_l / a_l  # Prandtl-number for air
    Sc = theta_l / delta(Theta_inf, h_NHN)  # Schmidt-number
    alpha = alpha_kon_he_o(u)

    beta_c = (Pr / Sc) ** (2/3) * alpha / (rho_l * c_p_l)

    return beta_c


# water vapour loading of saturated air at ambient conditions [vapour-kg / air-kg]
def X_D_inf(Theta_inf, Phi, h_NHN):
    ''' saturation vapour pressure of the environment at dew point temperature:
        p_v = p_s_ASHRAE(T_tau(Theta_inf, Phi))
    '''
    T_tau = CP.HAPropsSI('DewPoint', 'T', (Theta_inf + 273.15),
                         'P', 101325, 'R', Phi)  # Input in [K]
    p_v = p_s_ASHRAE(T_tau)  # Input in [K]

    return 0.622 * p_v / (p_inf(h_NHN) - p_v)


# water vapour loading of saturated air at heating element surface [vapour-kg / air-kg]
def X_D_sat_surf(Theta_surf, h_NHN):
    ''' saturation vapour pressure at the heating element surface:
        p_v = p_s_ASHRAE(Theta_surf)
    '''
    p_v = p_s_ASHRAE(Theta_surf + 273.15)  # Input in [K]

    return 0.622 * p_v / (p_inf(h_NHN) - p_v)
