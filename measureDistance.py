"""
Measure distance between fiducials: Exports the distance between the first two fiducials on each slice to a CSV file. Set orientation to None for euclidean distance, 0 for difference in x coordinates only, 1 for y coordinates.
Last tested on Python 3.8, PyJAMAS 2020.8.3
"""
from pyjamas.rplugins.base import PJSPluginABC
from PyQt5 import QtCore, QtWidgets, QtGui

import os
import pandas as pd
import numpy as np

class PJSPlugin(PJSPluginABC):
    def name(self) -> str:
        return "Measure distance between fiducials"

    def run(self, parameters: dict):
        print(__doc__)
        
        orientation = None #None for Euclidean distance, 0 for x, 1 for y

        affix, ok = QtWidgets.QInputDialog().getText(None, "QInputDialog().getText()",
                                            "Row name affix:", QtWidgets.QLineEdit.Normal)
        if not ok:
            return False

        columns: int = self.pjs.n_frames
        slices = np.arange(0, self.pjs.n_frames)
        row_names = ['loc1_' + affix, 'loc2_' + affix, 'distance_' + affix]
        rows: int = 3
        measurement: pd.DataFrame = pd.DataFrame(np.nan * np.zeros((rows, columns)), columns=slices+1, index=row_names) 

        for i in range(self.pjs.n_frames):
            first, second = self.pjs.fiducials[i][0], self.pjs.fiducials[i][1]

            if len(self.pjs.fiducials[i]) > 1:
                if orientation is None:
                    measurement.loc['loc1_' + affix, i + 1] = str(first[0]) + "," + str(first[1])
                    measurement.loc['loc2_' + affix, i + 1] = str(second[0]) + "," + str(second[1])  
                    measurement.loc['distance_' + affix, i + 1] = ((first[0] - second[0])**2 + (first[1] - second[1])**2)**0.5         
                else:
                    maxes = [first[orientation], second[orientation]]
                    measurement.loc['loc1_' + affix, i + 1] = min(maxes)
                    measurement.loc['loc2_' + affix, i + 1] = max(maxes)
                    measurement.loc['distance_' + affix, i + 1] = abs(maxes[0] - maxes[1])

        fname: tuple = QtWidgets.QFileDialog.getSaveFileName(None, 'Save height measurements...', self.pjs.cwd,
                                                             filter='CSV (*.csv)')
        if fname[0] == "":
            return False

        measurement.to_csv(fname[0]) 

        
        
        
            