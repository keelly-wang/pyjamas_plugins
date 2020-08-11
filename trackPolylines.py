"""
Track polylines: select polylines from the current timepoint and track them through the indicated time range using local cross-correlation flow. Each set of tracked polylines is saved as a separate annotation file in the indicated output folder.
"""
from pyjamas.rplugins.base import PJSPluginABC
from PyQt5 import QtCore, QtWidgets, QtGui
import pyjamas.rannotations.rpolyline as rpolyline
from pyjamas.rutils import RUtils
from pyjamas.rimage.rimutils import rimutils
import numpy as np
import os

class PJSPlugin(PJSPluginABC):
    def name(self) -> str:
        return "Track polylines"

    def run(self, parameters: dict) -> bool:
        print(__doc__)

        if len(self.pjs.polylines[self.pjs.curslice]) == 0:
            return False

        dialog = QtWidgets.QDialog()
        self.setupUI(dialog)
        dialog.exec()

        # If the dialog was closed by pressing OK, then run the measurements.
        if dialog.result() == QtWidgets.QDialog.Accepted:
            startIDs = self.processIDs(self.startPolylines.text()) # get IDs of polylines you want to track,
            if startIDs is None:
                print("Invalid polyline ID input")
                return False

            forwardslices = np.arange(self.pjs.curslice, self.lastSlice.value()) # and the slices you want to track them through
            backwardslices = np.arange(self.pjs.curslice, self.firstSlice.value() - 2, step = -1)
            print(forwardslices)
            print(backwardslices)

            self.newpolylines = [[] for frame in range(self.pjs.n_frames)] # create new array for storing polylines
            self.newpolylines[forwardslices[0]] = [self.pjs.polylines[forwardslices[0]][polyID] for polyID in startIDs] #copy starting polylines to new array
            self.trackPolylineXCorr(forwardslices)
            self.trackPolylineXCorr(backwardslices)

            self.savePolylines(startIDs)

            dialog.close()
            return True

        dialog.close()
        return False
        
    def setupUI(self, dialog):
        dialog.setObjectName("dialog")
        dialog.resize(300, 260)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(dialog.sizePolicy().hasHeightForWidth())
        dialog.setSizePolicy(sizePolicy)
        dialog.setWindowTitle("Track polyline")

        self.buttonBox = QtWidgets.QDialogButtonBox(dialog)
        self.buttonBox.setGeometry(QtCore.QRect(0, 210, 300, 32))
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")

        self.groupBox = QtWidgets.QGroupBox(dialog)
        self.groupBox.setGeometry(QtCore.QRect(20, 20, 260, 150))
        self.groupBox.setObjectName("groupBox")
        self.groupBox.setTitle("Parameters")

        self.startPolylines = QtWidgets.QLineEdit(dialog)
        self.startPolylines.setGeometry(QtCore.QRect(115, 45, 130, 24))

        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setGeometry(QtCore.QRect(31, 25, 56, 24))
        self.label.setObjectName("label")
        self.label.setText("Polyline IDs (leave blank to track all polylines)")

        self.firstSlice = QtWidgets.QSpinBox(self.groupBox)
        self.firstSlice.setGeometry(QtCore.QRect(95, 60, 48, 24))
        self.firstSlice.setMaximum(self.pjs.n_frames)
        self.firstSlice.setMinimum(1)

        self.firstSlice.setValue(self.pjs.curslice + 1)
        self.firstSlice.setObjectName("firstSlice")

        self.label2 = QtWidgets.QLabel(self.groupBox)
        self.label2.setGeometry(QtCore.QRect(31, 60, 56, 24))
        self.label2.setObjectName("label2")
        self.label2.setText("First slice")

        self.lastSlice = QtWidgets.QSpinBox(self.groupBox)
        self.lastSlice.setGeometry(QtCore.QRect(95, 95, 48, 24))
        self.lastSlice.setMaximum(self.pjs.n_frames)
        self.lastSlice.setMinimum(1)

        self.lastSlice.setValue(self.pjs.curslice + 1)
        self.lastSlice.setObjectName("LastSlice")

        self.label3 = QtWidgets.QLabel(self.groupBox)
        self.label3.setGeometry(QtCore.QRect(31, 95, 56, 24))
        self.label3.setObjectName("label3")
        self.label3.setText("last slice")

        self.buttonBox.rejected.connect(dialog.reject)
        self.buttonBox.accepted.connect(dialog.accept)
        QtCore.QMetaObject.connectSlotsByName(dialog)

    def processIDs(self, inputtext):
        if inputtext == "" or inputtext.casefold() == "all":
            IDs = [i for i in range(len(self.pjs.polylines[self.pjs.curslice]))]
            return IDs

        try: #segmenting input such as "2-4, 6"
            IDs = []
            segments = inputtext.split(",")

            for segment in segments:
                numbers = segment.split("-")
                if len(numbers) == 1:
                    IDs.append(int(numbers[0].strip()) - 1)
                elif len(numbers) == 2:
                    IDs.extend([i for i in range(int(numbers[0].strip()) - 1, int(numbers[1].strip()))])
                else:
                    return None
            
            IDs = list(set(IDs)) #removes all duplicates
            for polyid in IDs:
                if polyid >= len(self.pjs.polylines[self.pjs.curslice]): #removes IDs that are out of range
                    IDs.remove(polyid)
                    print("polyline ID " + str(polyid) + " out of range")
            
            return IDs

        except Exception:
            return None

    def trackPolylineXCorr(self, theslices):
        duplicatedPoly = [False for poly in self.newpolylines[theslices[0]]]

        for i in range(0, len(theslices)-1):
            curcentroids = np.array([RUtils.qpolygonf2polygon(poly).centroid.coords[0] for poly in self.newpolylines[theslices[i]]]) #get the centroids of current slice polygons

            Xflow, Yflow, _, _ = rimutils.flow(self.pjs.slices[theslices[i]], #propagate these centroids to next slice to find "ideal centroids"
                                               self.pjs.slices[theslices[i+1]],
                                               curcentroids, window_sz=64)
            curcentroids[:, 0] += Xflow 
            curcentroids[:, 1] += Yflow

            for j in range(len(curcentroids)): #for each "ideal centroid"
                thecentroid = QtCore.QPointF(curcentroids[j][0], curcentroids[j][1]) #get the "ideal centroid" and matching polyline
                curpoly = self.newpolylines[theslices[i]][j]

                if duplicatedPoly[j]: #if the matching polyline was duplicated from previous slice, clear it
                    self.newpolylines[theslices[i]][j] = []

                nextpoly = None
                minarea = float("inf")

                for thepoly in self.pjs.polylines[theslices[i+1]]: #iterate through next slice's polys and find the smallest one that encloses the ideal centroid
                    if thepoly.containsPoint(thecentroid, 0):
                        curarea = rpolyline.RPolyline(thepoly).area()
                        if curarea < minarea:
                            nextpoly = thepoly
                            minarea = curarea

                if nextpoly is None or minarea / rpolyline.RPolyline(curpoly).area() > 2 or minarea / rpolyline.RPolyline(curpoly).area() < 0.5:
                    #there is no enclosing poly, or enclosing poly is clearly incorrectly segmented (much larger or smaller than the current poly)
                    self.newpolylines[theslices[i+1]].append(curpoly) #duplicate current poly to next slice for tracking
                    duplicatedPoly[j] = True #but remember to delete the duplicated poly

                else:
                    self.newpolylines[theslices[i+1]].append(nextpoly) #add enclosing poly to next slice
                    duplicatedPoly[j] = False
        
        for j in range(len(curcentroids)): #handling duplicated polys for the last slice
            if duplicatedPoly[j]:
                self.newpolylines[theslices[-1]][j] = []

    def savePolylines(self, startIDs):
        folder_name = QtWidgets.QFileDialog.getExistingDirectory(None, 'Export files to folder ...', self.pjs.cwd) #get save folder
        if folder_name == "":
            return False
        folder_name = os.path.abspath(folder_name)

        for i in range(len(startIDs)): #save each polyline as a separate file
            polyID = startIDs[i]
            savepolylines = [[] for frame in range(self.pjs.n_frames)]
            polylines = [[self.newpolylines[frame][i]] if self.newpolylines[frame][i] != [] else [] for frame in range(self.firstSlice.value() - 1, self.lastSlice.value())]
            savepolylines[self.firstSlice.value() - 1 : self.lastSlice.value()] = polylines
            
            filepath = os.path.join(folder_name, "poly_" + str(polyID) + ".pjs")
            self.pjs.io.cbSaveAnnotations(filepath, savepolylines, [[] for i in range(self.pjs.n_frames)])

    def dist(self, point1, point2):
        return (point1.x - point2.x)**2 + (point1.y - point2.y)**2