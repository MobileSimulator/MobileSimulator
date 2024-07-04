__all__ = ["AnimationFPSModel", "BaseMovieCaptureWidget"]

import json
import carb
import omni
import weakref
import omni.ui as ui
from omni.rtx.window.settings import RendererSettingsFactory
from omni.kit.capture.viewport.capture_options import CaptureOptions
from omni.mobile.robots.params import DEFAULT_SELECTED_FPS, DEFAULT_ANIMATION_FPS

APP_OVC_DEVELOPMENT_SETTING_PATH = "/app/ovc_deployment"
MC_EXT_OVC_MODE_SETTING_PATH = "/exts/omni.kit.window.movie_capture/ovc_mode"
LEFT_COLUMN_WIDTH_IN_PERCENT = 30
FRAME_SPACING = 5



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


class AnimationFPSModel:
    def __init__(self):
        super().__init__()
        
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
