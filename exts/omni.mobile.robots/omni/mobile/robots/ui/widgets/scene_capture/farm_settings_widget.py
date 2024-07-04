# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import asyncio
from typing import List, Optional, Union

import carb

from omni.kit.window.movie_capture import base_widget
from omni.services.client import AsyncClient
import omni.ui as ui

from .ui import FarmStatusWidget
from .ui_values_storage import UIValuesStorage
from .utils.farm_queue_utils import get_farm_queue_settings, get_ui_should_upload, get_ui_skip_upload_to_s3, supports_ui_should_upload, \
    supports_ui_skip_upload_to_s3, supports_ui_task_extensions, supports_ui_task_registries, supports_ui_generate_shader_cache, \
    get_ui_generate_shader_cache, get_ovc_available_farm_queues
from.quick_input import QuickNumberInput, QuickNumberInputType

FRAME_SPACING = 5
RIGHT_SPACING = 12

USER_REGISTRIES_SETTING = "/persistent/exts/omni.kit.registry.nucleus/userRegistries"


def is_supported_farm_content_type_extension(extension: str) -> bool:
    """
    Check if the given file extension can be rendered using Omniverse Queue.

    Args:
        extension (str): The file extension to validate.

    Returns:
        bool: `true` if the given file extension can be rendered using Omniverse Queue, `false` otherwise.

    """
    UNSUPPORTED_EXTENSIONS = ["mp4"]
    if extension.replace(".", "").lower() in UNSUPPORTED_EXTENSIONS:
        return False
    return True


class StringModel(ui.SimpleStringModel):
    '''
    String Model activated when editing is finished.
    Adds item to combo box.
    '''
    def __init__(self):
        super().__init__("")
        self.combo = None

    def end_edit(self):
        combo_model = self.combo.model
        # Get all the options ad list of strings
        all_options = [
            combo_model.get_item_value_model(child).as_string
            for child in combo_model.get_item_children()
        ]

        # Get the current string of this model
        fieldString = self.as_string
        if fieldString:
            if fieldString in all_options:
                index = all_options.index(fieldString)
            else:
                # It's a new string in the combo box
                combo_model.append_child_item(
                    None,
                    ui.SimpleStringModel(fieldString)
                )
                index = len(all_options)

            combo_model.get_item_value_model().set_value(index)

    def populate(self, combo, default_value):
        self.combo = combo
        self.end_edit()
        self.set_value(default_value)


class FarmSettingsWidget(base_widget.BaseMovieCaptureWidget):
    def __init__(self):
        super(FarmSettingsWidget, self).__init__()
        self._farms = self._settings.get("exts/omni.kit.window.movie_capture/available_farms")
        self._default_job_type = self._settings.get_as_string("exts/omni.kit.window.movie_capture/farm_job_name") or "create-render"
        self._autoload_prefix = self._settings.get_as_string("exts/omni.kit.window.movie_capture/farm_autoload_job_type_prefix") or "create-render"
        self._queue_management_endpoint_prefix: str = self._settings.get_as_string(
            "exts/omni.kit.window.movie_capture/queue_management_endpoint_prefix")
        self._settings_service = self._settings.get_as_string("exts/omni.kit.window.movie_capture/settings_service")


        self._default_farm_index = 0
        self._farm_field_model = StringModel()
        self._task_type_field_model = StringModel()

        self._open_farm_queue_button: Optional[ui.Button] = None
        self._farm_task_types_future: Optional[asyncio.Task] = None
        self._farm_queues_future: Optional[asyncio.Task] = None
        self._handle_advanced_rendering_features_future: Optional[asyncio.Task] = None
        self._farm_status_widget: Optional[FarmStatusWidget] = None
        self._stored_upload_to_s3_value = True
        self._stored_skip_uploat_to_s3_value = True
        self._stored_generate_shader_cache_value = True

    def farm_location_combo_changed(self, combo_model, item):
        all_options = [
            combo_model.get_item_value_model(child).as_string
            for child in combo_model.get_item_children()
        ]
        current_index = combo_model.get_item_value_model().as_int
        self._farm_field_model.as_string = all_options[current_index]
        self._check_farm_queue_status()

        if self._farm_task_types_future:
            self._farm_task_types_future.cancel()

        self._farm_task_types_future = asyncio.ensure_future(self._populate_create_render_task_types())
        self._handle_advanced_rendering_features_future = asyncio.ensure_future(
            self.handle_advanced_rendering_features()
        )

    async def handle_advanced_rendering_features(self) -> None:
        """
        Query the Omniverse Farm Queue to see if it supports advanced rendering features, and expose the appropriate
        controls to the User.

        Args:
            None

        Returns:
            None

        """
        selected_farm_queue_url = self._get_selected_farm_queue_url()
        if not selected_farm_queue_url:
            queue_settings = {}
        else:
            queue_settings = await get_farm_queue_settings(farm_queue_server_url=selected_farm_queue_url)

        self._ui_should_upload.model.set_value(get_ui_should_upload(settings=queue_settings) and self._stored_upload_to_s3_value)
        self._ui_skip_upload.model.set_value(get_ui_skip_upload_to_s3(settings=queue_settings) and self._stored_skip_uploat_to_s3_value)
        self._ui_generate_shader_cache.model.set_value(get_ui_generate_shader_cache(settings=queue_settings) and self._stored_generate_shader_cache_value)
        self._ui_stack_should_upload.visible = supports_ui_should_upload(settings=queue_settings)
        self._ui_stack_skip_upload_to_s3.visible = supports_ui_skip_upload_to_s3(settings=queue_settings)
        self._ui_stack_generate_shader_cache.visible = supports_ui_generate_shader_cache(settings=queue_settings)
        self._ui_stack_task_extensions.visible = supports_ui_task_extensions(settings=queue_settings)
        self._ui_stack_task_registries.visible = supports_ui_task_registries(settings=queue_settings)

    def farm_job_type_combo_changed(self, combo_model, item):
        all_options = [
            combo_model.get_item_value_model(child).as_string
            for child in combo_model.get_item_children()
        ]
        if not all_options:
            return

        current_index = combo_model.get_item_value_model().as_int
        self._task_type_field_model.as_string = all_options[current_index]

    def _get_selected_farm_queue_url(self) -> Optional[str]:
        """
        Return the URL of the selected Farm Queue, or ``None`` if no Farm Queue is currently available.

        Args:
            None

        Returns:
            Optional[str]: The URL of the selected Farm Queue, or ``None`` if no Farm Queue is currently available.

        """
        if not self._farms:
            return None
        selected_farm_label = self._farm_field_model.get_value_as_string()

        # In the case the User typed in a domain directly, use it (i.e. the label in the comb-box) as the Farm's URL:
        if selected_farm_label in self._farms:
            selected_farm_url = self._farms[selected_farm_label]
        else:
            selected_farm_url = selected_farm_label
        return selected_farm_url

    def _check_farm_queue_status(self) -> None:
        selected_farm_url = self._get_selected_farm_queue_url()
        if selected_farm_url:
            self._farm_status_widget.set_farm_url(selected_farm_url)

    def build_ui(self):
        self._build_ui_farm_settings()
        self._check_farm_queue_status()

    def _build_ui_farm_settings(self):
        with ui.CollapsableFrame("Queue settings", height=0, collapsed=True):
            with ui.HStack(height=0):
                with ui.VStack(spacing=FRAME_SPACING):
                    self._build_ui_farm_location()
                    self._build_ui_farm_job_type()
                    self._build_ui_upload_to_s3()
                    self._build_ui_skip_upload_to_s3()
                    self._build_ui_generate_shader_cache()
                    self._build_ui_dispatch_delay()
                    self._build_ui_task_comment()
                    self._build_ui_batch_size()
                    self._build_ui_task_size_thresholds()
                    self._build_ui_task_priority()
                    self._build_ui_texture_streaming_memory_budget()
                    self._build_ui_task_extensions()
                    self._build_ui_task_registries()
                ui.Spacer(width=RIGHT_SPACING)

    def _build_ui_dispatch_delay(self):
        with ui.HStack():
            self._build_ui_left_column("Start delay")
            self._ui_server_delay = QuickNumberInput(
                input_type=QuickNumberInputType.INT,
                init_value=10,
                step=1,
                min_value=1,
                ending_text=" seconds",
                identifier="farm_setting_id_field_server_delay",
                tooltip="Delays the start of rendering by X seconds after the USD file has been opened to give time for shaders and textures to load"
            )


    def _build_ui_farm_location(self):
        self._farm_queues_future = asyncio.ensure_future(self._populate_farm_queues())
        with ui.HStack():
            self._build_ui_left_column("Queue instance")
            with ui.HStack(spacing=0):
                self._ui_stringfield_farm = ui.StringField(self._farm_field_model, height=22, identifier="farm_setting_id_stringfield_farm")
                self._ui_kit_farm_location = ui.ComboBox(self._default_farm_index, *self._farms.keys(), width=0, arrow_only=True, identifier="farm_setting_id_combo_farm_location")
                self._ui_kit_farm_location.model.add_item_changed_fn(self.farm_location_combo_changed)
                self._farm_field_model.populate(self._ui_kit_farm_location, list(self._farms.keys())[self._default_farm_index])
                ui.Spacer(width=FRAME_SPACING)
                self._farm_status_widget = FarmStatusWidget()
                self._farm_status_widget.visible = not self._is_ovc_mode()

    async def _get_job_templates(self) -> List[str]:
        queue_prefix = self._queue_management_endpoint_prefix
        current_farm = self.get_selected_farm()
        farm_services_client = AsyncClient(uri=f"{current_farm}{queue_prefix}")

        try:
            job_templates = await farm_services_client.jobs.load.get()
        except Exception as exc:
            carb.log_warn(f"Issue loading jobs from {current_farm}: {str(exc)}")
            return []

        return job_templates.keys()

    async def _get_available_farm_queues(self) -> List[str]:
        """Get available farm queues from settings service in ovc or local settings"""
        if self._is_ovc_mode():
            carb.log_warn("OVC mode reading from settings service")
            settings = await get_farm_queue_settings(farm_queue_server_url=self._settings_service)
            farms = get_ovc_available_farm_queues(settings=settings)
            # if no keys were found from ovc service, default back to settings
            if len(farms.keys()) == 0:
                self._farms = self._settings.get("exts/omni.kit.window.movie_capture/available_farms")
            else:
                self._farms = farms
        else:
            self._farms = self._settings.get("exts/omni.kit.window.movie_capture/available_farms")
        return self._farms.keys()

    async def _populate_farm_queues(self) -> None:
        """Get farm queues and populate ui"""
        model = self._ui_kit_farm_location.model

        # hack to store the old items before removing them to prevent the callback handler
        # from crashing.
        old_items = []
        for item in model.get_item_children():
            old_items.append(item)

        farm_queues = await self._get_available_farm_queues()
        for item in farm_queues:
            model.append_child_item(None, ui.SimpleStringModel(item))

        # delete old items only if we had retrieved any new queues
        if len(farm_queues) > 0:
            for item in model.get_item_children():
                if item in old_items:
                    model.remove_item(item)

    async def _populate_create_render_task_types(self) -> None:
        """Get job types in the farm that start with the string 'create-render'"""
        combo_model = self._ui_kit_farm_task_type.model

        # Remove the job types from the last queue we connected to, keep the default.
        for child in combo_model.get_item_children():
            current_task_type = combo_model.get_item_value_model(child).as_string
            if current_task_type != self._default_job_type:
                combo_model.remove_item(child)

        # Check if we have a queue that is up.
        queue_is_up = False
        attempts = 5
        while not queue_is_up and attempts:
            farm_status = self._farm_status_widget.get_farm_status()
            queue_is_up = farm_status == FarmStatusWidget.FarmStatus.UP
            await asyncio.sleep(2)
            attempts -= 1

        if not queue_is_up:
            return

        # Populate the combo box.
        for job_name in await self._get_job_templates():
            if self._autoload_prefix not in job_name:
                continue
            if job_name != self._default_job_type:
                combo_model.append_child_item(
                    None,
                    ui.SimpleStringModel(job_name)
                )

    def _get_default_texture_streaming_memory_budget(self) -> float:
        return self._settings.get_as_float("/rtx-transient/resourcemanager/texturestreaming/memoryBudget")

    def _build_ui_farm_job_type(self):
        self._farm_task_types_future = asyncio.ensure_future(self._populate_create_render_task_types())
        with ui.HStack():
            self._build_ui_left_column("Job Type")
            with ui.HStack(spacing=0):
                self._ui_stringfield_task_type = ui.StringField(self._task_type_field_model, height=22, identifier="farm_setting_id_stringfield_task_type")
                self._ui_kit_farm_task_type = ui.ComboBox(self._default_farm_index, *[self._default_job_type], width=0, arrow_only=True, identifier="farm_setting_id_combo_farm_task_type")
                self._ui_kit_farm_task_type.model.add_item_changed_fn(self.farm_job_type_combo_changed)
                self._task_type_field_model.populate(self._ui_kit_farm_task_type, self._default_job_type)
                ui.Spacer(width=FRAME_SPACING)

    def _build_ui_upload_to_s3(self):
        self._ui_stack_should_upload = ui.HStack(visible=False)
        with self._ui_stack_should_upload:
            self._build_ui_left_column("Use S3")
            with ui.VStack():
                ui.Spacer(height=FRAME_SPACING)
                self._ui_should_upload = ui.CheckBox(
                    tooltip="This option is required when rendering a version of a stage for the first time on the OVX farms.",
                    identifier="farm_setting_id_check_should_upload",
                )
                self._ui_should_upload.model.set_value(False)

    def _build_ui_skip_upload_to_s3(self):
        self._ui_stack_skip_upload_to_s3 = ui.HStack(visible=False)
        with self._ui_stack_skip_upload_to_s3:
            self._build_ui_left_column("Skip Upload to S3")
            with ui.VStack():
                ui.Spacer(height=FRAME_SPACING)
                self._ui_skip_upload = ui.CheckBox(
                    tooltip="Use this option if the stage has not changed and has been uploaded to S3 before",
                    identifier="farm_setting_id_check_skip_upload",
                )
                self._ui_skip_upload.model.set_value(False)

    def _build_ui_generate_shader_cache(self):
        self._ui_stack_generate_shader_cache = ui.HStack(visible=False)
        with self._ui_stack_generate_shader_cache:
            self._build_ui_left_column("Generate shader cache")
            with ui.VStack():
                ui.Spacer(height=FRAME_SPACING)
                self._ui_generate_shader_cache = ui.CheckBox(
                    tooltip="Flag indicating whether to generate the shader cache upon upload",
                    identifier="farm_setting_id_generate_shader_cache",
                )
                self._ui_generate_shader_cache.model.set_value(False)

    def _build_ui_batch_size(self):
        with ui.HStack():
            self._build_ui_left_column("Batch count")
            self._ui_batch_size = QuickNumberInput(
                input_type=QuickNumberInputType.INT,
                init_value=1,
                step=1,
                min_value=1,
                identifier="farm_setting_id_field_batch_size",
                tooltip="Amount of batches to divide the frames into"
            )

    def _build_ui_task_comment(self):
        with ui.HStack():
            self._build_ui_left_column("Task comment")
            with ui.HStack(spacing=FRAME_SPACING):
                self._ui_task_comment = ui.StringField(height=22, identifier="farm_setting_id_stringfield_task_comment")

    def _build_ui_task_size_thresholds(self):
        with ui.HStack():
            self._build_ui_left_column("Minimum valid file size")
            self._ui_task_valid_frame_size = QuickNumberInput(
                input_type=QuickNumberInputType.INT,
                init_value=0,
                step=1,
                min_value=0,
                identifier="farm_setting_id_field_task_valid_frame_size",
                tooltip="Minimum size of frame in kb for it to be considered a valid frame"
            )

        with ui.HStack():
            self._build_ui_left_column("Invalid frame count threshold")
            self._ui_task_valid_frame_threshold = QuickNumberInput(
                input_type=QuickNumberInputType.INT,
                init_value=3,
                step=1,
                min_value=0,
                identifier="farm_setting_id_field_invalid_frame_count_threshold",
                tooltip="Amount of times a frame can be invalid before the job is failed"
            )

    def _build_ui_task_priority(self):
        with ui.HStack():
            self._build_ui_left_column("Priority")
            self._ui_task_priority = QuickNumberInput(
                input_type=QuickNumberInputType.INT,
                init_value=65535,
                step=1,
                min_value=0,
                max_value=65535,
                identifier="farm_setting_id_stringfield_task_priority",
                tooltip="Task priority. Highest priority 0, lowest priority 65535"
            )

    def _build_ui_texture_streaming_memory_budget(self):
        with ui.HStack():
            self._build_ui_left_column(
                "Texture streaming memory budget (*experimental, Farm only)", base_widget.LEFT_COLUMN_WIDTH_IN_PERCENT_WIDE
            )
            self._ui_texture_streaming_memory_budget = QuickNumberInput(
                input_type=QuickNumberInputType.FLOAT,
                init_value=self._get_default_texture_streaming_memory_budget(),
                step=0.001,
                min_value=0.0,
                max_value=1.0,
                identifier="render_setting_id_drag_texture_streaming_memory_budget_input",
                tooltip="The proportion of available memory can be allocated at streaming textures, range is 0.0 to 1.0"
            )

    def _build_ui_task_extensions(self):
        self._ui_stack_task_extensions = ui.HStack(visible=False)
        with self._ui_stack_task_extensions:
            self._build_ui_left_column("Extensions")
            with ui.HStack(spacing=FRAME_SPACING):
                self._ui_task_extensions = ui.StringField(
                    tooltip="Extensions to enable for this task.",
                    height=100,
                    multiline=True,
                    identifier="farm_setting_id_stringfield_task_extensions",
                )
                extensions = self._settings.get("/crashreporter/data/extraExts") or ""
                extensions = extensions.split(",")
                if not extensions:
                    extensions = self._settings.get("/persistent/app/exts/enabled") or []

                to_enable = [extension for extension in extensions if all(keyword not in extension for keyword in ["gtc", "farm"])]
                self._ui_task_extensions.model.as_string = "\n".join(to_enable)

    def _build_ui_task_registries(self):
        user_registries = self._settings.get(USER_REGISTRIES_SETTING) or []
        registries = []
        for registry in user_registries:
            url = registry.get("url", None)
            if url:
                registries.append(url)

        self._ui_stack_task_registries = ui.HStack(visible=False)
        with self._ui_stack_task_registries:
            self._build_ui_left_column("Registries")
            with ui.HStack(spacing=FRAME_SPACING):
                self._ui_task_registries = ui.StringField(
                    tooltip="Registries to enable for this task.",
                    height=50,
                    multiline=True,
                    identifier="farm_setting_id_stringfield_task_registries",
                )
                self._ui_task_registries.model.as_string = "\n".join(registries)

    def get_selected_farm(self) -> str:
        key = self._farm_field_model.as_string
        try:
            return self._farms[key]
        except KeyError:
            return key

    def get_task_type(self) -> str:
        return self._task_type_field_model.as_string

    def get_start_delay(self) -> int:
        return self._ui_server_delay.value

    def get_batch_count(self) -> int:
        return self._ui_batch_size.value

    def get_task_comment(self) -> str:
        return self._ui_task_comment.model.as_string

    def get_task_priority(self, as_int=False) -> Union[str, int]:
        return self._ui_task_priority.value

    def get_texture_streaming_memory_budget(self) -> float:
        return self._ui_texture_streaming_memory_budget.value

    def get_task_extensions(self) -> Optional[List[str]]:
        """
        In the case where advanced rendering features are supported by the Farm Queue, return the list of task
        extensions provided by the task submitter which should be communicated to the Farm Agent.

        Args:
            None

        Returns:
            Optional[List[str]]: A list of extensions which should be enabled on the Farm Agent set to render the task,
                or ``None`` if advanced rendering features are not supported by the Farm Queue.

        """
        if self._ui_stack_task_extensions.visible:
            return self._ui_task_extensions.model.as_string.splitlines()
        return None

    def get_task_registries(self) -> Optional[List[str]]:
        """
        In the case where advanced rendering features are supported by the Farm Queue, return the list of extension
        registries where extensions may be found, so the Farm Agent handling the task may attempt to enable them.

        Args:
            None

        Returns:
            Optional[List[str]]: A list of extension registries where Farm Agents can attempt to find the provided
                extensions before attempting to handle the task, or ``None`` if advanced rendering features are not
                supported by the Farm Queue.

        """
        if self._ui_stack_task_registries.visible:
            return self._ui_task_registries.model.as_string.splitlines()
        return None

    def get_task_frame_size_threshold(self) -> int:
        return self._ui_task_valid_frame_threshold.value

    def get_task_valid_frame_size(self) -> int:
        return self._ui_task_valid_frame_size.value

    def get_upload_to_s3(self) -> Optional[bool]:
        """
        In the case where advanced rendering features are supported by the Farm Queue, return a flag indicating whether
        data should be uploaded to Cloud buckets.

        Args:
            None

        Returns:
            Optional[bool]: A flag indicating whether data should be uploaded to Cloud buckets, or ``None`` if advanced
                rendering features are not supported by the Farm Queue.

        """
        if self._ui_stack_should_upload.visible:
            return self._ui_should_upload.model.as_bool
        return None

    def get_upload_to_s3_ui_value(self) -> bool:
        """
        Return the data type to be persisted in the USD stage about the whether to upload to S3.

        Args:
            None

        Returns:
            bool: A flag indicating whether to upload to S3.

        """
        if self.get_upload_to_s3():
            return True
        return False

    def get_skip_upload_to_s3(self) -> Optional[bool]:
        """
        In the case where advanced rendering features are supported by the Farm Queue, return a flag indicating whether
        to skip uploading data to Cloud buckets.

        Args:
            None

        Returns:
            Optional[bool]: A flag indicating whether to skip uploading data to Cloud buckets, or ``None`` if advanced
                rendering features are not supported by the Farm Queue.

        """
        if self._ui_stack_skip_upload_to_s3.visible:
            return self._ui_skip_upload.model.as_bool
        return None

    def get_skip_upload_to_s3_ui_value(self) -> bool:
        """
        Return the data type to be persisted in the USD stage about the whether to skip the upload to S3.

        Args:
            None

        Returns:
            bool: A flag indicating whether to skip the upload to S3.

        """
        if self.get_skip_upload_to_s3():
            return True
        return False

    def get_generate_shader_cache(self) -> bool:
        """
        In the case where advanced rendering features are supported by the Farm Queue, return a flag indicating whether
        to generate the shader cache along with the rendering job.

        Args:
            None

        Returns:
            Optional[bool]: A flag indicating whether to generate the shader cache.

        """
        if self._ui_stack_generate_shader_cache.visible:
            return self._ui_generate_shader_cache.model.as_bool
        return None

    def get_generate_shader_cache_ui_value(self) -> bool:
        """
        Return the data type to be persisted in the USD stage about the whether to generate the shader cache.

        Args:
            None

        Returns:
            bool: A flag indicating whether to generate the shader cache.

        """
        if self.get_generate_shader_cache():
            return True
        return False

    def get_ui_values(self, ui_values: UIValuesStorage):
        ui_values.set(UIValuesStorage.SETTING_NAME_QUEUE_INSTANCE, self._farm_field_model.as_string)
        ui_values.set(UIValuesStorage.SETTING_NAME_TASK_TYPE, self.get_task_type())
        ui_values.set(UIValuesStorage.SETTING_NAME_START_DELAY_SECONDS, self.get_start_delay())
        ui_values.set(UIValuesStorage.SETTING_NAME_TASK_COMMENT, self.get_task_comment())
        ui_values.set(UIValuesStorage.SETTING_NAME_BATCH_COUNT, self.get_batch_count())
        ui_values.set(UIValuesStorage.SETTING_NAME_TASK_PRIORITY, self.get_task_priority())
        ui_values.set(UIValuesStorage.SETTING_NAME_UPLOAD_TO_S3, self.get_upload_to_s3_ui_value())
        ui_values.set(UIValuesStorage.SETTING_NAME_SKIP_UPLOAD_TO_S3, self.get_skip_upload_to_s3_ui_value())
        ui_values.set(UIValuesStorage.SETTING_NAME_GENERATE_SHADER_CACHE, self.get_generate_shader_cache_ui_value())
        ui_values.set(UIValuesStorage.SETTING_NAME_BAD_FRAME_SIZE_THRESHOLD, self.get_task_valid_frame_size())
        ui_values.set(UIValuesStorage.SETTING_NAME_MAX_BAD_FREAM_THRESHOLD, self.get_task_frame_size_threshold())
        ui_values.set(UIValuesStorage.SETTING_NAME_TEXTURE_STREAMING_MEMORY_BUDGET, self.get_texture_streaming_memory_budget())

    def apply_ui_values(self, ui_values: UIValuesStorage):
        self._farm_field_model.as_string = ui_values.get(UIValuesStorage.SETTING_NAME_QUEUE_INSTANCE)
        self._task_type_field_model.as_string = ui_values.get(UIValuesStorage.SETTING_NAME_TASK_TYPE)
        self._ui_server_delay.value = ui_values.get(UIValuesStorage.SETTING_NAME_START_DELAY_SECONDS)
        self._ui_task_comment.model.as_string = ui_values.get(UIValuesStorage.SETTING_NAME_TASK_COMMENT)
        self._ui_batch_size.value = ui_values.get(UIValuesStorage.SETTING_NAME_BATCH_COUNT)
        self._ui_task_priority.value = ui_values.get(UIValuesStorage.SETTING_NAME_TASK_PRIORITY)
        self._stored_upload_to_s3_value = ui_values.get(UIValuesStorage.SETTING_NAME_UPLOAD_TO_S3)
        self._stored_skip_uploat_to_s3_value = ui_values.get(UIValuesStorage.SETTING_NAME_SKIP_UPLOAD_TO_S3, False)
        self._stored_generate_shader_cache_value = ui_values.get(UIValuesStorage.SETTING_NAME_GENERATE_SHADER_CACHE, False)
        self._ui_should_upload.model.as_bool = self._stored_upload_to_s3_value
        self._ui_skip_upload.model.as_bool = self._stored_skip_uploat_to_s3_value
        self._ui_generate_shader_cache.model.as_bool = self._stored_generate_shader_cache_value
        self._ui_task_valid_frame_size.value = ui_values.get(UIValuesStorage.SETTING_NAME_BAD_FRAME_SIZE_THRESHOLD, 0)
        self._ui_task_valid_frame_threshold.value = ui_values.get(UIValuesStorage.SETTING_NAME_MAX_BAD_FREAM_THRESHOLD, 3)
        self._ui_texture_streaming_memory_budget.value = ui_values.get(
            UIValuesStorage.SETTING_NAME_TEXTURE_STREAMING_MEMORY_BUDGET,
            self._get_default_texture_streaming_memory_budget()
        )

        # update the visibility of advanced rendering feature options
        self._handle_advanced_rendering_features_future = asyncio.ensure_future(
            self.handle_advanced_rendering_features()
        )
