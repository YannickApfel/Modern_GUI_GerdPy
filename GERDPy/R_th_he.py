# -*- coding: utf-8 -*-
""" GERDPy - 'R_th_he.py'
    
    Modul für den thermischen Widerstand des Heizelements
    
    R_th_he:

    - analytisch ermittelter therm. Widerstand basierend auf der Norm
    VDI 2055-1 [2019] für die thermischen Verluste gedämmter Rohrleitungen
    verlegt in Registeranordnung in ein- oder mehrschichtigen Platten
    (z. B. Fußbodenheizungen) - vereinfacht und angepasst in [Apfel2020]
    
    - variable Größen:
        - minimaler Oberflächenabstand x_min [m]
        - Wärmeleitfähigkeiten Beton und Kondensatrohre [W/mK]
        - Rohrgeometrie des Kondensator (Durchmesser, Rohrabstand,
                                         Rohrlänge) [m]

    Autor(en): Yannick Apfel, Meike Martin
"""
from .heating_element_utils import *


def R_th_he(he):  # thermischer Widerstand [K/W]

    # 1.) zusätzliche Parameter des Heizelements
    x_o = he.x_min + 0.5 * he.d_R_a  # Achsabstand Kondensatrohr nach oben [m]
    x_u = he.D - x_o  # Achsabstand Kondensatrohr nach unten [m]

    # 2.) delta-T zwischen Kondensatrohren und Oberfläche zu 1 K definieren
    Theta_R = 1
    Theta_inf_o = 0

    # 3.) thermischer Widerstand des Heizelements in [K/W] --> R_th = 1 K / (q_l * l_R)
    ''' andere Seite wird als thermisch isoliert betrachtet: state_u_insul=True
    '''
    R_th_he = (he.l_R * q_l(x_o, x_u, he.d_R_a, he.d_R_i, he.lambda_B, he.lambda_R, he.s_R, Theta_R, Theta_inf_o,
                            state_u_insul=True)) ** -1

    return R_th_he
