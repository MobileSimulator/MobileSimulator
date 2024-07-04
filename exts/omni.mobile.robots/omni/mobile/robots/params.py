import os
import omni
import carb
from pathlib import Path
from omni.isaac.core.utils.nucleus import get_assets_root_path

# Extension configuration
EXTENSION_NAME = "Mobile Simulator"
WINDOW_TITLE = "Mobile Robot Simulator"
# MENU_PATH = "Window/" + WINDOW_TITLE
# DOC_LINK = "https://docs.omniverse.nvidia.com"
# EXTENSION_OVERVIEW = "This extension shows how to incorporate drones into Isaac Sim"

# Get the current directory of where this extension is located
EXTENSION_FOLDER_PATH = Path(os.path.dirname(os.path.realpath(__file__)))       # /home/go/Desktop/su/simulation/isaac/code/MobileSimulator/exts/omni.mobile.robots/omni/mobile/robots
ROOT = str(EXTENSION_FOLDER_PATH.parent.parent.parent.resolve())                # /home/go/Desktop/su/simulation/isaac/code/MobileSimulator/exts/omni.mobile.robots

# Define the Extension Assets Path
THUMNAIL_PATH = os.path.dirname(os.path.abspath(__file__)) + "/assets"
ROBOT_PATH = os.path.dirname(os.path.abspath(__file__)) + "/assets"
ICON_PATH = os.path.dirname(os.path.abspath(__file__)) + "/../../../data/icon"

# ROBOT_ENVIRONMENTS = {
#     "Husky": "husky.usd",
#     "WeCAR": "wecar.usd",
#     "franka": "fr3.usd",
#     "husky fr3": "husky_fr3.usd",
# }

# Setup the default simulation environments path
def _asset_server(asset_path):
    asset_root_path = get_assets_root_path()
    if asset_root_path is None:
        carb.log_error("Could not find Isaac Sim assets folder")
        return
    return asset_root_path + asset_path

SIMULATION_ENVIRONMENTS = ["Grid/default_environment.usd", "Grid/gridroom_black.usd", "Grid/gridroom_curved.usd", "Simple_Room/simple_room.usd", "Simple_Warehouse/warehouse.usd", "Simple_Warehouse/warehouse_with_forklifts.usd", "Simple_Warehouse/warehouse_multiple_shelves.usd", "Simple_Warehouse/full_warehouse.usd", "Hospital/hospital.usd", "Office/office.usd", "Jetracer/jetracer_track_solid.usd"]

WORLD_THUMBNAILS = {
    "Grid/default_environment.usd": THUMNAIL_PATH + "/default_env.png",
    "Grid/gridroom_black.usd": THUMNAIL_PATH + "/black_grid.png",
    "Grid/gridroom_curved.usd": THUMNAIL_PATH + "/curved_grid.png",
    "Simple_Room/simple_room.usd": THUMNAIL_PATH + "/simple_room.png",
    "Simple_Warehouse/warehouse.usd": THUMNAIL_PATH + "/warehouse.png",
    "Simple_Warehouse/warehouse_with_forklifts.usd": THUMNAIL_PATH + "/warehouse_with_forklifts.png",
    "Simple_Warehouse/warehouse_multiple_shelves.usd": THUMNAIL_PATH + "/warehouse_with_shelves.png",
    "Simple_Warehouse/full_warehouse.usd": THUMNAIL_PATH + "/full_warehouse.png",
    "Hospital/hospital.usd": THUMNAIL_PATH + "/hospital.png",
    "Office/office.usd": THUMNAIL_PATH + "/office.png",
    "Jetracer/jetracer_track_solid.usd": THUMNAIL_PATH + "/track.png",
}

ROBOT_ENVIRONMENTS = ["Husky", "WeCAR", "FR3", "Husky + FR3"]

# Define the default settings for the simulation environment
DEFAULT_WORLD_SETTINGS = {"physics_dt": 1.0 / 250.0, "stage_units_in_meters": 1.0, "rendering_dt": 1.0 / 60.0}

# Define where the thumbnail of the vehicle is located
ROBOT_THUMBNAIL = THUMNAIL_PATH + "/fr3.png"
ROBOT_ICON = ICON_PATH + "/robot.png"

# Define where the thumbail of the world is located
WORLD_THUMBNAIL = THUMNAIL_PATH + "/default_env.png"
WORLD_ICON = ICON_PATH + "/earth.png"

"""Recording Parameters"""
RECORD_TYPE = ["Sequence", "Sunstudy"]
RESOLUTION = ["HD", "Custom"]

DEFAULT_ANIMATION_FPS = ["24", "25", "29.97", "30", "60", "120"]
DEFAULT_SELECTED_FPS = 24
DEFAULT_FPS_SETTING_PATH = "/exts/omni.kit.window.movie_capture/default_fps"

CAPTURE_RANGE_TYPES = (omni.kit.capture.viewport.CaptureRangeType.FRAMES, omni.kit.capture.viewport.CaptureRangeType.SECONDS)
CAPTURE_RENDER_PRESET = (
    omni.kit.capture.viewport.CaptureRenderPreset.PATH_TRACE,
    omni.kit.capture.viewport.CaptureRenderPreset.RAY_TRACE,
)

"""Replay Trajectories"""
# default_file_path = os.path.join(os.path.abspath(__file__), "..", "..", "..", "..", "data", "example_data_file.json")
default_file_path = os.path.dirname(os.path.abspath(__file__)) + "/example_data.json"
output_default_path = os.path.dirname(os.path.abspath("__file__"))




"""Learning UI Property"""
LEARNING_TYPE = ["Husky_SLAM", "FR3-PAP", "Husky-FR3-SLAM-PAP"]


TYPE_INDEX_OF_PNG = 1
CAPTURE_FILE_TYPES = [".tga", ".png", ".exr"]
