# Details

# Instructions: to run, navigate to execute_tool.py and run the file

from PySide6.QtCore import * 
from PySide6.QtGui import *
from PySide6.QtUiTools import *
from PySide6.QtWidgets import *
from functools import partial
import maya.cmds as cmds
from maya import OpenMayaUI
from pathlib import Path
from shiboken6 import wrapInstance
from functools import wraps
from PySide6 import QtWidgets

class TextureFolderDialog(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Apply Textures")
        self.resize(463, 100)

        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_widgets(self):

        # Texture folder section
        self.label = QtWidgets.QLabel("Select Texture Folder:")

        self.filename_label = QtWidgets.QLabel("")
        self.select_button = QtWidgets.QPushButton("Select Folder")

        # Warning message
        self.warnings = QtWidgets.QLabel("")

        # Apply button
        self.apply_button = QtWidgets.QPushButton("Apply")

    def create_layouts(self):

        # Vertical layout containing:
        # Select Texture Folder
        # Filename
        texture_info_layout = QtWidgets.QVBoxLayout()
        texture_info_layout.addWidget(self.label)
        texture_info_layout.addWidget(self.filename_label)

        # Main grid
        grid_layout = QtWidgets.QGridLayout()

        grid_layout.addLayout(
            texture_info_layout,
            0, 0
        )

        grid_layout.addWidget(
            self.select_button,
            0, 1
        )

        grid_layout.addWidget(
            self.warnings,
            1, 0
        )

        # Main dialog layout
        main_layout = QtWidgets.QVBoxLayout(self)

        main_layout.addLayout(grid_layout)
        main_layout.addWidget(self.apply_button)

    def create_connections(self):

        self.select_button.clicked.connect(self.select_folder)
        self.apply_button.clicked.connect(self.apply)

    def select_folder(self):

        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Texture Folder"
        )

        if folder:
            self.filename_label.setText(folder)

    def apply(self):
        selectedObject = self.getSelectedObjects()
        print(selectedObject)

    # =========================== APPLY LOGIC ===========================

    # Set object/group to be textuerd
    def getSelectedObjects(self):
        selected_objects = cmds.ls(selection=True)
        if len(selected_objects) == 0:
            self.warnings.setText("Must select an object or group of objects")
        else:
            self.warnings.setText("")
            return selected_objects[0]


def show():
    global texture_folder_dialog

    try:
        texture_folder_dialog.close()
        texture_folder_dialog.deleteLater()
    except:
        pass

    texture_folder_dialog = TextureFolderDialog()
    texture_folder_dialog.show()

if __name__ == "__main__":
    show()
