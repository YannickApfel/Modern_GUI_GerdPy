# MAIN FILE
# ///////////////////////////////////////////////////////////////
from guimain import *
import pandas as pd

# SET AS GLOBAL WIDGETS
# ///////////////////////////////////////////////////////////////
widgets = None

class USEFunctions(MainWindow):

    def fcn_browse(self):
        f_name = QFileDialog.getOpenFileName(self, "Open file")
        return f_name

    def fcn_paras(self):
      # WEATHER- & LOCAL PARAMETERS
      c_path_weather_data = self.line_weather_file.text()
      d_therm_diff = self.sb_therm_diffu.value()
      d_therm_cond = self.sb_therm_cond.value()
      d_undis_soil_temp = self.sb_undis_soil_temp.value()
      h_NHN = self.sb_h_NHN.value()

      # BOREFIELD PARAMETERS
      c_path_borefield_data = self.line_borefield_file.text()
      i_boreholes = self.sb_number_boreholes.value()
      d_thermal_cond_backfill = self.sb_lambda_b.value()
      d_therm_cond_insulating_layer = self.sb_lambda_iso.value()
      d_therm_cond_heatpipe = self.sb_lambda_p.value()
      d_radius_heatpipe = self.sb_radius_w.value()
      d_radius_insulating_layer = self.sb_radius_pa.value()
      d_fillet_insulating_layer = self.sb_radius_iso.value()
      d_fillet_heatpipe = self.sb_radius_pi.value()

      # SURFACE PARAMETERS
      i_surface_area = self.sb_A_he.value()
      i_min_surface_dist = self.sb_x_min.value()
      d_therm_cond_pavement = self.sb_lambda_pavement.value()

      # SIMULATION PARAMETERS
      c_month = self.cb_month.currentText()
      i_day = self.sb_day.value()
      i_years = self.sb_years.value()
      i_dt = self.sb_dt.value()

      print(c_path_weather_data)
      print(d_therm_diff)
      print(d_therm_cond)
      print(d_undis_soil_temp)
      print(h_NHN)
      print(c_path_borefield_data)
      print(i_boreholes)
      print(d_thermal_cond_backfill)
      print(d_therm_cond_insulating_layer)
      print(d_therm_cond_heatpipe)
      print(d_radius_heatpipe)
      print(d_radius_insulating_layer)
      print(d_fillet_insulating_layer)
      print(d_fillet_heatpipe)
      print(i_surface_area)
      print(i_min_surface_dist)
      print(d_therm_cond_pavement)
      print(c_month)
      print(i_day)
      print(i_years)
      print(i_dt)

    def datecheck(self):

      day = self.ui.sb_day.value()
      month = int(self.ui.cb_month.currentData())

      # error handling
      if month == 2 and day > 28:
        print('February only has 28 days maximum.')
        print('Please adjust!')
        self.ui.text_console.insertPlainText('February only has 28 days maximum.\n')
        self.ui.text_console.insertPlainText('Please adjust!\n')
      elif month in [4, 6, 9, 11] and day > 30:
        print(self.ui.cb_month.currentText() + ' only has 30 days maximum!')
        print('Please adjust!')
        self.ui.text_console.insertPlainText(self.ui.cb_month.currentText() + ' only has 30 days maximum.\n')
        self.ui.text_console.insertPlainText('Please adjust!\n')




