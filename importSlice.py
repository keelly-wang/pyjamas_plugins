"""
Import slice: adds all annotations on a given slice in the selected annotation files onto the current slice of the current image. To enable replacement of existing annotations on the current slice, uncomment the commented code. 
"""
from pyjamas.rplugins.base import PJSPluginABC
from PyQt5 import QtCore, QtWidgets, QtGui
import pickle
from pyjamas.rutils import RUtils
import gzip

class PJSPlugin(PJSPluginABC):
    def name(self) -> str:
        return "Import slice"

    def run(self, parameters: dict):
        # Get file name.
        dialog = QtWidgets.QFileDialog(None, "Load annotations ...")
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        dialog.setDirectory(self.pjs.cwd)
        dialog.setNameFilter('PyJAMAS data (*' + '.pjs' + ')')
        dialog.exec()

        filenames = dialog.selectedFiles()
        if filenames == None or filenames == [] or filenames[0] == '':
            return False
                 
        filenames.sort(key=RUtils.natural_sort)
        
        fh = None
        allfiducials = []
        allpolylines = []

        for fname in filenames:
            try:
                fh = gzip.open(fname, "rb")
                curfiducials = pickle.load(fh)
                curpolylines = pickle.load(fh)

                if allfiducials == []:
                    allfiducials = curfiducials
                    allpolylines = curpolylines

                else:                   
                    for i in range(len(allfiducials)):
                        allfiducials[i].extend(curfiducials[i])
                        allpolylines[i].extend(curpolylines[i])

            except (IOError, OSError) as ex:
                if fh is not None:
                    fh.close()
                print(ex)
                return False
        
        framenum, ok = QtWidgets.QInputDialog().getInt(None, "Input slice number",
                                            "slice number (numbering starts at 1):", QtWidgets.QLineEdit.Normal)
        if not ok or framenum < 1 or framenum > len(allpolylines):
            return False
            
        framenum -= 1

        # self.pjs.fiducials[self.pjs.curslice] = []
        # self.pjs.polylines[self.pjs.curslice] = []

        self.pjs.fiducials[self.pjs.curslice].extend(allfiducials[framenum])

        for j, thepolyline in enumerate(allpolylines[framenum]):
            if thepolyline != [[]]:
                self.pjs.polylines[self.pjs.curslice].append(QtGui.QPolygonF())
                for thepoint in thepolyline:
                    self.pjs.polylines[self.pjs.curslice][-1].append(QtCore.QPointF(thepoint[0], thepoint[1]))

        self.pjs.repaint()
        
        return True