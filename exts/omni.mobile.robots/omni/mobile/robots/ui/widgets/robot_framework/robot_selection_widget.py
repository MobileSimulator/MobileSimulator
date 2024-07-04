"""
| File: robot_selection_widget.py
| Author: Ji Sue Lee (brunoleej@gmail.com)
| License: BSD-3-Clause. Copyright (c) 2024, Ji Sue Lee. All rights reserved.
| Description: Definition of the UiDelegate which is an abstraction layer betweeen the extension UI and code logic features
"""

__all__ = ["RobotSelectionWidget"]

import carb
import omni
import omni.ui as ui
from omni.mobile.robots.params import ROBOT_ENVIRONMENTS, ROBOT_THUMBNAIL, default_file_path, RECORD_TYPE
from omni.mobile.robots.ui.widgets.custom_multifield_widget import CustomMultifieldWidget
from omni.mobile.robots.ui.widgets.custom_env_combo_widget import EnvComboboxWidget, RobotComboboxWidget, RecordEnvComboboxWidget


class RobotSelectionWidget:
    def __init__(self, **kwargs) -> None:
        
        self._spacing = 3
        self._label_padding = 120
        self._button_height = 40    # 40
        
        self._title = "ROBOT LAYOUT"
        
    def _select_robot(self):
        """
        Implemented Functions:
            - DropDown (Environment selection)
            - 
        """
        
        with ui.CollapsableFrame(title=self._title, name="robot_selection"):
            with ui.VStack(height=0, spacing=7, name="frame_v_stack"):
                ui.Line(style_type_name_override="HeaderLine")
                ui.Spacer(height = 0)   # 5
                
                self.robot_type_ui = RobotComboboxWidget(label="Robot (", options=ROBOT_ENVIRONMENTS)
                
                with ui.HStack():
                    # Add a thumbnail image to have a preview of the world that is about to be loaded
                    with ui.ZStack(width=self._label_padding, height=self._button_height * 2):
                        ui.Rectangle()
                        ui.Image(
                            ROBOT_THUMBNAIL,
                            name="thumbnail", 
                            fill_policy=ui.FillPolicy.PRESERVE_ASPECT_CROP,
                            alignment=ui.Alignment.LEFT_CENTER,
                        )
                    
                    ui.Spacer(width=self._spacing)
                                        
                    with ui.VStack(spacing=0):
                        ui.Button("Load Robot", width=200, height=40, name="load_button", style={ "color": "lightblue"},
                                #   clicked_fn=,
                                    )
                        # Button for loading a desired scene
                        ui.Button("Clear Robot", width=200, height=40, name="load_button", style={ "color": "lightblue"},
                                  #   clicked_fn=,
                                    )
                            
                        # ui.Spacer(width=WidgetWindow.GENERAL_SPACING)
                    
                ui.Spacer(height=self._spacing)
                # CustomMultifieldWidget(label="Orientation: \t", default_vals=[0.0, 0.0, 0.0])
                # CustomMultifieldWidget(label="Scale: \t", default_vals=[0.0, 0.0, 0.0])
                
                ui.Line(style_type_name_override="HeaderLine")
                self._replay_data(default_val=default_file_path)
                
                ui.Line(style_type_name_override="HeaderLine")
                self._connect_robot_ui()
                                
    def _replay_data(self, default_val):
        with ui.CollapsableFrame(title="Replay Trajectories", name="replay_trajectories"):
            with ui.VStack(height=0, spacing=10, name="frame_v_stack"):
                ui.Spacer(spacing=self._spacing)
                with ui.HStack(width=350):
                    # ui.Label("Data File: \t", name=f"data_file", width=85)
                    ui.Label("Data File: ")
                    str_field = ui.StringField(
                        name="StringField", width=253, height=0, alignment=ui.Alignment.LEFT_CENTER
                    )
                    str_field.model.set_value(default_val)
                
                with ui.HStack(width=355):
                    # ui.Label("Replay Data: ", name=f"record_data", width=78)
                    ui.Label("Replay Data: ")
                    
                    ui.Button("Trajectories", height=40, width=130, name="load_button", style={ "color": "lightblue"}, 
                            # clicked_fn=self.record_data_btn,
                            )
                    ui.Button("Scene", height=40, width=130, name="load_button", style={ "color": "lightblue"}, 
                            # clicked_fn=self.record_data_btn,
                            )
    
    def _connect_robot_ui(self):
        with ui.CollapsableFrame(title="Connect with Real Robot", name="real_robot_connnection"):
            with ui.VStack(height=0, spacing=10, name="frame_v_stack"):
                ui.Spacer(spacing=self._spacing)
                
                with ui.HStack():
                    ui.Label("Connction IP")
                    ui.Spacer(width=30)
                    
                with ui.HStack(width=355):
                    ui.Label("Real World: ")
                    # ui.Spacer(width=30)
                    ui.Button("Connect", height=40, width=130, name="load_button", style={"color": "lightblue"})
                    ui.Button("Disconnect", height=40, width=130, name="load_button", style={"color": "lightblue"})