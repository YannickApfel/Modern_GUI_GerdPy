# -*- coding: utf-8 -*-
""" GERDPy - '_main.py'

    Main Control-File of GERDPy - The Simulation Tool for Geothermal Heat Pipe Surface Heating Systems

    Legend:
        Parameter [Unit]
        - Temperatures:
            - T in Kelvin [K] - for caloric equations
            - Theta in degrees Celsius [°C] - for object temperatures

    Author(s): Yannick Apfel, Meike Martin
"""
import sys
import matplotlib.pyplot as plt
import time as tim
import numpy as np
from matplotlib.ticker import AutoMinorLocator
from scipy.constants import pi

# import GERDPy-modules
import GERDPy.boreholes as boreholes
import GERDPy.heatpipes as heatpipes
import GERDPy.heating_element as heating_element
import GERDPy.gfunction as gfunction
import GERDPy.load_aggregation as load_aggregation
from .load_generator import *
from .R_th_tot import *
from .weather_data import get_weather_data
from .geometrycheck import check_geometry

# import progress-modules
from progress.vismain import SplashScreen
from PySide6.QtWidgets import *


def main(self):

    # -------------------------------------------------------------------------
    # 1.) Parametrization of the simulation (geometries, physical params, etc.)
    # -------------------------------------------------------------------------

    print(80 * '-')
    print('Initializing simulation...')
    print(80 * '-')
    self.ui.text_console.insertPlainText(80 * '-' + '\n')
    self.ui.text_console.insertPlainText('Initializing simulation...\n')
    self.ui.text_console.insertPlainText(80 * '-' + '\n')

    # Open progress window
    progapp = QApplication.instance()
    progwindow = SplashScreen()
    progwindow.show()

    progwindow.ui.running.setText("Initialization...")
    progapp.processEvents()

    # 1.0) Location
    h_NHN = self.ui.sb_h_NHN.value()                            # elevation (above sea-level) [m]

    # 1.1) Erdboden
    a = self.ui.sb_therm_diffu.value() * 1.0e-6                 # thermal diffusivity [m2/s] (default: 1.0)
    lambda_g = self.ui.sb_therm_cond.value()                    # thermal conductivity [W/mK] (default: 2.0)
    Theta_g = self.ui.sb_undis_soil_temp.value()                # undisturbed ground temperature [°C] (default: 10.0)

    # 1.2) Borehole heat exchanger layout

    # Geometry-Import (.txt) & object generation
    boreField = boreholes.field_from_file(self, self.ui.line_borefield_file.text())  # './data/custom_field_5.txt'

    # Total length of geothermal borefield (boring depth)
    H_field = boreholes.length_field(boreField)

    # Borefield layout plot
    boreholes.visualize_field(boreField)

    # 1.3) Borehole

    # Geometry
    N = self.ui.sb_number_heatpipes.value()                     # no. of heatpipes per borehole [-] (default: 6)
    r_b = self.ui.sb_r_borehole.value()                         # borehole radius [m] (boreField[0].r_b)
    r_w = self.ui.sb_radius_w.value()                           # radius of heatpipe-centres [m] (default: 0.12)
    r_iso_b = self.ui.sb_radius_iso.value()                     # outer radius of heatpipe insulation [m] (default: 0.016)
    r_pa = self.ui.sb_radius_pa.value()                         # outer radius of heatpipes [m] (default: 0.016)
    r_pi = self.ui.sb_radius_pi.value()                         # inner radius of heatpipes [m] (default: 0.015)

    # Thermal conductivities
    lambda_b = self.ui.sb_lambda_b.value()                      # ~ of borehole backfill [W/mK] (default: 2.0)
    lambda_iso = self.ui.sb_lambda_iso.value()                  # ~ of insulation layer [W/mK] (default: 0.03)
    lambda_p = self.ui.sb_lambda_p.value()                      # ~ of heatpipe material [W/mK] (default: 14.0)

    # Heatpipe-object generation
    hp = heatpipes.Heatpipes(N, r_b, r_w, r_iso_b, r_pa, r_pi, lambda_b,
                             lambda_iso, lambda_p)

    # Heatpipe configuration layout plot
    hp.visualize_hp_config()

    # 1.4) Connection borehole-to-heating element

    # Geometry
    D_iso_An = 0.005                                            # thickness of the insulation layer [m]
    r_iso_An = r_pa + D_iso_An                                  # outer radius of the insulation layer [m]

    # Total length of borehole-to-heating element connections (starting from ground surface) [m]
    ''' l_An is the total length of all borehole-to-heating element connections, while
        l_An * N yields the total heatpipe-length inside all borehole-to-heating element connections (= heatpipe bundles)
    '''
    l_An = 5

    # 1.5) Heating element

    # Surface area [m2]
    A_he = self.ui.sb_A_he.value()                              # (default: 35.0)

    # Minimum vertical pipe-to-surface distance [m]
    x_min = self.ui.sb_x_min.value()                            # (default: .025)

    # Thermal conductivity [W/mK]
    lambda_Bet = 2.1

    # Centre-distance of heatpipes [m]
    s_R = .050

    # Total length of heatpipes inside heating element [m]
    l_R = 1000

    # Vertical thickness of heating element [m]
    D_he = 0.25

    # Vertical thickness of insulation layer on underside of heating element [m]
    D_iso_he = 0.03

    # Heating element-object generation
    he = heating_element.HeatingElement(A_he, x_min, lambda_Bet, lambda_p,
                                        2 * r_pa, 2 * r_pi, s_R, l_R,
                                        D_he, D_iso_he)

    # 2.) Simulation

    # Simulation-Params
    ''' default value for 'dt' is 3600 seconds (equaling one hour) - usage of
        smaller time increments not suggested to stay within validity range of 
        long-term g-functions
    '''
    dt = 3600.                                                  # time increment (step size) [s] (default: 3600)
    tmax = self.ui.sb_simtime.value() * 3600                    # total simulation time [s] (default: 730 h * 3600 s)
    Nt = int(np.ceil(tmax / dt))                                # number of time steps [-]

    # -------------------------------------------------------------------------
    # 2.) Geometric compatibility check (boreholes & heat pipes)
    # -------------------------------------------------------------------------

    if check_geometry(boreField, hp, self):
        print(80*'-')
        print('Geometry-Check: not OK! - Simulation aborted')
        print(80*'-')
        self.ui.text_console.insertPlainText(80 * '-' + '\n')
        self.ui.text_console.insertPlainText('Geometry-Check: not OK! - Simulation aborted\n')
        self.ui.text_console.insertPlainText(80 * '-' + '\n')
        sys.exit()
    else:
        print(80*'-')
        print('Geometry-Check: OK!')
        print(80*'-')
        self.ui.text_console.insertPlainText(80 * '-' + '\n')
        self.ui.text_console.insertPlainText('Geometry-Check: OK!\n')
        self.ui.text_console.insertPlainText(80 * '-' + '\n')

        progwindow.ui.running.setText("Geometry-Check: OK!")

    # -------------------------------------------------------------------------
    # 3.) Determination of system thermal resistances
    # -------------------------------------------------------------------------

    R_th = R_th_tot(lambda_g, boreField, hp, he)                # ground-to-surface (whole system)
    R_th_ghp = R_th_g_hp(lambda_g, boreField, hp)               # ground-to-heatpipes (omits heating element)

    # -------------------------------------------------------------------------
    # 4.) G-Function generation (Pygfunction ground model)
    # -------------------------------------------------------------------------

    # Time stamp (start simulation)
    tic = tim.time()

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
        S_w         - snowfall rate [mm/s]
        B           - cloudiness [octal units/8]
        Phi         - relative air humidity [%]
    '''

    # -------------------------------------------------------------------------
    # 6.) Iterationsschleife (Simulation mit Nt Zeitschritten der Länge dt)
    # -------------------------------------------------------------------------

    time = 0.
    i = -1
    start_sb = False  # sb - snow balancing

    # Initialisierung Temperaturen [°C]
    ''' Vektoren:
            P[i] - Entzugsleistung f. Zeitschritt i 
            Theta_surf[i] - Oberflächentemp. f. Zeitschritt i
    '''
    Theta_b = np.zeros(Nt)  # Bohrlochrand
    Theta_surf = np.zeros(Nt)  # Oberfläche Heizelement

    # Initialisierung Vektor für Restwassermenge [mm]
    m_Rw = np.zeros(Nt)

    # Initialisierung Vektor für Restschneemenge [mm - Wasserequivalent]
    m_Rs = np.zeros(Nt)

    # Initialisierung Gesamt-Entzugsleistung, Nutzleistung und Verluste [W]
    Q = np.zeros(Nt)
    Q_N = np.zeros(Nt)
    Q_V = np.zeros(Nt)

    # Hilfsgrößen
    start_sb_counter = np.zeros(Nt)
    sb_active = np.zeros(Nt)
    sim_mod = np.zeros(Nt)

    print('-----------------Simulation gestartet-----------------\n')
    self.ui.text_console.insertPlainText('-----------------Simulation gestartet-----------------\n')

    progwindow.ui.running.setText("Simulation running...")

    while time < tmax:  # Iterationsschleife (ein Durchlauf pro Zeitschritt)

        # Zeitschritt um 1 inkrementieren
        if start_sb == False:
            time += dt
            i += 1

        LoadAgg.next_time_step(time)

        # Ermittlung der Entzugsleistung im 1. Zeitschritt
        if i == 0:  # Annahme Theta_b = Theta_surf = Theta_g, Heizelementoberfläche trocken und schneefrei
            Q[i], Q_N[i], Q_V[i], calc_T_surf, Theta_surf[i], m_Rw[i], m_Rs[i], sb_active[i], sim_mod[i] = \
                load(h_NHN, u_inf[i], Theta_inf[i], S_w[i], he, Theta_g,
                     R_th, R_th_ghp, Theta_g, B[i], Phi[i], RR[i], 0, 0, start_sb,
                     l_An * N, lambda_p, lambda_iso, r_iso_An, r_pa, r_pi)

        # Ermittlung der Entzugsleistung im Zeitschritt 2, 3, ..., Nt
        if i > 0:
            Q[i], Q_N[i], Q_V[i], calc_T_surf, Theta_surf[i], m_Rw[i], m_Rs[i], sb_active[i], sim_mod[i] = \
                load(h_NHN, u_inf[i], Theta_inf[i], S_w[i], he, Theta_b[i - 1],
                     R_th, R_th_ghp, Theta_surf[i - 1], B[i], Phi[i], RR[i], m_Rw[i - 1], m_Rs[i - 1], start_sb,
                     l_An * N, lambda_p, lambda_iso, r_iso_An, r_pa, r_pi)

        # Erhöhung der ermittelten Entzugsleistung um die Verluste an Anbindung (An) und Unterseite des Heizelements (He)
        Q[i] += Q_V[i]

        start_sb = False  # Variable Start-Schneebilanzierung zurücksetzen

        # Aufprägung der ermittelten Entzugsleistung auf Bodenmodell ('load_aggregation.py')
        LoadAgg.set_current_load(Q[i] / H_field)

        # Temperatur am Bohrlochrand [°C]
        deltaTheta_b = LoadAgg.temporal_superposition()
        Theta_b[i] = Theta_g - deltaTheta_b

        # Temperatur an der Oberfläche des Heizelements [°C]
        ''' Theta_surf wird hier nur ermittelt, falls Q. >= 0 (positive Entzugsleistung aus Boden), sonst
            erfolgt deren Ermittlung in 'load_generator.py' mit Hilfe einer vereinfachten Leistungsbilanz an der Oberfläche.
        '''
        if calc_T_surf is False:
            Theta_surf[i] = Theta_b[i] - Q[i] * R_th  # Oberflächentemp.

        # Schneebilanzierung starten
        ''' Zeitschritt wird einmalig wiederholt, falls sich eine Schneeschicht beginnt zu bilden:
            - Oberflächentemperatur Theta_surf[i] < 0 UND
            - Schneefallrate S_w[i] > 0 UND
            - Restschneemenge m_Rs[i] == 0 (noch keine Restschneemenge vorhanden)
            müssen erfüllt sein

            => Schnee bleibt liegen: Schneebilanz an Oberfläche
        '''
        if (Theta_surf[i] < 0 and S_w[i] > 0 and m_Rs[i] == 0):
            start_sb = True
            start_sb_counter[i] = 1

        # Konsolenausgabe des momentanen Zeitschritts
        print(f'Zeitschritt {i + 1} von {Nt}')

        # Update progress window
        progwindow.progress.set_value(int(i/Nt*100))
        progapp.processEvents()

    progwindow.close()

    # Zeitstempel (Simulationsdauer) [s]
    toc = tim.time()
    print('Total simulation time: {} sec'.format(toc - tic))
    self.ui.text_console.insertPlainText(80 * '-' + '\n')
    self.ui.text_console.insertPlainText('Total simulation time: {} sec\n'.format(toc - tic))
    self.ui.text_console.insertPlainText(80 * '-' + '\n')

    # -------------------------------------------------------------------------
    # 7.) Energiekennzahlen
    # -------------------------------------------------------------------------
    ''' Q_m                 - zeitlich gemittelte Entzugsleistung [W]
        E                   - Gesamtenergiemenge, die dem Boden entzogen wurde [MWh]
        f_N [%] = E_N / E   - Nutzenergiefaktor [%]
            E_N             - zur sensiblen Erwärmung und latenten Schmelze des Schnees verwendete Energie
            E - E_N         - Summe der Verluste durch Konvektion, Strahlung und Verdunstung
    '''

    # 24h-gemittelte Entzugsleistung (gleitender Mittelwert)
    Q_ma = Q_moving_average(Q)

    # Gesamtenergiemenge [MWh]
    E = (np.sum(Q) / len(Q)) * Nt * 1e-6

    print('-----------------Simulation beendet-----------------')

    print(f'Dem Boden wurden {round(E, 4)} MWh entnommen')
    self.ui.text_console.insertPlainText(80*'-'+'\n')
    self.ui.text_console.insertPlainText(f'Obtained energy from ground: {round(E, 4)} MWh\n')
    self.ui.text_console.insertPlainText(80 * '-' + '\n')

    # Nutzenergiefaktor [%]
    # f_N = (np.sum(Q_N) / len(Q_N)) / (np.sum(Q) / len(Q)) * 100
    # print(f'Davon wurden {round(f_N, 2)} % als Nutzenergie zur Schneeschmelze aufgewendet. '
    #       f'Der Rest sind Verluste an der Ober- und Unterseite des Heizelements sowie dessen Anbindungsleitungen.')
    # print(50*'-')
    # self.ui.text_console.insertPlainText(f'Davon wurden {round(f_N, 2)} % als Nutzenergie zur Schneeschmelze aufgewendet. '
    #                                      f'Der Rest sind Verluste an der Ober-, Unterseite und Anbindungsleitungen.')

    # -------------------------------------------------------------------------
    # 8.) Plots für End-User
    # -------------------------------------------------------------------------

    # x-Achse aller Plots (Simulationsstunden) [h]
    hours = np.array([(j+1)*dt/3600. for j in range(Nt)])

    plt.rc('figure')
    fig1 = plt.figure()

    font = {'weight': 'bold', 'size': 10}
    plt.rc('font', **font)

    # Lastprofil {Entzugsleistung - Entzugsleistung (24h-gemittelt) - Verluste (Anbindung + Unterseite Heizelement)}
    ax1 = fig1.add_subplot(411)
    ax1.set_ylabel(r'$q$ [W/m2]')
    ax1.plot(hours, Q / A_he, 'k-', lw=1.2)
    ax1.plot(hours, Q_m / A_he, 'r--', lw=1.2)
    ax1.plot(hours, Q_V / A_he, 'g-', lw=1.2)
    ax1.legend(['Entzugsleistung', 'Entzugsleistung-24h-gemittelt',
                'Verluste (Anbindung + Unterseite Heizelement)'],
               prop={'size': font['size']}, loc='upper left')
    ax1.grid('major')

    # Schneefallrate - Schneehöhe - Umgebungstemperatur - Windgeschwindigkeit
    ax2 = fig1.add_subplot(412)
    ax2.set_ylabel('Schneefallrate [mm/h] \n Schneehöhe [mm]')
    ax2.plot(hours, S_w, 'b-', lw=0.8)
    ax2.plot(hours, m_Rs / A_he, 'g-', lw=0.8)
    ax2.legend(['Schneefallrate', 'Schneehöhe'],
               prop={'size': font['size']}, loc='upper left')
    ax2.grid('major')
    
    # Umgebungstemperatur - Windgeschwindigkeit
    ax3 = fig1.add_subplot(413)
    ax3.set_ylabel('$T$ [degC] \n Windgeschwindigkeit [m/s]')
    ax3.plot(hours, Theta_inf, 'k-', lw=0.8)
    ax3.plot(hours, u_inf, 'm--', lw=0.8)
    ax3.legend(['Umgebungstemperatur', 'Windgeschwindigkeit'],
                 prop={'size': font['size']}, loc='upper right')
    ax3.grid('major')

    # Temperaturverläufe Bohrlochrand und Oberfläche Heizelement
    ax4 = fig1.add_subplot(414)
    ax4.set_xlabel(r'$t$ [h]')
    ax4.set_ylabel(r'$T$ [degC]')
    ax4.plot(hours, Theta_b, 'r-', lw=1.2)
    ax4.plot(hours, Theta_surf, 'c-', lw=0.6)
    ax4.legend(['T_Bohrlochrand', 'T_Oberflaeche'],
               prop={'size': font['size']}, loc='upper right')
    ax4.grid('major')

    # Beschriftung Achsenwerte
    ax1.xaxis.set_minor_locator(AutoMinorLocator())
    ax1.yaxis.set_minor_locator(AutoMinorLocator())
    ax2.xaxis.set_minor_locator(AutoMinorLocator())
    ax2.yaxis.set_minor_locator(AutoMinorLocator())
    ax3.xaxis.set_minor_locator(AutoMinorLocator())
    ax3.yaxis.set_minor_locator(AutoMinorLocator())
    ax4.xaxis.set_minor_locator(AutoMinorLocator())
    ax4.yaxis.set_minor_locator(AutoMinorLocator())

    # plt.tight_layout()
    plt.show()
    
    return


# Main function
if __name__ == '__main__':
    main()
