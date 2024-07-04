import carb
import omni.kit.capture.viewport
import omni.ui as ui
from omni.kit.window.popup_dialog import MessageDialog
from . import base_widget
from .quick_input import QuickNumberInput, QuickNumberInputType
from .ui_values_storage import UIValuesStorage
from .moive_capture_icons import MovieCaptureIcons
from .image_button import ImageButton
from omni.kit.viewport.utility import get_active_viewport


MOTION_BLUR_SHUTTER_STEP = 0.0167
MOTION_BLUR_SHUTTER_MIN = -1.0
MOTION_BLUR_SHUTTER_MAX = 1.0
DEFAULT_RENDER_PRODUCT_SETTING_PATH = "/exts/omni.kit.window.movie_capture/default_render_product"
DEFAULT_RENDER_PRESET_SETTING_PATH = "/exts/omni.kit.window.movie_capture/default_render_preset"
DEFAULT_SPP_PER_ITERATION_SETTING_PATH = "/exts/omni.kit.window.movie_capture/default_spp_per_iteration"
DEFAULT_SPP_PER_SUBFRAME_SETTING_PATH = "/exts/omni.kit.window.movie_capture/default_spp_per_subframe"
DEFAULT_SUBFRAME_PER_FRAME_SETTING_PATH = "/exts/omni.kit.window.movie_capture/default_subframe_per_frame"
DEFAULT_FRAME_SHUTTER_OPEN_SETTING_PATH = "/exts/omni.kit.window.movie_capture/default_frame_shutter_open"
DEFAULT_FRAME_SHUTTER_CLOSE_SETTING_PATH = "/exts/omni.kit.window.movie_capture/default_frame_shutter_close"
DEFAULT_IRAY_ITERATION_SETTING_PATH = "/exts/omni.kit.window.movie_capture/default_iray_iterations"
DEFAULT_IRAY_SUBFRAMES_PER_FRAME_SETTING_PATH = "/exts/omni.kit.window.movie_capture/default_iray_subframes_per_frame"
RENDER_PRESETS = ["PathTracing", "RaytracedLighting", "iray"]
RENDER_STYLE_IMAGE_SIZE = 20
RENDER_PRODUCT_REQUIRED_EXTS = ["omni.graph.nodes", "omni.graph.examples.cpp"]
RENDER_PRODUCT_CAPTURE_SETTING_PATH = "/exts/omni.kit.window.movie_capture/render_product_enabled"
RENDER_PRESET_SUPPORT_RENDER_PRODUCT_SETTING_PATH = "/exts/omni.kit.window.movie_capture/render_preset_support_render_product"


class RenderSettingsWidget(base_widget.BaseMovieCaptureWidget):
    def __init__(self, capture_instance):
        super(RenderSettingsWidget, self).__init__()
        self._render_mode_change_sub = self._settings.subscribe_to_node_change_events(
            "/rtx/rendermode", self._on_render_mode_in_viewport_changed
        )
        self._active_render_change_sub = self._settings.subscribe_to_node_change_events(
            "/renderer/active", self._on_active_render_in_viewport_changed
        )
        self._render_preset_setting_changed_sub = self._settings.subscribe_to_node_change_events(
            DEFAULT_RENDER_PRESET_SETTING_PATH, self._on_render_preset_setting_changed
        )
        self._spp_per_iteration_setting_changed_sub = self._settings.subscribe_to_node_change_events(
            DEFAULT_SPP_PER_ITERATION_SETTING_PATH, self._on_spp_per_iteration_setting_changed
        )
        self._spp_per_subframe_setting_changed_sub = self._settings.subscribe_to_node_change_events(
            DEFAULT_SPP_PER_SUBFRAME_SETTING_PATH, self._on_spp_per_subframe_setting_changed
        )
        self._subframe_per_frame_setting_changed_sub = self._settings.subscribe_to_node_change_events(
            DEFAULT_SUBFRAME_PER_FRAME_SETTING_PATH, self._on_subframe_per_frame_setting_changed
        )
        self._frame_shutter_open_setting_changed_sub = self._settings.subscribe_to_node_change_events(
            DEFAULT_FRAME_SHUTTER_OPEN_SETTING_PATH, self._on_frame_shutter_open_setting_changed
        )
        self._frame_shutter_close_setting_changed_sub = self._settings.subscribe_to_node_change_events(
            DEFAULT_FRAME_SHUTTER_CLOSE_SETTING_PATH, self._on_frame_shutter_close_setting_changed
        )
        self._iray_iterations_setting_changed_sub = self._settings.subscribe_to_node_change_events(
            DEFAULT_IRAY_ITERATION_SETTING_PATH, self._on_iray_iterations_setting_changed
        )
        self._render_product_setting_changed_sub = self._settings.subscribe_to_node_change_events(
            DEFAULT_RENDER_PRODUCT_SETTING_PATH, self._on_render_product_setting_changed
        )
        self._iray_subframe_per_frame_setting_changed_sub = self._settings.subscribe_to_node_change_events(
            DEFAULT_IRAY_SUBFRAMES_PER_FRAME_SETTING_PATH, self._on_iray_subframes_per_frame_setting_changed
        )
        self._dict = carb.dictionary.get_dictionary()
        self._active_render = "rtx"
        self._capture_instance = capture_instance
        self._render_product_required_exts = []
        self._iray_last_subframes_per_frame_value = self._settings.get_as_int(DEFAULT_IRAY_SUBFRAMES_PER_FRAME_SETTING_PATH)
        self._pt_last_subframes_per_frame_value = self._settings.get_as_int(DEFAULT_SUBFRAME_PER_FRAME_SETTING_PATH)

    def build_ui(self):
        viewport = get_active_viewport()
        render_mode = self._get_viewort_render_preset(viewport)
        self._build_ui_rendering_settings(render_mode)
        self._set_current_render_preset(render_mode)
        self._set_default_settings()
        self._update_render_product_area_visibility()

    def destroy(self):
        self._capture_instance = None
        self._settings.unsubscribe_to_change_events(self._render_mode_change_sub)
        self._settings.unsubscribe_to_change_events(self._active_render_change_sub)
        self._settings.unsubscribe_to_change_events(self._render_preset_setting_changed_sub)
        self._settings.unsubscribe_to_change_events(self._spp_per_iteration_setting_changed_sub)
        self._settings.unsubscribe_to_change_events(self._spp_per_subframe_setting_changed_sub)
        self._settings.unsubscribe_to_change_events(self._subframe_per_frame_setting_changed_sub)
        self._settings.unsubscribe_to_change_events(self._frame_shutter_open_setting_changed_sub)
        self._settings.unsubscribe_to_change_events(self._frame_shutter_close_setting_changed_sub)
        self._settings.unsubscribe_to_change_events(self._render_product_setting_changed_sub)

        # set ui.Image objects to None explicitly to avoid this error:
        # Client omni.ui Failed to acquire interface [omni::kit::renderer::IGpuFoundation v0.2] while unloading all plugins
        self._ui_render_style_shaded = None
        self._ui_render_style_white = None

    def _build_ui_rendering_settings(self, render_mode):
        self._collapsableFrame = ui.CollapsableFrame("Rendering", height=0)
        with self._collapsableFrame:
            with ui.VStack(height=0):
                self._build_ui_render_style_settings()
                self._build_ui_rendering_rtpt_settings()
                self._build_ui_rendering_iray_settings()
                self._build_ui_rendering_ptmb_settings()
                self._build_ui_rendering_realtime_settings()
                self._build_ui_rendering_common_settings()
                self._is_first_time_set_render_mode = True
                self._set_render_preset_from_mode(render_mode)
                self._set_pathtrace_settings_visibility(self._is_viewport_pathtracing(render_mode))

    def _build_ui_render_style_settings(self):
        with ui.HStack():
            self._build_ui_left_column("Render Style")
            with ui.HStack():
                with ui.HStack(width=ui.Percent(50)):
                    self._ui_render_style_shaded = ImageButton(
                        "Shaded",
                        MovieCaptureIcons().get("Style_Shaded"),
                        RENDER_STYLE_IMAGE_SIZE,
                        RENDER_STYLE_IMAGE_SIZE,
                        self._on_render_style_shaded_clicked,
                        identifier="render_setting_id_rect_render_style_shaded",
                    )
                    self._ui_render_style_shaded.selected = True
                    ui.Label(" Shaded mode")
                with ui.HStack(width=ui.Percent(50)):
                    self._ui_render_style_white = ImageButton(
                        "White",
                        MovieCaptureIcons().get("Style_White"),
                        RENDER_STYLE_IMAGE_SIZE,
                        RENDER_STYLE_IMAGE_SIZE,
                        self._on_render_style_white_clicked,
                        identifier="render_setting_id_rect_render_style_white"
                    )
                    self._ui_render_style_white.selected = False
                    ui.Label(" White mode")

    def _build_ui_render_product(self):
        self._ui_render_product_area = ui.VStack()
        with self._ui_render_product_area:
            ui.Spacer(height=base_widget.FRAME_SPACING)
            with ui.HStack(style=base_widget.WINDOW_DARK_STYLE):
                self._build_ui_left_column("")
                with ui.VStack(width=0):
                    ui.Spacer()
                    self._ui_use_render_product_check = ui.CheckBox(height=0, name="green_check", identifier="render_setting_id_check_use_render_product")
                    self._ui_use_render_product_check.model.as_bool = False
                    self._ui_use_render_product_check.model.add_value_changed_fn(self._on_use_render_product_clicked)
                    ui.Spacer()
                ui.Label(" Use render product to capture")
                ui.Spacer()
            self._ui_render_product_input_area = ui.VStack()
            with self._ui_render_product_input_area:
                ui.Spacer(height=base_widget.FRAME_SPACING)
                with ui.HStack(spacing=base_widget.FRAME_SPACING, style=base_widget.WINDOW_DARK_STYLE):
                    self._build_ui_left_column("Render Product")
                    self._ui_render_product = ui.ComboBox(0, "", "/renderview", identifier="render_setting_id_combo_render_product")
                    self._selected_render_product = ""
                    self._refresh_render_products()
                    with ui.VStack(width=0):
                        ui.Spacer()
                        self._ui_render_preset_refresh = ui.Button(
                            text="",
                            name="icon_button",
                            image_url=MovieCaptureIcons().get("refresh"),
                            width=base_widget.ICON_BUTTON_SIZE,
                            height=base_widget.ICON_BUTTON_SIZE,
                            mouse_pressed_fn=lambda x, y, b, _: self._on_render_preset_refresh_clicked(),
                            identifier="render_setting_id_button_render_product_refresh",
                        )
                        ui.Spacer()
                    self.check_render_product_availability()
                    ui.Spacer(width=base_widget.RIGHT_SPACING)
            self._ui_render_product_input_area.visible = False

    def _build_ui_rendering_rtpt_settings(self):
        with ui.VStack(spacing=0):
            ui.Spacer(height=base_widget.FRAME_SPACING)
            with ui.HStack(spacing=base_widget.FRAME_SPACING, style=base_widget.WINDOW_DARK_STYLE):
                self._build_ui_left_column("Render Preset")
                if self._is_iray_enabled():
                    self._ui_kit_render_preset = ui.ComboBox(
                        0,
                        "Use Current (RTX-Interactive (Path Tracing))",
                        "RTX-Interactive (Path Tracing) (Current)",
                        "RTX-Real-Time",
                        "RTX-Accurate (Iray)",
                    )
                else:
                    self._ui_kit_render_preset = ui.ComboBox(
                        0, "Use Current (RTX-Interactive (Path Tracing))", "RTX-Interactive (Path Tracing) (Current)", "RTX-Real-Time",
                        identifier="render_setting_id_combo_render_preset",
                    )
                self._current_viewport_render_mode = omni.kit.capture.viewport.CaptureRenderPreset.PATH_TRACE
                self._render_preset_selection_changed_fn = self._ui_kit_render_preset.model.add_item_changed_fn(
                    self._on_render_preset_selection_changed
                )
                with ui.VStack(width=0):
                    ui.Spacer()
                    self._ui_kit_render_preset_settings = ui.Button(
                        text="",
                        name="icon_button",
                        image_url=MovieCaptureIcons().get("cog"),
                        width=base_widget.ICON_BUTTON_SIZE_SMALL,
                        height=base_widget.ICON_BUTTON_SIZE_SMALL,
                        mouse_pressed_fn=lambda x, y, b, _: self._on_render_preset_settings_clicked(),
                        tooltip="Open render settings window",
                        identifier="render_setting_id_button_render_preset_settings",
                    )
                    ui.Spacer()
                ui.Spacer(width=base_widget.RIGHT_SPACING)

            self._build_ui_render_product()

            self._ui_kit_pathtrace_spp_settings_area = ui.VStack()
            with self._ui_kit_pathtrace_spp_settings_area:
                ui.Spacer(height=base_widget.FRAME_SPACING)
                with ui.HStack():
                    self._build_ui_left_column(
                        "Samples per pixel per iteration (useful for multi-GPU)",
                        base_widget.LEFT_COLUMN_WIDTH_IN_PERCENT_WIDE,
                    )
                    self._ui_spp_per_iteration_input = QuickNumberInput(
                        input_type=QuickNumberInputType.INT,
                        init_value=1,
                        step=1,
                        min_value=1,
                        identifier="render_setting_id_drag_spp_per_iteration_input",
                    )
                    ui.Spacer(width=base_widget.RIGHT_SPACING)
                with ui.HStack():
                    self._build_ui_left_column(
                        "Path Trace samples per pixel", base_widget.LEFT_COLUMN_WIDTH_IN_PERCENT_WIDE
                    )
                    tooltip_msg = (
                        "Maximum number of samples to accumulate per frame if motion blur is not enabled. \r\n"
                        "For motion blur, it will do as many samples as needed across subframes."
                    )
                    self._ui_spp_input = QuickNumberInput(
                        input_type=QuickNumberInputType.INT,
                        init_value=1,
                        step=1,
                        min_value=1,
                        tooltip=tooltip_msg,
                        identifier="render_setting_id_drag_spp_input",
                    )
                    ui.Spacer(width=base_widget.RIGHT_SPACING)

    def _build_ui_rendering_realtime_settings(self):
        self._ui_kit_realtime_settings_area = ui.VStack()
        with self._ui_kit_realtime_settings_area:
            ui.Spacer(height=base_widget.FRAME_SPACING)

    def _build_ui_rendering_common_settings(self):
        self._ui_kit_common_render_settings_area = ui.VStack()
        with self._ui_kit_common_render_settings_area:
            with ui.HStack():
                self._build_ui_left_column(
                    "Settle latency", base_widget.LEFT_COLUMN_WIDTH_IN_PERCENT_WIDE
                )
                # Value of 0 will use a default wait for frame sequences, allow opt out with -1
                min_value = -1
                tooltip_msg = (
                    "Number of frames to run/warm up before capture actually starts for a frame. \r\n"
                    "Useful for cases that require accumulation or pre-simulation to get better results. \r\n"
                    "Set to -1 to disable it, and 0 to let movie capture decide the number of frames automatically."
                )
                self._ui_common_settle_latency_input = QuickNumberInput(
                    input_type=QuickNumberInputType.INT,
                    init_value=0,
                    step=1,
                    min_value=min_value,
                    tooltip=tooltip_msg,
                    identifier="render_setting_id_drag_settle_latency_input",
                )
                ui.Spacer(width=base_widget.RIGHT_SPACING)
        self._ui_kit_common_render_settings_area.visible = True

    def _build_ui_rendering_iray_settings(self):
        self._ui_kit_iray_settings_area = ui.VStack()
        with self._ui_kit_iray_settings_area:
            ui.Spacer(height=base_widget.FRAME_SPACING)
            with ui.HStack():
                self._build_ui_left_column(
                    "Path Trace samples per pixel", base_widget.LEFT_COLUMN_WIDTH_IN_PERCENT_WIDE
                )
                tooltip_msg = (
                    "Maximum number of samples to accumulate per frame if motion blur is not enabled. \r\n"
                    "For motion blur, it will do as many samples as needed across subframes."
                )
                self._ui_iray_spp_input = QuickNumberInput(
                    input_type=QuickNumberInputType.INT,
                    init_value=1,
                    step=1,
                    min_value=1,
                    tooltip=tooltip_msg,
                    identifier="render_setting_id_drag_iray_spp_input",
                )
                ui.Spacer(width=base_widget.RIGHT_SPACING)
        self._ui_kit_iray_settings_area.visible = False

    def _build_ui_rendering_ptmb_settings(self):
        self._ui_kit_pathtrace_motionblur_settings_area = ui.VStack(spacing=0)
        with self._ui_kit_pathtrace_motionblur_settings_area:
            with ui.HStack(style=base_widget.WINDOW_DARK_STYLE):
                self._build_ui_left_column("")
                with ui.VStack(width=0):
                    ui.Spacer()
                    self._ui_kit_motion_blur_check = ui.CheckBox(height=0, name="green_check", identifier="render_setting_id_check_motion_blur")
                    self._ui_kit_motion_blur_check.model.as_bool = True
                    self._ui_kit_motion_blur_check.model.add_value_changed_fn(self._on_enable_motion_blur_clicked)
                    ui.Spacer()
                ui.Label(" Enable motion blur")
            self._ui_kit_pathtrace_motionblur_values_area = ui.VStack()
            with self._ui_kit_pathtrace_motionblur_values_area:
                with ui.HStack():
                    ui.Spacer(width=base_widget.FRAME_SPACING)
                    ui.Label("Path Trace Motion Blur Settings   ", width=0)
                    ui.Line()
                    ui.Spacer(width=base_widget.RIGHT_SPACING)
                ui.Spacer(height=base_widget.FRAME_SPACING)
                with ui.HStack():
                    self._build_ui_left_column("        Subframes per frame", base_widget.LEFT_COLUMN_WIDTH_IN_PERCENT_WIDE)
                    self._ui_ptmb_spf_input = QuickNumberInput(
                        input_type=QuickNumberInputType.INT,
                        init_value=5,
                        step=1,
                        min_value=1,
                        value_changed_fn=self._on_ptmb_spf_input_changed,
                        identifier="render_setting_id_drag_ptmb_spf_input",
                    )
                    ui.Spacer(width=base_widget.RIGHT_SPACING)
                with ui.HStack():
                    self._build_ui_left_column(
                        "        Frame shutter open ([-1.0, close])", base_widget.LEFT_COLUMN_WIDTH_IN_PERCENT_WIDE
                    )
                    self._ui_ptmb_fso_input = QuickNumberInput(
                        input_type=QuickNumberInputType.FLOAT,
                        init_value=0,
                        step=MOTION_BLUR_SHUTTER_STEP,
                        max_value=0.5,
                        min_value=-1.0,
                        value_changed_fn=self._on_ptmb_fso_input_changed,
                        identifier="render_setting_id_drag_ptmb_fso_input",
                    )
                    ui.Spacer(width=base_widget.RIGHT_SPACING)
                with ui.HStack():
                    self._build_ui_left_column(
                        "        Frame shutter close ([open, 1.0])", base_widget.LEFT_COLUMN_WIDTH_IN_PERCENT_WIDE
                    )
                    self._ui_ptmb_fsc_input = QuickNumberInput(
                        input_type=QuickNumberInputType.FLOAT,
                        init_value=0.5,
                        step=MOTION_BLUR_SHUTTER_STEP,
                        max_value=1.0,
                        min_value=-0.5,
                        value_changed_fn=self._on_ptmb_fsc_input_changed,
                        identifier="render_setting_id_drag_ptmb_fsc_input",
                    )
                    ui.Spacer(width=base_widget.RIGHT_SPACING)

    def check_render_product_availability(self):
        if self._is_ext_enabled("omni.graph.nodes") and self._is_ext_enabled("omni.graph.examples.cpp"):
            self._ui_render_product.enabled = True
            self._ui_render_product.set_tooltip("")
            return True
        else:
            self._ui_render_product.enabled = False
            fact_str = "Render Product is disabled because either omni.graph.nodes or omni.graph.examples.cpp extension is not enabled. "
            reason_str = "\r\nRender Product can work only if both of them are enabled. "
            action_str = "\r\nPlease enable them via Extension Manager and reopen Movie Capture to enable Render Product."
            self._ui_render_product.set_tooltip(f"{fact_str}{reason_str}{action_str}")
            return False

    def refresh_ui(self):
        self.check_render_product_availability()
        self._refresh_render_products()

    def _get_render_products_of_cur_stage(self):
        rps = [""]

        try:
            import omni.usd
            from pxr import UsdRender

            usd_context = omni.usd.get_context()
            stage = usd_context.get_stage()
            if stage is not None:
                for prim in stage.Traverse():
                    if prim.IsA(UsdRender.Product):
                        prim_path = prim.GetPath().pathString
                        if not prim_path.endswith("_MovieRecord_Script"):
                            rps.append(prim_path)
        except Exception as e:
            rps.clear()

        return rps

    def _refresh_render_products(self):
        model = self._ui_render_product.model
        self._selected_render_product = self._get_combobox_string_value(self._ui_render_product)
        for item in model.get_item_children():
            model.remove_item(item)

        rps = self._get_render_products_of_cur_stage()
        for rp in rps:
            model.append_child_item(None, ui.SimpleStringModel(rp))

        if len(self._selected_render_product) and len(rps) > 0:
            self._set_combobox_string_value(self._ui_render_product, self._selected_render_product)

    def _get_selected_render_preset(self):
        render_preset = omni.kit.capture.viewport.CaptureRenderPreset.PATH_TRACE
        selection = self._ui_kit_render_preset.model.get_item_value_model().as_int
        if selection == 0:
            render_preset = self._current_viewport_render_mode
        elif selection == 1:
            render_preset = omni.kit.capture.viewport.CaptureRenderPreset.PATH_TRACE
        elif selection == 2:
            render_preset = omni.kit.capture.viewport.CaptureRenderPreset.RAY_TRACE
        else:
            render_preset = omni.kit.capture.viewport.CaptureRenderPreset.IRAY
        return render_preset

    def _does_render_preset_support_render_preset(self, render_preset):
        return render_preset == omni.kit.capture.viewport.CaptureRenderPreset.PATH_TRACE

    def _update_render_product_area_visibility(self):
        render_preset = self._get_selected_render_preset()
        self._ui_render_product_area.visible = self._does_render_preset_support_render_preset(render_preset)

    def _check_to_enable_render_product_exts(self):
        exts_required = ""
        self._render_product_required_exts.clear()
        for ext in RENDER_PRODUCT_REQUIRED_EXTS:
            if not self._is_ext_enabled(ext):
                exts_required += f"\r\n {ext}"
                self._render_product_required_exts.append(ext)

        attention_msg = "".join([
                ("Please be noted that when using render product to capture, "
                    "Movie Capture will take the camera and resolution set in the UI, "
                    "instead of use the camera and resolution values in render product."),
                "",
            ])
        if len(exts_required) > 0:
            fact_msg = f"The following extension(s) are required to capture with render product: {exts_required}."
            confirm_msg = "Do you want movie capture to enable them?"
            message = f"{attention_msg} \r\n\r\n{fact_msg}\r\n\r\n{confirm_msg}"
            dialog = MessageDialog(
                parent=self._collapsableFrame,
                title="Movie Capture - enable render product extentions",
                message=message,
                ok_handler=self._on_render_product_ext_yes_clicked,
                cancel_handler=self._on_render_product_ext_no_clicked,
                ok_label="Yes",
                cancel_label="No",
                width=500,
            )
            dialog.show()
        else:
            dialog = MessageDialog(
                parent=self._collapsableFrame,
                title="Movie Capture - render product notes",
                message=attention_msg,
                ok_handler=self._on_render_product_ext_enable_result,
                ok_label="OK",
                disable_cancel_button=True,
                width=500,
            )
            dialog.show()
            self._settings.set_bool(RENDER_PRODUCT_CAPTURE_SETTING_PATH, True)
            self.check_render_product_availability()

    def _on_render_product_ext_enable_result(self, dialog):
        dialog.hide()

    def _on_render_product_ext_yes_clicked(self, dialog):
        exts_enable_failed = ""
        for ext in self._render_product_required_exts:
            enabled = self._enable_ext(ext)
            if enabled:
                carb.log_warn(f"Movie Capture: {ext} enabled for render product capture.")
            else:
                exts_enable_failed += f"\r\n {ext}"
                carb.log_warn(f"Movie Capture: Failed to enable {ext} for render product capture. Capture will not be done with render product.")
        dialog.hide()

        if len(exts_enable_failed) > 0:
            message = f"Failed to enable the following extensions: {exts_enable_failed}. \r\n\r\nCapture can't be done with render product."
            self._ui_use_render_product_check.model.as_bool = False
            self._settings.set_bool(RENDER_PRODUCT_CAPTURE_SETTING_PATH, False)
        else:
            message = "Render product capture required extensions are successfully enabled."
            self._settings.set_bool(RENDER_PRODUCT_CAPTURE_SETTING_PATH, True)
        carb.log_warn(message)
        enable_result_dialog = MessageDialog(
            parent=self._collapsableFrame,
            title="Movie Capture - render product enable results",
            message=message,
            ok_handler=self._on_render_product_ext_enable_result,
            ok_label="OK",
            disable_cancel_button=True,
            width=500,
        )
        enable_result_dialog.show()
        self.check_render_product_availability()

    def _on_render_product_ext_no_clicked(self, dialog):
        self._settings.set_bool(RENDER_PRODUCT_CAPTURE_SETTING_PATH, True)
        self.check_render_product_availability()
        dialog.hide()

    def _on_render_style_shaded_clicked(self, style_value):
        self._ui_render_style_shaded.selected = True
        self._ui_render_style_white.selected = False

    def _on_render_style_white_clicked(self, style_value):
        self._ui_render_style_shaded.selected = False
        self._ui_render_style_white.selected = True

    def _on_enable_motion_blur_clicked(self, model):
        self._ui_kit_pathtrace_motionblur_values_area.visible = model.as_bool

    def _on_use_render_product_clicked(self, model):
        if model.as_bool:
            self._check_to_enable_render_product_exts()
        else:
            self._settings.set_bool(RENDER_PRODUCT_CAPTURE_SETTING_PATH, False)

        self._ui_render_product_input_area.visible = model.as_bool
        if self._ui_render_product_input_area.visible:
            self.check_render_product_availability()

    def _update_subframe_default_value(self, render_preset):
        if render_preset == omni.kit.capture.viewport.CaptureRenderPreset.PATH_TRACE:
            self._ui_ptmb_spf_input.value_changed_fn = None
            self._apply_int_setting("subframe per frame", self._pt_last_subframes_per_frame_value, 1, self._ui_ptmb_spf_input)
            self._ui_ptmb_spf_input.value_changed_fn = self._on_ptmb_spf_input_changed
        elif render_preset == omni.kit.capture.viewport.CaptureRenderPreset.IRAY:
            self._ui_ptmb_spf_input.value_changed_fn = None
            self._apply_int_setting("subframe per frame", self._iray_last_subframes_per_frame_value, 1, self._ui_ptmb_spf_input)
            self._ui_ptmb_spf_input.value_changed_fn = self._on_ptmb_spf_input_changed
        else:
            return

    def _on_render_preset_selection_changed(self, model, item):
        render_preset = self._get_selected_render_preset()
        self._set_pathtrace_settings_visibility(render_preset == omni.kit.capture.viewport.CaptureRenderPreset.PATH_TRACE)
        self._set_iray_settings_visibility(render_preset == omni.kit.capture.viewport.CaptureRenderPreset.IRAY)
        self._set_realtime_settings_visibility(render_preset == omni.kit.capture.viewport.CaptureRenderPreset.RAY_TRACE)
        self._set_pathtrace_motionblur_visibility(render_preset == omni.kit.capture.viewport.CaptureRenderPreset.IRAY or
            render_preset == omni.kit.capture.viewport.CaptureRenderPreset.PATH_TRACE
        )
        self._update_render_product_area_visibility()

        self._settings.set_bool(
            RENDER_PRESET_SUPPORT_RENDER_PRODUCT_SETTING_PATH,
            self._does_render_preset_support_render_preset(render_preset)
        )

        self._update_subframe_default_value(render_preset)

    def _on_ptmb_spf_input_changed(self, model):
        render_preset = self._get_selected_render_preset()
        if render_preset == omni.kit.capture.viewport.CaptureRenderPreset.PATH_TRACE:
            self._pt_last_subframes_per_frame_value = model.as_int
        elif render_preset == omni.kit.capture.viewport.CaptureRenderPreset.IRAY:
            self._iray_last_subframes_per_frame_value = model.as_int

    def _on_ptmb_fso_input_changed(self, model):
        if model.as_float > self._ui_ptmb_fsc_input.value:
            model.as_float = self._ui_ptmb_fsc_input.value
            self._ui_ptmb_fso_input.max = model.as_float
        elif model.as_float < self._ui_ptmb_fso_input.min:
            model.as_float = self._ui_ptmb_fso_input.min
        self._ui_ptmb_fsc_input.min = model.as_float

    def _on_ptmb_fsc_input_changed(self, model):
        if model.as_float < self._ui_ptmb_fso_input.value:
            model.as_float = self._ui_ptmb_fso_input.value
            self._ui_ptmb_fsc_input.min = model.as_float
        elif model.as_float > self._ui_ptmb_fsc_input.max:
            model.as_float = self._ui_ptmb_fsc_input.max
        self._ui_ptmb_fso_input.max = model.as_float

    def _set_current_render_mode_selection(self, render_mode):
        model = self._ui_kit_render_preset.model
        model.remove_item_changed_fn(self._render_preset_selection_changed_fn)
        for item in model.get_item_children():
            model.remove_item(item)

        if render_mode == omni.kit.capture.viewport.CaptureRenderPreset.PATH_TRACE:
            model.append_child_item(None, ui.SimpleStringModel("Use Current (RTX-Interactive (Path Tracing))"))
            model.append_child_item(None, ui.SimpleStringModel("RTX-Interactive (Path Tracing) (Current)"))
            model.append_child_item(None, ui.SimpleStringModel("RTX-Real-Time"))
            if self._is_iray_enabled():
                model.append_child_item(None, ui.SimpleStringModel("RTX-Accurate (Iray)"))
            model.get_item_value_model().set_value(0)
            self._current_viewport_render_mode = omni.kit.capture.viewport.CaptureRenderPreset.PATH_TRACE
        elif render_mode == omni.kit.capture.viewport.CaptureRenderPreset.RAY_TRACE:
            model.append_child_item(None, ui.SimpleStringModel("Use Current (RTX-Real-Time)"))
            model.append_child_item(None, ui.SimpleStringModel("RTX-Interactive (Path Tracing)"))
            model.append_child_item(None, ui.SimpleStringModel("RTX-Real-Time (Current)"))
            if self._is_iray_enabled():
                model.append_child_item(None, ui.SimpleStringModel("RTX-Accurate (Iray)"))
            model.get_item_value_model().set_value(0)
            self._current_viewport_render_mode = omni.kit.capture.viewport.CaptureRenderPreset.RAY_TRACE
        elif render_mode == omni.kit.capture.viewport.CaptureRenderPreset.IRAY:
            model.append_child_item(None, ui.SimpleStringModel("Use Current (RTX-Accurate (Iray))"))
            model.append_child_item(None, ui.SimpleStringModel("RTX-Interactive (Path Tracing)"))
            model.append_child_item(None, ui.SimpleStringModel("RTX-Real-Time"))
            model.append_child_item(None, ui.SimpleStringModel("RTX-Accurate (Iray) (Current)"))
            model.get_item_value_model().set_value(0)
            self._current_viewport_render_mode = omni.kit.capture.viewport.CaptureRenderPreset.IRAY
        else:
            carb.log_warn(f"Movie capture: Unknown render mode: {render_mode}")

        if self._is_first_time_set_render_mode:
            model.get_item_value_model().set_value(0)
            self._is_first_time_set_render_mode = False

        self._on_render_preset_selection_changed(None, None)
        self._render_preset_selection_changed_fn = model.add_item_changed_fn(self._on_render_preset_selection_changed)

    def _is_viewport_raytracing(self, render_mode: str = None):
        rm = render_mode or self._settings.get("/rtx/rendermode")
        return rm is not None and rm.startswith("Raytrac")

    def _is_viewport_pathtracing(self, render_mode: str = None):
        rm = render_mode or self._settings.get("/rtx/rendermode")
        return rm is not None and rm.startswith("PathTrac")

    def _get_viewort_render_preset(self, viewport):
        render_preset = ""
        renderer_active = viewport.hydra_engine
        if renderer_active == "iray":
            render_preset = "iray"
        elif renderer_active == "rtx":
            render_preset = viewport.render_mode
        else:
            render_preset = ""
        return render_preset

    def _set_pathtrace_settings_visibility(self, visible):
        self._ui_kit_pathtrace_spp_settings_area.visible = visible
        self._ui_kit_pathtrace_motionblur_settings_area.visible = visible and self._ui_kit_motion_blur_check.model.as_bool

    def _set_iray_settings_visibility(self, visible):
        self._ui_kit_iray_settings_area.visible = visible

    def _set_pathtrace_motionblur_visibility(self, visible):
        self._ui_kit_pathtrace_motionblur_settings_area.visible = visible

    def _set_realtime_settings_visibility(self, visible):
        self._ui_kit_realtime_settings_area.visible = visible

    def _set_current_render_preset(self, render_preset):
        if render_preset == "PathTracing":
            self._set_current_render_mode_selection(omni.kit.capture.viewport.CaptureRenderPreset.PATH_TRACE)
        elif render_preset == "RaytracedLighting":
            self._set_current_render_mode_selection(omni.kit.capture.viewport.CaptureRenderPreset.RAY_TRACE)
        elif render_preset == "iray" and self._is_iray_enabled():
            self._set_current_render_mode_selection(omni.kit.capture.viewport.CaptureRenderPreset.IRAY)
        else:
            carb.log_warn(f"Movie Capture can't set unsupported render mode {render_preset}")

    def _choose_render_preset(self, render_preset):
        if render_preset == "PathTracing":
            key = "Path"
        elif render_preset == "RaytracedLighting":
            key = "Real"
        elif render_preset == "iray" and self._is_iray_enabled():
            key = "Iray"
        else:
            carb.log_warn(f"Movie Capture can't choose unsupported render mode {render_preset}")
            return

        render_preset_index = 0
        for item in self._ui_kit_render_preset.model.get_item_children():
            if self._ui_kit_render_preset.model.get_item_value_model(item).as_string.find(key) >= 0:
                break
            else:
                render_preset_index += 1
        if render_preset_index < len(self._ui_kit_render_preset.model.get_item_children()):
            self._ui_kit_render_preset.model.get_item_value_model().as_int = render_preset_index
        else:
            carb.log_warn(f"Movie Capture can't find render mode {render_preset} in the render preset list.")

    def _on_render_preset_setting_changed(self, item, event_type):
        render_preset = self._dict.get(item)
        self._choose_render_preset(render_preset)

    def _set_default_settings(self):
        render_preset = self._settings.get_as_string(DEFAULT_RENDER_PRESET_SETTING_PATH)
        render_product = self._settings.get_as_string(DEFAULT_RENDER_PRODUCT_SETTING_PATH)
        spp_per_iter = self._settings.get_as_int(DEFAULT_SPP_PER_ITERATION_SETTING_PATH)
        spp_per_subframe = self._settings.get_as_int(DEFAULT_SPP_PER_SUBFRAME_SETTING_PATH)
        subframe_per_frame = self._settings.get_as_int(DEFAULT_SUBFRAME_PER_FRAME_SETTING_PATH)
        frame_shutter_open = self._settings.get_as_float(DEFAULT_FRAME_SHUTTER_OPEN_SETTING_PATH)
        frame_shutter_close = self._settings.get_as_float(DEFAULT_FRAME_SHUTTER_CLOSE_SETTING_PATH)
        iray_iterations = self._settings.get_as_int(DEFAULT_IRAY_ITERATION_SETTING_PATH)
        self._choose_render_preset(render_preset)
        self._apply_int_setting("SPP per iteration", spp_per_iter, 1, self._ui_spp_per_iteration_input)
        self._apply_int_setting("SPP per subframe", spp_per_subframe, 1, self._ui_spp_input)
        self._apply_int_setting("subframe per frame", subframe_per_frame, 1, self._ui_ptmb_spf_input)
        self._apply_frame_shutter_open_setting(frame_shutter_open)
        self._apply_frame_shutter_close_setting(frame_shutter_close)
        self._apply_int_setting("IRay Path Trace samples per pixel", iray_iterations, 1, self._ui_iray_spp_input)
        self._apply_render_product_setting(render_product)

    def _apply_int_setting(self, setting, value, default_value, input_widget):
        if value < 1:
            carb.log_warn(f"Movie capture's {setting} is set to invalid value {value}. Set to {default_value}.")
            value = default_value
        input_widget.value = value

    def _apply_frame_shutter_open_setting(self, value):
        if value < -1.0:
            carb.log_warn("Movie capture's frame shutter open value should be no less than -1.0. Set to -1.0.")
            value = -1.0
        elif value > self._ui_ptmb_fsc_input.value:
            carb.log_warn(f"Movie capture's frame shutter open value should be no greater than the close value. Set to {self._ui_ptmb_fsc_input.value}.")
            value = self._ui_ptmb_fsc_input.value
        self._ui_ptmb_fso_input.value = value

    def _apply_frame_shutter_close_setting(self, value):
        if value < self._ui_ptmb_fso_input.value:
            carb.log_warn(f"Movie capture's frame shutter close value should be no less than the open value. Set to {self._ui_ptmb_fso_input.value}.")
            value = self._ui_ptmb_fso_input.value
        elif value > 1.0:
            carb.log_warn("Movie capture's frame shutter open value should be no greater than 1.0. Set to 1.0.")
            value = 1.0
        self._ui_ptmb_fsc_input.value = value

    def _apply_render_product_setting(self, value):
        self._set_combobox_string_value(self._ui_render_product, value)

    def _is_capturing(self):
        return self._capture_instance.progress.capture_status != omni.kit.capture.viewport.CaptureStatus.NONE

    def _on_spp_per_iteration_setting_changed(self, item, event_type):
        spp_per_iter = int(self._dict.get(item))
        self._apply_int_setting("SPP per iteration", spp_per_iter, 1, self._ui_spp_per_iteration_input)

    def _on_spp_per_subframe_setting_changed(self, item, event_type):
        spp_per_subframe = int(self._dict.get(item))
        self._apply_int_setting("SPP per subframe", spp_per_subframe, 1, self._ui_spp_input)

    def _on_subframe_per_frame_setting_changed(self, item, event_type):
        subframe_per_frame = int(self._dict.get(item))
        self._apply_int_setting("subframe per frame", subframe_per_frame, 1, self._ui_ptmb_spf_input)

    def _on_frame_shutter_open_setting_changed(self, item, event_type):
        frame_shutter_open = float(self._dict.get(item))
        self._apply_frame_shutter_open_setting(frame_shutter_open)

    def _on_frame_shutter_close_setting_changed(self, item, event_type):
        frame_shutter_close = float(self._dict.get(item))
        self._apply_frame_shutter_close_setting(frame_shutter_close)

    def _on_iray_iterations_setting_changed(self, item, event_type):
        iterations = int(self._dict.get(item))
        self._apply_int_setting("IRay Path Trace samples per pixel", iterations, 1, self._ui_iray_spp_input)

    def _on_iray_subframes_per_frame_setting_changed(self, item, event_type):
        subframe_per_frame = int(self._dict.get(item))
        self._apply_int_setting("subframe per frame", subframe_per_frame, 1, self._ui_ptmb_spf_input)

    def _on_render_product_setting_changed(self, item, event_type):
        render_product = str(self._dict.get(item))
        self._apply_render_product_setting(render_product)

    def _set_render_preset_from_mode(self, render_mode: str):
        if render_mode == "PathTracing":
            self._set_current_render_mode_selection(omni.kit.capture.viewport.CaptureRenderPreset.PATH_TRACE)
        elif render_mode == "RaytracedLighting":
            self._set_current_render_mode_selection(omni.kit.capture.viewport.CaptureRenderPreset.RAY_TRACE)
        else:
            carb.log_warn(f"Movie capture: Unknown render mode: {render_mode}")

    def _on_render_mode_in_viewport_changed(self, item, event_type):
        if self._is_capturing():
            return
        if self._active_render == "iray":
            return

        render_mode = self._settings.get("/rtx/rendermode") if item is None else self._dict.get(item)
        self._set_render_preset_from_mode(render_mode)

    def _on_active_render_in_viewport_changed(self, item, event_type):
        if self._is_capturing():
            return
        self._active_render = self._dict.get(item)
        if self._active_render == "iray":
            self._set_current_render_mode_selection(omni.kit.capture.viewport.CaptureRenderPreset.IRAY)

    def _on_render_preset_settings_clicked(self):
        render_preset = self._get_selected_render_preset()
        if render_preset == omni.kit.capture.viewport.CaptureRenderPreset.PATH_TRACE:
            self.show_render_settings("Path-Traced")
        elif render_preset == omni.kit.capture.viewport.CaptureRenderPreset.RAY_TRACE:
            self.show_render_settings("Real-Time")
        else:  # expected to be iray as it's the only one option left for selection
            self.show_render_settings("Iray")

    def _on_render_preset_refresh_clicked(self):
        self._refresh_render_products()

    def collect_settings(self, options: omni.kit.capture.viewport.capture_options.CaptureOptions):
        options.render_preset = self._get_selected_render_preset()
        options.spp_per_iteration = self._ui_spp_per_iteration_input.value
        if self._ui_render_product_area.visible is True and self._ui_use_render_product_check.model.as_bool is True:
            rp_string = self._get_combobox_string_value(self._ui_render_product)
            if len(rp_string) > 0:
                options.render_product = rp_string
            else:
                carb.log_warn("Movie Capture: render product capture is enabled but no render product is selected so will not do render product capture.")
                options.render_product = ""
        else:
            options.render_product = ""
        if self._ui_render_style_shaded.selected is True:
            options.debug_material_type = omni.kit.capture.viewport.CaptureDebugMaterialType.SHADED
        else:
            options.debug_material_type = omni.kit.capture.viewport.CaptureDebugMaterialType.WHITE
        if options.render_preset == omni.kit.capture.viewport.CaptureRenderPreset.PATH_TRACE:
            options.path_trace_spp = self._ui_spp_input.value
            if self._ui_kit_motion_blur_check.model.as_bool is True:
                options.ptmb_subframes_per_frame = self._ui_ptmb_spf_input.value
                options.ptmb_fso = self._ui_ptmb_fso_input.value
                options.ptmb_fsc = self._ui_ptmb_fsc_input.value
            else:
                options.ptmb_subframes_per_frame = 1
                options.ptmb_fso = 0.0
                options.ptmb_fsc = 0.0
        elif options.render_preset == omni.kit.capture.viewport.CaptureRenderPreset.IRAY:
            options.path_trace_spp = self._ui_iray_spp_input.value
            if self._ui_kit_motion_blur_check.model.as_bool is True:
                options.ptmb_subframes_per_frame = self._ui_ptmb_spf_input.value
                options.ptmb_fso = self._ui_ptmb_fso_input.value
                options.ptmb_fsc = self._ui_ptmb_fsc_input.value
            else:
                options.ptmb_subframes_per_frame = 1
                options.ptmb_fso = 0.0
                options.ptmb_fsc = 0.0
        else:
            options.path_trace_spp = 1
            options.ptmb_subframes_per_frame = 1
            options.ptmb_fso = 0
            options.ptmb_fsc = 1
        # Common
        options.real_time_settle_latency_frames = self._ui_common_settle_latency_input.value

    def get_ui_values(self, ui_values: UIValuesStorage):
        global RENDER_PRESETS
        ui_values.set(UIValuesStorage.SETTING_NAME_RENDER_STYLE, self._ui_render_style_shaded.selected)
        ui_values.set(UIValuesStorage.SETTING_NAME_RENDER_PRESET, RENDER_PRESETS[self._get_selected_render_preset()])
        ui_values.set(UIValuesStorage.SETTING_NAME_REALTIME_SETTLE_LATENCY, self._ui_common_settle_latency_input.value)
        ui_values.set(UIValuesStorage.SETTING_NAME_PATHTRACE_SPP_PER_ITERATION_MGPU, self._ui_spp_per_iteration_input.value)
        ui_values.set(UIValuesStorage.SETTING_NAME_PATHTRACE_SPP_PER_SUBFRAME, self._ui_spp_input.value)
        ui_values.set(UIValuesStorage.SETTING_NAME_PATHTRACE_ENABLE_MB_CHECKED, self._ui_kit_motion_blur_check.model.as_bool)
        ui_values.set(UIValuesStorage.SETTING_NAME_PATHTRACE_MB_SUBFRAMES, self._pt_last_subframes_per_frame_value)
        ui_values.set(UIValuesStorage.SETTING_NAME_PATHTRACE_MB_FRAME_SHUTTER_OPEN, self._ui_ptmb_fso_input.value)
        ui_values.set(UIValuesStorage.SETTING_NAME_PATHTRACE_MB_FRAME_SHUTTER_CLOSE, self._ui_ptmb_fsc_input.value)
        ui_values.set(UIValuesStorage.SETTING_NAME_IRAY_PATHTRACE_SPP, self._ui_iray_spp_input.value)
        ui_values.set(UIValuesStorage.SETTING_NAME_IRAY_MB_SUBFRAMES, self._iray_last_subframes_per_frame_value)

    def apply_ui_values(self, ui_values: UIValuesStorage):
        self._ui_render_style_shaded.selected = ui_values.get(UIValuesStorage.SETTING_NAME_RENDER_STYLE)
        self._ui_render_style_white.selected = not self._ui_render_style_shaded.selected
        self._ui_common_settle_latency_input.value = ui_values.get(UIValuesStorage.SETTING_NAME_REALTIME_SETTLE_LATENCY)
        self._ui_spp_per_iteration_input.value = ui_values.get(UIValuesStorage.SETTING_NAME_PATHTRACE_SPP_PER_ITERATION_MGPU)
        self._ui_spp_input.value = ui_values.get(UIValuesStorage.SETTING_NAME_PATHTRACE_SPP_PER_SUBFRAME)
        self._ui_kit_motion_blur_check.model.as_bool = ui_values.get(UIValuesStorage.SETTING_NAME_PATHTRACE_ENABLE_MB_CHECKED)
        self._pt_last_subframes_per_frame_value = ui_values.get(UIValuesStorage.SETTING_NAME_PATHTRACE_MB_SUBFRAMES)
        self._ui_ptmb_fso_input.value = ui_values.get(UIValuesStorage.SETTING_NAME_PATHTRACE_MB_FRAME_SHUTTER_OPEN)
        self._ui_ptmb_fsc_input.value = ui_values.get(UIValuesStorage.SETTING_NAME_PATHTRACE_MB_FRAME_SHUTTER_CLOSE)
        self._ui_iray_spp_input.value = ui_values.get(UIValuesStorage.SETTING_NAME_IRAY_PATHTRACE_SPP)

        # in case we're reading options from old versions of data then it doesn't have subframes value for Iray
        # thus we don't read and use bad data, and keep using the value we have already
        iray_last_subframes_per_frame_value = ui_values.get(UIValuesStorage.SETTING_NAME_IRAY_MB_SUBFRAMES)
        if iray_last_subframes_per_frame_value is not None:
            self._iray_last_subframes_per_frame_value = iray_last_subframes_per_frame_value

        # setting render preset will trigger render_preset_changed callback to set the subframe value read above for Iray or PT
        self._choose_render_preset(ui_values.get(UIValuesStorage.SETTING_NAME_RENDER_PRESET))
