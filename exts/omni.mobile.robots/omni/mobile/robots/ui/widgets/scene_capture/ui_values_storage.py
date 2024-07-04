# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import carb
import omni.usd


class UIValuesStorage:
    SETTING_ENTRY_IN_USD = "MovieCaptureSettings"

    SETTING_NAME_MOVIE_TYPE = "movie_type"
    SETTING_NAME_CAMERA_NAME = "camera_name"
    SETTING_NAME_FPS = "fps"  # reserve this name for movie encoding fps
    SETTING_NAME_ANIMATION_FPS = "animation_fps"  # use this new name for animation fps
    SETTING_NAME_CAPTURE_RANGE = "capture_range"
    SETTING_NAME_CAPTURE_FRAME_START = "capture_frame_start"
    SETTING_NAME_CAPTURE_FRAME_END = "capture_frame_end"
    SETTING_NAME_CAPTURE_TIME_START = "capture_time_start"
    SETTING_NAME_CAPTURE_TIME_END = "capture_time_end"
    SETTING_NAME_RENUMBER_NEGATIVE_FRAMES_CHECKED = "renumber_negtive_frames_checked"
    SETTING_NAME_RUN_N_FRAMES_CHECKED = "run_n_frames_before_start_checked"
    SETTING_NAME_RUN_N_FRAMES = "run_n_frames_before_start"
    SETTING_NAME_CAPTURE_EVERY_NTH_FRAMES_CHECKED = "capture_every_nth_frames_checked"
    SETTING_NAME_CAPTURE_EVERY_NTH_FRAMES = "capture_every_nth_frames"
    SETTING_NAME_RESOLUTION_TYPE = "resolution_type"
    SETTING_NAME_RESOLUTION_WIDTH = "resolution_width"
    SETTING_NAME_RESOLUTION_HEIGHT = "resolution_height"
    SETTING_NAME_RESOLUTION_W_H_LINKED = "resolution_w_h_linked"
    SETTING_NAME_ASPECT_RATIO_SELECTED = "resolution_aspect_ratio_selected"
    SETTING_NAME_ASPECT_RATIOS = "resolution_aspect_ratios"
    SETTING_NAME_SUNSTUDY_START = "sunstudy_start"
    SETTING_NAME_SUNSTUDY_CURRENT = "sunstudy_end"
    SETTING_NAME_SUNSTUDY_END = "sunstudy_end"
    SETTING_NAME_SUNSTUDY_MOVIE_MINUTES = "sunstudy_movie_minutes"
    SETTING_NAME_SUNSTUDY_MOVIE_SECONDS = "sunstudy_movie_seconds"
    SETTING_NAME_CAPTURE_APPLICATION = "capture_application"

    SETTING_NAME_RENDER_STYLE = "render_style"
    SETTING_NAME_RENDER_PRESET = "render_preset"
    SETTING_NAME_REALTIME_SETTLE_LATENCY = "realtime_settle_latency"
    SETTING_NAME_PATHTRACE_SPP_PER_ITERATION_MGPU = "pathtrace_spp_per_iteration_mgpu"
    SETTING_NAME_PATHTRACE_SPP_PER_SUBFRAME = "pathtrace_spp_per_subframe"
    SETTING_NAME_PATHTRACE_ENABLE_MB_CHECKED = "pathtrace_mb_checked"
    SETTING_NAME_PATHTRACE_MB_SUBFRAMES = "pathtrace_mb_subframes"
    SETTING_NAME_PATHTRACE_MB_FRAME_SHUTTER_OPEN = "pathtrace_mb_frame_shutter_open"
    SETTING_NAME_PATHTRACE_MB_FRAME_SHUTTER_CLOSE = "pathtrace_mb_frame_shutter_close"
    SETTING_NAME_IRAY_PATHTRACE_SPP = "iray_pathtrace_spp"
    SETTING_NAME_IRAY_MB_SUBFRAMES = "iray_subframes_per_frame"

    SETTING_NAME_QUEUE_INSTANCE = "queue_instance"
    SETTING_NAME_TASK_TYPE = "task_type"
    SETTING_NAME_START_DELAY_SECONDS = "start_delay_seconds"
    SETTING_NAME_TASK_COMMENT = "task_comment"
    SETTING_NAME_BATCH_COUNT = "batch_count"
    SETTING_NAME_TASK_PRIORITY = "task_priority"
    SETTING_NAME_UPLOAD_TO_S3 = "upload_to_s3"
    SETTING_NAME_SKIP_UPLOAD_TO_S3 = "skip_upload_to_s3"
    SETTING_NAME_GENERATE_SHADER_CACHE = "generate_shader_cache"
    SETTING_NAME_BAD_FRAME_SIZE_THRESHOLD = "bad_frame_size_threshold"
    SETTING_NAME_MAX_BAD_FREAM_THRESHOLD = "max_bad_frame_threshold"
    SETTING_NAME_TEXTURE_STREAMING_MEMORY_BUDGET = "texture_streaming_memory_budget"

    SETTING_NAME_OUTPUT_PATH = "output_path"
    SETTING_NAME_CAPTURE_NAME = "capture_name"
    SETTING_NAME_OUTPUT_FORMAT = "output_format"
    SETTING_NAME_SAVE_ALPHA_CHECKED = "save_alpha_checked"
    SETTING_NAME_OVERWRITE_EXISTING_FRAME_CHECKED = "overwrite_existing_frame_checked"
    SETTING_NAME_HDR_FOR_EXR_CHECKED = "hdr_for_exr_checked"
    SETTING_NAME_HDR_FOR_EXT_VISIBLE = "hdr_for_exr_visible"
    SETTING_NAME_EXR_COMPRESSION_METHOD = "exr_compression_method"

    SETTING_NAME_MP4_ENCODING_BITRATE = "mp4_encoding_bitrate"
    SETTING_NAME_MP4_ENCODING_IFRAME_INTERVAL = "mp4_encoding_iframe_interval"
    SETTING_NAME_MP4_ENCODING_PRESET = "mp4_encoding_preset"
    SETTING_NAME_MP4_ENCODING_PROFILE = "mp4_encoding_profile"
    SETTING_NAME_MP4_ENCODING_RC_MODE = "mp4_encoding_rc_mode"
    SETTING_NAME_MP4_ENCODING_RC_TARGET_QUALITY = "mp4_encoding_rc_target_quality"
    SETTING_NAME_MP4_ENCODING_VIDEO_FULL_RANGE_FLAG = "mp4_encoding_video_full_range_flag"

    def __init__(self) -> None:
        self._settings = carb.settings.get_settings()
        self._internal_init()

    def _internal_init(self):
        self._all_settings = {}

    def set(self, setting_name, value):
        self._all_settings[setting_name] = value

    def get(self, setting_name, default_value=None):
        return self._all_settings.get(setting_name, default_value)

    def ui_values_available_in_current_stage(self):
        curr_stage = omni.usd.get_context().get_stage()
        if curr_stage is None:
            return False
        rootLayer = curr_stage.GetRootLayer()
        customLayerData = rootLayer.customLayerData
        try:
            settingsDict = customLayerData[UIValuesStorage.SETTING_ENTRY_IN_USD]
            return True
        except:
            return False

    def read_from_current_stage(self):
        curr_stage = omni.usd.get_context().get_stage()
        rootLayer = curr_stage.GetRootLayer()
        customLayerData = rootLayer.customLayerData
        self._all_settings.clear()
        self._all_settings = customLayerData[UIValuesStorage.SETTING_ENTRY_IN_USD]

    def save_to_current_stage(self):
        curr_stage = omni.usd.get_context().get_stage()
        rootLayer = curr_stage.GetRootLayer()
        customLayerData = rootLayer.customLayerData
        customLayerData[UIValuesStorage.SETTING_ENTRY_IN_USD] = self._all_settings
        rootLayer.customLayerData = customLayerData
        # curr_stage.Save()
