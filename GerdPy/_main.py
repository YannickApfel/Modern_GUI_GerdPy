# -*- coding: utf-8 -*-
""" GERDPy - Main-File
    Steuerungsfile des Auslegungstools für GERDI

    Autor: Yannick Apfel

    todos:
        - GUI für End-User
        - Kontrollstruktur für Sondenfeld (Einträge leer / falscher Datentyp)
"""
import sys
import matplotlib.pyplot as plt
import time as tim
import numpy as np
from matplotlib.ticker import AutoMinorLocator
from scipy.constants import pi

# import GERDPy-modules
import GerdPy.boreholes as boreholes
import GerdPy.heatpipes as heatpipes
import GerdPy.heating_element as heating_element
import GerdPy.gfunction as gfunction
import GerdPy.load_aggregation as load_aggregation
from .load_generator_synthetic import synthetic_load
from .load_generator import *
from .weather_data import *
from .geometrycheck import check_geometry
from .R_th_tot import R_th_tot


def main(self):
    # -------------------------------------------------------------------------
    # 1.) Parametrierung der Simulation (Geometrien, Stoffwerte, etc.)
    # -------------------------------------------------------------------------
    self.ui.text_console.insertPlainText(50 * '-' + '\n')
    self.ui.text_console.insertPlainText('Initializing simulation...\n')
    self.ui.text_console.insertPlainText(50 * '-' + '\n')
    # 1.0) Standort
    h_NHN = self.ui.sb_h_NHN.value()    # Höhe über Normal-Null des Standorts (default: 520)

    # 1.1) Erdboden
    a = self.ui.sb_therm_diffu.value()*1.0e-6   # Temperaturleitfähigkeit [m2/s] (default: 1)
    lambda_g = self.ui.sb_therm_cond.value()    # Wärmeleitfähigkeit [W/mK] (default: 2.0)
    T_g = self.ui.sb_undis_soil_temp.value()    # ungestörte Bodentemperatur [degC] (default: 10.0)

    # 1.2) Erdwärmesondenfeld

    # Geometrie-Import (.txt-Datei)
    boreField = boreholes.field_from_file(self.ui.line_borefield_file.text())     # './data/custom_field.txt'

    # Sondenmeter (gesamt)
    H_field = boreholes.length_field(boreField)

    # Layout-Plot des Erdwärmesondenfelds
    fig = boreholes.visualize_field(boreField)

    # 1.3) Bohrloch

    # Geometrie
    N = self.ui.sb_number_heatpipes.value()     # Anzahl Heatpipes pro Bohrloch [-] (default: 6)
    r_b = self.ui.sb_r_borehole.value()         # Radius der Erdwärmesondenbohrung [m] # boreField[0].r_b
    r_w = self.ui.sb_radius_w.value()           # Radius der Wärmerohr-Mittelpunkte [m] (default: 0.12)
    r_pa = self.ui.sb_radius_pa.value()         # Außenradius der Isolationsschicht [m] (default: 0.016)
    r_iso = self.ui.sb_radius_iso.value()       # Innenradius der Isolationsschicht [m] (default: 0.016)
    r_pi = self.ui.sb_radius_pi.value()         # Innenradius des Wärmerohrs [m] (default: 0.015)

    # Wärmeleitfähigkeiten
    lambda_b = self.ui.sb_lambda_b.value()        # lambda der Hinterfüllung [W/mK] (default: 2)
    lambda_iso = self.ui.sb_lambda_iso.value()    # lambda der Isolationsschicht [W/mK] (default: 0.3)
    lambda_p = self.ui.sb_lambda_p.value()        # lambda der Heatpipe [W/mK] (default: 14.0)

    # Geometrie-Erstellung
    hp = heatpipes.Heatpipes(N, r_b, r_w, r_pa, r_iso, r_pi, lambda_b,
                             lambda_iso, lambda_p)
    # Layout-Plot der Wärmerohrkonfiguration
    hp.visualize_hp_config()

    # 1.4) Heizelement

    # Fläche Heizelement [m2]
    A_he = self.ui.sb_A_he.value()      # (default: 35)

    # minimaler Oberflächenabstand [mm]
    x_min = self.ui.sb_x_min.value()    # (default: 25)

    # Wärmeleitfähigkeit des Betonelements [W/mk]
    lambda_Bet = 2.3

    # Geometrie-Erstellung
    he = heating_element.HeatingElement(A_he, x_min, lambda_Bet)

    # 2.) Simulation

    # Simulationsparameter
    dt = 3600.                           # Zeitschrittweite [s]
    tmax = self.ui.sb_years.value() * 365 * 86400      # 0.25 * 1 * (8760./12) * 3600.    # Gesamt-Simulationsdauer [s]
    # tmax = 100 * 3600.
    Nt = int(np.ceil(tmax/dt))           # Anzahl Zeitschritte [-]

    # -------------------------------------------------------------------------
    # 2.) Überprüfung der geometrischen Verträglichkeit (Sonden & Heatpipes)
    # -------------------------------------------------------------------------

    if check_geometry(boreField, hp, self):
        self.ui.text_console.insertPlainText(50 * '-' + '\n')
        self.ui.text_console.insertPlainText('Geometry-Check: not OK! - Simulation aborted\n')
        self.ui.text_console.insertPlainText(50 * '-' + '\n')
        sys.exit()
    else:
        self.ui.text_console.insertPlainText(50 * '-' + '\n')
        self.ui.text_console.insertPlainText('Geometry-Check: OK!\n')
        self.ui.text_console.insertPlainText(50 * '-' + '\n')

    # -------------------------------------------------------------------------
    # 3.) Ermittlung thermischer Widerstand Bohrlochrand bis Oberfläche
    # -------------------------------------------------------------------------

    R_th = R_th_tot(lambda_g, boreField, hp, he)

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

    # Generierung der Wetterdaten-Vektoren
    u_inf = load_u_inf(Nt)      # Windgeschwindigkeit [m/s]
    T_inf = load_T_inf(Nt)      # Umgebungstemperatur [°C]
    S_w = load_S_w(Nt)          # Schneefallrate (Wasserequivalent) [mm/s]
    B = load_B(Nt) / 8          # Bewölkungsgrad [octal units]
    Phi = load_Phi(Nt)          # rel Luftfeuchte [%]

    # -------------------------------------------------------------------------
    # 6.) Iterationsschleife (Simulation mit Nt Zeitschritten der Länge dt)
    # -------------------------------------------------------------------------

    time = 0.
    i = -1

    # Initialisierung Temperaturvektoren (ein Eintrag pro Zeitschritt)
    T_b = np.zeros(Nt)      # Bohrlochrand
    T_surf = np.zeros(Nt)   # Oberfläche Heizelement

    Q = np.zeros(Nt)

    self.ui.text_console.insertPlainText('Simulating...\n')

    while time < tmax:  # Iterationsschleife (ein Durchlauf pro Zeitschritt)

        # Zeitschritt um 1 inkrementieren
        time += dt
        i += 1
        LoadAgg.next_time_step(time)

        # Q[i] = synthetic_load(time/3600.)

        # Ermittlung der Entzugsleistung
        if i == 0:  # Annahme T_b = T_surf = T_g für ersten Zeitschritt
            Q[i], net_neg, T_surf[i] = load(h_NHN, u_inf[i], T_inf[i], S_w[i], A_he, T_g, R_th, T_g, B[i], Phi[i])

        if i > 0:  # alle weiteren Zeitschritte (ermittelte Bodentemperatur)
            Q[i], net_neg, T_surf[i] = load(h_NHN, u_inf[i], T_inf[i], S_w[i], A_he, T_b[i-1], R_th, T_surf[i-1], B[i], Phi[i])

        # Aufprägung der ermittelten Entzugsleistung mit 'load_aggregation.py'
        LoadAgg.set_current_load(Q[i]/H_field)

        # Temperatur am Bohrlochrand
        deltaT_b = LoadAgg.temporal_superposition()
        T_b[i] = T_g - deltaT_b

        # Temperatur an der Oberfläche des Heizelements
        if net_neg == False:
            T_surf[i] = T_b[i] - Q[i] * R_th

    # -------------------------------------------------------------------------
    # 7.) Plots
    # -------------------------------------------------------------------------

    # Zeitstempel (Simulationsdauer)
    toc = tim.time()

    self.ui.text_console.insertPlainText('Total simulation time: {} sec'.format(toc - tic) + '\n')

    plt.rc('figure')
    fig = plt.figure()

    font = {'weight': 'bold', 'size': 22}
    plt.rc('font', **font)

    # Lastprofil (thermische Leistung Q. über die Simulationsdauer)
    ax1 = fig.add_subplot(211)
    ax1.set_xlabel(r'$t$ (hours)')
    ax1.set_ylabel(r'$Q$ (W)')
    hours = np.array([(j+1)*dt/3600. for j in range(Nt)])
    ax1.plot(hours, Q, 'b-', lw=1.5)  # plot
    ax1.legend(['Entzugsleistung [W]'],
               prop={'size': font['size'] - 5}, loc='upper right')

    # Temperaturverläufe
    ax2 = fig.add_subplot(212)
    ax2.set_xlabel(r'$t$ (hours)')
    ax2.set_ylabel(r'$T_b$ (degC)')
    # plots
    ax2.plot(hours, T_b, 'r-', lw=2.0)
    ax2.plot(hours, T_surf, 'c-', lw=1.0)
    ax2.legend(['T_Bohrlochrand [°C]', 'T_Heizelement [°C]'],
               prop={'size': font['size'] - 5}, loc='upper right')

    # Beschriftung Achsenwerte
    ax1.xaxis.set_minor_locator(AutoMinorLocator())
    ax1.yaxis.set_minor_locator(AutoMinorLocator())
    ax2.xaxis.set_minor_locator(AutoMinorLocator())
    ax2.yaxis.set_minor_locator(AutoMinorLocator())
    # Fenstergröße anpassen
    # plt.tight_layout()

    return fig


# Main function
if __name__ == '__main__':
    main()
