# -*- coding: utf-8 -*-
""" GERDPy - '_main.py'

    Main Control-Module of GERDPy - The Simulation Tool for Geothermal Heat Pipe Surface Heating Systems

    Legend:
        Parameter [Unit]
        - Temperatures:
            - T in Kelvin [K] - for caloric equations
            - Theta in degrees Celsius [°C] - for object temperatures

    Authors: Yannick Apfel, Meike Martin
"""
# import python libraries
import sys
import matplotlib.pyplot as plt
import time as tim
import numpy as np
import pandas as pd
from matplotlib.ticker import AutoMinorLocator
from scipy.constants import pi

# import GUI libraries
from progress.vismain import SplashScreen
from PySide6.QtWidgets import *

# import GERDPy modules
import GERDPy.boreholes as boreholes
import GERDPy.heatpipes as heatpipes
import GERDPy.heating_element as heating_element
import GERDPy.gfunction as gfunction
import GERDPy.load_aggregation as load_aggregation
import GERDPy.utilities as utilities
from .load_generator import *
from .R_th import *
from .weather_data import get_weather_data
from .geometrycheck import check_geometry


def main(self):

    # -------------------------------------------------------------------------
    # 1.) Parametrization of the simulation (geometries, physical params, etc.)
    # -------------------------------------------------------------------------

    tic = tim.time()  # time stamp (start simulation)

    print(80 * '-')
    print('Initializing simulation...')
    print(80 * '-')
    self.ui.text_console.insertPlainText(80 * '-' + '\n')  # GUI-console output
    self.ui.text_console.insertPlainText('Initializing simulation...\n')
    self.ui.text_console.insertPlainText(80 * '-' + '\n')

    # Open GUI-progress window
    progapp = QApplication.instance()
    progwindow = SplashScreen()
    progwindow.show()

    progwindow.ui.running.setText("Initialization...")
    progapp.processEvents()

    # 1.0) Location
    h_NHN = self.ui.sb_h_NHN.value()  # elevation (above sea-level) [m]

    # 1.1) Erdboden
    a = self.ui.sb_therm_diffu.value() * 1.0e-6  # thermal diffusivity [m2/s] (default: 1.0)
    lambda_g = self.ui.sb_therm_cond.value()  # thermal conductivity [W/mK] (default: 2.0)
    Theta_g = self.ui.sb_undis_soil_temp.value()  # undisturbed ground temperature [°C] (default: 10.0)

    # 1.2) Borehole heat exchanger layout

    # Geometry-Import (.txt) & object generation
    boreField = boreholes.field_from_file(self, self.ui.line_borefield_file.text())  # './data/custom_field_5.txt'

    # Total depth of geothermal borefield (sum of all boreholes)
    H_field = boreholes.length_field(boreField)

    # Borefield layout plot
    boreholes.visualize_field(boreField)

    # 1.3) Borehole

    # Geometry
    N = self.ui.sb_number_heatpipes.value()  # no. of heatpipes per borehole [-] (default: 6)
    r_b = self.ui.sb_r_borehole.value()  # borehole radius [m] (boreField[0].r_b)
    r_w = self.ui.sb_radius_w.value()  # radius of heatpipe-centres [m] (default: 0.12)
    r_iso_b = self.ui.sb_radius_iso.value()  # outer radius of heatpipe insulation [m] (default: 0.016)
    r_pa = self.ui.sb_radius_pa.value()  # outer radius of heatpipes [m] (default: 0.016)
    r_pi = self.ui.sb_radius_pi.value()  # inner radius of heatpipes [m] (default: 0.015)

    # Thermal conductivities
    lambda_b = self.ui.sb_lambda_b.value()  # ~ of borehole backfill [W/mK] (default: 2.0)
    lambda_iso = self.ui.sb_lambda_iso.value()  # ~ of insulation layer [W/mK] (default: 0.03)
    lambda_p = self.ui.sb_lambda_p.value()  # ~ of heatpipe material [W/mK] (default: 14.0)

    # Heatpipe-object generation
    hp = heatpipes.Heatpipes(N, r_b, r_w, r_iso_b, r_pa, r_pi, lambda_b,
                             lambda_iso, lambda_p)

    # Heatpipe configuration layout plot
    hp.visualize_hp_config()

    # 1.4) Connection borehole-to-heating element

    # Geometry
    D_iso_an = self.ui.sb_D_iso_an.value()  # thickness of the insulation layer [m] (default: 0.005)
    r_iso_an = r_pa + D_iso_an  # outer radius of the insulation layer [m]

    # Total length of borehole-to-heating element connections (starting from ground surface) [m]
    ''' l_an is the total length of all borehole-to-heating element connections, while
        l_an * N yields the total heatpipe-length inside all borehole-to-heating element connections (= heatpipe bundles)
    '''
    l_an = self.ui.sb_l_An.value()  # default: 5

    # 1.5) Heating element

    # Surface area [m2]
    A_he = self.ui.sb_A_he.value()  # (default: 35.0)

    # Minimum vertical pipe-to-surface distance [m]
    x_min = self.ui.sb_x_min.value()  # (default: .025)

    # Thermal conductivity [W/mK]
    lambda_Bet = self.ui.sb_lambda_Bet.value()  # default: 2.1

    # centre-distance between heatpipes [m]
    s_R = self.ui.sb_s_R.value()    # default: 0.050

    # Total heatpipe length inside heating element [m]
    l_R = self.ui.sb_l_R.value()    # default: 1000

    # Vertical thickness of heating element [m]
    D_he = self.ui.sb_D_he.value()  # default: 0.25

    # Vertical thickness of insulation layer on underside of heating element [m]
    D_iso_he = self.ui.sb_D_iso_he.value()  # default: 0.03

    # Heating element-object generation
    he = heating_element.HeatingElement(A_he, x_min, lambda_Bet, lambda_p,
                                        2 * r_pa, 2 * r_pi, s_R, l_R,
                                        D_he, D_iso_he)

    # 2.) Simulation

    # Simulation-Params
    ''' default value for 'dt' is 3600 seconds (equaling one hour)
    '''
    dt = 3600.  # time increment (step size) [s] (default: 3600)
    if self.ui.rb_multiyearsim.isChecked():
        tmax = self.ui.sb_simtime.value() * 365 * 24 * dt  # total simulation time (multiple years) [s]
    else:
        tmax = self.ui.sb_simtime.value() * dt  # total simulation time [s] (default: 730 h * 3600 s)
    Nt = int(np.ceil(tmax / dt))  # number of time steps [-]

    # -------------------------------------------------------------------------
    # 2.) Geometric compatibility check (boreholes & heat pipes)
    # -------------------------------------------------------------------------

    if check_geometry(boreField, hp, self):
        print(80*'-')
        print('Geometry-Check: not OK! - Simulation aborted')
        print(80*'-')
        self.ui.text_console.insertPlainText(80 * '-' + '\n')  # GUI-console output
        self.ui.text_console.insertPlainText('Geometry-Check: not OK! - Simulation aborted\n')
        self.ui.text_console.insertPlainText(80 * '-' + '\n')
        sys.exit()
    else:
        print(80*'-')
        print('Geometry-Check: OK!')
        print(80*'-')
        self.ui.text_console.insertPlainText(80 * '-' + '\n')  # GUI-console output
        self.ui.text_console.insertPlainText('Geometry-Check: OK!\n')
        self.ui.text_console.insertPlainText(80 * '-' + '\n')

        progwindow.ui.running.setText("Geometry-Check: OK!")  # update GUI-progress window

    # -------------------------------------------------------------------------
    # 3.) Determination of system thermal resistances
    # -------------------------------------------------------------------------
    
    # ground-to-surface (whole system)
    R_th = R_th_c(boreField) + R_th_b(lambda_g, boreField, hp) + \
        R_th_hp(boreField, hp) + R_th_he(he)

    # ground-to-heatpipes (omits heating element)
    R_th_ghp = R_th_c(boreField) + R_th_b(lambda_g, boreField, hp) + \
        R_th_hp(boreField, hp)

    # -------------------------------------------------------------------------
    # 4.) G-Function generation (Pygfunction ground model)
    # -------------------------------------------------------------------------

    # Simulation environment setup using 'load_aggregation.py'
    LoadAgg = load_aggregation.ClaessonJaved(dt, tmax)
    time_req = LoadAgg.get_times_for_simulation()

    # G-Function calculation using 'gfunction.py'
    gFunc = gfunction.uniform_temperature(boreField, time_req, a, self,
                                          nSegments=12)

    # Simulation initialization using 'load_aggregation.py'
    LoadAgg.initialize(gFunc/(2*pi*lambda_g))

    # -------------------------------------------------------------------------
    # 5.) Weather data import
    # -------------------------------------------------------------------------

    # Import weather data from 'weather_data.py'
    u_inf, Theta_inf, S_w, B, Phi, RR = get_weather_data(Nt, self)
    ''' u_inf       - ambient wind speed [m/s]
        Theta_inf   - ambient temperature [°C]
        S_w         - snowfall rate [mm/h]
        B           - cloudiness [octal units/8]
        Phi         - relative air humidity [%]
        RR          - precipitation (total) [mm/h]
    '''

    # -------------------------------------------------------------------------
    # 6.) Iteration loop (Simulation using Nt time steps of stepsize dt)
    # -------------------------------------------------------------------------

    time = 0.
    i = -1
    start_sb = False  # start snow balancing variable

    # Initialization of result vectors
    ''' Vectors: (i - current timestep)
        - thermal powers [W]:
            - Q[i]              - thermal extraction power (the total power extracted from the ground)
            - Q_N[i]            - net used power (power used for melting snow & ice)
            - Q_V[i]            - thermal power losses via connection & heating element underside
        - temperatures [°C]:
            - Theta_b[i]        - borehole wall temperature
            - Theta_surf[i]     - heating element surface temperature
        - mass balances [kg]:
            - m_Rw[i]           - residual water
            - m_Rs[i]           - residual snow
    '''
    
    # Initialization of power vectors [W]
    Q = np.zeros(Nt)  # total extracted thermal power
    Q_N = np.zeros(Nt)  # net used power
    Q_V = np.zeros(Nt)  # losses
    
    # Initialization of temperature vectors [°C]
    Theta_b = np.zeros(Nt)  # borehole wall temperature
    Theta_surf = np.zeros(Nt)  # heating element surface temperature

    # Initialization of water mass balancing vector [kg]
    m_Rw = np.zeros(Nt)

    # Initialization of snow mass balancing vector [kg]
    m_Rs = np.zeros(Nt)

    # Auxiliary variables
    start_sb_vector = np.zeros(Nt)
    sb_active = np.zeros(Nt)
    sim_mod = np.zeros(Nt)

    R_f = self.ui.sb_rf.value() # Snow free area ration (default: 0.2)

    print('-----------------Simulation started-----------------\n')
    self.ui.text_console.insertPlainText('-----------------Simulation started-----------------\n')  # GUI-console output

    progwindow.ui.running.setText("Simulation running...")

    while time < tmax:  # iteration loop for each timestep

        # increment timestep by 1
        if start_sb == False:  # timestep not incremented in case snow balancing starts
            time += dt
            i += 1

        LoadAgg.next_time_step(time)

        # Timestep 1
        ''' Assumptions: 
            - Theta_b = Theta_surf = Theta_g (undisturbed ground temperature for all temperature objects)
            - heating element surface dry and free of snow
        '''
        if i == 0:
            Q[i], Q_N[i], Q_V[i], calc_T, Theta_surf[i], m_Rw[i], m_Rs[i], sb_active[i], sim_mod[i] = \
                load(h_NHN, u_inf[i], Theta_inf[i], S_w[i], he, Theta_g,
                     R_th, R_th_ghp, Theta_g, B[i], Phi[i], RR[i], 0, 0, start_sb,
                     l_an * N, lambda_p, lambda_iso, r_iso_an, r_pa, r_pi, R_f)

        # Timesteps 2, 3, ..., Nt
        if i > 0:
            Q[i], Q_N[i], Q_V[i], calc_T, Theta_surf[i], m_Rw[i], m_Rs[i], sb_active[i], sim_mod[i] = \
                load(h_NHN, u_inf[i], Theta_inf[i], S_w[i], he, Theta_b[i - 1],
                     R_th, R_th_ghp, Theta_surf[i - 1], B[i], Phi[i], RR[i], m_Rw[i - 1], m_Rs[i - 1], start_sb,
                     l_an * N, lambda_p, lambda_iso, r_iso_an, r_pa, r_pi, R_f)

        # Determined extraction power is incremented by the connection losses (An) and losses of the heating element underside (he)
        Q[i] += Q_V[i]

        start_sb = False  # reset snow balancing variable

        # Load extraction power of current time step into the ground model using 'load_aggregation.py'
        LoadAgg.set_current_load(Q[i] / H_field)

        # Calculate "new" borehole wall temperature after heat extraction [°C]
        deltaTheta_b = LoadAgg.temporal_superposition()
        Theta_b[i] = Theta_g - deltaTheta_b

        # Calculate "new" surface temperature after heat extraction [°C]
        ''' Theta_surf is only calculated here, if Q. >= 0 (positive heat extraction from ground),
            otherwise it is calculated in 'load_generator.py', using the simplified power balance F_T = 0.
        '''
        if calc_T is False:
            Theta_surf[i] = Theta_b[i] - Q[i] * R_th  # heating element surface temperature

        # Start snow balancing
        ''' The time step i will be repeated once in snow balancing mode if the following conditions 
            for the formation of a snow layer are met:
            - Theta_surf[i] < 0 AND
            - S_w[i] > 0 AND
            - m_Rs[i] == 0 (no remaining snow on surface)
        '''
        if (Theta_surf[i] < 0 and S_w[i] > 0 and m_Rs[i] == 0):
            start_sb = True
            start_sb_vector[i] = 1

        # Current timestep: output to console
        print(f'Zeitschritt {i + 1} von {Nt}')

        # Update GUI-progress window
        progwindow.progress.set_value(int(i/Nt*100))
        progapp.processEvents()

    progwindow.close()

    toc = tim.time()  # time stamp (end simulation)
    print('Total simulation time: {} sec'.format(toc - tic))
    self.ui.text_console.insertPlainText(80 * '-' + '\n')  # GUI-console output
    self.ui.text_console.insertPlainText('Total simulation time: {} sec\n'.format(toc - tic))
    self.ui.text_console.insertPlainText(80 * '-' + '\n')

    # -------------------------------------------------------------------------
    # 7.) Energy performance indicators
    # -------------------------------------------------------------------------
    ''' Q_ma                - total extracted thermal power, 24h-moving-average [W]
        E                   - total extracted thermal energy [MWh]
        f_N [%] = E_N / E   - net energy usage factor [%]
            E_N             - net used energy (latent & sensible energy for melting of snow and ice)
            E - E_N         - net energy "lost" through convection, radiation and evaporation (surface losses)
    '''

    # 24h-moving-average total extracted thermal power [W]
    Q_ma = utilities.Q_moving_average(Q)

    # Total extracted thermal energy [MWh]
    E = (np.sum(Q) / len(Q)) * Nt * 1e-6

    print('-----------------Simulation finished-----------------')

    print(f'Energy extracted from the ground: {round(E, 4)} MWh')
    self.ui.text_console.insertPlainText(80*'-'+'\n')
    self.ui.text_console.insertPlainText(f'Energy extracted from the ground: {round(E, 4)} MWh\n')
    self.ui.text_console.insertPlainText(80 * '-' + '\n')

    # Net energy usage factor [%]
    # f_N = (np.sum(Q_N) / len(Q_N)) / (np.sum(Q) / len(Q)) * 100
    # print(f'{round(f_N, 2)} % of that energy went into melting snow and ice.'
    #       f'The rest are surface losses in the form of convection, radiation and evaporation and \n'
    #       f'thermal losses at the heating element underside and borehole-to-heating element connections.')
    # print(50*'-')
    # self.ui.text_console.insertPlainText(
    #     f'{round(f_N, 2)} % of that energy went into melting snow and ice.'
    #     f'The rest are surface losses in the form of convection, radiation and evaporation and \n'
    #     f'thermal losses at the heating element underside and borehole-to-heating element connections.')

    # -------------------------------------------------------------------------
    # 8.) Result Plots
    # -------------------------------------------------------------------------

    # x-Axis (simulation hours) [h]
    hours = np.array([(j+1)*dt/3600. for j in range(Nt)])

    plt.rc('figure')
    fig1 = plt.figure()
    fig2 = plt.figure()

    font = {'weight': 'bold', 'size': 10}
    plt.rc('font', **font)

    # Load profile
    # fig1
    ax1 = fig1.add_subplot(411)
    ax1.set_ylabel(r'$q$ [W/m2]')
    ax1.plot(hours, Q / A_he, 'k-', lw=1.2)  # total extracted thermal power [W]
    ax1.plot(hours, Q_ma / A_he, 'r--', lw=1.2)  # total extracted thermal power (24h-moving-average) [W]
    ax1.plot(hours, Q_V / A_he, 'g-', lw=1.2)  # thermal losses (underside heating element & connection) [W]
    ax1.legend(['Extracted thermal power', 'Extracted thermal power (24h-moving-average)',
                'Thermal losses (underside heating element & connection)'],
               prop={'size': font['size']}, loc='upper left')
    ax1.grid('major')

    # Snowfall rate - snow height
    # fig1
    ax2 = fig1.add_subplot(412)
    ax2.set_ylabel('Snowfall rate [mm/h] \n Snow height on heating element [H2O-mm]')
    ax2.plot(hours, S_w, 'b-', lw=0.8)  # snowfall rate [mm/h]
    ax2.plot(hours, m_Rs / (A_he * (997 / 1000)), 'g-', lw=0.8)  # snow height on heating element [mm]
    ax2.legend(['Snowfall rate', 'Snow height on heating element'],
               prop={'size': font['size']}, loc='upper left')
    ax2.grid('major')
    
    # Ambient temperature - ambient wind speed
    # fig1
    ax3 = fig1.add_subplot(413)
    ax3.set_ylabel('$T$ [degC] \n Ambient wind speed [m/s]')
    ax3.plot(hours, Theta_inf, 'k-', lw=0.8)  # ambient temperature [°C]
    ax3.plot(hours, u_inf, 'm--', lw=0.8)  # ambient wind speed [m/s]
    ax3.legend(['Ambient temperature', 'Ambient wind speed'],
                 prop={'size': font['size']}, loc='upper right')
    ax3.grid('major')

    # Temperature curves
    # fig1
    ax4 = fig1.add_subplot(414)
    ax4.set_xlabel(r'$t$ [h]')
    ax4.set_ylabel(r'$T$ [degC]')
    ax4.plot(hours, Theta_b, 'r-', lw=1.2)  # borehole wall temperature [°C]
    ax4.plot(hours, Theta_surf, 'c-', lw=0.6)  # heating element surface temperature [°C]
    ax4.legend(['T_borehole-wall', 'T_surface'],
               prop={'size': font['size']}, loc='upper right')
    ax4.grid('major')
    
    # Borehole wall temperature annual stacked curves
    # fig2
    ax5 = fig2.add_subplot(211)
    ax5.set_xlabel(r'$t$ [h]')
    ax5.set_ylabel(r'$T$ [degC]')
    if self.ui.rb_multiyearsim.isChecked():
        colour_map = iter(plt.cm.gist_rainbow(np.linspace(0, 1, self.ui.sb_simtime.value())))
        for j in range(self.ui.sb_simtime.value()):
            ax5.plot(np.arange(1, 8761, 1, dtype=int), Theta_b[(0+j*8760):(8760+j*8760)], c=next(colour_map), 
                     lw=0.7, label=f'Borehole wall temperature - Year {j+1}')
    else:
        ax5.plot(hours, Theta_b, 'r-', lw=1.2, label='Borehole wall temperature - Year 1')
    ax5.legend(prop={'size': font['size'] - 2}, loc='lower center')
    ax5.grid('major')
    
    # Borehole wall temperature single value over years
    # fig2

    # Axis ticks
    ax1.xaxis.set_minor_locator(AutoMinorLocator())
    ax1.yaxis.set_minor_locator(AutoMinorLocator())
    ax2.xaxis.set_minor_locator(AutoMinorLocator())
    ax2.yaxis.set_minor_locator(AutoMinorLocator())
    ax3.xaxis.set_minor_locator(AutoMinorLocator())
    ax3.yaxis.set_minor_locator(AutoMinorLocator())
    ax4.xaxis.set_minor_locator(AutoMinorLocator())
    ax4.yaxis.set_minor_locator(AutoMinorLocator())
    ax5.xaxis.set_minor_locator(AutoMinorLocator())
    ax5.yaxis.set_minor_locator(AutoMinorLocator())
    # ax6.xaxis.set_minor_locator(AutoMinorLocator())
    # ax6.yaxis.set_minor_locator(AutoMinorLocator())

    # plt.tight_layout()
    #plt.show()

    # -------------------------------------------------------------------------
    # 9.) Results dataframe
    # -------------------------------------------------------------------------

    results = pd.DataFrame({'timestep': hours, 'Q_extracted [W]': Q/A_he, 'Q_losses [W]': Q_V/A_he,
                            'T_borehole-wall [°C]': Theta_b, 'T_surface [°C]': Theta_surf, 'T_ambient [°C]': Theta_inf,
                            'u_wind [m/s]': u_inf, 'Snowfall rate [mm/h]': S_w, 'Snow heigth [mm]': m_Rs / (A_he * (997/1000))})

    return results


# Main function
if __name__ == '__main__':
    main()
