# Mantid Repository : https://github.com/mantidproject/mantid
#
# Copyright &copy; 2017 ISIS Rutherford Appleton Laboratory UKRI,
#     NScD Oak Ridge National Laboratory, European Spallation Source
#     & Institut Laue - Langevin
# SPDX - License - Identifier: GPL - 3.0 +
#    This file is part of the mantid workbench.
#
#
from __future__ import (absolute_import, unicode_literals)

# system imports

# third-party library imports
from mantidqt.widgets.algorithmselector import AlgorithmSelectorWidget
from qtpy.QtWidgets import QVBoxLayout

# local package imports
from workbench.plugins.base import PluginWidget
# from mantidqt.utils.qt import toQSettings when readSettings/writeSettings are implemented


class AlgorithmSelector(PluginWidget):
    """Provides an algorithm selector widget for selecting algorithms to run"""

    def __init__(self, parent):
        super(AlgorithmSelector, self).__init__(parent)

        # layout
        self.algorithm_selector = AlgorithmSelectorWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.algorithm_selector)
        self.setLayout(layout)

    def refresh(self):
        """Refreshes the algorithm list"""
        self.algorithm_selector.refresh()

# ----------------- Plugin API --------------------

    def register_plugin(self):
        self.main.add_dockwidget(self)

    def get_plugin_title(self):
        return "Algorithms"

    def readSettings(self, _):
        pass

    def writeSettings(self, _):
        pass
