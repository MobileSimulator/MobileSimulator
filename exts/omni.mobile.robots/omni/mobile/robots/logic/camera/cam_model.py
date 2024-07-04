__all__ = ["CamerasModel"]

import carb
import omni
import omni.ui as ui
from pxr import Usd, UsdGeom
from collections import OrderedDict
from omni.kit.viewport.utility import get_viewport_window_camera_string

SEQUENCER_CAMERA = "[ Sequencer Camera ]"
USE_SEQUENCER_CAMERA = "/persistent/exts/omni.kit.window.sequencer/useSequencerCamera"


class CamerasItem(ui.AbstractItem):
    def __init__(self, model):
        super().__init__()
        self.model = model
        

class CamerasModel(ui.AbstractItemModel):
    def __init__(self):
        super().__init__()

        # Omniverse interfaces
        self._app = omni.kit.app.get_app_interface()
        self._stage_update = omni.stageupdate.get_stage_update_interface()
        self._usd_context = omni.usd.get_context()
        self._stage_subscription = self._stage_update.create_stage_update_node(
            "CamerasModel", None, None, None, self._on_prim_created, None, self._on_prim_removed
        )
        self._update_sub = self._app.get_update_event_stream().create_subscription_to_pop(
            self._on_update, name="omni.kit.window.moive_capture cameras"
        )
        self._capture_instance = omni.kit.capture.viewport.CaptureExtension.get_instance()
        self._active_camera = ""
        # define if we want to automatically change the camera in viewport
        self._track_current_camera = True

        # The current index of the editable_combo box
        self._current_index = ui.SimpleIntModel()
        self._camera_value_changed_fn = self._current_index.add_value_changed_fn(self._current_index_changed)

        # OM-103468 When sequencer sync is toggled, update the camera menu and the current selection
        self._camera_switch_setting_sub = omni.kit.app.SettingChangeSubscription(
            USE_SEQUENCER_CAMERA, on_change=lambda *_: self._on_sequencer_camera_synced())

        self._refresh_cameras()

    def __del__(self):
        self._camera_switch_setting_sub = None

    @property
    def track_current_camera(self):
        return self._track_current_camera

    @track_current_camera.setter
    def track_current_camera(self, value):
        self._track_current_camera = value

    def clear(self):
        self._capture_instance = None

    def get_item_children(self, item):
        return self._cameras

    def get_current_camera(self):
        value_model = self.get_item_value_model(self._cameras[self._current_index.as_int], 0)
        camera = value_model.as_string
        return self._strip_current_from_camera_name(camera)

    def set_current_camera(self, camera_name):
        cameras = [cam.model.as_string for cam in self._cameras]
        index = 0
        for cam in cameras:
            real_cam_name = self._strip_current_from_camera_name(cam)
            if camera_name == real_cam_name:
                break
            index += 1
        if index == len(cameras):
            carb.log_warn(f"Movie capture: {camera_name} is not available so can't set it for capture.")
        else:
            self._current_index.set_value(index)

    def get_item_value_model(self, item, column_id):
        if item is None:
            return self._current_index

        return item.model

    def _strip_current_from_camera_name(self, camera_name):
        if camera_name.startswith("Current ("):
            return camera_name[9 : len(camera_name) - 1]
        else:
            return camera_name

    def _refresh_cameras(self, index=0):
        self._current_index.remove_value_changed_fn(self._camera_value_changed_fn)

        # Make sure we don't have duplicate entries
        new_cameras = OrderedDict()
        self._active_camera = get_viewport_window_camera_string(window_name=None)

        # OM-103468 Add active camera along with sequencer camera.  If sequence sync is on, then add the sequencer
        # camera to top of list, otherwise second.
        if carb.settings.get_settings().get_as_bool(USE_SEQUENCER_CAMERA):
            new_cameras[SEQUENCER_CAMERA] = CamerasItem(ui.SimpleStringModel(SEQUENCER_CAMERA))
            new_cameras[self._active_camera] = CamerasItem(ui.SimpleStringModel("Current (" + self._active_camera + ")"))
        else:
            new_cameras[self._active_camera] = CamerasItem(ui.SimpleStringModel("Current (" + self._active_camera + ")"))
            new_cameras[SEQUENCER_CAMERA] = CamerasItem(ui.SimpleStringModel(SEQUENCER_CAMERA))
        self._current_index.set_value(0)

        if self._track_current_camera:
            # Iterate the stage and get all the cameras
            stage = self._usd_context.get_stage()
            if stage is not None:
                for prim in Usd.PrimRange(stage.GetPseudoRoot()):
                    if prim.IsA(UsdGeom.Camera):
                        camera_name = prim.GetPath().pathString
                        if camera_name not in new_cameras:
                            new_cameras[camera_name] = CamerasItem(ui.SimpleStringModel(camera_name))
        else:
            # if we don't track the current camera in viewport, we still update the current camera option in the dropdown
            # to make it show the current camera, but we don't change the selection in the dropdown
            # Also, in case the current camera in viewport is new, append it to the end of the list
            cur_cameras = [cam.model.as_string for cam in self._cameras]
            for cam in cur_cameras:
                real_cam_name = self._strip_current_from_camera_name(cam)
                if real_cam_name not in new_cameras:
                    new_cameras[real_cam_name] = CamerasItem(ui.SimpleStringModel(real_cam_name))

        # Sort the cameras outside the top 2
        sorted_cameras = list(new_cameras)[2:]
        sorted_cameras.sort()
        self._cameras = [new_cameras[name] for name in list(new_cameras)[0:2] + sorted_cameras]
        self._camera_value_changed_fn = self._current_index.add_value_changed_fn(self._current_index_changed)

        # Trigger a menu redraw
        self._item_changed(None)

    def _on_update(self, event):
        if (
            self._capture_instance is not None
            and self._capture_instance.progress.capture_status == omni.kit.capture.viewport.CaptureStatus.NONE
        ):
            # Get camera from default/active Viewport Window for now
            active_camera = get_viewport_window_camera_string(window_name=None)
            if self._active_camera != active_camera:
                self._current_index_changed(None)

    def _on_prim_created(self, path):
        stage = self._usd_context.get_stage()
        prim = stage.GetPrimAtPath(path)
        if prim.IsValid() and prim.IsA(UsdGeom.Camera):
            self._cameras.append(CamerasItem(ui.SimpleStringModel(path)))
        self._item_changed(None)

    def _on_prim_removed(self, path):
        cameras = [cam.model.as_string for cam in self._cameras]
        if path in cameras:
            index = cameras.index(path)
            del self._cameras[index]
            self._current_index.as_int = 0
            self._item_changed(None)

    def _current_index_changed(self, model):
        if model is None:
            self._refresh_cameras()
        else:
            # Enable/disable sequencer camera on selection changed
            index = model.get_value_as_int()
            value_model = self.get_item_value_model(self._cameras[index], 0)
            # Deactivate subscribed callback before changing the setting to avoid circular updates
            self._camera_switch_setting_sub = None
            omni.kit.app.SettingChangeSubscription(USE_SEQUENCER_CAMERA, None)
            carb.settings.get_settings().set(USE_SEQUENCER_CAMERA, value_model.as_string==SEQUENCER_CAMERA)
            # Reactivate subscribed callback
            self._camera_switch_setting_sub = omni.kit.app.SettingChangeSubscription(
                USE_SEQUENCER_CAMERA, on_change=lambda *_: self._on_sequencer_camera_synced())

        self._item_changed(None)

    def _on_sequencer_camera_synced(self):
        sync_sequencer_camera = carb.settings.get_settings().get_as_bool(USE_SEQUENCER_CAMERA)
        cameras = [cam.model.as_string for cam in self._cameras]
        for index, camera_name in enumerate(cameras):
            if (sync_sequencer_camera and camera_name == SEQUENCER_CAMERA) or (not sync_sequencer_camera and camera_name.startswith("Current (")):
                # If sequence sync is disabled, then select current camera
                self._current_index.set_value(index)
                break