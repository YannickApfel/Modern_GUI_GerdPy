# -*- coding: utf-8 -*-
""" GERDPy - 'geometrycheck.py'
    
    Module for testing geometric compatibility:
        - distance of boreholes to each other must be > 2 * r_b
        - outer radii of boreholes (r_b) must be identical
        - compatible heatpipe geometry

    Authors: Yannick Apfel, Meike Martin
"""
import numpy as np


def check_geometry(borefield, heatpipes, self):
    # initialize with 0 errors
    errors_exist = 0
    
    # test for borehole duplicates
    duplicate_pairs = []
    for i in range(len(borefield)):
        borehole_1 = borefield[i]
        for j in range(i, len(borefield)):  # loop
            borehole_2 = borefield[j]
            if i == j:  # comparison of borehole with itself omitted
                continue
            else:
                dist = borehole_1.distance(borehole_2)
            if abs(dist - borehole_1.r_b) < borehole_1.r_b:
                duplicate_pairs.append((i+1, j+1))
    if duplicate_pairs:
        print(f'Geometric conflict between the following borehole pairs:')
        print(*duplicate_pairs, sep = ", ")
        print('Please adjust!')
        self.ui.text_console.insertPlainText(f'Geometric conflict between the following borehole pairs:\n')
        self.ui.text_console.insertPlainText(*duplicate_pairs, sep=", ")
        self.ui.text_console.insertPlainText('Please adjust!\n')
        errors_exist = 1

    # test for identical borehole radii
    for i in range(len(borefield) - 1):
        if borefield[i].r_b != borefield[i+1].r_b:
            print('Borehole radii must be identical!')
            print('Please adjust!')
            self.ui.text_console.insertPlainText('Borehole radii must be identical!\n')
            self.ui.text_console.insertPlainText('Please adjust!\n')
            errors_exist = 1
            break

    # test for compatible heatpipe geometry
    xy = heatpipes.xy_mat()
    heatpipe_distance = np.sqrt((xy[1, 0] - xy[2, 0])**2 + (xy[1, 1] - xy[2, 1])**2)
    if ((heatpipes.r_pa + heatpipes.r_w) >= heatpipes.r_b):
        print("Heatpipe circle too big!")
        self.ui.text_console.insertPlainText("Heatpipe circle too big!\n")
        errors_exist = 1
    elif heatpipe_distance <= (2 * heatpipes.r_pa):
        print("Too many heat pipes!")
        self.ui.text_console.insertPlainText("Too many heat pipes!\n")
        errors_exist = 1

    return errors_exist
