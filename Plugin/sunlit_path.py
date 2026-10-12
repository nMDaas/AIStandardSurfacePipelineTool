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
import os

class TextureFolderDialog(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Apply Textures")
        self.resize(463, 100)

        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    # =========================== USER INTERFACE ===========================

    def create_widgets(self):

        # Texture folder section
        self.label = QtWidgets.QLabel("Select Texture Folder:")

        self.filename_label = QtWidgets.QLabel("")
        self.select_button = QtWidgets.QPushButton("Select Folder")

        # Warning message
        self.warnings = QtWidgets.QLabel("")
        self.warnings.setStyleSheet("color: red;")

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

        self.folder_path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Texture Folder"
        )

        if self.folder_path:
            self.filename_label.setText(self.folder_path)

    def apply(self):
        selectedObjects = self.getSelectedObjects() # TODO: this can be 1 or many, but assuming 1 for now

        print("Selected Objects: ", selectedObjects)

        if self.folder_path == "":
            self.warnings.setText("Must select a folder path to folder textures")
        else:
            for obj in selectedObjects:
                mat_name = self.createTextures(obj)
                #self.apply_textures(selectedObject, mat_name)

    # =========================== APPLY LOGIC ===========================

    # Set object/group to be textuerd
    def getSelectedObjects(self):
        selected_objects = cmds.ls(selection=True)
        if len(selected_objects) == 0:
            self.warnings.setText("Must select an object or group of objects")
        else:
            self.warnings.setText("")
            return selected_objects

    
    def createTextures(self, objName):
        texture_files = [
            f for f in os.listdir(self.folder_path)
            if os.path.isfile(os.path.join(self.folder_path, f))
            and f.endswith('.png')
            and objName in f
        ]

        print("Object name:", objName)
        print("Matching files:", texture_files)

        texture_groups = {}

        for file in texture_files:
            strTemp = file[-8:]  # texture number + .png
            textureNum = strTemp[:4]

            if textureNum not in texture_groups:
                texture_groups[textureNum] = []

            texture_groups[textureNum].append(file)

        for key, value in texture_groups.items():
            material_name = objName + key

            baseColorFile = None
            normalFile = None
            roughnessFile = None

            for file in value:
                if "BaseColor" in file:
                    baseColorFile = file
                elif "Normal" in file:
                    normalFile = file
                elif "Roughness" in file:
                    roughnessFile = file

            self.cleanNodes(material_name)
            self.createMaterial(
                material_name,
                baseColorFile,
                normalFile,
                roughnessFile,
                key
            )

        return objName
    
    # clean nodes for this texture
    def cleanNodes(self, texture_name):
        # get all nodes in the scene
        all_nodes = cmds.ls()

        # Iterate through each node and delete its construction history
        for node in all_nodes:
            if texture_name in node:
                cmds.delete(node)

        print(f"Cleaning {texture_name}")

    def createMaterial(self, material_name, baseColorFile,normalFile, roughnessFile, textureNum):
            print(f"Creating material: {material_name}")
            
            # Create a new material
            material = cmds.shadingNode('standardSurface', asShader=True, name=material_name)
            
            # Create a shading group
            shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="set")
            cmds.connectAttr(material + '.outColor', shading_group + '.surfaceShader', force=True) # Connect material to shading group

            # Create a file texture node for baseColor
            baseColorNodeName = material_name + "_" + "BaseColor" + "_" + textureNum
            baseColor_file_node = cmds.shadingNode('file', asTexture=True, name=baseColorNodeName)
            baseColorFilePath = baseColorFile
            cmds.setAttr(f"{baseColor_file_node}.fileTextureName", baseColorFilePath, type="string")
            cmds.setAttr(f'{baseColor_file_node}.colorSpace', 'Raw', type='string')

            # Create a place2dTexture node
            place2d_baseColor = cmds.shadingNode('place2dTexture', asUtility=True, name=f'place2dTexture_baseColor_{material}')

            # Create a file texture node for Roughness
            roughnessNodeName = material_name + "_" + "Roughness" + "_" + textureNum
            roughness_file_node = cmds.shadingNode('file', asTexture=True, name=roughnessNodeName)
            roughnessFilePath = roughnessFile
            cmds.setAttr(f"{roughness_file_node}.fileTextureName", roughnessFilePath, type="string")
            cmds.setAttr(f'{roughness_file_node}.colorSpace', 'Raw', type='string')

            # Create a place2dTexture node
            place2d_roughness = cmds.shadingNode('place2dTexture', asUtility=True, name=f'place2dTexture_roughness_{material}')

            # Create a bump2d node
            bump2dNodeName = "bump2dname" + "_" + material_name
            bump2d_node = cmds.shadingNode('bump2d', asUtility=True, name=bump2dNodeName)
            cmds.setAttr(bump2d_node + '.bumpInterp', 1)

            # Create a file texture node for Normal
            normalNodeName = material_name + "_" + "Normal" + "_" + textureNum
            normal_file_node = cmds.shadingNode('file', asTexture=True, name=normalNodeName)
            normalFilePath = normalFile
            cmds.setAttr(f"{normal_file_node}.fileTextureName", normalFilePath, type="string")
            cmds.setAttr(f"{normal_file_node}.alphaIsLuminance", True)
            cmds.setAttr(f'{normal_file_node}.colorSpace', 'Raw', type='string')

            # Create a place2dTexture node
            place2d_normal = cmds.shadingNode('place2dTexture', asUtility=True, name=f'place2dTexture_normal_{material}')

            connections = [
                ('coverage', 'coverage'),
                ('translateFrame', 'translateFrame'),
                ('rotateFrame', 'rotateFrame'),
                ('mirrorU', 'mirrorU'),
                ('mirrorV', 'mirrorV'),
                ('stagger', 'stagger'),
                ('wrapU', 'wrapU'),
                ('wrapV', 'wrapV'),
                ('repeatUV', 'repeatUV'),
                ('offset', 'offset'),
                ('rotateUV', 'rotateUV'),
                ('noiseUV', 'noiseUV'),
                ('vertexUvOne', 'vertexUvOne'),
                ('vertexUvTwo', 'vertexUvTwo'),
                ('vertexUvThree', 'vertexUvThree'),
                ('vertexCameraOne', 'vertexCameraOne'),
                ('outUV', 'uvCoord'),
                ('outUvFilterSize', 'uvFilterSize')
            ]
    
            # Connect all place2dTexture nodes to file nodes
            # place2d_baseColor -> baseColor_file_node
            for src, dest in connections:
                cmds.connectAttr(f"{place2d_baseColor}.{src}", f"{baseColor_file_node}.{dest}", force=True)
                cmds.connectAttr(f"{place2d_roughness}.{src}", f"{roughness_file_node}.{dest}", force=True)
                cmds.connectAttr(f"{place2d_normal}.{src}", f"{normal_file_node}.{dest}", force=True)
    
            # file nodes -> standard surface node
            cmds.connectAttr(f"{baseColor_file_node}.outColor", f"{material}.baseColor", force=True) # base color -> material (Base Color)
            cmds.connectAttr(f"{roughness_file_node}.outAlpha", f"{material}.specularRoughness", force=True) # roughness -> material (Specular Rougness)
            cmds.connectAttr(f"{bump2d_node}.outNormal", f"{material}.normalCamera", force=True) # bump2d -> material (Normal Camera)
            cmds.connectAttr(f"{normal_file_node}.outAlpha", f"{bump2d_node}.bumpValue", force=True) # normal -> bump2d
            

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
