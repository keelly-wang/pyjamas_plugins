from pyjamas.rplugins.base import PJSPluginABC
from pyjamas.pjscore import PyJAMAS

class PJSPlugin(PJSPluginABC):
    def name(self) -> str:
        return "Delete all fiducials"

    def run(self, parameters: dict) -> bool:
        self.pjs.fiducials = [[] for i in range(self.pjs.n_frames)]
        self.pjs.repaint()
        
        return True
