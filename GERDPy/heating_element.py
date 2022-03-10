# -*- coding: utf-8 -*-
""" GERDPy - 'heating_element.py'
    
    Class for the heating element

    Authors: Yannick Apfel, Meike Martin
"""
class HeatingElement(object):
    """
    Contains class for the heating element.

    Attributes
    ----------
    A_he:           float 
                    area of the heating element [m²]
    x_min:          float
                    minimum vertical pipe-to-surface distance [m]
    lambda_B:       float
                    thermal conductivity of heating element material [W/mK]
    lambda_R:       float 
                    thermal conductivity of heat pipes [W/mK]
    d_R_a:          float 
                    outer radius of heatpipes [m]
    d_R_i:          float
                    inner radius of heatpipes [m]
    s_R:            float
                    centre-distance between heatpipes [m]
    l_R:            float
                    total heatpipe length inside heating element [m]
    D:              float
                    vertical thickness of heating element [m]
    D_iso:          float
                    vertical thickness of insulation layer on underside of heating element [m]

    """

    def __init__(self, A_he, x_min, lambda_B, lambda_R, d_R_a, d_R_i, s_R,
                 l_R, D, D_iso):
        self.A_he = float(A_he)
        self.x_min = float(x_min)
        self.lambda_B = float(lambda_B)
        self.lambda_R = float(lambda_R)
        self.d_R_a = float(d_R_a)
        self.d_R_i = float(d_R_i)
        self.s_R = float(s_R)
        self.l_R = float(l_R)
        self.D = float(D)
        self.D_iso = float(D_iso)

    def __repr__(self):
        s = ('HeatingElement(A_he={self.A_he}, x_min={self.x_min}, \
             lambda_B={self.lambda_B}, lambda_R={self.lambda_R},'
             ' d_R_a={self.d_R_a}, d_R_i={self.d_R_i}, \
                     s_R={self.s_R}, l_R={self.l_R}, D={self.D}, \
                         D_iso={self.D_iso}').format(self=self)
        return s
