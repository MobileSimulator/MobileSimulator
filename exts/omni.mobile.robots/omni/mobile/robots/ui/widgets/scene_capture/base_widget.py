from pxr import Usd, UsdGeom
from collections import OrderedDict

import weakref
import carb
import json
import omni.ui as ui
import omni.kit.app
import omni.kit.ui
import omni.stageupdate
import omni.usd
import omni.ext
from omni.rtx.window.settings import RendererSettingsFactory
from omni.kit.capture.viewport.capture_options import CaptureOptions
from omni.kit.viewport.utility import get_viewport_window_camera_string

from .moive_capture_icons import MovieCaptureIcons


APP_OVC_DEVELOPMENT_SETTING_PATH = "/app/ovc_deployment"
MC_EXT_OVC_MODE_SETTING_PATH = "/exts/omni.kit.window.movie_capture/ovc_mode"
WINDOW_WIDTH = 590
WINDOW_HEIGHT = 690
LEFT_COLUMN_WIDTH_IN_PERCENT = 30
LEFT_COLUMN_WIDTH_IN_PERCENT_WIDE = 80
FRAME_SPACING = 5
RIGHT_SPACING = 12
GLYPH_CODE_UP = omni.kit.ui.get_custom_glyph_code("${glyphs}/arrow_up.svg")
GLYPH_CODE_DOWN = omni.kit.ui.get_custom_glyph_code("${glyphs}/arrow_down.svg")
GLYPH_CODE_SETTINGS = omni.kit.ui.get_custom_glyph_code("${glyphs}/cog.svg")
GLYPH_CODE_FOLDER = omni.kit.ui.get_custom_glyph_code("${glyphs}/folder.svg")
GLYPH_CODE_FOLDER_OPEN = omni.kit.ui.get_custom_glyph_code("${glyphs}/folder_open.svg")
GLYPH_CODE_JUMP_TO = omni.kit.ui.get_custom_glyph_code("${glyphs}/share.svg")
GLYPH_CODE_LINK = omni.kit.ui.get_custom_glyph_code("${glyphs}/link.svg")
GLYPH_CODE_UNLINK = omni.kit.ui.get_custom_glyph_code("${glyphs}/unlink.svg")
TUNE_ARROW_SIZE = 10
CHECKBOX_BACKGROUND_COLOR = 0xFF9E9E9E
CHECKBOX_COLOR = 0xFF23211F
ICON_BUTTON_SIZE = 18
ICON_BUTTON_SIZE_SMALL = 15
DEFAULT_ANIMATION_FPS = ["24", "25", "29.97", "30", "60", "120"]
DEFAULT_SELECTED_FPS = 24
SEQUENCER_CAMERA = "[ Sequencer Camera ]"
USE_SEQUENCER_CAMERA = "/persistent/exts/omni.kit.window.sequencer/useSequencerCamera"

WINDOW_DARK_STYLE = {
    "Button.Image::res_link": {"image_url": MovieCaptureIcons().get("link")},
    "Button::res_link": {"background_color": 0x0},
    "Button.Image::res_unlink": {"image_url": MovieCaptureIcons().get("link_dark")},
    "Button::res_unlink": {"background_color": 0x0},
    "Button::icon_button": {"background_color": 0x0, "margin": 0.0, "padding": 0.0},
    "Rectangle::input_with_spinners": {"background_color": 0x0},
    "CheckBox::green_check": {"font_size": 12, "background_color": CHECKBOX_BACKGROUND_COLOR, "color": CHECKBOX_COLOR, "border_radius": 1.5},
}


def get_extension_obj(extension_name):
    if extension_name in g_extensions:
        return g_extensions[extension_name]
    else:
        return None


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


class WeakMethod(weakref.WeakMethod):
    def __call__(self, *args, **kwargs):
        obj = weakref.ref.__call__(self)
        func = self._func_ref()
        if obj is None or func is None:
            return None
        return func(obj, *args, **kwargs)


class AnimationFpsItem(ui.AbstractItem):
    def __init__(self, model):
        super().__init__()
        self.model = model


class AnimationFpsModel(ui.AbstractItemModel):
    def __init__(self):
        super().__init__()

        # Omniverse interfaces
        self._app = omni.kit.app.get_app_interface()
        self._stage_update = omni.stageupdate.get_stage_update_interface()
        self._usd_context = omni.usd.get_context()
        self._timeline = omni.timeline.get_timeline_interface()
        self._current_fps = self._timeline.get_time_codes_per_seconds()
        self._capture_instance = omni.kit.capture.viewport.CaptureExtension.get_instance()
        self._timeline_event_sub = self._timeline.get_timeline_event_stream().create_subscription_to_pop_by_type(
            omni.timeline.TimelineEventType.TIME_CODE_PER_SECOND_CHANGED, WeakMethod(self._on_timeline_event)
        )

        self._active_fps = DEFAULT_SELECTED_FPS
        self._all_fps = []
        # define if we want to automatically update the selected FPS to be the current in timeline window
        self._track_current_fps = True

        # The current index of the editable_combo box
        self._current_index = ui.SimpleIntModel()
        self._fps_value_changed_fn = self._current_index.add_value_changed_fn(self._current_index_changed)
        self._refresh_fps()

    @property
    def track_current_fps(self):
        return self._track_current_fps

    @track_current_fps.setter
    def track_current_fps(self, value):
        self._track_current_fps = value

    def clear(self):
        self._capture_instance = None

    def get_item_children(self, item):
        return self._all_fps

    def get_current_fps(self):
        value_model = self.get_item_value_model(self._all_fps[self._current_index.as_int], 0)
        fps = value_model.as_string
        return float(self._strip_current_from_fps_name(fps))

    def set_current_fps(self, fps_name):
        all_fps = [fps.model.as_string for fps in self._all_fps]
        index = 0
        for fps in all_fps:
            real_fps_name = float(self._strip_current_from_fps_name(fps))
            if fps_name == real_fps_name:
                break
            index += 1
        if index == len(all_fps):
            carb.log_warn(f"Movie capture: {fps_name} is not available so can't set it for capture.")
        else:
            self._current_index.as_int = index

    def get_item_value_model(self, item, column_id):
        if item is None:
            return self._current_index

        return item.model

    def _is_same_fps(self, fps1, fps2):
        return abs(fps1 - fps2) < 0.0001

    def _fps_exists(self, fps):
        all_fps = [fps.model.as_string for fps in self._all_fps]
        index = 0
        for fps in all_fps:
            real_fps = float(self._strip_current_from_fps_name(fps))
            if self._is_same_fps(fps, real_fps):
                break
            index += 1
        return index != len(all_fps)

    def _on_timeline_event(self, evt):
        self._current_fps = self._timeline.get_time_codes_per_seconds()
        self._current_index_changed(None)

    def _strip_current_from_fps_name(self, fps_name):
        if fps_name.startswith("Current ("):
            return fps_name[9 : len(fps_name) - 1]
        else:
            return fps_name

    def _get_fps_from_timeline_window(self):
        all_fps_values = []
        try:
            import omni.anim.window.timeline as wt
            if hasattr(wt, "get_instance"):
                all_fps_values = wt.get_instance().get_FPS_list()
            else:
                all_fps_values = DEFAULT_ANIMATION_FPS
                self._track_current_fps = False
        except Exception as e:
            carb.log_warn(f"Movie capture: failed to read FPS values from timeline window due to {e}")
            all_fps_values = DEFAULT_ANIMATION_FPS
            self._track_current_fps = False
        return all_fps_values

    def _format_fps_num(self, fps):
        return '{0:g}'.format(fps)

    def _get_active_fps(self) -> int:
        active_fps = self._timeline.get_time_codes_per_seconds()
        if active_fps == 0:
            carb.log_info(f"Movie capture fps: get 0 FPS from timeline. Set to {DEFAULT_SELECTED_FPS} by default.")
            active_fps = DEFAULT_SELECTED_FPS
        return active_fps

    def _refresh_fps(self, index=0):
        self._current_index.remove_value_changed_fn(self._fps_value_changed_fn)
        if not self._track_current_fps:
            all_fps_new = []
            self._active_fps = self._get_active_fps()
            all_fps_new.append(AnimationFpsItem(ui.SimpleStringModel("Current (" + self._format_fps_num(self._active_fps) + ")")))
            all_fps = [fps.model.as_string for fps in self._all_fps]
            index = 0
            append_active_fps = True
            for fps in all_fps:
                if index > 0:
                     all_fps_new.append(AnimationFpsItem(ui.SimpleStringModel(fps)))
                     # to check if the new active fps equals to any fps, if yes, do not add it twice
                     if self._is_same_fps(self._active_fps, float(fps)):
                         append_active_fps = False
                index += 1
            if append_active_fps:
                all_fps_new.append(AnimationFpsItem(ui.SimpleStringModel(self._format_fps_num(self._active_fps))))
            self._all_fps = []
            self._all_fps = all_fps_new
        else:
            self._all_fps = []
            self._active_fps = self._get_active_fps()
            self._all_fps.append(AnimationFpsItem(ui.SimpleStringModel("Current (" + self._format_fps_num(self._active_fps) + ")")))

            # get all the fps values from timeline window, and populate them
            all_fps_values = self._get_fps_from_timeline_window()
            for fps in all_fps_values:
                self._all_fps.append(AnimationFpsItem(ui.SimpleStringModel(self._format_fps_num(float(fps)))))

            self._current_index.as_int = 0

        self._fps_value_changed_fn = self._current_index.add_value_changed_fn(self._current_index_changed)

    def _current_index_changed(self, model):
        if model is None:
            self._refresh_fps()

        self._item_changed(None)


class BaseMovieCaptureWidget:
    def __init__(self):
        self._settings = carb.settings.get_settings()
        self._usd_context = omni.usd.get_context()

    def _build_ui_left_column(self, desc, width_in_percent=LEFT_COLUMN_WIDTH_IN_PERCENT):
        with ui.HStack(width=ui.Percent(width_in_percent)):
            ui.Spacer(width=FRAME_SPACING)
            if len(desc) > 0:
                ui.Label(desc)
            else:
                ui.Spacer()

    def _is_iray_enabled(self):
        render_string = self._settings.get("/renderer/enabled") or ''
        return render_string.find("iray") >= 0

    def _launch_render_setting_window(self, renderer):
        RendererSettingsFactory.set_current_renderer(renderer)
        RendererSettingsFactory._get_render_settings_extension().show_window(None, True)
        render_settings_wnd = ui.Workspace.get_window("Render Settings")
        if render_settings_wnd is not None:
            render_settings_wnd.focus()

    def _show_iray_settings(self):
        if self._is_iray_enabled() is False:
            return None

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        iray_ext_name = "omni.iray.settings.core"
        enabled = ext_manager.set_extension_enabled_immediate(iray_ext_name, True)
        if enabled:
            self._launch_render_setting_window("Iray")
        else:
            carb.log_warn(f"Movie Capture: Failed to enable {iray_ext_name} for Iray settings")

    def show_render_settings(self, renderer):
        if renderer == "Iray":
            self._show_iray_settings()
        else:
            self._launch_render_setting_window(renderer)

    def _get_combobox_value(self, combobox, values_tuple):
        index = combobox.model.get_item_value_model().as_int
        return values_tuple[index]

    def _get_combobox_string_value(self, combobox):
        model = combobox.model
        index = model.get_item_value_model().as_int
        selected_string = model.get_item_value_model(model.get_item_children()[index]).as_string
        return selected_string

    def _get_combobox_all_string_values(self, combobox):
        string_items = combobox.model.get_item_children()
        str_index = 0
        string_values = []
        while str_index < len(string_items):
            str_value = combobox.model.get_item_value_model(string_items[str_index]).as_string
            string_values.append(str_value)
            str_index += 1
        values_json = json.dumps(string_values)
        return values_json

    def _set_combobox_string_value(self, combobox, value):
        string_items = combobox.model.get_item_children()
        str_index = 0
        while str_index < len(string_items):
            str_value = combobox.model.get_item_value_model(string_items[str_index]).as_string
            if value == str_value:
                break
            str_index += 1
        if str_index == len(string_items):
            carb.log_warn(f"Movie capture: {value} is not available so can't set it for capture.")
            str_index = 0
        combobox.model.get_item_value_model().as_int = str_index

    def _is_ext_enabled(self, ext_name):
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        return ext_manager.is_extension_enabled(ext_name)

    def _enable_ext(self, ext_name):
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        if not ext_manager.is_extension_enabled(ext_name):
            return ext_manager.set_extension_enabled_immediate(ext_name, True)
        return True

    def _is_ovc_mode(self) -> bool:
        is_app_ovc = self._settings.get_as_bool(APP_OVC_DEVELOPMENT_SETTING_PATH)
        is_ext_ovc = self._settings.get_as_bool(MC_EXT_OVC_MODE_SETTING_PATH)
        return is_app_ovc or is_ext_ovc

    def collect_settings(self, options: CaptureOptions):
        pass

    def destroy(self):
        pass
