__all__ = ["WidgetWindow"]


# Omniverse general API
import carb
import numpy as np
import omni.ui as ui
from omni.mobile.robots.ui.styles import style
from omni.mobile.robots.ui.widgets.world_framework import world_selection_widget
from omni.mobile.robots.ui.widgets.robot_framework import robot_selection_widget
from omni.mobile.robots.ui.widgets.learning_framework import learning_framework_widget
from omni.mobile.robots.ui.widgets.scene_capture import capture_settings_widget


class WidgetWindow(ui.Window):
    def __init__(self, title: str, **kwargs) -> None:
        super().__init__(title, **kwargs)
        
        self._world_selection_widget = world_selection_widget.WorldSelectionWidget()
        self._robot_selection_widget = robot_selection_widget.RobotSelectionWidget()
        self._movie_capture_widget = capture_settings_widget.MovieCaptureWidget()
        self._learning_widget = learning_framework_widget.LearningFrameworkWidget()
        
        self._build_window()
        
    def _build_window(self):
        with self.frame:
            self.frame.style = style.julia_modeler_style
            with ui.ScrollingFrame():
                
                self.task_desc_ui = ui.StringField(height=20, style={ "margin_height": 2})
                self.task_desc_ui.model.set_value(" Welcome to Mobile Simulator!")
                
                # Vertical Stack of menus
                with ui.VStack(height=0):
                    
                    # Create a frame for selecting which scene to load
                    # self._world_selection_widget._main_ui()
                    ui.Spacer(height=5)
                    
                    # Create a frame for selecting which vehicle to load in the simulation environment
                    self._robot_selection_widget._select_robot()
                    ui.Spacer(height=5)
                    
                    # Create a frame for selecting the camera position, and what it should point torwards to
                    self._movie_capture_widget._build_ui_capture_settings()
                    ui.Spacer(height=5)
                    
                    self._learning_widget._main_ui()
                    ui.Spacer(height=5)
    
                