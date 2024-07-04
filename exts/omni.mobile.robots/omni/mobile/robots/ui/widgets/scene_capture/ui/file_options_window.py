# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import carb
import omni.ui as ui
from omni.kit.window.movie_capture.base_widget import WINDOW_DARK_STYLE, FRAME_SPACING, RIGHT_SPACING
from omni.kit.window.movie_capture.moive_capture_icons import MovieCaptureIcons
from omni.kit.window.movie_capture.file_options import FileOptions
from omni.kit.window.movie_capture.quick_input import QuickNumberInput, QuickNumberInputType


class FileOptionsWindow:

    WINDOW_NAME = "Movie Capture File Options"
    WINDOW_WIDTH = 440
    WINDOW_HEIGHT = 160
    WINDOW_HEIGHT_EXR = 240
    LEFT_SPACING = 20

    def __init__(self):
        self._init()

    def _init(self):
        self.__file_type = ".png"
        self.__window = None
        self.__options = None

    def _collect_common_options(self):
        self.__options.set_option(FileOptions.OPTION_FILE_TYPE, self.__file_type)
        self.__options.set_option(FileOptions.OPTION_COMM_SAVE_ALPHA, self._ui_save_alpha_check.model.as_bool)

    def _collect_png_options(self):
        return

    def _collect_tga_options(self):
        return

    def _collect_exr_options(self):
        self.__options.set_option(FileOptions.OPTION_EXR_HDR_OUTPUT, self._ui_hdr_output_check.model.as_bool)
        self.__options.set_option(FileOptions.OPTION_EXR_COMP_METHOD, FileOptions.EXR_COMP_METHODS[self._ui_exr_cm_radio_collection.model.as_int])

    def _collect_mp4_options(self):
        self.__options.set_option(FileOptions.OPTION_MP4_ENCODING_BITRATE, self._ui_mp4_bitrate.value)
        self.__options.set_option(FileOptions.OPTION_MP4_ENCODING_IFRAME_INTERVAL, self._ui_mp4_iframe_interval.value)
        self.__options.set_option(FileOptions.OPTION_MP4_ENCODING_PRESET, self._get_combobox_string_value(self._ui_mp4_preset))
        self.__options.set_option(FileOptions.OPTION_MP4_ENCODING_PROFILE, self._get_combobox_string_value(self._ui_mp4_profile))
        self.__options.set_option(FileOptions.OPTION_MP4_ENCODING_RC_MODE, self._get_combobox_string_value(self._ui_mp4_rc_mode))
        self.__options.set_option(FileOptions.OPTION_MP4_ENCODING_RC_TARGET_QUALITY, self._ui_mp4_rc_target_quality.value)
        self.__options.set_option(FileOptions.OPTION_MP4_ENCODING_VIDEO_FULL_RANGE_FLAG, self._ui_mp4_video_full_range_flag_check.model.as_bool)

    def _collect_options(self):
        self._collect_common_options()
        self._collect_png_options()
        self._collect_tga_options()
        self._collect_exr_options()
        self._collect_mp4_options()

    def _get_combobox_string_value(self, combobox):
        model = combobox.model
        index = model.get_item_value_model().as_int
        selected_string = model.get_item_value_model(model.get_item_children()[index]).as_string
        return selected_string

    def _set_combobox_string_value(self, combobox, value):
        string_items = combobox.model.get_item_children()
        str_index = 0
        while str_index < len(string_items):
            str_value = combobox.model.get_item_value_model(string_items[str_index]).as_string
            if value == str_value:
                break
            str_index += 1
        if str_index == len(string_items):
            carb.log_warn(f"Movie capture file option: {value} is not allowed so can't set it for capture.")
            str_index = 0
        combobox.model.get_item_value_model().as_int = str_index

    def _get_exr_comp_method_index(self, exr_comp_method):
        try:
            index = FileOptions.EXR_COMP_METHODS.index(exr_comp_method)
            return index
        except Exception as e:
            carb.log_warn(f"Exr compression method {exr_comp_method} is invalid. Except: {e}")
            return 0

    def _apply_common_options(self):
        self.__file_type = self.__options.get_option(FileOptions.OPTION_FILE_TYPE, ".png")
        self._ui_save_alpha_check.model.as_bool = self.__options.get_option(FileOptions.OPTION_COMM_SAVE_ALPHA, False)

    def _apply_png_options(self):
        return

    def _apply_tga_options(self):
        return

    def _apply_exr_options(self):
        self._ui_hdr_output_check.model.as_bool = self.__options.get_option(FileOptions.OPTION_EXR_HDR_OUTPUT, False)
        exr_cmp_mtd = self.__options.get_option(FileOptions.OPTION_EXR_COMP_METHOD, FileOptions.DEFAULT_EXR_COPM_METHOD)
        index = self._get_exr_comp_method_index(exr_cmp_mtd)
        self._ui_exr_cm_radio_collection.model.as_int = index

    def _apply_mp4_options(self):
        self._ui_mp4_bitrate.value = self.__options.get_option(FileOptions.OPTION_MP4_ENCODING_BITRATE, FileOptions.DEFAULT_MP4_ENCODING_BITRATE)
        self._ui_mp4_iframe_interval.value = self.__options.get_option(FileOptions.OPTION_MP4_ENCODING_IFRAME_INTERVAL, FileOptions.DEFAULT_MP4_ENCODING_IFRAME_INTERVAL)
        self._set_combobox_string_value(self._ui_mp4_preset, self.__options.get_option(FileOptions.OPTION_MP4_ENCODING_PRESET, FileOptions.DEFAULT_MP4_ENCODING_PRESET))
        self._set_combobox_string_value(self._ui_mp4_profile, self.__options.get_option(FileOptions.OPTION_MP4_ENCODING_PROFILE, FileOptions.DEFAULT_MP4_ENCODING_PROFILE))
        self._set_combobox_string_value(self._ui_mp4_rc_mode, self.__options.get_option(FileOptions.OPTION_MP4_ENCODING_RC_MODE, FileOptions.DEFAULT_MP4_ENCODING_RCMODE))
        self._ui_mp4_rc_target_quality.value = self.__options.get_option(FileOptions.OPTION_MP4_ENCODING_RC_TARGET_QUALITY, FileOptions.DEFAULT_MP4_ENCODING_RC_TARGET_QUALITY)
        self._ui_mp4_video_full_range_flag_check.model.as_bool = self.__options.get_option(FileOptions.OPTION_MP4_ENCODING_VIDEO_FULL_RANGE_FLAG, FileOptions.DEFAULT_MP4_ENCODING_VIDEO_FULL_RANGE_FLAG)

    def _apply_options(self):
        self._apply_common_options()
        self._apply_png_options()
        self._apply_tga_options()
        self._apply_exr_options()
        self._apply_mp4_options()

        self._set_options_visibility()
        self._adjust_window_height()

    def _adjust_window_height(self):
        ### to work around OM-94767 that the height of a window can't shrink automatically
        if self.__file_type == ".png":
            self.__window.height = FileOptionsWindow.WINDOW_HEIGHT
        elif self.__file_type == ".tga":
            self.__window.height = FileOptionsWindow.WINDOW_HEIGHT
        elif self.__file_type == ".exr":
            self.__window.height = FileOptionsWindow.WINDOW_HEIGHT_EXR
        else:
            # for .mp4, it needs the largest height, so let it to be calculated by omni.ui
            self.__window.height = 0

    def _set_options_visibility(self):
        self._ui_png_options.visible = self.__file_type == ".png"
        self._ui_tga_options.visible = self.__file_type == ".tga"
        self._ui_exr_options.visible = self.__file_type == ".exr"
        self._ui_mp4_options.visible = self.__file_type == ".mp4"

    def _build_ui(self):
        window_flags = ui.WINDOW_FLAGS_NO_SCROLLBAR | ui.WINDOW_FLAGS_MODAL | ui.WINDOW_FLAGS_NO_RESIZE | ui.WINDOW_FLAGS_NO_CLOSE
        self.__window = ui.Window(
            self.WINDOW_NAME,
            width=self.WINDOW_WIDTH,
            height=self.WINDOW_HEIGHT,
            style=WINDOW_DARK_STYLE,
            flags=window_flags,
            dockPreference=ui.DockPreference.DISABLED,
            visible=False
        )
        with self.__window.frame:
            with ui.VStack(spacing=FRAME_SPACING):
                self._build_common_options()
                self._build_exr_options()
                self._build_png_options()
                self._build_tga_options()
                self._build_mp4_options()
                ui.Spacer(height=FRAME_SPACING)
                self._build_action_buttons()

    def _build_settings_head(self, head_text):
        with ui.HStack():
            ui.Spacer(width=self.LEFT_SPACING)
            ui.Label(head_text, width=0)
            ui.Spacer(width=RIGHT_SPACING)

    def _build_common_options(self):
        with ui.VStack(height=0, spacing=FRAME_SPACING):
            self._build_settings_head("Common options")
            with ui.HStack():
                ui.Spacer(width=self.LEFT_SPACING * 2)
                with ui.VStack():
                    ui.Spacer()
                    with ui.HStack(style=WINDOW_DARK_STYLE):
                        self._ui_save_alpha_check = ui.CheckBox(width=0, name="green_check", identifier="file_option_id_check_save_alpha")
                        ui.Label(" Save Alpha")
                    ui.Spacer()

    def _build_png_options(self):
        self._ui_png_options = ui.VStack(height=0, spacing=FRAME_SPACING)
        with self._ui_png_options:
            self._build_settings_head("PNG options")
            with ui.HStack():
                self._build_left_white_space()
                ui.Label("Currently no PNG specific options.")
        self._ui_png_options.visible = False

    def _build_tga_options(self):
        self._ui_tga_options = ui.VStack(height=0, spacing=FRAME_SPACING)
        with self._ui_tga_options:
            self._build_settings_head("TGA options")
            with ui.HStack():
                self._build_left_white_space()
                ui.Label("Currently no TGA specific options.")
        self._ui_tga_options.visible = False

    def _build_left_column(self, label_text, width_percentage=40):
        with ui.HStack(width=ui.Percent(width_percentage)):
            self._build_left_white_space()
            ui.Label(label_text)

    def _build_mp4_options(self):
        self._ui_mp4_options = ui.VStack(height=0)
        with self._ui_mp4_options:
            self._build_settings_head("MP4 options")
            with ui.HStack():
                self._build_left_column("Bitrate")
                self._ui_mp4_bitrate = QuickNumberInput(
                    input_type=QuickNumberInputType.INT,
                    init_value=FileOptions.DEFAULT_MP4_ENCODING_BITRATE, # 16777216, 16Mbps
                    step=1,
                    max_value=870400000, # 850000kbps
                    min_value=1024000, # 1000kbps
                    tooltip="Video encoding bitrate",
                    identifier="file_option_id_drag_mp4_bitrate",
                )
                ui.Spacer(width=RIGHT_SPACING)
            with ui.HStack():
                self._build_left_column("I-Frame interval")
                self._ui_mp4_iframe_interval = QuickNumberInput(
                    input_type=QuickNumberInputType.INT,
                    init_value=60,
                    step=1,
                    min_value=1,
                    max_value=60,
                    tooltip="Every nth frame is an I-Frame",
                    identifier="file_option_id_drag_mp4_iframe_interval",
                )
                ui.Spacer(width=RIGHT_SPACING)
            ui.Spacer(height=5)
            with ui.HStack():
                self._build_left_column("Preset")
                self._ui_mp4_preset = ui.ComboBox(
                    0,
                    *FileOptions.MP4_ENCODING_PRESETS,
                    tooltip="Video encoding preset",
                    identifier="file_option_id_combo_mp4_preset"
                )
                ui.Spacer(width=RIGHT_SPACING)
            ui.Spacer(height=10)
            with ui.HStack():
                self._build_left_column("Profile")
                self._ui_mp4_profile = ui.ComboBox(
                    0,
                    *FileOptions.MP4_ENCODING_PROFILES,
                    tooltip="Video encoding profile",
                    identifier="file_option_id_combo_mp4_profile"
                )
                ui.Spacer(width=RIGHT_SPACING)
            ui.Spacer(height=10)
            with ui.HStack():
                self._build_left_column("RC Mode")
                self._ui_mp4_rc_mode = ui.ComboBox(
                    0,
                    *FileOptions.MP4_ENCODING_RCMODES,
                    tooltip="Video encoding rate control mode",
                    identifier="file_option_id_combo_mp4_rc_mode"
                )
                ui.Spacer(width=RIGHT_SPACING)
            ui.Spacer(height=5)
            with ui.HStack():
                self._build_left_column("RC target quality")
                self._ui_mp4_rc_target_quality = QuickNumberInput(
                    input_type=QuickNumberInputType.INT,
                    init_value=0,
                    step=1,
                    min_value=0,
                    max_value=51,
                    tooltip="Rate control target quality. Range: 0-51, with 0 means automatic",
                    identifier="file_option_id_drag_mp4_rc_target_quality",
                )
                ui.Spacer(width=RIGHT_SPACING)
            with ui.HStack():
                self._build_left_column("Video full range flag")
                with ui.VStack():
                    ui.Spacer()
                    with ui.HStack(style=WINDOW_DARK_STYLE):
                        self._ui_mp4_video_full_range_flag_check = ui.CheckBox(
                            width=0,
                            name="green_check",
                            tooltip="Specifies the output range of the luma and chroma samples(as defined in Annex E of the ITU-T Specification)",
                            identifier="file_option_id_check_mp4_video_full_range_flag"
                        )
                    ui.Spacer()
                ui.Spacer(width=RIGHT_SPACING)

        self._ui_mp4_options.visible = False

    def _build_ui_exr_compression_method(self, exr_comp_md):
        style = {
            "": {"background_color": 0x0, "image_url": MovieCaptureIcons().get("radio_off")},
            ":checked": {"image_url": MovieCaptureIcons().get("radio_on")},
        }
        with ui.VStack(width=0):
            ui.Spacer()
            ui.RadioButton(
                radio_collection=self._ui_exr_cm_radio_collection,
                width=24,
                height=24,
                style=style,
                identifier="file_option_id_radiobutton_" + exr_comp_md,
            )
            ui.Spacer()
        ui.Label(exr_comp_md)

    def _build_left_white_space(self):
        ui.Spacer(width=self.LEFT_SPACING * 2)

    def _build_exr_options(self):
        self._ui_exr_options = ui.VStack(height=0, spacing=FRAME_SPACING)
        with self._ui_exr_options:
            self._build_settings_head("EXR options")
            with ui.HStack():
                self._build_left_white_space()
                with ui.VStack():
                    ui.Spacer()
                    with ui.HStack(style=WINDOW_DARK_STYLE):
                        self._ui_hdr_output_check = ui.CheckBox(width=0, name="green_check", identifier="file_option_id_check_hdr_output")
                        ui.Label(" HDR Output")
                    ui.Spacer()
            with ui.HStack():
                ui.Spacer(width=self.LEFT_SPACING)
                with ui.VStack():
                    self._build_settings_head("EXR Compresson Method")
                    self._ui_exr_cm_radio_collection = ui.RadioCollection()
                    with ui.HStack():
                        ui.Spacer(width=20)
                        with ui.HStack():
                            self._build_ui_exr_compression_method("zip16")
                            self._build_ui_exr_compression_method("zip")
                            self._build_ui_exr_compression_method("dwaa")
                            self._build_ui_exr_compression_method("dwab")
                    with ui.HStack():
                        ui.Spacer(width=20)
                        with ui.HStack():
                            self._build_ui_exr_compression_method("piz")
                            self._build_ui_exr_compression_method("rle")
                            self._build_ui_exr_compression_method("b44")
                            self._build_ui_exr_compression_method("b44a")
        self._ui_exr_options.visible = False

    def _on_cancel_clicked(self):
        self.hide()

    def _on_apply_clicked(self):
        self._collect_options()
        self.hide()

    def _build_action_buttons(self):
        with ui.HStack():
            ui.Spacer(width=self.LEFT_SPACING)
            self._ui_kit_apply_button = ui.Button(
                "Apply",
                clicked_fn=self._on_apply_clicked,
                height=20,
                identifier="file_option_id_button_apply",
            )
            ui.Spacer(width=self.LEFT_SPACING)
            self._ui_kit_cancel_button = ui.Button(
                "Cancel",
                clicked_fn=self._on_cancel_clicked,
                height=20,
                identifier="file_option_id_button_cancel",
            )
            ui.Spacer(width=RIGHT_SPACING)
        ui.Spacer(height=FRAME_SPACING)

    def show(self, file_options):
        if not self.__window:
            self._build_ui()

        self.__options = file_options
        self._apply_options()

        self.__window.visible = True

    def hide(self):
        if self.__window:
            self.__window.visible = False

    def get_options(self):
        return self.__options
