# MAIN FILE
# ///////////////////////////////////////////////////////////////
from main import *


class USEFunctions(MainWindow):

    def fcn_browse(self):
        f_name = QFileDialog.getOpenFileName(self, "Open file")
        return f_name

