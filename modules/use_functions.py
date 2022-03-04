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
    

    def errorhandling(self):

      day = self.ui.sb_day.value()
      month = int(self.ui.cb_month.currentData())

      # error handling
      if month == 2 and day > 28:
        check = False
        print('February only has 28 days maximum.')
        print('Please adjust!')
        self.ui.text_console.insertPlainText('February only has 28 days maximum.\n')
        self.ui.text_console.insertPlainText('Please adjust!\n')
      elif month in [4, 6, 9, 11] and day > 30:
        check = False
        print(self.ui.cb_month.currentText() + ' only has 30 days maximum!')
        print('Please adjust!')
        self.ui.text_console.insertPlainText(self.ui.cb_month.currentText() + ' only has 30 days maximum.\n')
        self.ui.text_console.insertPlainText('Please adjust!\n')
      elif not self.ui.line_weather_file.text():
        check = False
        self.ui.text_console.insertPlainText('Please choose a weather data file.')
      elif not self.ui.line_borefield_file.text():
        check = False
        self.ui.text_console.insertPlainText('Please choose a borefield geometry file.')
      else:
        check = True

      return check




