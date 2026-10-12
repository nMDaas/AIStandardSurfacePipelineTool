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
        selectedObject = self.getSelectedObjects() # TODO: this can be 1 or many, but assuming 1 for now

        if self.folder_path == "":
            self.warnings.setText("Must select a folder path to folder textures")
        else:
            mat_name = self.createTextures()
            #self.apply_textures(selectedObject, mat_name)

    # =========================== APPLY LOGIC ===========================

    # Set object/group to be textuerd
    def getSelectedObjects(self):
        selected_objects = cmds.ls(selection=True)
        if len(selected_objects) == 0:
            self.warnings.setText("Must select an object or group of objects")
        else:
            self.warnings.setText("")
            return selected_objects[0]

    def createTextures(self):
        global folder_path
        global texture_files

        # get all files in folder_path
        texture_files = [f for f in os.listdir(self.folder_path) if os.path.isfile(os.path.join(self.folder_path, f))]
        
        result = ""

        # organize texture_files by texture numbers
        texture_groups = {}
        for file in texture_files:
            if file.endswith('.png'):
                # get texture number
                length = len(file)
                strTemp = file[length - 8:] # texture number + .png
                textureNum = strTemp[:4]

                if textureNum in texture_groups:
                    # textureNum exists, append file to the existing array
                    texture_groups[textureNum].append(file)
                else:
                    # textureNum does not exist, initialize a new array with the value
                    texture_groups[textureNum] = [file]
        
        # iterate through texture_groups and create textures
        for key,value in texture_groups.items():
            # extract name
            my_string = value[0]
            index = my_string.find('_')
            result = my_string[:index]
            material_name = result + key
            #print("material_name", material_name)

            for file in value:
                if "BaseColor" in file:
                    baseColorFile = file
                if "Normal" in file:
                    normalFile = file
                if "Roughness" in file:
                    roughnessFile = file

            # clean previously created nodes with same name
            self.cleanNodes(material_name)

            self.createMaterial(material_name, baseColorFile, normalFile, roughnessFile, key)

        return result
    
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

            """
            # Create a file texture node for Normal
            normalNodeName = material_name + "_" + "Normal" + "_" + textureNum
            normal_file_node = cmds.shadingNode('file', asTexture=True, name=normalNodeName)
            normalFilePath = normalFile
            cmds.setAttr(f"{normal_file_node}.fileTextureName", normalFilePath, type="string")
            cmds.setAttr(f"{normal_file_node}.alphaIsLuminance", True)
            cmds.setAttr(f'{normal_file_node}.colorSpace', 'Raw', type='string')
    
            # Create a file texture node for Metalness
            metalnessNodeName = material_name + "_" + "Metalness" + "_" + textureNum
            metalness_file_node = cmds.shadingNode('file', asTexture=True, name=metalnessNodeName)
            metalnessFilePath = metalnessFile
            cmds.setAttr(f"{metalness_file_node}.fileTextureName", metalnessFilePath, type="string")
            cmds.setAttr(f"{metalness_file_node}.alphaIsLuminance", True)
            cmds.setAttr(f'{metalness_file_node}.colorSpace', 'Raw', type='string')
    
            # Create a file texture node for Height
            heightNodeName = material_name + "_" + "Height" + "_" + textureNum
            height_file_node = cmds.shadingNode('file', asTexture=True, name=heightNodeName)
            heightFilePath = heightFile
            cmds.setAttr(f"{height_file_node}.fileTextureName", heightFilePath, type="string")
            cmds.setAttr(f"{height_file_node}.alphaIsLuminance", True)
            cmds.setAttr(f'{height_file_node}.colorSpace', 'Raw', type='string')
            """

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
                #cmds.connectAttr(f"{place2d_texture}.{src}", f"{normal_file_node}.{dest}", force=True)
                #cmds.connectAttr(f"{place2d_texture}.{src}", f"{metalness_file_node}.{dest}", force=True)
                
                #cmds.connectAttr(f"{place2d_texture}.{src}", f"{height_file_node}.{dest}", force=True)

            """
            # Create a multiplyDivide node
            multiply_divide_node = cmds.shadingNode('multiplyDivide', asUtility=True, name='multiplyDivide1')
            cmds.setAttr(f"{multiply_divide_node}.operation", 1) # Set operation as Multiply (1: multiply, 2: divide, 3: power)
            cmds.setAttr(f"{multiply_divide_node}.input2", 1, 1, 1, type="double3")
    
            # Create a bump2d node
            bump2d_node = cmds.shadingNode('bump2d', asUtility=True, name='bump2d1')
            cmds.setAttr(bump2d_node + '.bumpInterp', 1)
    
            # Create a displacement shader
            displacement_shader = cmds.shadingNode('displacementShader', asShader=True)
            """
    
            # file nodes -> standard surface node
            cmds.connectAttr(f"{baseColor_file_node}.outColor", f"{material}.baseColor", force=True) # Connect baseColor file to material
            cmds.connectAttr(f"{roughness_file_node}.outAlpha", f"{material}.specularRoughness", force=True) # Connect roughness file to material

            #cmds.connectAttr(f"{multiply_divide_node}.output", f"{material}.baseColor", force=True) # Connect multiplyDivide to material
            #cmds.connectAttr(f"{bump2d_node}.outNormal", f"{material}.normalCamera", force=True) # Connect bump2d to Normal Camera of material
            #cmds.connectAttr(f"{normal_file_node}.outAlpha", f"{bump2d_node}.bumpValue", force=True) # Connect normal file to bump2d
            #cmds.connectAttr(f"{metalness_file_node}.outAlpha", f"{material}.metalness", force=True) # Connect metalness file to material
            #
            #cmds.connectAttr(f"{height_file_node}.outAlpha", f"{displacement_shader}.displacement", force=True) 
            #cmds.connectAttr(f"{displacement_shader}.displacement", f"{shading_group}.displacementShader", force=True)
            

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
