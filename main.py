# ///////////////////////////////////////////////////////////////
#
# BY: WANDERSON M.PIMENTA
# PROJECT MADE WITH: Qt Designer and PySide6
# V: 1.0.0
#
# This project can be used freely for all uses, as long as they maintain the
# respective credits only in the Python scripts, any information in the visual
# interface (GUI) can be modified without any implication.
#
# There are limitations on Qt licenses if you want to use your products
# commercially, I recommend reading them on the official website:
# https://doc.qt.io/qtforpython/licenses.html
#
# ///////////////////////////////////////////////////////////////

import sys
import os
import platform

# IMPORT / GUI AND MODULES AND WIDGETS
# ///////////////////////////////////////////////////////////////

from modules import *
from widgets import *
os.environ["QT_FONT_DPI"] = "96" # FIX Problem for High DPI and Scale above 100%

# SET AS GLOBAL WIDGETS
# ///////////////////////////////////////////////////////////////
widgets = None

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        # SET AS GLOBAL WIDGETS
        # ///////////////////////////////////////////////////////////////
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        global widgets
        widgets = self.ui

        # USE CUSTOM TITLE BAR | USE AS "False" FOR MAC OR LINUX
        # ///////////////////////////////////////////////////////////////
        Settings.ENABLE_CUSTOM_TITLE_BAR = True

        # APP NAME
        # ///////////////////////////////////////////////////////////////
        title = "GerdPy"
        description = "GerdPy - Simulation tool for dimensioning heatpipe systems"
        # APPLY TEXTS
        self.setWindowTitle(title)
        widgets.titleRightInfo.setText(description)

        # TOGGLE MENU
        # ///////////////////////////////////////////////////////////////
        widgets.toggleButton.clicked.connect(lambda: UIFunctions.toggleMenu(self, True))

        # SET UI DEFINITIONS
        # ///////////////////////////////////////////////////////////////
        UIFunctions.uiDefinitions(self)

        # QTableWidget PARAMETERS
        # ///////////////////////////////////////////////////////////////
        widgets.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # DROPDOWN MONTHS
        widgets.cb_month.addItem("January", 1)
        widgets.cb_month.addItem("February", 2)
        widgets.cb_month.addItem("March", 3)
        widgets.cb_month.addItem("April", 4)
        widgets.cb_month.addItem("May", 5)
        widgets.cb_month.addItem("June", 6)
        widgets.cb_month.addItem("July", 7)
        widgets.cb_month.addItem("August", 8)
        widgets.cb_month.addItem("September", 9)
        widgets.cb_month.addItem("October", 10)
        widgets.cb_month.addItem("November", 11)
        widgets.cb_month.addItem("December", 12)

        # DROPDOWN PAVEMENT
        widgets.cb_pavement.addItem("Concrete")
        widgets.cb_pavement.addItem("Tarmac")

        # BUTTONS CLICK
        # ///////////////////////////////////////////////////////////////

        # LEFT MENUS
        widgets.btn_home.clicked.connect(self.buttonClick)
        widgets.btn_weather.clicked.connect(self.buttonClick)
        widgets.btn_borefield.clicked.connect(self.buttonClick)
        widgets.btn_surface.clicked.connect(self.buttonClick)
        widgets.btn_sim.clicked.connect(self.buttonClick)

        # WEATHER SHEET
        widgets.btn_browse_weather.clicked.connect(self.buttonClick)

        # BOREFIELD SHEET
        widgets.btn_browse_borefield.clicked.connect(self.buttonClick)

        # SIMULATION SHEET
        widgets.btn_startsim.clicked.connect(self.buttonClick)

        # SHOW APP
        # ///////////////////////////////////////////////////////////////
        self.show()

        # SET CUSTOM THEME
        # ///////////////////////////////////////////////////////////////
        useCustomTheme = True
        themeFile = "themes\py_dark.qss"

        # SET THEME AND HACKS
        if useCustomTheme:
            # LOAD AND APPLY STYLE
            UIFunctions.theme(self, themeFile, True)

            # SET HACKS
            AppFunctions.setThemeHack(self)

        # SET HOME PAGE AND SELECT MENU
        # ///////////////////////////////////////////////////////////////
        widgets.stackedWidget.setCurrentWidget(widgets.home)
        widgets.btn_home.setStyleSheet(UIFunctions.selectMenu(widgets.btn_home.styleSheet()))


    # BUTTONS CLICK
    # Post here your functions for clicked buttons
    # ///////////////////////////////////////////////////////////////
    def buttonClick(self):
        # GET BUTTON CLICKED
        btn = self.sender()
        btnName = btn.objectName()

        # SHOW HOME PAGE
        if btnName == "btn_home":
            widgets.stackedWidget.setCurrentWidget(widgets.home)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        # SHOW WEATHER PAGE
        if btnName == "btn_weather":
            widgets.stackedWidget.setCurrentWidget(widgets.weather)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        # SHOW GROUND PAGE
        if btnName == "btn_borefield":
           widgets.stackedWidget.setCurrentWidget(widgets.borefield)
           UIFunctions.resetStyle(self, btnName)
           btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        # SHOW SURFACE PAGE
        if btnName == "btn_surface":
           widgets.stackedWidget.setCurrentWidget(widgets.surface)
           UIFunctions.resetStyle(self, btnName)
           btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        # SHOW SIMULATION PAGE
        if btnName == "btn_sim":
           widgets.stackedWidget.setCurrentWidget(widgets.simulation)
           UIFunctions.resetStyle(self, btnName)
           btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        # BROWSE WEATHER DATA
        if btnName == "btn_browse_weather":
            w_file = USEFunctions.fcn_browse(self)
            widgets.line_weather_file.setText(w_file[0])

        # BROWSE BOREFIELD DATA
        if btnName == "btn_browse_borefield":
            b_file = USEFunctions.fcn_browse(self)
            widgets.line_borefield_file.setText(b_file[0])

        if btnName == "btn_save":
            print("Save BTN clicked!")

        # PRINT BTN NAME
        print(f'Button "{btnName}" pressed!')


    # RESIZE EVENTS
    # ///////////////////////////////////////////////////////////////
    def resizeEvent(self, event):
        # Update Size Grips
        UIFunctions.resize_grips(self)

    # MOUSE CLICK EVENTS
    # ///////////////////////////////////////////////////////////////
    def mousePressEvent(self, event):
        # SET DRAG POS WINDOW
        self.dragPos = event.globalPos()

        # PRINT MOUSE EVENTS
        if event.buttons() == Qt.LeftButton:
            print('Mouse click: LEFT CLICK')
        if event.buttons() == Qt.RightButton:
            print('Mouse click: RIGHT CLICK')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))
    window = MainWindow()
    sys.exit(app.exec_())
