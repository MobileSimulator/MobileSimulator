"""
| File: world_selection_widget.py
| Author: Ji Sue Lee (brunoleej@gmail.com)
| License: BSD-3-Clause. Copyright (c) 2024, Ji Sue Lee. All rights reserved.
| Description: Definition of the UiDelegate which is an abstraction layer betweeen the extension UI and code logic features
"""

__all__ = ["WorldSelectionWidget"]

import gc
import pxr
import carb
import omni
import asyncio
import numpy as np
import omni.ui as ui
from pxr import Usd, Sdf, UsdGeom, Gf
from abc import abstractmethod
from omni.isaac.core import World
from omni.isaac.core.scenes import Scene
from omni.isaac.core.utils.stage import create_new_stage_async, update_stage_async, clear_stage
from omni.mobile.robots.params import SIMULATION_ENVIRONMENTS, WORLD_THUMBNAIL, WORLD_THUMBNAILS, _asset_server
from omni.mobile.robots.ui.widgets import custom_multifield_widget, custom_env_combo_widget
from omni.isaac.core.utils.prims import create_prim


class WorldSelectionWidget(object):
    def __init__(self, **kwargs):
        self._spacing = 3
        self._label_padding = 120
        
        self._title = "WORLD LAYOUT"
        self._stage = omni.usd.get_context().get_stage()
        self._scene = Scene()
        pxr.UsdGeom.SetStageUpAxis(self._stage, pxr.UsdGeom.Tokens.y)
        self.timeline = omni.timeline.get_timeline_interface()

        self._current_tasks = None
        
        self._world = None
        self._world_settings = {"physics_dt": 1.0 / 60.0, "stage_units_in_meters": 1.0, "rendering_dt": 1.0 / 60.0}
    
    def _main_ui(self):
        """
        Implemented Functions:
            - DropDown (Environment selection)
            - 
        """
        
        with ui.CollapsableFrame(title=self._title, name="env_frame"):
            with ui.VStack(height=0, spacing=5, name="frame_v_stack"):
                ui.Line(style_type_name_override="HeaderLine")
                ui.Spacer(height = 5)
                
                self.env_type_ui = custom_env_combo_widget.EnvComboboxWidget(label="Environment (", options=SIMULATION_ENVIRONMENTS, on_restore_fn=self._env_info_func)
                
                with ui.HStack():
                    # Add a thumbnail image to have a preview of the world that is about to be loaded
                    with ui.ZStack(width=self._label_padding, height=40*2):
                        self.thumbnail_image = ui.Image(
                            WORLD_THUMBNAIL,
                            name="thumbnail", 
                            fill_policy=ui.FillPolicy.PRESERVE_ASPECT_CROP,
                            alignment=ui.Alignment.LEFT_CENTER,
                            )

                    ui.Spacer(width=self._spacing)
                    
                    with ui.VStack():
                        # Button for loading a desired scene
                        self._load_world_btn = ui.Button("Load Scene", width=200, height=40, name="load_button", style={ "color": "lightblue"}, clicked_fn=self._on_click_load_func)
                        self._clear_world_btn = ui.Button("Clear Scene", width=200, height=40, name="load_button", style={ "color": "lightblue"}, clicked_fn=self.clear_test)
                        
                ui.Spacer(height=self._spacing)
                # pos = custom_multifield_widget.CustomMultifieldWidget(label="Orientation: \t", default_vals=[0.0, 0.0, 0.0])
                # scale = custom_multifield_widget.CustomMultifieldWidget(label="Scale: \t", default_vals=[0.0, 0.0, 0.0])
                # ui.Spacer(height=self._spacing)

    """ WORLD THUMBNAIL Change """
    # def env_thumbnail_change(self):
    #     world_keys = list(WORLD_THUMBNAILS.keys())
    #     index = self.env_type_ui.get_item_value_model().get_value_as_int()
        
    #     cur_env_name = world_keys[index]
    #     new_thumbnail = WORLD_THUMBNAILS[cur_env_name]
    #     self.thumbnail_image.source = new_thumbnail
        
    #     self.thumbnail_image.update()
    
    """ World Selection Combobox """
    def _env_info_func(self, reset=False):
        env_type_id = np.random.randint(len(SIMULATION_ENVIRONMENTS)) if not reset else 0
        self.env_type_ui.model.get_item_value_model().set_value(env_type_id)
    
    """ World Load Button"""    
    def _on_click_load_func(self):
        asyncio.ensure_future(self.load_world_async())
    
    async def load_world_async(self):
        if World.instance() is None:
            print("World instance is None!!")
            await create_new_stage_async()
            self._world = World(**self._world_settings)
            await self._world.initialize_simulation_context_async()
            self.setup_scene(self._scene)
        else:
            self._world = World.instance()
        self._current_tasks = self._world.get_current_tasks()
        await self._world.reset_async()
        await self._world.pause_async()
        await self.setup_post_load()  # setup_post_load 호출
        if len(self._current_tasks) > 0:
            self._world.add_physics_callback("tasks_step", self._world.step_async)
        
        try:
            self._load_env(self.env_type_ui._env_name, "/World", "/World/base_env")
        except Exception as e:
            carb.log_warn("Could not load the desired environment: " + str(e))

        carb.log_info("A new environment has been loaded successfully")
    
        return
    
    @abstractmethod
    def setup_scene(self, scene: Scene) -> None:
        """used to setup anything in the world, adding tasks happen here for instance.

        Args:
            scene (Scene): [description]
        """
        return
    
    async def setup_post_load(self):
        """Called after first reset of the world when pressing load."""
        print("Post load setup complete.")
    
    
    def _load_env(self, usd_path: str, stage_prefix: str, asset_stage_prefix: str):
        if self._world.stage.GetPrimAtPath(stage_prefix):
            raise Exception("A primitive already exists at the specified path")
        
        # Create the stage primitive and load the usd into it
        prim = self._world.stage.DefinePrim(stage_prefix)
        custom_env = prim.GetReferences().AddReference(usd_path)
        
        if not custom_env:
            raise Exception("The usd asset" + usd_path + "is not load at stage path " + stage_prefix)
        
        self.set_env_pos(custom_env, pos=np.array([1, 2, 3]), scale=np.array([0.1, 0.1, 0.1]))
        
        # usd_asset = create_prim(prim_path=asset_stage_prefix,
        #                         position=[2.0, 0.0, 0.0],
        #                         orientation=[0.0, 0.0, 0.0, 1.0],
        #                         usd_path=usd_path,
        #                         semantic_label="Warehouse")
    
    def set_default_prim(self, stage, stage_prefix: str):
        default_prim = UsdGeom.Xform.Define(stage, Sdf.Path(stage_prefix))
        stage.SetDefaultPrim(default_prim.GetPrim())
    
    def set_env_pos(self, base_env, pos: np.ndarray, scale: np.ndarray):
        if not isinstance(base_env, Usd.Prim):
            raise ValueError("base_env must be a Usd.Prim object")
    
        xformable_env = UsdGeom.Xformable(base_env)
        
        # Translation operation
        translateOp = xformable_env.AddXformOp(UsdGeom.XformOp.TypeTranslate, UsdGeom.XformOp.PrecisionDouble)
        translateOp.Set(Gf.Vec3d(*pos))  # Convert numpy array to Gf.Vec3d
        
        # Scale operation
        scaleOp = xformable_env.AddXformOp(UsdGeom.XformOp.TypeScale, UsdGeom.XformOp.PrecisionDouble)
        scaleOp.Set(Gf.Vec3d(*scale))  # Convert numpy array to Gf.Vec3d
        
        print(f"Set position to: {pos}")
        print(f"Set scale to: {scale}")
        
        # Uncomment if you need to set rotation as well
        # rotateOp = xformable_env.AddXformOp(UsdGeom.XformOp.TypeRotateXYZ, UsdGeom.XformOp.PrecisionDouble)
        # rotateOp.Set(ori)  # Set rotation
        
        # Save the stage if needed
        # stage.GetRootLayer().Save()

    """ World reset Button """    
    def clear_test(self):
        if self._world is not None:
            self._world.stop()
        
        if self._world is not None:
            self._world.clear_all_callbacks()
            self._world.clear()
        
        clear_stage()
        
        gc.collect()
        
        asyncio.ensure_future(self._world.initialize_simulation_context_async())
        carb.log_info("Current Scene has been deleted")
        
    def _on_click_reset_func(self):
        async def _on_reset_async():
            await self.reset_async()
            await omni.kit.app.get_app().next_update_async()
        
        asyncio.ensure_future(_on_reset_async())
    
    async def reset_async(self):
        """Function called when clicking reset button"""
        if self._world.is_tasks_scene_built() and len(self._current_tasks) > 0:
            self._world.remove_physics_callback("tasks_step")
        await self._world.play_async()
        await omni.isaac.core.utils.stage.update_stage_async()
        await self.setup_pre_reset()
        await self._world.reset_async()
        await self._world.pause_async()
        await self.setup_post_reset()
        if self._world.is_tasks_scene_built() and len(self._current_tasks) > 0:
            self._world.add_physics_callback("tasks_step", self._world.step_async)
        return
    
    async def setup_pre_reset(self):
        """Called in reset button before resetting the world."""
        print("Pre reset setup complete.")
        
    async def setup_post_reset(self):
        """Called in reset button after resetting the world."""
        print("Post reset setup complete.")  