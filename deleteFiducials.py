"""
Delete fiducials: deletes all fiducials on the current slice, or all slices in the image.
Last tested on Python 3.8, PyJAMAS 2020.8.3
"""

from pyjamas.rplugins.base import PJSPluginABC
from pyjamas.pjscore import PyJAMAS
from PyQt5 import QtWidgets

class PJSPlugin(PJSPluginABC):
    def name(self) -> str:
        return "Delete fiducials"

    def run(self, parameters: dict) -> bool:
        ret = QtWidgets.QMessageBox.question(None,'', "Do you want to delete all fiducials on all slices (yes to all), or just the current slice (yes)? ", QtWidgets.QMessageBox.YesToAll | QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)

        if ret == QtWidgets.QMessageBox.Cancel:
            return False

        elif ret == QtWidgets.QMessageBox.YesToAll:
            self.pjs.fiducials = [[] for i in range(self.pjs.n_frames)]
        else:
            self.pjs.fiducials[self.pjs.curslice] = []

        self.pjs.repaint()
        
        return True
