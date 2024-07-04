"""
| File: movie_capture_widget.py
| Author: Ji Sue Lee (brunoleej@gmail.com)
| License: BSD-3-Clause. Copyright (c) 2024, Ji Sue Lee. All rights reserved.
| Description: Definition of the UiDelegate which is an abstraction layer betweeen the extension UI and code logic features
"""

__all__ = ["MovieCaptureWidget"]

import os
import json
import carb
import omni
import omni.ui as ui
from omni.mobile.robots.params import output_default_path, RECORD_TYPE, TYPE_INDEX_OF_PNG, CAPTURE_FILE_TYPES
from omni.mobile.robots.ui.widgets.custom_multifield_widget import CustomMultifieldWidget
from omni.mobile.robots.ui.widgets.custom_env_combo_widget import RecordEnvComboboxWidget
from omni.mobile.robots.ui.widgets.custom_bool_widget import CustomBoolWidget

from . import base_widget
from .quick_input import QuickNumberInput, QuickNumberInputType
from .ui_values_storage import UIValuesStorage 


###################### Capture_settings_widget ######################
CAPTURE_RANGE_TYPES = (omni.kit.capture.viewport.CaptureRangeType.FRAMES, omni.kit.capture.viewport.CaptureRangeType.SECONDS)
CAPTURE_RENDER_PRESET = (
    omni.kit.capture.viewport.CaptureRenderPreset.PATH_TRACE,
    omni.kit.capture.viewport.CaptureRenderPreset.RAY_TRACE,
)

CAPTURE_RES_RATIO = ["16:9", "4:3"]
DEFAULT_VIDEO_SECONDS = 2
DEFAULT_NTH_FRAME = 20
DEFAULT_FPS_SETTING_PATH = "/exts/omni.kit.window.movie_capture/default_fps"
FPS_LIST_SETTING_PATH = "/exts/omni.kit.window.movie_capture/fps_list"
SUNSTUDY_EXT_NAME = "omni.kit.environment.sunstudy"
SEQUENCE_TYPE_DESC = "Sequence"
SUNSTUDY_TYPE_DESC = "Sunstudy"
###################### Capture_settings_widget ######################


class MovieCaptureWidget(base_widget.BaseMovieCaptureWidget):
    def __init__(self):
        super(MovieCaptureWidget, self).__init__()
        self._spacing = 3
        self._title = "RECORDING LAYOUT"
        
        ###################### Capture_settings_widget ######################
        self._appwindow = omni.appwindow.get_default_app_window()
        self._timeline = omni.timeline.get_timeline_interface()
        self._res_linked = True
        self._is_res_hd = False
        self._start_time = 6.0
        self._end_time = 18.0
        self._current_time = 12.0
        self._sunstudy_player = None
        self._sunstudy_widgets_built = False
        self._animation_fps_model = None
        
        self._stage_sub = self._usd_context.get_stage_event_stream().create_subscription_to_pop(
            self._on_stage, name="movie capture stage update"
        )
        
        self._fps_setting_changed_sub = self._settings.subscribe_to_node_change_events(
            DEFAULT_FPS_SETTING_PATH, self._on_fps_setting_changed
        )
        self._dict = carb.dictionary.get_dictionary()
        ###################### Capture_settings_widget ######################
    
    def _on_fps_setting_changed(self, item, event_type):
        fps = self._dict.get(item)
        self._animation_fps_model.set_current_fps(fps)
    
    def _on_stage(self, stage_event):
        stage = self._usd_context.get_stage()
        if stage and stage_event.type == int(omni.usd.StageEventType.OPENED):
            self._on_stage_opened()
    
    def _on_stage_opened(self):
        self._kit_update_time_range()
    
    def destroy(self):
        self._stage_sub = None
        self._settings.unsubscribe_to_change_events(self._fps_setting_changed_sub)
        self._camera_combo_model.clear()
        self._camera_combo_model = None
        self._animation_fps_model.clear()
        self._animation_fps_model = None
    
    def update_widgets_for_new_movie_type(self, movie_type: omni.kit.capture.viewport.CaptureMovieType):
        self._ui_capture_range_sequence.visible = movie_type == omni.kit.capture.viewport.CaptureMovieType.SEQUENCE
        self._ui_capture_range_sunstudy.visible = movie_type == omni.kit.capture.viewport.CaptureMovieType.SUNSTUDY
    
    def refresh_movie_types(self):
        self._refresh_list()
        if self._sunstudy_player is not None and self._sunstudy_widgets_built is False:
            self._build_ui_capture_range_sunstudy()
    
    ############################ Main ############################
    def _build_ui_capture_settings(self):
        with ui.CollapsableFrame(title=self._title, name="robot_selection"):
            with ui.VStack(height=0, spacing=7, name="frame_v_stack"):
                ui.Line(style_type_name_override="HeaderLine")
                ui.Spacer(height = 0)   # 5
                
                self._build_ui_movie_type_settings()
                with ui.HStack(width=400):
                    ui.Label("Camera")
                    with ui.ZStack(width=300):
                        ui.Rectangle(name="combobox", height=22)
                        self._camera_combo_model = base_widget.CamerasModel()
                        self._ui_kit_combobox_camera_type = ui.ComboBox(self._camera_combo_model, name="dropdown_menu", identifier="cap_setting_id_combo_camera_type")
                        self._ui_kit_combobox_camera_type.model.add_item_changed_fn(self._on_kit_camera_changed)
                        ui.Spacer(width=base_widget.RIGHT_SPACING)
                ui.Spacer()
                self._build_ui_capture_range_settings()
                self._build_ui_capture_resolution_settings()
                self._build_ui_app_level_capture_settings()

                # self._render_ui()
                # ui.Spacer(spacing=self._spacing)
                
                # self._queue_setting_ui()
                # ui.Spacer(spacing=self._spacing)
                
                # self._output_ui(file_path=output_default_path)
                # ui.Spacer(spacing=self._spacing)
    
    def _build_ui_app_level_capture_settings(self):
        with ui.HStack(width=260):
            ui.Label("Capture Application")
            with ui.HStack(width=0, tooltip="To capture scene elements, it will show the viewport only and hide other UI parts during capture, e.g. title and menu bars."):
                with ui.VStack(width=0):
                    ui.Spacer()
                    self._ui_kit_capture_app_check = ui.CheckBox(height=0, name="green_check", identifier="cap_setting_id_check_capture_app")
                    ui.Spacer()
                ui.Label(" *If checked, scene elements will be captured")
        ui.Spacer(height=base_widget.FRAME_SPACING)                
    
    def _build_ui_capture_range_settings(self):
        with ui.VStack():
            self._build_ui_capture_range()
            self._build_ui_preroll_frames()
            self._build_ui_capture_nth_frames()
            
    def _build_ui_capture_range(self):
        with ui.HStack(width=400):
            ui.Label("Frame Rate")
            
            with ui.ZStack(width=300):
                ui.Rectangle(name="combobox", height=22)
                self._animation_fps_model = base_widget.AnimationFpsModel()
                self._ui_kit_combobox_fps = ui.ComboBox(self._animation_fps_model, name="dropdown_menu", identifier="cap_setting_id_combo_fps")
                self._ui_kit_combobox_fps.model.add_item_changed_fn(self._on_kit_capture_fps_changed)
                self._capture_time_step = 1 / self._animation_fps_model.get_current_fps()
                ui.Spacer(width=base_widget.RIGHT_SPACING)
        ui.Spacer(height=base_widget.FRAME_SPACING * 2)
        self._ui_capture_range_sequence = ui.VStack()
        self._build_ui_capture_range_sequence()
        self._ui_capture_range_sunstudy = ui.VStack()
        self._build_ui_capture_range_sunstudy()
        self._ui_capture_range_sunstudy.visible = False
    
    def _build_ui_movie_type_settings(self):
        with ui.VStack(spacing=base_widget.FRAME_SPACING, height=0):
            with ui.HStack(width=412):      # width => 박스 위치 조정
                ui.Label("Movie Type")
                
                with ui.ZStack(width=300):  # width => 박스 길이 조정
                    ui.Rectangle(name="combobox", height=22)
                    self._ui_kit_combobox_movie_type = ui.ComboBox(0, "Sequence", "Sunstudy", name="dropdown_menu", identifier="cap_setting_id_combo_movie_type")
                    self._movie_type_changed_fn = self._ui_kit_combobox_movie_type.model.add_item_changed_fn(self._on_movie_type_changed)
                    self._refresh_list()
                ui.Spacer(width=base_widget.RIGHT_SPACING)
            ui.Spacer()
    
    def _build_ui_capture_range_sequence(self):
        with self._ui_capture_range_sequence:
            with ui.HStack(width=400):
                ui.Label("Capture Range")

                with ui.ZStack(width=300):
                    ui.Rectangle(name="combobox", height=22)
                    self._ui_kit_combobox_range = ui.ComboBox(0, "Custom Range - Frames", "Custom Range - Seconds", name="dropdown_menu", identifier="cap_setting_id_combo_range")
                    self._ui_kit_combobox_range.model.add_item_changed_fn(self._on_kit_capture_range_changed)
                    ui.Spacer(width=base_widget.RIGHT_SPACING)
            ui.Spacer(height=base_widget.FRAME_SPACING)
            self._ui_kit_capture_range_input_frames = ui.HStack()
            self._buid_ui_frames_input()
            self._ui_kit_capture_range_input_seconds = ui.HStack()
            self._buid_ui_seconds_input()
            self._ui_kit_capture_range_input_seconds.visible = False
            self._build_ui_renumber_negative_frames()

    def _build_ui_renumber_negative_frames(self):
        with ui.HStack(height=5, width=0):  # checkbox 땡기기
            self._build_ui_left_column("")
            with ui.HStack(width=ui.Percent(30)):
                with ui.VStack(width=0):
                    ui.Spacer()
                    # self._ui_kit_renumber_negative_frames_check = ui.CheckBox(height=0, name="green_check", identifier="cap_setting_id_checkbox_renumber_negative_frames")
                    self._ui_kit_renumber_negative_frames_check = CustomBoolWidget(default_value=False)
                    ui.Spacer()
                # ui.Label(" Renumber negative frame numbers from 0")
            ui.Spacer()
    
    def _build_ui_capture_setting_time_of_day(self):
        if self._sunstudy_player is None:
            carb.log_warn("Movie Capture: Sunstudy player is not available so unable to create sunstudy widgets.")
        with ui.HStack():
            self._build_ui_left_column("Time of Day")
            with ui.VStack(spacing=base_widget.FRAME_SPACING):
                from omni.kit.environment.core import SunstudyTimeSlider
                self._ui_sunstudy_slider = SunstudyTimeSlider(self._sunstudy_player)
    
    def _build_ui_capture_setting_time_length(self):
        with ui.HStack():
            self._build_ui_left_column("")
            with ui.HStack(width=150):
                ui.Label(" Minutes", width=ui.Percent(46))
                ui.Label("  :", width=ui.Percent(8))
                ui.Label(" Seconds", width=ui.Percent(46))
        with ui.HStack():
            self._build_ui_left_column("Movie Length")
            with ui.HStack(width=150):
                self._ui_sunstudy_movie_length_minutes_input = QuickNumberInput(
                    input_type=QuickNumberInputType.INT,
                    init_value=1,
                    step=1,
                    min_value=0,
                    value_changed_fn=self._on_sunstudy_movie_length_minutes_input_changed,
                    identifier="cap_setting_id_drag_ss_movie_length_minutes",
                )
                ui.Label("  :", width=ui.Percent(8))
                self._ui_sunstudy_movie_length_seconds_input = QuickNumberInput(
                    input_type=QuickNumberInputType.INT,
                    init_value=1,
                    step=1,
                    max_value=59,
                    min_value=0,
                    value_changed_fn=self._on_sunstudy_movie_length_seconds_input_changed,
                    identifier="cap_setting_id_drag_ss_movie_length_seconds",
                )
                
    def _build_ui_capture_range_sunstudy(self):
        if self._sunstudy_player is not None and self._sunstudy_widgets_built is False:
            self._sunstudy_widgets_built = True
            with self._ui_capture_range_sunstudy:
                self._build_ui_capture_setting_time_of_day()
                ui.Spacer(height=base_widget.FRAME_SPACING * 2)
                self._build_ui_capture_setting_time_length()
    
    def _build_ui_preroll_frames(self):
        with ui.HStack():
            self._build_ui_left_column("")
            with ui.HStack(width=ui.Percent(50)):
                with ui.VStack(width=0):
                    ui.Spacer()
                    self._ui_kit_preroll_frames_check = ui.CheckBox(height=0, name="green_check", identifier="cap_setting_id_check_preroll_frames")
                    self._ui_kit_preroll_frames_check.model.add_value_changed_fn(self._on_preroll_frames_clicked)
                    ui.Spacer()
                self._ui_preroll_frame_input = QuickNumberInput(
                    input_type=QuickNumberInputType.INT,
                    init_value=200,
                    step=1,
                    beginning_text=" Run ",
                    ending_text=" frames before start",
                    min_value=1,
                    identifier="cap_setting_id_drag_preroll_frame_input",
                )
            ui.Spacer()
    
    def _build_ui_capture_nth_frames(self):
        with ui.HStack():
            self._build_ui_left_column("")
            with ui.HStack(width=ui.Percent(50)):
                with ui.VStack(width=0):
                    ui.Spacer()
                    self._ui_kit_nth_frames_check = ui.CheckBox(height=0, name="green_check", identifier="cap_setting_id_check_nth_frame")
                    self._ui_kit_nth_frames_check.model.add_value_changed_fn(self._on_nth_frames_clicked)
                    ui.Spacer()
                self._ui_nth_frame_input = QuickNumberInput(
                    input_type=QuickNumberInputType.INT,
                    init_value=DEFAULT_NTH_FRAME,
                    step=1,
                    beginning_text=" Capture every ",
                    ending_text="th frames",
                    min_value=1,
                    identifier="cap_setting_id_drag_nth_frame_input",
                )
            ui.Spacer()

    def _buid_ui_seconds_input(self):
        with self._ui_kit_capture_range_input_seconds:
            self._build_ui_left_column("")
            with ui.HStack(spacing=base_widget.FRAME_SPACING):
                ui.Label("Start ", width=0)
                self._ui_start_time_input = QuickNumberInput(
                    input_type=QuickNumberInputType.FLOAT,
                    init_value=0.0,
                    step=self._capture_time_step,
                    max_value=10.0,
                    value_changed_fn=self._on_start_time_input_changed,
                    identifier="cap_setting_id_drag_start_time_input",
                )
            with ui.HStack(spacing=base_widget.FRAME_SPACING):
                ui.Spacer(width=base_widget.FRAME_SPACING)
                ui.Label("End ", width=0)
                self._ui_end_time_input = QuickNumberInput(
                    input_type=QuickNumberInputType.FLOAT,
                    init_value=10.0,
                    step=self._capture_time_step,
                    min_value=0.0,
                    value_changed_fn=self._on_end_time_input_changed,
                    identifier="cap_setting_id_drag_end_time_input",
                )
            ui.Spacer(width=base_widget.RIGHT_SPACING)
    
    def _buid_ui_frames_input(self):
        with self._ui_kit_capture_range_input_frames:
            self._build_ui_left_column("")
            with ui.HStack(spacing=base_widget.FRAME_SPACING):
                ui.Label("Start ", width=0)
                self._ui_start_frame_input = QuickNumberInput(
                    input_type=QuickNumberInputType.INT,
                    init_value=1,
                    step=1,
                    max_value=40,
                    value_changed_fn=self._on_start_frame_input_changed,
                    identifier="cap_setting_id_drag_start_frame_input",
                )
            with ui.HStack(spacing=base_widget.FRAME_SPACING):
                ui.Spacer(width=base_widget.FRAME_SPACING)
                ui.Label("End ", width=0)
                self._ui_end_frame_input = QuickNumberInput(
                    input_type=QuickNumberInputType.INT,
                    init_value=40,
                    step=1,
                    min_value=1,
                    value_changed_fn=self._on_end_frame_input_changed,
                    identifier="cap_setting_id_drag_end_frame_input",
                )
            ui.Spacer(width=base_widget.RIGHT_SPACING)
    
    def _build_ui_capture_resolution_settings(self):
        with ui.HStack(width=400):
            ui.Label("Resolution")
            with ui.ZStack(width=300):
                ui.Rectangle(name="combobox", height=22)
                self._ui_kit_combobox_res_type = ui.ComboBox(1, "HD", "Custom", name="dropdown_menu", identifier="cap_setting_id_combo_res_type")
                self._is_res_hd = False
                self._ui_kit_combobox_res_type.model.add_item_changed_fn(self._on_res_type_changed)
                ui.Spacer(width=base_widget.RIGHT_SPACING)
        with ui.VStack(spacing=0):
            ui.Spacer(height=base_widget.FRAME_SPACING)
            with ui.HStack(width=400):
                ui.Label("")
                with ui.HStack(width=300):
                    ui.Label("Width", alignment=ui.Alignment.CENTER_BOTTOM, width=ui.Percent(28), style={"font-weight": "bold", "color": "lightsteelblue"})
                    ui.Spacer(width=ui.Percent(5))
                    ui.Label("Height", alignment=ui.Alignment.CENTER_BOTTOM, width=ui.Percent(42), style={"font-weight": "bold", "color": "lightsteelblue"})
                    ui.Spacer()
            with ui.HStack(width=400):
                ui.Label("")
                with ui.HStack(width=300):
                    self._ui_res_width_input=QuickNumberInput(
                        input_type=QuickNumberInputType.INT,
                        init_value=1920,
                        step=1,
                        min_value=1,
                        value_changed_fn=self._on_res_width_input_changed,
                        # name="choose_id",
                        identifier="cap_setting_id_drag_res_width_input",
                    )
                    self._ui_kit_res_link = ui.Button(
                        name="res_link",
                        width=35,
                        mouse_pressed_fn=lambda x, y, b, _: self._on_res_link_clicked(),
                        identifier="cap_setting_id_button_res_link",
                    )
                    
                    self._ui_res_height_input = QuickNumberInput(
                        input_type=QuickNumberInputType.INT,
                        init_value=1080,
                        step=1,
                        min_value=1,
                        value_changed_fn=self._on_res_height_input_changed,
                        identifier="cap_setting_id_drag_res_height_input",
                    )
                    ui.Spacer(width=base_widget.FRAME_SPACING)
                    with ui.VStack():
                        ui.Spacer(height=5)
                        with ui.ZStack():
                            ui.Rectangle(name="combobox", height=22)
                            self._ui_kit_res_ratio = ui.ComboBox(0, "16:9", "4:3", name="dropdown_menu", identifier="cap_setting_id_combo_res_ratio")
                            self._res_ratio_changed_fn = self._ui_kit_res_ratio.model.add_item_changed_fn(self._on_res_ratio_changed)
                    ui.Spacer(width=base_widget.RIGHT_SPACING)
    
    ##################### Start ################################
    # def _render_ui(self):
    #     with ui.CollapsableFrame(title="RENDERING", name="rendering_layout"):
    #         with ui.VStack(height=0, spacing=7, name="frame_v_stack"):
    #             ui.Line(style_type_name_override="HeaderLine")
    #             ui.Spacer(height = 0)   # 5

    #             with ui.HStack():
    #                 ui.Label("Render Style")
    #                 ui.Spacer(width=40)                    
                
    #             with ui.HStack():
    #                 ui.Label("Render Preset")
    #                 ui.Spacer(width=40)
                
    #             with ui.HStack():
    #                 ui.Label("Settle latency")
    #                 ui.Spacer(width=40)
    
    # def _queue_setting_ui(self):
    #     with ui.CollapsableFrame(title="QUEUE SETTINGS", name="queue_layout"):
    #         with ui.VStack(height=0, spacing=7, name="frame_v_stack"):
    #             ui.Line(style_type_name_override="HeaderLine")
    #             ui.Spacer(height = 0)   # 5

    #             with ui.HStack():
    #                 ui.Label("Render Style")
    #                 ui.Spacer(width=40)
                    
    #             with ui.HStack():
    #                 ui.Label("Render Preset")
    #                 ui.Spacer(width=40)
                    
    #             with ui.HStack():
    #                 ui.Label("Settle latency")
    #                 ui.Spacer(width=40)
    
    # def _output_ui(self, file_path):
    #     with ui.CollapsableFrame(title="OUTPUT", name="output_layout"):
    #         with ui.VStack(height=0, spacing=7, name="frame_v_stack"):
    #             ui.Line(style_type_name_override="HeaderLine")
    #             ui.Spacer(height = 0)   # 5

    #             with ui.HStack():
    #                 ui.Label("Path")
    #                 ui.Spacer(width=40)
    #                 self._ui_output_path = ui.StringField(name="StringField", width=330, height=0, alignment=ui.Alignment.LEFT_CENTER, identifier="output_setting_id_stringfield_path")
    #                 self._ui_output_path.model.set_value(file_path)

    #             with ui.HStack():
    #                 ui.Label("Name")
    #                 ui.Spacer(width=30)
                    
    #                 self._ui_kit_default_capture_name = ui.StringField(width=ui.Percent(50), height=0, name="path_field", identifier="output_setting_id_stringfield_default_capture_name")
    #                 self._ui_kit_default_capture_name.model.set_value("capture")
    #                 with ui.ZStack():
    #                     ui.Rectangle(name="combobox", height=22)
    #                     # self._ui_kit_combobox_res_type = ui.ComboBox(1, "HD", "Custom", name="dropdown_menu", identifier="cap_setting_id_combo_res_type")
    #                     self._ui_kit_capture_num_pattern = ui.ComboBox(0, ".# # # #", name="dropdown_menu", identifier="output_setting_id_combo_capture_num_pattern")
                    
    #                 with ui.ZStack():
    #                     ui.Rectangle(name="combobox", height=22)
    #                     self._ui_kit_capture_type = ui.ComboBox(TYPE_INDEX_OF_PNG, *CAPTURE_FILE_TYPES, name="dropdown_menu", identifier="output_setting_id_combo_capture_type")
    #                 # self._ui_kit_capture_type.model.add_item_changed_fn(self._on_kit_capture_type_changed)

                    
    #             with ui.HStack():
    #                 ui.Label("")
    #                 with ui.VStack(width=0):
    #                     ui.Spacer()
    #                     self._ui_kit_overwrite_existing_frames_check = ui.CheckBox(height=0, name="green_check", identifier="output_setting_id_check_overwrite_existing_frames")
    #                     self._overwrite_image_change_fn = self._ui_kit_overwrite_existing_frames_check.model.add_value_changed_fn(
    #                     self._on_overwrite_existing_frames_clicked)
    #                     ui.Spacer()
    #                 ui.Label(" Overwrite existing frame images")
    #             ui.Spacer()
                
    #             with ui.HStack():
    #                 ui.Label("")
    #                 self._top_container = ui.Stack(ui.Direction.LEFT_TO_RIGHT)
    #                 with self._top_container:
    #                     self._ui_capture_buttons = ui.HStack()
    #                     with self._ui_capture_buttons:
    #                         self._ui_kit_capture_sequence_button = ui.Button(
    #                             "Capture Sequence",
    #                             clicked_fn=self._on_capture_sequence_clicked,
    #                             style=SUBMIT_BUTTON_STYLE,
    #                             width=0,
    #                             identifier="output_setting_id_button_capture_sequence",
    #                         )
    #                         self._ui_kit_capture_button = ui.Button(
    #                             "Capture Current Frame",
    #                             clicked_fn=self._on_capture_current_frame_clicked,
    #                             style=SUBMIT_BUTTON_STYLE,
    #                             identifier="output_setting_id_button_capture_current_frame",
    #                             )
    #                         self._ui_kit_dispatch_button = ui.Button(
    #                 "Submit to Queue",
    #                 clicked_fn=self._on_dispatch_clicked,
    #                 style=SUBMIT_BUTTON_STYLE,
    #                 identifier="output_setting_id_button_submit_to_queue",
    #             )
                    
    ########################### Camera Capture Settings ###########################
    def _format_float_time(self, time):
        section = " PM"
        if time < 1.0:
            section = " AM"
            hour = 12
        elif time < 12.0:
            hour = int(time)
            section = " AM"
        elif time < 13.0:
            hour = int(time)
        else:
            hour = int(time) - 12

        minute = int((time - int(time)) * 60)
        return "{:2d}:{:02d} {}".format(hour, minute, section)

    def _get_sunstudy(self):
        if self._is_ext_enabled(SUNSTUDY_EXT_NAME):
            try:
                from omni.kit.environment.core import get_sunstudy_player, SunstudyTimeSlider
                ext_manager = omni.kit.app.get_app().get_extension_manager()
                self._sunstudy_player = get_sunstudy_player()
                self._start_time = self._sunstudy_player.start_time
                self._end_time = self._sunstudy_player.end_time
                self._current_time = self._sunstudy_player.current_time
            except Exception as e:
                carb.log_warn(f"{e}")
                carb.log_warn("Movie capture can't do sunstudy capture due to unable to load necessary extensions.")
                self._sunstudy_player = None
            return self._sunstudy_player is not None
        else:
            return False

    def _refresh_list(self):
        model = self._ui_kit_combobox_movie_type.model
        model.remove_item_changed_fn(self._movie_type_changed_fn)
        for item in model.get_item_children():
            model.remove_item(item)

        model.append_child_item(None, ui.SimpleStringModel(SEQUENCE_TYPE_DESC))
        if self._get_sunstudy():
            model.append_child_item(None, ui.SimpleStringModel(SUNSTUDY_TYPE_DESC))

        self._movie_type_changed_fn = model.add_item_changed_fn(self._on_movie_type_changed)

    def _get_selected_movie_type(self):
        model = self._ui_kit_combobox_movie_type.model
        index = model.get_item_value_model().as_int
        selected_value = model.get_item_value_model(model.get_item_children()[index]).as_string
        carb.log_warn(f"movie type changed to {selected_value}")
        movie_type = omni.kit.capture.viewport.CaptureMovieType.SEQUENCE
        if selected_value == SUNSTUDY_TYPE_DESC:
            movie_type = omni.kit.capture.viewport.CaptureMovieType.SUNSTUDY
        return movie_type

    def _on_sunstudy_movie_length_minutes_input_changed(self, model):
        if self._ui_sunstudy_movie_length_seconds_input.value == 0 and model.as_int == 0:
            model.as_int = 1

    def _on_sunstudy_movie_length_seconds_input_changed(self, model):
        if self._ui_sunstudy_movie_length_minutes_input.value == 0 and model.as_int == 0:
            model.as_int = 1

    def _on_sunstudy_start_changed(self, value):
        self._start_time = value
        if self._sunstudy_player is not None:
            self._sunstudy_player.start_time = self._start_time

    def _on_sunstudy_end_changed(self, value):
        self._end_time = value
        if self._sunstudy_player is not None:
            self._sunstudy_player.end_time = self._end_time

    def _on_sunstudy_current_changed(self, value):
        self._current_time = value
        if self._sunstudy_player is not None:
            self._sunstudy_player.current_time = self._current_time

    def _on_start_changed(self, start):
        if self._sunstudy_player is not None and not self._sunstudy_player._is_playing:
            self._start_time = start
            self._ui_sunstudy_slider.set_start(start)

    def _on_end_changed(self, end):
        if self._sunstudy_player is not None and not self._sunstudy_player._is_playing:
            self._end_time = end
            self._ui_sunstudy_slider.set_end(end)

    def _on_current_changed(self, current):
        if self._sunstudy_player is not None and not self._sunstudy_player._is_playing:
            self._current_time = current
            self._ui_sunstudy_slider.set_current(current)

    def _on_movie_type_changed(self, model, item):
        movie_type = self._get_selected_movie_type()
        self.update_widgets_for_new_movie_type(movie_type)

    def _on_kit_capture_range_changed(self, model, item):
        if model.get_item_value_model(item).as_int == omni.kit.capture.viewport.CaptureRangeType.FRAMES:
            self._ui_kit_capture_range_input_seconds.visible = False
            self._ui_kit_capture_range_input_frames.visible = True
        else:
            self._ui_kit_capture_range_input_seconds.visible = True
            self._ui_kit_capture_range_input_frames.visible = False
        self._kit_update_time_range()

    def _kit_update_time_range(self):
        if self._ui_kit_combobox_range.model.get_item_value_model().as_int == omni.kit.capture.viewport.CaptureRangeType.SECONDS:
            self._ui_start_time_input.value = self._timeline.get_start_time()
            end_time = self._timeline.get_end_time()
            if end_time <= self._timeline.get_start_time():
                end_time = self._timeline.get_start_time() + DEFAULT_VIDEO_SECONDS
            self._ui_end_time_input.value = end_time
        else:
            fps = self._animation_fps_model.get_current_fps()
            start_frame = self._timeline.get_start_time() * fps
            self._ui_start_frame_input.value = start_frame
            end_frame = self._timeline.get_end_time() * fps
            if end_frame <= start_frame:
                end_frame = start_frame + DEFAULT_VIDEO_SECONDS * fps
            self._ui_end_frame_input.value = end_frame

    def _on_kit_camera_changed(self, model, item):
        self._camera_combo_model.track_current_camera = False

    def _on_kit_capture_fps_changed(self, model, item):
        if self._animation_fps_model is None:
            return

        new_fps = self._animation_fps_model.get_current_fps()
        self._animation_fps_model.track_current_fps = False

        # update start/end frames
        # we don't change the start/end time because only the number of frames will change as a result of the FPS change, animation time won't change
        # Since the input fields have checks to ensure start value is not greater than end value, we also need to check before updating
        # Please also note that since the capture range may not be divided evenly by the new fps, there might be additional frames added to make it up
        new_start_frame = round(self._ui_start_frame_input.value * self._capture_time_step * new_fps)
        new_end_frame = round(self._ui_end_frame_input.value * self._capture_time_step * new_fps)
        if new_start_frame >= self._ui_end_frame_input.value:
            self._ui_end_frame_input.value = new_end_frame
            self._ui_start_frame_input.value = new_start_frame
        else:
            self._ui_start_frame_input.value = new_start_frame
            self._ui_end_frame_input.value = new_end_frame

        self._capture_time_step = 1.0 / new_fps
        self._ui_start_time_input.step = self._capture_time_step
        self._ui_end_time_input.step = self._capture_time_step

    def _on_preroll_frames_clicked(self, model):
        pass

    def _on_nth_frames_clicked(self, model):
        pass

    def _on_ptmb_fso_input_changed(self, model):
        self._ui_ptmb_fsc_input.min = model.as_float

    def _on_ptmb_fsc_input_changed(self, model):
        self._ui_ptmb_fso_input.max = model.as_float

    def _on_start_frame_input_changed(self, model):
        if model.as_int > self._ui_end_frame_input.value:
            model.as_int = self._ui_end_frame_input.value
            self._ui_start_frame_input.max = model.as_int
        self._ui_end_frame_input.min = model.as_int

    def _on_end_frame_input_changed(self, model):
        if model.as_int < self._ui_start_frame_input.value:
            model.as_int = self._ui_start_frame_input.value
            self._ui_end_frame_input.min = model.as_int
        self._ui_start_frame_input.max = model.as_int

    def _on_start_time_input_changed(self, model):
        if model.as_float > self._ui_end_time_input.value:
            model.as_float = self._ui_end_time_input.value
            self._ui_start_time_input.max = model.as_float
        self._ui_end_time_input.min = model.as_float

    def _on_end_time_input_changed(self, model):
        if model.as_float < self._ui_start_time_input.value:
            model.as_float = self._ui_start_time_input.value
            self._ui_end_time_input.min = model.as_float
        self._ui_start_time_input.max = model.as_float

    def _on_res_width_input_changed(self, model):
        self._ensure_custom_res()
        if self._res_linked:
            self._ui_res_height_input.value_changed_fn = None
            global CAPTURE_RES_RATIO
            aspect_ration = self._get_combobox_value(self._ui_kit_res_ratio, CAPTURE_RES_RATIO)
            width = self._ui_res_width_input.value
            if aspect_ration == "16:9":
                self._ui_res_height_input.value = int(width * 9.0 / 16.0)
            elif aspect_ration == "4:3":
                self._ui_res_height_input.value = int(width * 3.0 / 4.0)
            else:
                self._ui_res_height_input.value = int(width * self._custom_res_height / self._custom_res_with)
            self._ui_res_height_input.value_changed_fn = self._on_res_height_input_changed
        else:
            self._refresh_res_ratio_options()

    def _on_res_height_input_changed(self, model):
        self._ensure_custom_res()
        if self._res_linked:
            self._ui_res_width_input.value_changed_fn = None
            global CAPTURE_RES_RATIO
            aspect_ration = self._get_combobox_value(self._ui_kit_res_ratio, CAPTURE_RES_RATIO)
            height = self._ui_res_height_input.value
            if aspect_ration == "16:9":
                self._ui_res_width_input.value = int(height * 16.0 / 9.0)
            elif aspect_ration == "4:3":
                self._ui_res_width_input.value = int(height * 4.0 / 3.0)
            else:
                self._ui_res_width_input.value = int(height * self._custom_res_with / self._custom_res_height)
            self._ui_res_width_input.value_changed_fn = self._on_res_width_input_changed
        else:
            self._refresh_res_ratio_options()

    def _refresh_res_ratio_options(self):
        model = self._ui_kit_res_ratio.model
        model.remove_item_changed_fn(self._res_ratio_changed_fn)
        for item in model.get_item_children():
            model.remove_item(item)

        self._custom_res_with = self._ui_res_width_input.value
        self._custom_res_height = self._ui_res_height_input.value
        if self._custom_res_with >= self._custom_res_height:
            r = self._custom_res_with / self._custom_res_height
            s = "{:.3f}:1".format(r)
        else:
            r = self._custom_res_height / self._custom_res_with
            s = "1:{:.3f}".format(r)
        global CAPTURE_RES_RATIO
        CAPTURE_RES_RATIO = [s, "16:9", "4:3"]

        model.append_child_item(None, ui.SimpleStringModel(s))
        model.append_child_item(None, ui.SimpleStringModel("16:9"))
        model.append_child_item(None, ui.SimpleStringModel("4:3"))
        model.get_item_value_model().set_value(0)
        self._res_ratio_changed_fn = model.add_item_changed_fn(self._on_res_ratio_changed)

    def _set_res_for_hd(self):
        # 2 items means there is no custom aspect ratio, otherwise the first one is the custom ratio
        if len(self._ui_kit_res_ratio.model.get_item_children()) == 2:
            self._ui_kit_res_ratio.model.get_item_value_model().set_value(0)
        else:
            self._ui_kit_res_ratio.model.get_item_value_model().set_value(1)

        self._ui_res_width_input.value = 1920
        self._ui_res_height_input.value = 1080

    def _on_res_type_changed(self, model, item):
        if model.get_item_value_model(item).as_int == 0:
            self._is_res_hd = True
            self._set_res_for_hd()
        else:
            self._is_res_hd = False

    def _ensure_custom_res(self):
        if self._is_res_hd:
            carb.log_warn(
                "Current resolution is HD, which requires width=1920 and height=1080. Switching to Custom to allow customized resolutions."
            )
            self._ui_kit_combobox_res_type.model.get_item_value_model().set_value(1)
            self._is_res_hd = False

    def _on_res_ratio_changed(self, model, item):
        self._ensure_custom_res()

        if self._res_linked:
            self._on_res_width_input_changed(None)

    def _on_res_link_clicked(self):
        self._res_linked = not self._res_linked
        if self._res_linked:
            self._ui_kit_res_link.name = "res_link"
            self._on_res_width_input_changed(None)
        else:
            self._ui_kit_res_link.name = "res_unlink"

    def _read_sequence_capture_settings(self, options: omni.kit.capture.viewport.capture_options.CaptureOptions):
        options.range_type = self._get_combobox_value(self._ui_kit_combobox_range, CAPTURE_RANGE_TYPES)
        if options.range_type == omni.kit.capture.viewport.CaptureRangeType.FRAMES:
            options.start_frame = self._ui_start_frame_input.value
            options.end_frame = self._ui_end_frame_input.value
            if options.start_frame < 0:
                options.renumber_negative_frame_number_from_0 = self._ui_kit_renumber_negative_frames_check.model.as_bool
            else:
                options.renumber_negative_frame_number_from_0 = False
                if self._ui_kit_renumber_negative_frames_check.model.as_bool:
                    carb.log_warn("Movie capture will only renumber negative frame numbers. This renumber option will be ignored.")
        else:
            options.start_time = self._ui_start_time_input.value
            options.end_time = self._ui_end_time_input.value
            if options.start_time < 0:
                options.renumber_negative_frame_number_from_0 = self._ui_kit_renumber_negative_frames_check.model.as_bool
            else:
                options.renumber_negative_frame_number_from_0 = False
                if self._ui_kit_renumber_negative_frames_check.model.as_bool:
                    carb.log_warn("Movie capture will only renumber negative frame numbers. This renumber option will be ignored.")

    def _read_sunstudy_capture_settings(self, options: omni.kit.capture.viewport.capture_options.CaptureOptions):
        options.range_type = omni.kit.capture.viewport.CaptureRangeType.FRAMES
        options.sunstudy_start_time = self._sunstudy_player.start_time
        options.sunstudy_current_time = self._sunstudy_player.current_time
        options.sunstudy_end_time = self._sunstudy_player.end_time
        minutes = self._ui_sunstudy_movie_length_minutes_input.value
        seconds = self._ui_sunstudy_movie_length_seconds_input.value
        options.sunstudy_movie_length_in_seconds = minutes * 60 + seconds
        options.start_frame = 0
        options.end_frame = options.fps * options.sunstudy_movie_length_in_seconds
        options.sunstudy_player = self._sunstudy_player

    def collect_settings(self, options: omni.kit.capture.viewport.capture_options.CaptureOptions):
        options.movie_type = self._get_selected_movie_type()
        options.camera = self._camera_combo_model.get_current_camera()
        # set both movie encoding fps and animation fps to the same value for now, until we make decision on
        # whether to allow a differenct movie encoding fps or not.
        options.animation_fps = self._animation_fps_model.get_current_fps()
        options.fps = self._animation_fps_model.get_current_fps()

        if options.movie_type == omni.kit.capture.viewport.CaptureMovieType.SEQUENCE:
            self._read_sequence_capture_settings(options)
        elif options.movie_type == omni.kit.capture.viewport.CaptureMovieType.SUNSTUDY:
            self._read_sunstudy_capture_settings(options)
        else:
            carb.log_warn(f"Unsupported movie type {options.movie_type}. Please check the capture settings.")

        if self._ui_kit_preroll_frames_check.model.as_bool:
            options.preroll_frames = self._ui_preroll_frame_input.value
        else:
            options.preroll_frames = 0

        options.res_width = self._ui_res_width_input.value
        options.res_height = self._ui_res_height_input.value
        if self._ui_kit_nth_frames_check.model.as_bool == True:
            options.capture_every_Nth_frames = self._ui_nth_frame_input.value
        else:
            options.capture_every_Nth_frames = -1

        options.app_level_capture = self._ui_kit_capture_app_check.model.as_bool

    def get_ui_values(self, ui_values: UIValuesStorage):
        ui_values.set(
            UIValuesStorage.SETTING_NAME_MOVIE_TYPE,
            self._get_combobox_string_value(self._ui_kit_combobox_movie_type)
        )
        ui_values.set(
            UIValuesStorage.SETTING_NAME_CAMERA_NAME,
            self._camera_combo_model.get_current_camera()
        )
        # set both movie encoding fps and animation fps to the same value for now, until we make decision on
        # whether to allow a differenct movie encoding fps or not.
        ui_values.set(
            UIValuesStorage.SETTING_NAME_FPS,
            self._animation_fps_model.get_current_fps()
        )
        ui_values.set(
            UIValuesStorage.SETTING_NAME_ANIMATION_FPS,
            self._animation_fps_model.get_current_fps()
        )
        ui_values.set(
            UIValuesStorage.SETTING_NAME_CAPTURE_RANGE,
            self._get_combobox_string_value(self._ui_kit_combobox_range)
        )
        ui_values.set(
            UIValuesStorage.SETTING_NAME_CAPTURE_FRAME_START,
            self._ui_start_frame_input.value
        )
        ui_values.set(
            UIValuesStorage.SETTING_NAME_CAPTURE_FRAME_END,
            self._ui_end_frame_input.value
        )
        ui_values.set(
            UIValuesStorage.SETTING_NAME_CAPTURE_RANGE,
            self._get_combobox_string_value(self._ui_kit_combobox_range)
        )
        ui_values.set(
            UIValuesStorage.SETTING_NAME_CAPTURE_TIME_START,
            self._ui_start_time_input.value
        )
        ui_values.set(
            UIValuesStorage.SETTING_NAME_CAPTURE_TIME_END,
            self._ui_end_time_input.value
        )
        ui_values.set(
            UIValuesStorage.SETTING_NAME_RENUMBER_NEGATIVE_FRAMES_CHECKED,
            self._ui_kit_renumber_negative_frames_check.model.as_bool
        )
        ui_values.set(
            UIValuesStorage.SETTING_NAME_RUN_N_FRAMES_CHECKED,
            self._ui_kit_preroll_frames_check.model.as_bool
        )
        ui_values.set(
            UIValuesStorage.SETTING_NAME_RUN_N_FRAMES,
            self._ui_nth_frame_input.value
        )
        ui_values.set(
            UIValuesStorage.SETTING_NAME_CAPTURE_EVERY_NTH_FRAMES_CHECKED,
            self._ui_kit_nth_frames_check.model.as_bool
        )
        ui_values.set(
            UIValuesStorage.SETTING_NAME_CAPTURE_EVERY_NTH_FRAMES,
            self._ui_nth_frame_input.value
        )
        ui_values.set(
            UIValuesStorage.SETTING_NAME_RESOLUTION_TYPE,
            self._get_combobox_string_value(self._ui_kit_combobox_res_type)
        )
        ui_values.set(
            UIValuesStorage.SETTING_NAME_RESOLUTION_WIDTH,
            self._ui_res_width_input.value
        )
        ui_values.set(
            UIValuesStorage.SETTING_NAME_RESOLUTION_HEIGHT,
            self._ui_res_height_input.value
        )
        ui_values.set(
            UIValuesStorage.SETTING_NAME_RESOLUTION_W_H_LINKED,
            self._res_linked
        )
        ui_values.set(
            UIValuesStorage.SETTING_NAME_ASPECT_RATIOS,
            self._get_combobox_all_string_values(self._ui_kit_res_ratio)
        )
        ui_values.set(
            UIValuesStorage.SETTING_NAME_ASPECT_RATIO_SELECTED,
            self._ui_kit_res_ratio.model.get_item_value_model().as_int
        )
        ui_values.set(
            UIValuesStorage.SETTING_NAME_CAPTURE_APPLICATION,
            self._ui_kit_capture_app_check.model.as_bool
        )

        # sunstudy settings
        if self._sunstudy_widgets_built:
            ui_values.set(UIValuesStorage.SETTING_NAME_SUNSTUDY_START, self._ui_sunstudy_slider.get_start())
            ui_values.set(UIValuesStorage.SETTING_NAME_SUNSTUDY_CURRENT, self._ui_sunstudy_slider.get_current())
            ui_values.set(UIValuesStorage.SETTING_NAME_SUNSTUDY_END, self._ui_sunstudy_slider.get_end())
            ui_values.set(UIValuesStorage.SETTING_NAME_SUNSTUDY_MOVIE_MINUTES, self._ui_sunstudy_movie_length_minutes_input.value)
            ui_values.set(UIValuesStorage.SETTING_NAME_SUNSTUDY_MOVIE_SECONDS, self._ui_sunstudy_movie_length_seconds_input.value)
        else:
            ui_values.set(UIValuesStorage.SETTING_NAME_SUNSTUDY_START, 6.0)
            ui_values.set(UIValuesStorage.SETTING_NAME_SUNSTUDY_CURRENT, 12.0)
            ui_values.set(UIValuesStorage.SETTING_NAME_SUNSTUDY_END, 18.0)
            ui_values.set(UIValuesStorage.SETTING_NAME_SUNSTUDY_MOVIE_MINUTES, 1)
            ui_values.set(UIValuesStorage.SETTING_NAME_SUNSTUDY_MOVIE_SECONDS, 1)

    def apply_ui_values(self, ui_values: UIValuesStorage):
        self._set_combobox_string_value(
            self._ui_kit_combobox_movie_type,
            ui_values.get(UIValuesStorage.SETTING_NAME_MOVIE_TYPE)
        )
        self._camera_combo_model.set_current_camera(
            ui_values.get(UIValuesStorage.SETTING_NAME_CAMERA_NAME)
        )
        # since movie encoding fps is the same to animation fps for now, don't need to read it back
        # *need to read it back after we decide to allow movie encoding fps to be a different value
        self._animation_fps_model.set_current_fps(ui_values.get(UIValuesStorage.SETTING_NAME_ANIMATION_FPS, 30))
        self._set_combobox_string_value(
            self._ui_kit_combobox_range,
            ui_values.get(UIValuesStorage.SETTING_NAME_CAPTURE_RANGE)
        )
        self._ui_start_frame_input.value = ui_values.get(UIValuesStorage.SETTING_NAME_CAPTURE_FRAME_START)
        self._ui_end_frame_input.value = ui_values.get(UIValuesStorage.SETTING_NAME_CAPTURE_FRAME_END)
        self._ui_start_time_input.value = ui_values.get(UIValuesStorage.SETTING_NAME_CAPTURE_TIME_START)
        self._ui_end_time_input.value = ui_values.get(UIValuesStorage.SETTING_NAME_CAPTURE_TIME_END)
        self._ui_kit_renumber_negative_frames_check.model.as_bool = ui_values.get(UIValuesStorage.SETTING_NAME_RENUMBER_NEGATIVE_FRAMES_CHECKED)
        self._ui_kit_preroll_frames_check.model.as_bool = ui_values.get(UIValuesStorage.SETTING_NAME_RUN_N_FRAMES_CHECKED)
        self._ui_preroll_frame_input.value = ui_values.get(UIValuesStorage.SETTING_NAME_RUN_N_FRAMES)
        self._ui_kit_nth_frames_check.model.as_bool = ui_values.get(UIValuesStorage.SETTING_NAME_CAPTURE_EVERY_NTH_FRAMES_CHECKED)
        self._ui_nth_frame_input.value = ui_values.get(UIValuesStorage.SETTING_NAME_CAPTURE_EVERY_NTH_FRAMES)

        self._ui_res_width_input.value = ui_values.get(UIValuesStorage.SETTING_NAME_RESOLUTION_WIDTH)
        self._ui_res_height_input.value = ui_values.get(UIValuesStorage.SETTING_NAME_RESOLUTION_HEIGHT)
        self._res_linked = ui_values.get(UIValuesStorage.SETTING_NAME_RESOLUTION_W_H_LINKED)
        if self._res_linked:
            self._ui_kit_res_link.name = "res_link"
            self._on_res_width_input_changed(None)
        else:
            self._ui_kit_res_link.name = "res_unlink"

        model = self._ui_kit_res_ratio.model
        model.remove_item_changed_fn(self._res_ratio_changed_fn)
        for item in model.get_item_children():
            model.remove_item(item)
        ratio_index = 0
        aspect_ratios = json.loads(ui_values.get(UIValuesStorage.SETTING_NAME_ASPECT_RATIOS))
        while ratio_index < len(aspect_ratios):
            model.append_child_item(None, ui.SimpleStringModel(aspect_ratios[ratio_index]))
            ratio_index += 1
        model.get_item_value_model().set_value(ui_values.get(UIValuesStorage.SETTING_NAME_ASPECT_RATIOS))
        self._res_ratio_changed_fn = model.add_item_changed_fn(self._on_res_ratio_changed)
        self._set_combobox_string_value(
            self._ui_kit_combobox_res_type,
            ui_values.get(UIValuesStorage.SETTING_NAME_RESOLUTION_TYPE)
        )

        self._ui_kit_capture_app_check.model.as_bool = ui_values.get(UIValuesStorage.SETTING_NAME_CAPTURE_APPLICATION, False)

        # sunstudy settings
        if self._sunstudy_widgets_built:
            try:
                self._ui_sunstudy_slider.set_start(ui_values.get(UIValuesStorage.SETTING_NAME_SUNSTUDY_START))
                self._ui_sunstudy_slider.set_current(ui_values.get(UIValuesStorage.SETTING_NAME_SUNSTUDY_CURRENT))
                self._ui_sunstudy_slider.set_end(ui_values.get(UIValuesStorage.SETTING_NAME_SUNSTUDY_END))
                self._ui_sunstudy_movie_length_minutes_input.value = ui_values.get(UIValuesStorage.SETTING_NAME_SUNSTUDY_MOVIE_MINUTES)
                self._ui_sunstudy_movie_length_seconds_input.value = ui_values.get(UIValuesStorage.SETTING_NAME_SUNSTUDY_MOVIE_SECONDS)
            except Exception as e:
                carb.log_warn(f"{e}")
                fact = "Movie capture: failed to read UI settings for sunstudy from stage. "
                reason = "It may be caused by the usd was saved with older versions of movie capture. "
                fix = "It can be fixed by capturing and resaving the stage."
                carb.log_warn(f"{fact}{reason}{fix}")
