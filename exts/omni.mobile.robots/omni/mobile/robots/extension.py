import os
import gc
import carb
import omni.ext
import omni.ui as ui
# from ui.ui_window import WidgetWindow
from omni.ui import color as cl
import omni.isaac.core.utils.nucleus as nucleus
from omni.mobile.robots.params import OMNIVERSE_ENVIRONMENTS, SIMULATION_ENVIRONMENTS
from omni.mobile.robots.ui.ui_window import WidgetWindow

cur_path = os.path.dirname(os.path.abspath(__file__))
WORLD_THUMBNAIL = cur_path + "/Empty_thumbnail.png"


class MobileExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        carb.log_info("Pegasus Simulator is starting up")

        # Save the extension id
        self._ext_id = ext_id
        
        self._count = 0

        self._window = APIWindowExample("Mobile Simulator", width=260, height=270)

    def on_shutdown(self):
        """
        Callback called when the extension is shutdown
        """
        carb.log_info("Pegasus Isaac extension shutdown")
        
        if self._window:
            self._window.destroy()
            self._window = None

        # Call the garbage collector
        gc.collect()

class APIWindowExample(ui.Window):
    # Design constants for the widgets
    LABEL_PADDING = 120
    BUTTON_HEIGHT = 50
    GENERAL_SPACING = 5

    WINDOW_WIDTH = 325
    WINDOW_HEIGHT = 850
    
    BUTTON_SELECTED_STYLE = {
        "Button": {
            "background_color": 0xFF5555AA,
            "border_color": 0xFF5555AA,
            "border_width": 2,
            "border_radius": 5,
            "padding": 5,
        }
    }

    BUTTON_BASE_STYLE = {
        "Button": {
            "background_color": cl("#292929"),
            "border_color": cl("#292929"),
            "border_width": 2,
            "border_radius": 5,
            "padding": 5,
        }
    }
        
    def __init__(self, title: str, **kwargs) -> None:
        super().__init__(title, **kwargs)
        
        self._build_window()
        
        
    def _build_window(self):
        with self.frame:
            with ui.ScrollingFrame(horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON, vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON):
                # Vertical Stack of menus
                with ui.VStack():

                    # Create a frame for selecting which scene to load
                    self._scene_selection_frame()
                    ui.Spacer(height=5)
                    
                    # Create a frame for selecting which vehicle to load in the simulation environment
                    ui.Spacer(height=5)
                    
                    # Create a frame for selecting the camera position, and what it should point torwards to
                    ui.Spacer()
    
    
    def _scene_selection_frame(self):
        """
        Method that implements a dropdown menu with the list of available simulation environemts for the vehicle
        """
        
        # Frame for selecting the simulation environment to load
        with ui.CollapsableFrame("Scene Selection"):
            with ui.VStack(height=0, spacing=10, name="frame_v_stack"):
                ui.Spacer(height=APIWindowExample.GENERAL_SPACING)
                
                # Iterate over all existing pre-made worlds bundled with this extension
                with ui.HStack():
                    ui.Label("World Assets", width=APIWindowExample.LABEL_PADDING, height=10.0)
                    
                    # Combo box with the available environments to select from
                    dropdown_menu = ui.ComboBox(0, height=10, name="environments")
                    for environment in SIMULATION_ENVIRONMENTS:
                        dropdown_menu.model.append_child_item(None, ui.SimpleStringModel(environment))
                    
                ui.Spacer(height=0)
                
                with ui.HStack():
                    # Add a thumbnail image to have a preview of the world that is about to be loaded
                    with ui.ZStack(width=APIWindowExample.LABEL_PADDING, height=APIWindowExample.BUTTON_HEIGHT * 2):
                        ui.Rectangle()
                        ui.Image(
                            WORLD_THUMBNAIL,
                            fill_policy=ui.FillPolicy.PRESERVE_ASPECT_FIT,
                            alignment=ui.Alignment.LEFT_CENTER,
                        )

                    ui.Spacer(width=APIWindowExample.GENERAL_SPACING)

                    with ui.VStack():
                        # Button for loading a desired scene
                        ui.Button(
                            "Load Scene",
                            height=APIWindowExample.BUTTON_HEIGHT,
                            # clicked_fn=self._delegate.on_load_scene,
                            style=APIWindowExample.BUTTON_BASE_STYLE,
                        )

                        # Button to reset the stage
                        ui.Button(
                            "Clear Scene",
                            height=APIWindowExample.BUTTON_HEIGHT,
                            # clicked_fn=self._delegate.on_clear_scene,
                            style=APIWindowExample.BUTTON_BASE_STYLE,
                        )