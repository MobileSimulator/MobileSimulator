"""
| File: learning_framework_widget.py
| Author: Ji Sue Lee (brunoleej@gmail.com)
| License: BSD-3-Clause. Copyright (c) 2024, Ji Sue Lee. All rights reserved.
| Description: Definition of the UiDelegate which is an abstraction layer betweeen the extension UI and code logic features
"""

__all__ = ["LearningFrameworkWidget"]


import carb
import omni
import omni.ui as ui
from omni.mobile.robots.ui.functions import ui_function
from omni.mobile.robots.params import ROBOT_ENVIRONMENTS, ROBOT_THUMBNAIL, default_file_path, LEARNING_TYPE
from omni.mobile.robots.ui.widgets.custom_multifield_widget import CustomMultifieldWidget
from omni.mobile.robots.ui.widgets.custom_env_combo_widget import RecordEnvComboboxWidget


class LearningFrameworkWidget():
    def __init__(self, **kwargs) -> None:
        
        self._vert_spacing = 0
        self._hori_spacing = 0
        self._name = ""
        self._spacing = 3
        self._label_padding = 120
        self._button_height = 40    # 40
        self._button_width = 20
        
        self._title = "LEARNING LAYOUT"
        self.ui_func = ui_function.UIFunction()
        
    def _main_ui(self):
        """
        Implemented UI:
            - DropDown (Select Task selection)
            - 
        """
        
        with ui.CollapsableFrame(title=self._title, name="learning_layout"):
            with ui.VStack(height=0, spacing=7, name="frame_v_stack"):
                ui.Line(style_type_name_override="HeaderLine")
                ui.Spacer(height = 0)   # 5

                self._task_setup_ui()
                            
                ui.Spacer(height=self._spacing)
    
    def _task_setup_ui(self):
        with ui.HStack():
            self.select_task_combo = RecordEnvComboboxWidget(label="Select Task: \t", options=LEARNING_TYPE)

    
    
            