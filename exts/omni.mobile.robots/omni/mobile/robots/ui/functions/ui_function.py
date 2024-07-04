"""
| File: ui_function.py
| Author: Ji Sue Lee (brunoleej@gmail.com)
| License: BSD-3-Clause. Copyright (c) 2024, Ji Sue Lee. All rights reserved.
| Description: Definition of the UiDelegate which is an abstraction layer betweeen the extension UI and code logic features
"""
import omni
import carb
import asyncio
from abc import abstractmethod
from omni.isaac.core import World
from omni.isaac.core.scenes.scene import Scene
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.stage import create_new_stage_async, update_stage_async


class UIFunction:
    def __init__(self):
        super().__init__()
        self._window = None
        
        self._env_asset = None
        self._robot = None
        
        self._record_type = None
        self._resolution_type = None
        
        self._world = None
        self._world_settings = {"physics_dt": 1.0 / 60.0, "stage_units_in_meters": 1.0, "rendering_dt": 1.0 / 60.0}
        
        return

    def _get_world(self):
        return World.instance()
    
    def asset_server(self, asset_path):
        asset_root_path = get_assets_root_path()
        if asset_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return
        return asset_root_path + asset_path
        
    def _choose_env_dropdown(self, val=None):
        if val:
            self._env_asset = self.asset_server("/Isaac/Environments/" + f"{val}")
            print(f"{val} is chosen!!")
        
    async def set_env(self):
        usd_context = omni.usd.get_context()
        usd_context.open_stage(self._env_asset)
    
    def _choose_record_type(self, val=None):
        if val:
            self._record_type = val
            print(f"Choose {val} record type.")
    
    def _choose_resolution_type(self, val=None):
        if val:
            self._resolution_type = val
            print(f"Choose {val} type of resolution.")
    