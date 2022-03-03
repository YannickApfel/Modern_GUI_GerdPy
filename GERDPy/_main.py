# -*- coding: utf-8 -*-
""" GERDPy - Main-File
    Steuerungsfile des Auslegungstools für das Projekt GERDI

    Legende:
        - Temperaturen:
            - T in Kelvin [K] - für (kalorische) Gleichungen
            - Theta in Grad Celsius [°C] - Input aus dem Wetterdatenfile

    Autor: Yannick Apfel
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
    # 1.) Parametrierung der Simulation (Geometrien, Stoffwerte, etc.)
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

    # 1.0) Standort
    h_NHN = self.ui.sb_h_NHN.value()                            # Höhe des Standorts über Normal-Null

    # 1.1) Erdboden
    a = self.ui.sb_therm_diffu.value() * 1.0e-6                 # Temperaturleitfähigkeit [m2/s] (default: 1)
    lambda_g = self.ui.sb_therm_cond.value()                    # Wärmeleitfähigkeit [W/mK] (default: 2.0)
    Theta_g = self.ui.sb_undis_soil_temp.value()                # ungestörte Bodentemperatur [°C] (default: 10.0)

    # 1.2) Erdwärmesondenfeld

    # Geometrie-Import (.txt-Datei)
    boreField = boreholes.field_from_file(self, self.ui.line_borefield_file.text())  # './data/custom_field_5.txt'

    # Sondenmeter (gesamt)
    H_field = boreholes.length_field(boreField)

    # Layout-Plot des Erdwärmesondenfeldes
    boreholes.visualize_field(boreField)

    # 1.3) Bohrloch

    # Geometrie
    N = self.ui.sb_number_heatpipes.value()                     # Anzahl Heatpipes pro Bohrloch [-] (default: 6)
    r_b = self.ui.sb_r_borehole.value()                         # Radius der Erdwärmesondenbohrung [m] # boreField[0].r_b
    r_w = self.ui.sb_radius_w.value()                           # Radius der Wärmerohr-Mittelpunkte [m] (default: 0.12)
    r_iso_b = self.ui.sb_radius_iso.value()                     # Außenradius der Isolationsschicht [m] (default: 0.016)
    r_pa = self.ui.sb_radius_pa.value()                         # Außenradius der Wärmerohre [m] (default: 0.016)
    r_pi = self.ui.sb_radius_pi.value()                         # Innenradius der Wärmerohre [m] (default: 0.015)

    # Wärmeleitfähigkeiten
    lambda_b = self.ui.sb_lambda_b.value()                      # lambda der Hinterfüllung [W/mK] (default: 2)
    lambda_iso = self.ui.sb_lambda_iso.value()                  # lambda der Isolationsschicht [W/mK] (default: 0.03)
    lambda_p = self.ui.sb_lambda_p.value()                      # lambda der Heatpipe [W/mK] (default: 14.0)

    # Geometrie-Erstellung
    hp = heatpipes.Heatpipes(N, r_b, r_w, r_iso_b, r_pa, r_pi, lambda_b,
                             lambda_iso, lambda_p)
    # Layout-Plot der Wärmerohrkonfiguration
    hp.visualize_hp_config()

    # 1.4) Anbindung zum Heizelement (zusätzliche Größen)

    # Geometrie
    D_iso_An = 0.005                                            # Dicke der Isolationsschicht [m]
    r_iso_An = r_pa + D_iso_An                                  # Außenradius der Isolationsschicht [m]

    # Länge der Anbindungen zwischen Bohrlöchern und Heizelement (ab Geländeoberkante) [m]
    ''' l_An * N ergibt die Gesamtlänge an Heatpipe im Bereich der Anbindung
    '''
    l_An = 5

    # 1.5) Heizelement

    # Fläche Heizelement [m2]
    A_he = self.ui.sb_A_he.value()      # (default: 35)

    # minimaler Oberflächenabstand [m]
    x_min = self.ui.sb_x_min.value()    # (default: .025)

    # Wärmeleitfähigkeit des Betonelements [W/mk]
    lambda_Bet = 2.1

    # Mittelachsabstand der Kondensatrohre im Heizelement [m]
    s_R = .050

    # Gesamtlänge im Heizelement verbauter Kondensatrohre [m]
    l_R = 1000

    # Betondicke des Heizelements [m]
    D_he = 0.25

    # Dicke der Isolationsschicht an der Unterseite [m]
    D_iso_he = 0.03

    # Geometrie-Erstellung
    he = heating_element.HeatingElement(A_he, x_min, lambda_Bet, lambda_p,
                                        2 * r_pa, 2 * r_pi, s_R, l_R,
                                        D_he, D_iso_he)

    # 2.) Simulation

    # Simulationsparameter
    ''' dt darf 3600s (eine Stunde) aufgrund des Gültigkeitsbereichs der G-Functions
        nicht unterschreiten
    '''
    dt = 3600.                                                  # Zeitschrittweite [s] (default: 3600)
    tmax = self.ui.sb_simtime.value() * 3600                    # Gesamt-Simulationsdauer [s] (default: 730 h)
    Nt = int(np.ceil(tmax / dt))                                # Anzahl Zeitschritte [-]

    # -------------------------------------------------------------------------
    # 2.) Überprüfung der geometrischen Verträglichkeit (Sonden & Heatpipes)
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
    # 3.) Ermittlung thermischer Widerstände
    # -------------------------------------------------------------------------

    R_th = R_th_tot(lambda_g, boreField, hp, he)                # Gesamtsystem
    R_th_ghp = R_th_g_hp(lambda_g, boreField, hp)               # Boden bis Heatpipes

    # -------------------------------------------------------------------------
    # 4.) Ermittlung der G-Function (Bodenmodell)
    # -------------------------------------------------------------------------

    # Initialisierung Zeitstempel (Simulationsdauer)
    tic = tim.time()

    # Aufsetzen der Simulationsumgebung mit 'load_aggregation.py'
    LoadAgg = load_aggregation.ClaessonJaved(dt, tmax)
    time_req = LoadAgg.get_times_for_simulation()

    # Berechnung der G-Function mit 'gfunction.py'
    gFunc = gfunction.uniform_temperature(boreField, time_req, a, self,
                                          nSegments=12)

    # Initialisierung der Simulation mit 'load_aggregation.py'
    LoadAgg.initialize(gFunc/(2*pi*lambda_g))

    # -------------------------------------------------------------------------
    # 5.) Import / Generierung der Wetterdaten
    # -------------------------------------------------------------------------

    # Import Wetterdaten aus weather_data.py
    u_inf, Theta_inf, S_w, B, Phi, RR = get_weather_data(Nt, self)
    ''' u_inf       - Windgeschwindigkeit [m/s]
        Theta_inf   - Umgebungstemperatur [°C]
        S_w         - Schneefallrate (Wasserequivalent) [mm/s]
        B           - Bewölkungsgrad [octal units / 8]
        Phi         - rel. Luftfeuchte [%]
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

    print('-----------------Simulationsstart-----------------\n')

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

    # gemittelte Entzugsleistung [W]
    h_interv = 24                                   # Zeitintervall der gemittelten Entzugsleistung [h]

    Q_m = np.zeros(Nt)
    for i in range(0, Nt, h_interv):
        Q_interv = [x for x in Q[i:(i+h_interv)]]
        Q_m[i:(i+h_interv)] = np.mean(Q_interv)

    # Gesamtenergiemenge [MWh]
    E = (np.sum(Q) / len(Q)) * Nt * 1e-6
    print(80*'-')
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
    # 8.) Plot
    # -------------------------------------------------------------------------

    # x-Achse aller Plots (Simulationsstunden) [h]
    hours = np.array([(j+1)*dt/3600. for j in range(Nt)])

    # -------------------------------------------------------------------------
    # 8.1) Figure 1 (Plots für End-User)
    # -------------------------------------------------------------------------
 
    plt.rc('figure')
    fig1 = plt.figure()
 
    font = {'weight': 'bold', 'size': 14}
    plt.rc('font', **font)
 
    # Lastprofil {Entzugsleistung - Entzugsleistung (24h-gemittelt) - Verluste (Anbindung + Unterseite Heizelement)}
    ax1 = fig1.add_subplot(311)
    ax1.set_ylabel(r'$q$ [W/m2]')
    ax1.plot(hours, Q / A_he, 'k-', lw=1.2)
    ax1.plot(hours, Q_m / A_he, 'r--', lw=1.2)
    ax1.plot(hours, Q_V / A_he, 'g-', lw=1.2)
    ax1.legend(['Entzugsleistung', 'Entzugsleistung-24h-gemittelt',
                'Verluste (Anbindung + Unterseite Heizelement)'],
               prop={'size': font['size'] - 5}, loc='upper left')
    ax1.grid('major')
 
    # Schneefallrate - Schneehöhe - Umgebungstemperatur - Windgeschwindigkeit
    ax2 = fig1.add_subplot(312)
    ax2_2 = ax2.twinx()
    ax2.set_ylabel('Schneefallrate [mm/h] \n Schneehöhe [mm]')
    ax2_2.set_ylabel('$T$ [degC] \n Windgeschwindigkeit [m/s]')
    ax2.plot(hours, S_w, 'b-', lw=0.8)
    ax2.plot(hours, m_Rs / A_he, 'g-', lw=0.8)
    ax2_2.plot(hours, Theta_inf, 'k-', lw=0.8)
    ax2_2.plot(hours, u_inf, 'm--', lw=0.8)
    ax2.legend(['Schneefallrate', 'Schneehöhe'],
               prop={'size': font['size'] - 5}, loc='upper left')
    ax2_2.legend(['Umgebungstemperatur', 'Windgeschwindigkeit'],
                 prop={'size': font['size'] - 5}, loc='upper right')
    ax2.grid('major')
 
    # Temperaturverläufe Bohrlochrand und Oberfläche Heizelement
    ax3 = fig1.add_subplot(313)
    ax3.set_xlabel(r'$t$ [h]')
    ax3.set_ylabel(r'$T$ [degC]')
    ax3.plot(hours, Theta_b, 'r-', lw=1.2)
    ax3.plot(hours, Theta_surf, 'c-', lw=0.6)
    ax3.legend(['T_Bohrlochrand', 'T_Oberflaeche'],
               prop={'size': font['size'] - 5}, loc='upper right')
    ax3.grid('major')
 
    # -------------------------------------------------------------------------
    # 8.2) Figure 2 (zusätzliche Plots)
    # -------------------------------------------------------------------------
 
    plt.rc('figure')
    fig2 = plt.figure()
 
    font = {'weight': 'bold', 'size': 14}
    plt.rc('font', **font)
 
    # Darstellungen Simulationsmodus
    ax4 = fig2.add_subplot(311)
    ax4.plot(hours, start_sb_counter, 'k--', lw=1.5)
    ax4.plot(hours, sb_active, 'g-', lw=1.3)
    ax4.plot(hours, sim_mod, 'y-', lw=1.3)
    ax4.plot(hours, sim_mod, 'y-', lw=1.3)    
    ax4.legend(['sb_active', 'sim_mod'],
               prop={'size': font['size'] - 5}, loc='upper right')
    ax4.grid('major')
    
    # Wasser- und Schneebilanzlinie (Wasserequivalent)
    ax5 = fig2.add_subplot(312)
    ax5.set_ylabel('[mm]')
    ax5.plot(hours, m_Rw / A_he, 'b-', lw=0.8)
    ax5.plot(hours, m_Rs / A_he, 'g-', lw=0.8)
    ax5.legend(['Wasserhoehe', 'Schneehoehe'],
               prop={'size': font['size'] - 5}, loc='upper left')
    ax5.grid('major')
 
    # Temperaturverläufe Bohrlochrand und Oberfläche Heizelement
    ax6 = fig2.add_subplot(313)
    ax6.set_xlabel(r'$t$ [h]')
    ax6.set_ylabel(r'$T$ [degC]')
    ax6.plot(hours, Theta_b, 'r-', lw=1.2)
    ax6.plot(hours, Theta_surf, 'c-', lw=0.6)
    ax6.legend(['T_Bohrlochrand', 'T_Oberflaeche'],
               prop={'size': font['size'] - 5}, loc='upper right')
    ax6.grid('major')
 
    # Beschriftung Achsenwerte
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
    ax6.xaxis.set_minor_locator(AutoMinorLocator())
    ax6.yaxis.set_minor_locator(AutoMinorLocator())
 
    # plt.tight_layout()
    plt.show()
    
    return


# Main function
if __name__ == '__main__':
    main()
