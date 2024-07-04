# Copyright (c) 2021-2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import asyncio
import getpass
import os
import sys
import typing
from uuid import uuid4

import carb

import omni.client
import omni.kit.capture.viewport
from omni.kit.widget.prompt import Prompt
import omni.ui as ui
import omni.usd
import omni.kit.usd.layers as layers

import omni.services.client as _services_client

from omni.kit.window.filepicker import FilePickerDialog
from omni.kit.widget.filebrowser import FileBrowserItem
from omni.kit.window.popup_dialog import MessageDialog

from . import base_widget
from .farm_settings_widget import is_supported_farm_content_type_extension
from .moive_capture_icons import MovieCaptureIcons
from .ui_values_storage import UIValuesStorage
from .utils.farm_queue_utils import get_farm_aws_profile, get_farm_queue_settings, get_farm_ingress_bucket, \
    get_farm_ingress_bucket_url, get_farm_egress_bucket, get_farm_egress_archive_bucket, get_farm_utilities_server
from .ui import FileOptionsWindow
from .file_options import FileOptions


CAPTURE_FILE_NUM_PATTERN = (".####",)
CAPTURE_FILE_TYPES = [".tga", ".png", ".exr"]
TYPE_INDEX_OF_PNG = 1
VIDEO_FRAMES_DIR_NAME = "frames"
DEFAULT_IMAGE_FRAME_TYPE_FOR_VIDEO = ".png"
DEFAULT_VIDEO_SECONDS = 2
ICON_SIZE = 13
DEFAULT_CAPTURE_TYPE_SETTING_PATH = "/exts/omni.kit.window.movie_capture/default_capture_type"
RENDER_PRODUCT_CAPTURE_SETTING_PATH = "/exts/omni.kit.window.movie_capture/render_product_enabled"
RENDER_PRESET_SUPPORT_RENDER_PRODUCT_SETTING_PATH = "/exts/omni.kit.window.movie_capture/render_preset_support_render_product"
LIVE_SESSION_RESTRICTION_WARNING = "We currently do not support submitting renders during a live-session, due to the dynamic nature of the shared scene."

SUBMIT_BUTTON_STYLE = {
    "Button": {
        "background_color": 0xFFD1981D,
    },
    "Button:disabled": {
        "background_color": 0xFF694C0F,
    },
}


RADIO_BUTTON_STYLE = {
    "RadioButton": {
        "width": 20,
        "RadioButton.Image": {
            "image_url": MovieCaptureIcons().get("checkbox_off_style1_dark"),
        },
        "RadioButton.Image:checked": {
            "image_url": MovieCaptureIcons().get("checkbox_on_style1_dark"),
        },
    }
}


def is_in_live_session() -> bool:
    usd_context = omni.usd.get_context()
    live_syncing = layers.get_layers(usd_context).get_live_syncing()
    return live_syncing.is_stage_in_live_session()


class OutputSettingsWidget(base_widget.BaseMovieCaptureWidget):
    def __init__(self, collect_capture_settings_fn: typing.Callable, capture_instance):
        super(OutputSettingsWidget, self).__init__()
        self._collect_capture_settings_fn = collect_capture_settings_fn
        self._capture_instance = capture_instance
        self._filepicker = None
        self._filepicker_selected_folder = ""
        self._capture_type_setting_changed_sub = self._settings.subscribe_to_node_change_events(
            DEFAULT_CAPTURE_TYPE_SETTING_PATH, self._on_capture_type_setting_changed
        )
        self._render_product_capture_enabled_sub = self._settings.subscribe_to_node_change_events(
            RENDER_PRODUCT_CAPTURE_SETTING_PATH, self._on_render_product_capture_enabled
        )
        self._render_preset_rp_support_sub = self._settings.subscribe_to_node_change_events(
            RENDER_PRESET_SUPPORT_RENDER_PRODUCT_SETTING_PATH, self._on_render_preset_rp_support_change
        )
        self._dict = carb.dictionary.get_dictionary()
        self._overwrite_warning_popup = None
        self._ui_ready = False
        self._init_file_options()

        # NOTE: [OM-101730]
        # If video encoding is not found or if we are in OVC mode, we can't support .mp4 capture
        # This way, if omni.videoencoding exists and we are _not_ in ovc mode,
        # we add .mp4 capture type type to the global list - @gamato
        global CAPTURE_FILE_TYPES
        try:
            import video_encoding
            if not self._is_ovc_mode():
                CAPTURE_FILE_TYPES.append(".mp4")
        except ImportError:
            carb.log_warn("Movie capture: Unable to support .mp4 capture due to failed to import the video encoding extension.")

        self._client_bookmarks_changed_subscription = None
        self._current_servers = []
        self._user_name = ""

    def _init_file_options(self):
        self._file_options_wnd = FileOptionsWindow()
        self._file_options = FileOptions()
        # OM-86448: set HDR option to Ture by default for .exr; as we only read HDR option when it's to capture .exr image so it's fine for other image types
        # Also set it here we won't need to manage/save the status of the HDR option on the FileOptionWindow when the file option buttion gets clicked
        self._file_options.set_option(self._file_options.OPTION_EXR_HDR_OUTPUT, True)
        self._file_options_from_storage_applied = False

    def destroy(self):
        self._capture_instance = None
        self._filepicker = None
        self._settings.unsubscribe_to_change_events(self._capture_type_setting_changed_sub)
        self._settings.unsubscribe_to_change_events(self._render_product_capture_enabled_sub)
        self._overwrite_warning_popup = None
        self._file_options_wnd = None
        self._client_bookmarks_changed_subscription = None
        self._current_servers = []

        # set ui.Image objects to None explicitly to avoid this error:
        # Client omni.ui Failed to acquire interface [omni::kit::renderer::IGpuFoundation v0.2] while unloading all plugins
        self._ui_kit_open_path = None

    def _subscribe_client_bookmarks_changed(self) -> None:
        """Subscribe to omni.client bookmark changes."""
        def on_client_bookmarks_changed(client_bookmarks: typing.Dict):
            self._update_nucleus_servers(client_bookmarks)
        self._client_bookmarks_changed_subscription = omni.client.list_bookmarks_with_callback(on_client_bookmarks_changed)

    def _update_nucleus_servers(self, client_bookmarks: typing.Dict) -> None:
        new_servers = {name: url for name, url in client_bookmarks.items() if self._is_nucleus_server_url(url)}
        self._current_servers = []
        # we only need the server path to get logged user name
        for name, path in new_servers.items():
            self._current_servers.append(path)

    def _is_nucleus_server_url(self, url: str) -> bool:
        if not url:
            return False
        broken_url = omni.client.break_url(url)
        if broken_url.scheme == "omniverse" and broken_url.path == "/" and broken_url.host is not None:
            # Url of the form "omniverse://server_name/" should be recognized as server connection
            return True
        return False

    async def _get_user_name(self) -> str:
        # To minimize side effects, we only get the logged in user name when it's OVC & server connection is successful
        # And in case there is multiple servers, we only try to get the user info from the first server for now, assuming
        # all servers are logged in by the same user
        if self._is_ovc_mode() and len(self._current_servers) > 0:
            server_url = self._current_servers[0]
            result, server_info = await omni.client.get_server_info_async(server_url)
            if result != omni.client.Result.OK:
                self._user_name =  getpass.getuser()
            else:
                self._user_name = server_info.username
        else:
            self._user_name = getpass.getuser()
        return self._user_name

    def build_ui(self):
        self._build_ui_output_settings()
        self._ui_ready = True
        self._subscribe_client_bookmarks_changed()

    def _build_ui_output_settings(self):
        with ui.CollapsableFrame("Output", height=0):
            with ui.HStack(height=0):
                with ui.VStack(spacing=base_widget.FRAME_SPACING):
                    self._build_ui_output_path()
                    self._build_ui_output_name()
                    self._build_ui_overwrite_existing_frames()
                    self._build_ui_output_capture()
                    self._set_default_capture_type()
                ui.Spacer(width=base_widget.RIGHT_SPACING)

    def _build_ui_overwrite_existing_frames(self):
        with ui.HStack(style=base_widget.WINDOW_DARK_STYLE, height=0):
            self._build_ui_left_column("")
            with ui.HStack(width=ui.Percent(50)):
                with ui.VStack(width=0):
                    ui.Spacer()
                    self._ui_kit_overwrite_existing_frames_check = ui.CheckBox(height=0, name="green_check", identifier="output_setting_id_check_overwrite_existing_frames")
                    self._overwrite_image_change_fn = self._ui_kit_overwrite_existing_frames_check.model.add_value_changed_fn(
                        self._on_overwrite_existing_frames_clicked
                    )
                    ui.Spacer()
                ui.Label(" Overwrite existing frame images")
            ui.Spacer()

    def _build_ui_output_path(self):
        with ui.HStack(height=0):
            self._build_ui_left_column("Path")
            with ui.VStack():
                ui.Spacer(height=base_widget.FRAME_SPACING)
                self._ui_kit_path = ui.StringField(identifier="output_setting_id_stringfield_path")
                ui.Spacer(height=base_widget.FRAME_SPACING)
                if self._is_ovc_mode():
                    default_dir = ""
                else:
                    default_dir = carb.tokens.get_tokens_interface().resolve("${shared_documents}/capture")
                self._ui_kit_path.model.set_value(default_dir)
            with ui.HStack(width=0, style=base_widget.WINDOW_DARK_STYLE):
                ui.Label("   ")
                with ui.VStack():
                    ui.Spacer()
                    self._ui_kit_change_path = ui.Button(
                        text="",
                        name="icon_button",
                        image_url=MovieCaptureIcons().get("folder"),
                        width=base_widget.ICON_BUTTON_SIZE_SMALL,
                        height=base_widget.ICON_BUTTON_SIZE_SMALL,
                        mouse_pressed_fn=lambda x, y, b, _: self._on_path_change_clicked(),
                        tooltip="Click to choose the target folder for captured images",
                        identifier="output_setting_id_button_change_path",
                    )
                    ui.Spacer()
                ui.Spacer(width=base_widget.FRAME_SPACING)
                with ui.VStack():
                    ui.Spacer()
                    self._ui_kit_open_path = ui.Button(
                        text="",
                        name="icon_button",
                        image_url=MovieCaptureIcons().get("folder_open"),
                        width=base_widget.ICON_BUTTON_SIZE_SMALL,
                        height=base_widget.ICON_BUTTON_SIZE_SMALL,
                        mouse_pressed_fn=lambda x, y, b, _: self._on_open_path_clicked(),
                        tooltip="Click to open the target folder",
                        identifier="output_setting_id_button_open_path",
                    )
                    self._ui_kit_open_path.visible = not self._is_ovc_mode()
                    ui.Spacer()

    def _build_ui_output_name(self):
        with ui.HStack(height=0):
            self._build_ui_left_column("Name")

            with ui.HStack(spacing=base_widget.FRAME_SPACING, style=base_widget.WINDOW_DARK_STYLE):
                self._ui_kit_default_capture_name = ui.StringField(width=ui.Percent(50), height=0, identifier="output_setting_id_stringfield_default_capture_name")
                self._ui_kit_default_capture_name.model.set_value("Capture")
                self._ui_kit_capture_num_pattern = ui.ComboBox(0, ".# # # #", identifier="output_setting_id_combo_capture_num_pattern")
                self._ui_kit_capture_type = ui.ComboBox(TYPE_INDEX_OF_PNG, *CAPTURE_FILE_TYPES, identifier="output_setting_id_combo_capture_type")
                self._ui_kit_capture_type.model.add_item_changed_fn(self._on_kit_capture_type_changed)
                with ui.VStack(width=0):
                    ui.Spacer()
                    self._ui_kit_capture_type_settings = ui.Button(
                        text="",
                        name="icon_button",
                        image_url=MovieCaptureIcons().get("cog"),
                        width=base_widget.ICON_BUTTON_SIZE_SMALL,
                        height=base_widget.ICON_BUTTON_SIZE_SMALL,
                        mouse_pressed_fn=lambda x, y, b, _: self._on_capture_type_settings_clicked(),
                        tooltip="Open file options window",
                        identifier="output_setting_id_button_capture_type_settings",
                    )
                    ui.Spacer()
                self._update_num_pattern_visibility()

    def _build_ui_output_capture(self):
        with ui.HStack():
            self._build_ui_left_column("")
            self._top_container = ui.Stack(ui.Direction.LEFT_TO_RIGHT)
            with self._top_container:
                self._ui_capture_buttons = ui.HStack()
                with self._ui_capture_buttons:
                    self._ui_kit_capture_sequence_button = ui.Button(
                        "Capture Sequence",
                        clicked_fn=self._on_capture_sequence_clicked,
                        style=SUBMIT_BUTTON_STYLE,
                        width=0,
                        identifier="output_setting_id_button_capture_sequence",
                    )
                    self._ui_kit_capture_button = ui.Button(
                        "Capture Current Frame",
                        clicked_fn=self._on_capture_current_frame_clicked,
                        style=SUBMIT_BUTTON_STYLE,
                        identifier="output_setting_id_button_capture_current_frame",
                    )
                self._ui_kit_dispatch_button = ui.Button(
                    "Submit to Queue",
                    clicked_fn=self._on_dispatch_clicked,
                    style=SUBMIT_BUTTON_STYLE,
                    identifier="output_setting_id_button_submit_to_queue",
                )
                self._ui_capture_buttons.visible = not self._is_ovc_mode()

    def on_window_width_changed(self, width) -> None:
        if self._is_ovc_mode():
            return

        if width < 545:
            self._top_container.direction = ui.Direction.TOP_TO_BOTTOM

            # Strange that have to update container height manually
            async def __adjust_height():
                await omni.kit.app.get_app().next_update_async()
                self._top_container.height = ui.Pixel(self._ui_kit_capture_sequence_button.computed_height + self._ui_kit_dispatch_button.computed_height)

            asyncio.ensure_future(__adjust_height())
        else:
            self._top_container.direction = ui.Direction.LEFT_TO_RIGHT
            self._top_container.height = ui.Pixel(0)

    def _on_overwrite_mp4_popup_yes_clicked(self, dialog):
        dialog.hide()
        self._capture_instance.start()

    def _on_render_product_conflict_popup_yes_clicked(self, dialog):
        dialog.hide()

    def _on_overwrite_warn_popup_yes_clicked(self, dialog):
        carb.log_warn("Movie capture: existing image frames will be overwritten during capture.")
        self._overwrite_warning_popup.hide()

    def _on_overwrite_warn_popup_no_clicked(self, dialog):
        self._ui_kit_overwrite_existing_frames_check.model.as_bool = False
        self._overwrite_warning_popup.hide()

    def _build_overwrite_warning_popup(self, parent: ui.Widget = None) -> MessageDialog:
        message = "Do you really want to overwrite the existing image frames captured?"
        dialog = MessageDialog(
            parent=parent,
            title="Movie Capture - please confirm to overwrite images",
            message=message,
            ok_handler=self._on_overwrite_warn_popup_yes_clicked,
            cancel_handler=self._on_overwrite_warn_popup_no_clicked,
            ok_label="Yes",
            cancel_label="No, uncheck it"
        )
        return dialog

    def _on_overwrite_existing_frames_clicked(self, model):
        if model.as_bool is True:
            if self._overwrite_warning_popup is None:
                self._overwrite_warning_popup = self._build_overwrite_warning_popup()
            self._overwrite_warning_popup.show()

    def _on_render_preset_rp_support_change(self, item, event_type):
        pass

    def _on_render_product_capture_enabled(self, item, event_type):
        if not self._ui_ready:
            return
        if event_type == carb.settings.ChangeEventType.CHANGED:
            enabled = self._dict.get(item)
            carb.log_warn(f"render product capture enabled: {enabled}")
            if enabled:
                self._set_combobox_string_value(self._ui_kit_capture_type, ".exr")

    def _on_capture_type_setting_changed(self, item, event_type):
        capture_type = self._dict.get(item)
        self._set_default_capture_type(capture_type)

    def _on_path_change_clicked(self):
        if self._filepicker is None:
            if self._is_ovc_mode():
                show_collections = ["bookmarks", "omniverse"]
            else:
                show_collections = ["my-computer"]
            self._filepicker = FilePickerDialog(
                "Select Folder",
                show_only_collections=show_collections,
                apply_button_label="Select",
                item_filter_fn=lambda item: self._on_filepicker_filter_item(item),
                selection_changed_fn=lambda items: self._on_filepicker_selection_change(items),
                click_apply_handler=lambda filename, dirname: self._on_dir_pick(self._filepicker, filename, dirname),
            )
        self._filepicker.set_filebar_label_name("Folder Name: ")
        self._filepicker.refresh_current_directory()
        self._filepicker.show(self._ui_kit_path.model.get_value_as_string())

    def _on_capture_type_settings_clicked(self):
        self._file_options_wnd.show(self._file_options)

    def _on_filepicker_filter_item(self, item: FileBrowserItem) -> bool:
        if not item or item.is_folder:
            return True
        return False

    def _on_filepicker_selection_change(self, items: [FileBrowserItem] = []):
        last_item = items[-1]
        self._filepicker.set_filename(last_item.name)
        self._filepicker_selected_folder = last_item.path

    def _on_open_path_clicked(self):
        self._make_sure_dir_existed(self._ui_kit_path.model.as_string)
        path = os.path.realpath(self._ui_kit_path.model.as_string)
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform.startswith("linux"):
            import subprocess
            opener = "xdg-open"
            subprocess.call([opener, path])
        else:
            carb.log_warn(f"Movie capture: unable to open folder {path} due to unsupported platform {sys.platform}")

    def _no_output_path_handler(self, dialog):
        dialog.hide()
        # TODO: better to focus the path input, couldn't find a proper API now

    def _check_output_path(self):
        if len(self._ui_kit_path.model.get_value_as_string()) == 0:
            dialog = MessageDialog(
                title="Movie Capture - please provide an output path",
                message="\n\n".join([
                    "Please set the output path so the the capture can be processed.",
                    "Click the folder icon to show the folder picker dialog to choose the desired target output path."
                ]),
                ok_handler=self._no_output_path_handler,
                ok_label="OK",
                disable_cancel_button=True
            )
            dialog.show()
            return False
        else:
            return True

    def _make_sure_dir_existed(self, dir):
        if not os.path.exists(dir):
            try:
                os.makedirs(dir, exist_ok=True)
            except OSError as error:
                carb.log_warn(f"Output directory cannot be created: {dir}. Error: {error}")
                return False
        return True

    def _on_dir_pick(self, dialog: FilePickerDialog, filename: str, dirname: str):
        dialog.hide()
        self._ui_kit_path.model.set_value(self._filepicker_selected_folder)

    def _on_capture_sequence_clicked(self):
        if is_in_live_session():
            Prompt(title="Movie Capture unavailable", text=LIVE_SESSION_RESTRICTION_WARNING, modal=True).show()
            return

        if not self._check_output_path():
            return

        self._collect_capture_settings_fn(True)
        # if mp4 type to check if the result file is exist or not, and warn it
        file_type = self._get_combobox_value(self._ui_kit_capture_type, CAPTURE_FILE_TYPES)
        mp4_path = os.path.join(
            self._ui_kit_path.model.as_string, self._ui_kit_default_capture_name.model.as_string + file_type
        )
        if file_type == ".mp4" and os.path.exists(mp4_path):
            dialog = MessageDialog(
                parent=None,
                title="Movie Capture - MP4 file exists",
                message=f"The MP4 file {mp4_path} exists already. Do you want to overwrite it?",
                ok_handler=self._on_overwrite_mp4_popup_yes_clicked,
                ok_label="Yes",
                cancel_label="No"
            )
            dialog.show()
        else:
            if self._check_render_product_and_exr() is False:
                self._capture_instance.start()

    def _check_render_product_and_exr(self):
        if self._capture_instance.options.file_type != ".exr" and len(self._capture_instance.options.render_product) > 0:
            reason_str = "Render product only works with .exr files now. "
            fact_str = f"Render product is set to {self._capture_instance.options.render_product} and output file format is set to {self._capture_instance.options.file_type}. "
            action_str = "Please double check the two settings."
            dialog = MessageDialog(
                parent=None,
                title="Movie Capture - render product capture",
                message=f"{reason_str}{fact_str}{action_str}",
                ok_handler=self._on_render_product_conflict_popup_yes_clicked,
                ok_label="OK",
                disable_cancel_button=True
            )
            dialog.show()
            return True
        return False

    def _on_capture_current_frame_clicked(self):
        if is_in_live_session():
            Prompt(title="Frame Capture unavailable", text=LIVE_SESSION_RESTRICTION_WARNING, modal=True).show()
            return

        if not self._check_output_path():
            return

        self._collect_capture_settings_fn(False)
        if self._check_render_product_and_exr() is False:
            self._capture_instance.start()

    def _on_kit_capture_type_changed(self, model, item):
        file_type = self._get_combobox_value(self._ui_kit_capture_type, CAPTURE_FILE_TYPES)
        self._file_options.set_option(self._file_options.OPTION_FILE_TYPE, file_type)

        # Disable the "Submit to Farm" button if the selected file type cannot be produced using Omniverse Farm:
        self._ui_kit_dispatch_button.enabled = is_supported_farm_content_type_extension(file_type)

        self._update_num_pattern_visibility()

    def _set_default_capture_type(self, default_capture_type=None):
        if default_capture_type is None:
            default_capture_type = self._settings.get_as_string(DEFAULT_CAPTURE_TYPE_SETTING_PATH)
        ct_index = 0
        while ct_index < len(CAPTURE_FILE_TYPES):
            if default_capture_type == CAPTURE_FILE_TYPES[ct_index]:
                break
            ct_index += 1
        if ct_index == len(CAPTURE_FILE_TYPES):
            ct_index = 0
        self._ui_kit_capture_type.model.get_item_value_model().as_int = ct_index

    def _update_num_pattern_visibility(self):
        file_type = self._get_combobox_value(self._ui_kit_capture_type, CAPTURE_FILE_TYPES)
        if file_type == ".mp4":
            self._ui_kit_capture_num_pattern.visible = False
        else:
            self._ui_kit_capture_num_pattern.visible = True

    def _sanitize_output_folder(self):
        """If our folder ends in `/` we remove it, S3/windows doesn't like it. """
        return self._ui_kit_path.model.as_string.rstrip("/")

    def _collect_file_options(self, options: omni.kit.capture.viewport.capture_options.CaptureOptions):
        options.save_alpha = self._file_options.get_option(self._file_options.OPTION_COMM_SAVE_ALPHA, False)
        if options.file_type == ".exr":
            options.hdr_output = self._file_options.get_option(self._file_options.OPTION_EXR_HDR_OUTPUT, False)
        else:
            options.hdr_output = False
        options.exr_compression_method = self._file_options.get_option(self._file_options.OPTION_EXR_COMP_METHOD, self._file_options.DEFAULT_EXR_COPM_METHOD)

    def _read_file_options_from_storage(self, ui_values: UIValuesStorage):
        self._file_options.set_option(self._file_options.OPTION_COMM_SAVE_ALPHA, ui_values.get(UIValuesStorage.SETTING_NAME_SAVE_ALPHA_CHECKED))
        self._file_options.set_option(self._file_options.OPTION_EXR_HDR_OUTPUT, ui_values.get(UIValuesStorage.SETTING_NAME_HDR_FOR_EXR_CHECKED))
        self._file_options.set_option(
            self._file_options.OPTION_EXR_COMP_METHOD,
            ui_values.get(UIValuesStorage.SETTING_NAME_EXR_COMPRESSION_METHOD, self._file_options.DEFAULT_EXR_COPM_METHOD)
        )
        self._file_options.set_option(FileOptions.OPTION_MP4_ENCODING_BITRATE, ui_values.get(UIValuesStorage.SETTING_NAME_MP4_ENCODING_BITRATE, FileOptions.DEFAULT_MP4_ENCODING_BITRATE))
        self._file_options.set_option(FileOptions.OPTION_MP4_ENCODING_IFRAME_INTERVAL, ui_values.get(UIValuesStorage.SETTING_NAME_MP4_ENCODING_IFRAME_INTERVAL, FileOptions.DEFAULT_MP4_ENCODING_IFRAME_INTERVAL))
        self._file_options.set_option(FileOptions.OPTION_MP4_ENCODING_PRESET, ui_values.get(UIValuesStorage.SETTING_NAME_MP4_ENCODING_PRESET, FileOptions.DEFAULT_MP4_ENCODING_PRESET))
        self._file_options.set_option(FileOptions.OPTION_MP4_ENCODING_PROFILE, ui_values.get(UIValuesStorage.SETTING_NAME_MP4_ENCODING_PROFILE, FileOptions.DEFAULT_MP4_ENCODING_PROFILE))
        self._file_options.set_option(FileOptions.OPTION_MP4_ENCODING_RC_MODE, ui_values.get(UIValuesStorage.SETTING_NAME_MP4_ENCODING_RC_MODE, FileOptions.DEFAULT_MP4_ENCODING_RCMODE))
        self._file_options.set_option(FileOptions.OPTION_MP4_ENCODING_RC_TARGET_QUALITY, ui_values.get(UIValuesStorage.SETTING_NAME_MP4_ENCODING_RC_TARGET_QUALITY, FileOptions.DEFAULT_MP4_ENCODING_RC_TARGET_QUALITY))
        self._file_options.set_option(FileOptions.OPTION_MP4_ENCODING_VIDEO_FULL_RANGE_FLAG, ui_values.get(UIValuesStorage.SETTING_NAME_MP4_ENCODING_VIDEO_FULL_RANGE_FLAG, FileOptions.DEFAULT_MP4_ENCODING_VIDEO_FULL_RANGE_FLAG))

    def _save_file_options_to_storage(self, ui_values: UIValuesStorage):
        ui_values.set(UIValuesStorage.SETTING_NAME_SAVE_ALPHA_CHECKED, self._file_options.get_option(self._file_options.OPTION_COMM_SAVE_ALPHA, False))
        ui_values.set(UIValuesStorage.SETTING_NAME_HDR_FOR_EXR_CHECKED, self._file_options.get_option(self._file_options.OPTION_EXR_HDR_OUTPUT, False))
        ui_values.set(UIValuesStorage.SETTING_NAME_HDR_FOR_EXT_VISIBLE, False)
        ui_values.set(
            UIValuesStorage.SETTING_NAME_EXR_COMPRESSION_METHOD,
            self._file_options.get_option(self._file_options.OPTION_EXR_COMP_METHOD, self._file_options.DEFAULT_EXR_COPM_METHOD)
        )
        ui_values.set(UIValuesStorage.SETTING_NAME_MP4_ENCODING_BITRATE, self._file_options.get_option(FileOptions.OPTION_MP4_ENCODING_BITRATE, FileOptions.DEFAULT_MP4_ENCODING_BITRATE))
        ui_values.set(UIValuesStorage.SETTING_NAME_MP4_ENCODING_IFRAME_INTERVAL, self._file_options.get_option(FileOptions.OPTION_MP4_ENCODING_IFRAME_INTERVAL, FileOptions.DEFAULT_MP4_ENCODING_IFRAME_INTERVAL))
        ui_values.set(UIValuesStorage.SETTING_NAME_MP4_ENCODING_PRESET, self._file_options.get_option(FileOptions.OPTION_MP4_ENCODING_PRESET, FileOptions.DEFAULT_MP4_ENCODING_PRESET))
        ui_values.set(UIValuesStorage.SETTING_NAME_MP4_ENCODING_PROFILE, self._file_options.get_option(FileOptions.OPTION_MP4_ENCODING_PROFILE, FileOptions.DEFAULT_MP4_ENCODING_PROFILE))
        ui_values.set(UIValuesStorage.SETTING_NAME_MP4_ENCODING_RC_MODE, self._file_options.get_option(FileOptions.OPTION_MP4_ENCODING_RC_MODE, FileOptions.DEFAULT_MP4_ENCODING_RCMODE))
        ui_values.set(UIValuesStorage.SETTING_NAME_MP4_ENCODING_RC_TARGET_QUALITY, self._file_options.get_option(FileOptions.OPTION_MP4_ENCODING_RC_TARGET_QUALITY, FileOptions.DEFAULT_MP4_ENCODING_RC_TARGET_QUALITY))
        ui_values.set(UIValuesStorage.SETTING_NAME_MP4_ENCODING_VIDEO_FULL_RANGE_FLAG, self._file_options.get_option(FileOptions.OPTION_MP4_ENCODING_VIDEO_FULL_RANGE_FLAG, FileOptions.DEFAULT_MP4_ENCODING_VIDEO_FULL_RANGE_FLAG))

    def collect_settings(self, options: omni.kit.capture.viewport.capture_options.CaptureOptions):
        options.output_folder = self._sanitize_output_folder()
        options.file_name = self._ui_kit_default_capture_name.model.as_string
        options.file_name_num_pattern = self._get_combobox_value(
            self._ui_kit_capture_num_pattern, CAPTURE_FILE_NUM_PATTERN
        )
        options.file_type = self._get_combobox_value(self._ui_kit_capture_type, CAPTURE_FILE_TYPES)

        self._collect_file_options(options)
        carb.log_info(f"file options read back: {self._file_options.get_options()}")

        options.overwrite_existing_frames = self._ui_kit_overwrite_existing_frames_check.model.as_bool

    def _stage_url_is_versioned(self, stage_url: str) -> bool:
        """
        Check if the given USD Stage path already contains versioned parameters.

        Args:
            stage_url (str): Path to the USD Stage to check for versioned parameters.

        Returns:
            bool: A flag indicating whether the given USD Stage path contains versioned parameters.

        """
        # Attempt to retrieve the checkpoint version from the USD stage's path:
        client_url = omni.client.break_url(url=stage_url)
        if client_url.query:
            _, checkpoint_id = omni.client.get_branch_and_checkpoint_from_query(query=client_url.query)
            return checkpoint_id is not None
        return False

    def _get_current_stage_checkpoint_version(self, stage_url: str) -> typing.Optional[str]:
        """
        Return the checkpoint version of the given USD Stage already opened, or retrieve the latest version available on storage.

        Args:
            stage_url (str): Path to the USD Stage for which to return the latest available checkpoint version.

        Returns:
            Optional[str]: The checkpoint version of the given USD Stage.

        """
        checkpoint_id: typing.Optional[str] = None

        # Attempt to retrieve the checkpoint version from the USD stage's path:
        client_url = omni.client.break_url(url=stage_url)
        if client_url.query:
            _, checkpoint_id = omni.client.get_branch_and_checkpoint_from_query(query=client_url.query)

        # If no checkpoint version could be retrieved from the USD stage's path, it may be that the version currently
        # opened is the latest one at (as of this instant). In this case, attempt to retrieve the checkpoint version
        # from the last checkpoint associated to the stage:
        if checkpoint_id is None:
            result, entries = omni.client.list_checkpoints(url=stage_url)
            if result != omni.client.Result.OK:
                carb.log_warn(f'Failed to get checkpoints for "{stage_url}": {result}')
                return None
            if len(entries) > 0:
                version_query = entries[-1].relative_path
                _, checkpoint_id = omni.client.get_branch_and_checkpoint_from_query(query=version_query)

        return checkpoint_id

    def _get_versioned_stage_url(self, stage_url: str) -> str:
        """
        Return the versioned URL of the given USD Stage.

        Args:
            stage_url (str): Path to the USD Stage for which to return the versioned segment.

        Returns:
            str: The formatted version of the given USD Stage path, including the versioned segment.

        """
        # Stage is already versioned, return the raw given path:
        if self._stage_url_is_versioned(stage_url=stage_url):
            return stage_url

        # Format a versioned Stage path from the given Stage, and its version from the Stage context and the persisted
        # checkpoints:
        client_url = omni.client.break_url(url=stage_url)
        checkpoint_id = self._get_current_stage_checkpoint_version(stage_url=stage_url)
        versioned_stage_url = omni.client.make_url(
            scheme=client_url.scheme,
            user=client_url.user,
            host=client_url.host,
            port=client_url.port,
            path=client_url.path,
            query=client_url.query if checkpoint_id is None else f"&{checkpoint_id}",
            fragment=client_url.fragment,
        )
        return versioned_stage_url

    def _get_flat_path(self, path: str, url_chunks: omni.client.Url) -> str:
        if not url_chunks.query:
            return path

        branch_checkpoint = omni.client.get_branch_and_checkpoint_from_query(url_chunks.query)
        if branch_checkpoint:
            branch, checkpoint = branch_checkpoint
            file_name, ext = os.path.splitext(path)
            if not branch:
                branch = "default"
            path = f"{file_name}__{branch}__v{checkpoint}{ext}"
        return path

    def _show_submit_to_farm_confirmation(self) -> None:
        dialog = MessageDialog(
            title="Movie Capture - confirm submission to Omniverse Queue",
            message="\n\n".join([
                "Submitting the render task to Omniverse Queue will execute it outside this application.",
                "Are you sure you wish to proceed?",
            ]),
            ok_handler=self._send_render_request_to_queue,
            ok_label="Yes",
            cancel_label="No",
        )
        dialog.show()

    def _on_check_stage_continue(self, dialog) -> None:
        dialog.hide()
        self._show_submit_to_farm_confirmation()

    def _on_check_stage_cancel(self, dialog) -> None:
        dialog.hide()

    def _check_stage_has_pending_edit(self) -> bool:
        """
        Check if the USD stage currently opened in the Omniverse Application has pending edits, and has been persisted
        to storage at least once after creating a new stage. In case the stage has any pending edits, prompt the User to
        save the Stage before submitting it to the selected Omniverse Farm Queue for rendering.

        Args:
            None

        Returns:
            bool: A flag indicating whether the USD stage currently opened has any pending edits that have not been
                saved yet.

        """
        # validate only if the setting is enabled, default is True
        validate_usd = self._settings.get_as_bool( "exts/omni.kit.window.movie_capture/validate_usd")

        if validate_usd is False:
            return True
        if omni.usd.get_context().has_pending_edit() or omni.usd.get_context().is_new_stage():
            dialog = MessageDialog(
                title="Movie Capture - unsaved changes",
                message="\n\n".join([
                    "This USD scene has changes that have not been saved. Are you sure you want to continue?",
                    "Farm will use the saved version for rendering, any unsaved changes will not be included.",
                ]),
                ok_label="Continue",
                ok_handler=self._on_check_stage_continue,
                cancel_label="Cancel",
                cancel_handler=self._on_check_stage_cancel,
            )
            dialog.show()
            return False
        return True

    def _on_dispatch_clicked(self) -> None:
        if is_in_live_session():
            Prompt(title="Render submission unavailable", text=LIVE_SESSION_RESTRICTION_WARNING, modal=True).show()
            return

        if not self._check_stage_has_pending_edit() or not self._check_output_path():
            return

        self._show_submit_to_farm_confirmation()

    def _send_render_request_to_queue(self, dialog) -> None:
        dialog.hide()
        options, farm_settings = self._collect_capture_settings_fn(True)
        options = options.to_dict()

        farm_url = farm_settings["farm_url"]
        task_type = farm_settings["task_type"]
        render_start_delay = farm_settings.get("start_delay", 10)
        batch_count = farm_settings.get("batch_count", 1)
        task_comment = farm_settings.get("task_comment", "")
        usd_file = self._usd_context.get_stage_url()
        task_priority = farm_settings.get("priority", 65535)
        metadata = farm_settings.get("metadata", {})
        bad_frame_size_threshold = farm_settings.get("bad_frame_size_threshold", 0)
        max_bad_frame_threshold = farm_settings.get("max_bad_frame_threshold", 3)
        should_upload_to_s3 = farm_settings.get("upload_to_s3", False)
        skip_upload = farm_settings.get("skip_upload", False)
        generate_shader_cache = farm_settings.get("generate_shader_cache", False)

        # add the texture streaming memory budget into capture options to send it to Farm without changing the interface
        # eventually, it will be in capture options after we support it in omni.kit.capture.viewport
        texture_streaming_memory_budget = farm_settings.get("texture_streaming_memory_budget", 0.1)
        options["texture_streaming_memory_budget"] = texture_streaming_memory_budget

        # Ensure the USD Stage path to submit to the Omniverse Farm Queue contains metadata information about the
        # version to render:
        usd_file = self._get_versioned_stage_url(stage_url=usd_file)

        asyncio.ensure_future(
            self._dispatch_for_remote_rendering(
                server=farm_url,
                task_type=task_type,
                usd_file=usd_file,
                options=options,
                render_start_delay=render_start_delay,
                task_comment=task_comment,
                batch_count=batch_count,
                priority=task_priority,
                metadata=metadata,
                bad_frame_size_threshold=bad_frame_size_threshold,
                max_bad_frame_threshold=max_bad_frame_threshold,
                should_upload_to_s3=should_upload_to_s3,
                skip_upload=skip_upload,
                generate_shader_cache=generate_shader_cache,
            )
        )

    def _prepare_batches(self, start_frame: int, end_frame: int, batch_count: int) -> typing.List[typing.Tuple[int, int]]:
        batches = []

        if batch_count in (0, 1):
            return [(start_frame, end_frame)]

        frame_range = range(start_frame, end_frame)
        if batch_count > len(frame_range) + 1:
            raise ValueError(f"Batch count {batch_count} is larger than the frame range {len(frame_range)}")

        # for the remainder, we will give batches 1 more frame from the end to beginning in the batches list
        # till we run out of the remainder
        steps, remainder = divmod(len(frame_range) + 1, batch_count)

        start_frame_step = start_frame
        end_frame_step = 0
        batch_index = 0
        batch_index_to_add_1_frame = batch_count - remainder
        for end_frame_step in range(start_frame + steps - 1, end_frame, steps):
            if len(batches) == batch_count - 1:
                end_frame_step = end_frame

            # # add the 1 more frame from the remainder of remainder
            actual_end_frame = end_frame_step
            if remainder > 0:
                if batch_index >= batch_index_to_add_1_frame:
                    actual_end_frame = end_frame_step + (batch_index - batch_index_to_add_1_frame) + 1
                    if actual_end_frame > end_frame:
                        actual_end_frame = end_frame
            batch_index += 1

            batches.append((start_frame_step, actual_end_frame))
            start_frame_step = actual_end_frame + 1

            # # in the case the frames can evenly distributed into batches, the last batch will fail the for loop check
            # # so pre-check it here and add it as the last batch
            if end_frame_step + steps == end_frame:
                batches.append((start_frame_step, end_frame))

            if len(batches) == batch_count:
                break

        return batches

    async def _dispatch_for_remote_rendering(
        self,
        server: str,
        task_type: str,
        usd_file: str,
        options: typing.Dict[str, typing.Any],
        render_start_delay: int,
        task_comment: str,
        batch_count: int,
        priority: int,
        metadata: typing.Dict[str, typing.Any],
        bad_frame_size_threshold: int,
        max_bad_frame_threshold: int,
        should_upload_to_s3: bool,
        skip_upload: bool,
        generate_shader_cache: typing.Optional[bool],
    ) -> None:
        initial_button_text = self._ui_kit_dispatch_button.text
        self._ui_kit_dispatch_button.text = "Submitting task..."
        self._ui_kit_dispatch_button.enabled = False

        try:
            batches = self._prepare_batches(options["start_frame"], options["end_frame"], batch_count)
            task_function = "render.run"
            queue_management_endpoint_prefix = self._settings.get_as_string(
                "exts/omni.kit.window.movie_capture/queue_management_endpoint_prefix"
            )

            management_services = _services_client.AsyncClient(uri=f"{server}{queue_management_endpoint_prefix}")

            final_batch_index = len(batches) - 1
            batch_id = str(uuid4())
            metadata = {
                "batches": {
                    "last_index": final_batch_index,
                    "batch_id": batch_id
                }
            }

            task_ids = []
            root_usd_stage = usd_file
            chunks: omni.client.Url = omni.client.break_url(usd_file)
            path = chunks.path
            user_name = await self._get_user_name()
            if chunks.query:
                path = self._get_flat_path(path, chunks)

            if should_upload_to_s3:
                farm_settings = await get_farm_queue_settings(farm_queue_server_url=server)
                ingress_bucket_url = get_farm_ingress_bucket_url(settings=farm_settings)
                egress_bucket = get_farm_egress_bucket(settings=farm_settings)
                usd_file = ingress_bucket_url + path

                output_path = options["output_folder"]
                _, output_path = os.path.splitdrive(output_path)
                output_path = output_path.replace("\\", "/")
                options["output_folder"] = "s3://" + egress_bucket + output_path

            for idx, batch in enumerate(batches):
                batch_options = options.copy()
                batch_options["start_frame"] = batch[0]
                batch_options["end_frame"] = batch[1]
                metadata["batches"]["index"] = idx

                task_args = {
                    "user": user_name,
                    "task_type": task_type,
                    "task_args": {},
                    "task_function": task_function,
                    "task_function_args": {
                        "usd_file": usd_file,
                        "render_settings": batch_options,
                        "render_start_delay": render_start_delay,
                        "bad_frame_size_threshold": bad_frame_size_threshold,
                        "max_bad_frame_threshold": max_bad_frame_threshold,
                    },
                    "task_requirements": {},
                    "task_comment": task_comment,
                    "priority": priority,
                    "metadata": metadata,
                }

                if should_upload_to_s3 and not skip_upload:
                    task_args["status"] = "paused"

                data = await management_services.tasks.submit(**task_args)
                task_ids.append(data["task_id"])

            if should_upload_to_s3 and not skip_upload:
                await self._submit_for_collection(
                    server=server,
                    source_queue=server,
                    task_ids=task_ids,
                    usd_full_stage_url=root_usd_stage,
                    usd_path=path,
                    task_type=task_type,
                    task_function=task_function,
                    priority=priority,
                    generate_shader_cache=generate_shader_cache,
                )

            self._ui_kit_dispatch_button.text = "Task submitted!"

        except Exception as exc:
            self._ui_kit_dispatch_button.text = "Task submission failed"
            carb.log_error(f"Error submitting render to Queue: {str(exc)}")
        finally:
            # Sleep 2 seconds for the text on the button to be visible
            await asyncio.sleep(2)
            self._ui_kit_dispatch_button.text = initial_button_text
            self._ui_kit_dispatch_button.enabled = True

    async def _submit_for_collection(
        self,
        server: str,
        source_queue: str,
        task_ids: typing.List[str],
        usd_full_stage_url: str,
        usd_path,
        task_type: str,
        task_function: str,
        priority: int,
        generate_shader_cache: typing.Optional[bool],
    ) -> None:
        queue_prefix = self._settings.get_as_string("exts/omni.kit.window.movie_capture/queue_management_endpoint_prefix")
        farm_settings = await get_farm_queue_settings(farm_queue_server_url=server)
        farm_utilities_server = get_farm_utilities_server(settings=farm_settings)

        utilities_services = _services_client.AsyncClient(uri=f"{farm_utilities_server}{queue_prefix}")

        # TODO: should this come from the utilities farm?
        farm_utilities_settings = farm_settings  #await get_farm_queue_settings(farm_queue_server_url=farm_utilities_server)
        ingress_bucket = get_farm_ingress_bucket(settings=farm_utilities_settings)
        aws_profile = get_farm_aws_profile(settings=farm_utilities_settings)

        metadata = {
            "dependants": [{"source_queue": source_queue, "task_ids": task_ids, "task_type": task_type, "task_function": task_function}]
        }
        task_comment = f"Collecting {usd_full_stage_url}"

        collect_task_type = "stage-collect-gtc-s3"  # TODO: grab this from the settings.
        collect_task_function = "collect.process.s3"
        collect_dir = os.path.dirname(usd_path).lstrip("/")
        task_args = {
            "user": getpass.getuser(),
            "task_type": collect_task_type,
            "task_args": {},
            "task_function": collect_task_function,
            "task_function_args": {
                "usd_path": usd_full_stage_url,
                "collect_dir": collect_dir,
                "s3_bucket": ingress_bucket,
                "aws_profile": aws_profile
            },
            "task_requirements": {},
            "task_comment": task_comment,
            "priority": priority,
            "metadata": metadata,
        }
        collect_task_data = await utilities_services.tasks.submit(**task_args)

        # If supported by the Farm and requested by the User, submit a task to generate shader caches for the given scene:
        if generate_shader_cache:
            await self._submit_for_shader_cache_generation(
                usd_full_stage_url=usd_full_stage_url,
                shader_upload_location=f"{collect_dir}/cache",
                s3_upload_task_id=collect_task_data["task_id"],
                priority=priority,
                dependent_source_queue=server,
                dependent_task_type=collect_task_type,
                dependent_task_function=collect_task_function,
                utilities_services=utilities_services,
            )

    async def _submit_for_shader_cache_generation(
        self,
        usd_full_stage_url: str,
        shader_upload_location: str,
        s3_upload_task_id: str,
        priority: int,
        dependent_source_queue: str,
        dependent_task_type: str,
        dependent_task_function: str,
        utilities_services: _services_client.AsyncClient,
    ) -> typing.Dict[str, typing.Any]:
        task_args = {
            "user": getpass.getuser(),
            "task_type": "generate-shader-cache",
            "task_args": {},
            "task_function": "shaders.generate",
            "task_function_args": {
                "usd_file": usd_full_stage_url,
                "shader_upload_location": shader_upload_location,
            },
            "task_requirements": {},
            "task_comment": f"Generating shader cache for \"{usd_full_stage_url}\".",
            "priority": priority,
            "metadata": {
                # Add a dependency on the collect job:
                "dependants": [
                    {
                        "source_queue": dependent_source_queue,
                        "task_ids": [s3_upload_task_id],
                        "task_type": dependent_task_type,
                        "task_function": dependent_task_function,
                    },
                ],
            },
        }
        return await utilities_services.tasks.submit(**task_args)

    def get_ui_values(self, ui_values: UIValuesStorage):
        ui_values.set(UIValuesStorage.SETTING_NAME_OUTPUT_PATH, self._ui_kit_path.model.as_string)
        ui_values.set(UIValuesStorage.SETTING_NAME_CAPTURE_NAME, self._ui_kit_default_capture_name.model.as_string)
        ui_values.set(
            UIValuesStorage.SETTING_NAME_OUTPUT_FORMAT,
            self._get_combobox_value(self._ui_kit_capture_type, CAPTURE_FILE_TYPES)
        )

        ui_values.set(
            UIValuesStorage.SETTING_NAME_OVERWRITE_EXISTING_FRAME_CHECKED,
            self._ui_kit_overwrite_existing_frames_check.model.as_bool
        )

        self._save_file_options_to_storage(ui_values)

    def apply_ui_values(self, ui_values: UIValuesStorage):
        self._ui_kit_path.model.as_string = ui_values.get(UIValuesStorage.SETTING_NAME_OUTPUT_PATH)
        self._ui_kit_default_capture_name.model.as_string = ui_values.get(UIValuesStorage.SETTING_NAME_CAPTURE_NAME)
        self._set_combobox_string_value(self._ui_kit_capture_type, ui_values.get(UIValuesStorage.SETTING_NAME_OUTPUT_FORMAT))

        self._ui_kit_overwrite_existing_frames_check.model.remove_value_changed_fn(self._overwrite_image_change_fn)
        self._ui_kit_overwrite_existing_frames_check.model.as_bool = ui_values.get(UIValuesStorage.SETTING_NAME_OVERWRITE_EXISTING_FRAME_CHECKED)
        self._overwrite_image_change_fn = self._ui_kit_overwrite_existing_frames_check.model.add_value_changed_fn(
            self._on_overwrite_existing_frames_clicked
        )

        self._read_file_options_from_storage(ui_values)
        self._file_options_from_storage_applied = False
