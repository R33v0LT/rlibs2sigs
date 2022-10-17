import cutter
import libs2sigs
import re

from PySide2.QtCore import QObject, SIGNAL
from PySide2.QtWidgets import QAction


class DockWidget(cutter.CutterDockWidget):
    def __init__(self, parent, action):
        super(DockWidget, self).__init__(parent, action)
        QObject.connect(cutter.core(), SIGNAL(
            "seekChanged(RVA)"), self.update_contents)

    def update_contents(self):
        pattern = re.compile(r'([\w\d\-_]+)-(\d\.\d\.\d)')
        libs = set(re.findall(pattern, cutter.cmd('izQ')))

        libs2sigs.rlib_to_sig(libs, 'rizin')


class GetRlibsPlugin(cutter.CutterPlugin):
    name = "Rlibs2Sigs Plugin"
    description = "This plugin creates signatures for binary's rust libs"
    version = "1.0"
    author = "R3v0LT"

    def setupPlugin(self):
        pass

    def setupInterface(self, main):
        action = QAction("My Plugin", main)
        action.setCheckable(True)
        widget = DockWidget(main, action)
        main.addPluginDockWidget(widget, action)

    def terminate(self):
        pass


def create_cutter_plugin():
    return GetRlibsPlugin()
