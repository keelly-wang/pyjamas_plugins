from pyjamas.rplugins.base import PJSPluginABC
from PyQt5 import QtCore, QtWidgets, QtGui

import os
import pandas as pd
import numpy as np

class PJSPlugin(PJSPluginABC):
    def name(self) -> str:
        return "Measure height"

    def run(self, parameters: dict):
        prefix, ok = QtWidgets.QInputDialog().getText(None, "QInputDialog().getText()",
                                            "Prefix:", QtWidgets.QLineEdit.Normal)
        if not ok:
            return False

        row_names = ['max1_' + prefix, 'max2_' + prefix, 'height_' + prefix]

        if self.pjs.width > self.pjs.height:
            orientation = 1
        else:
            orientation = 0

        rows: int = 3
        columns: int = self.pjs.n_frames
        slices = np.arange(0, self.pjs.n_frames)
        measurement: pd.DataFrame = pd.DataFrame(np.nan * np.zeros((rows, columns)), columns=slices+1, index=row_names) 

        for i in range(self.pjs.n_frames): #for every slice
            if len(self.pjs.fiducials[i]) > 1:
                maxes = [self.pjs.fiducials[i][0][orientation], self.pjs.fiducials[i][1][orientation]]
                
                measurement.loc['max1_' + prefix, i + 1] = min(maxes)
                measurement.loc['max2_' + prefix, i + 1] = max(maxes)
                measurement.loc['height_' + prefix, i + 1] = abs(maxes[0] - maxes[1])

        fname: tuple = QtWidgets.QFileDialog.getSaveFileName(None, 'Save height measurements ...', self.pjs.cwd,
                                                             filter='CSV (*.csv)')
        if fname[0] == "":
            return False

        measurement.to_csv(fname[0]) 

        
        
        
            