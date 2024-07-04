# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


class FileOptions:

    OPTION_FILE_TYPE = "File Type"
    OPTION_COMM_SAVE_ALPHA = "Save Alpha"
    OPTION_EXR_HDR_OUTPUT = "HDR Output"
    OPTION_EXR_COMP_METHOD = "EXR Compression Method"
    OPTION_MP4_ENCODING_BITRATE = "Mp4 encoding bitrate"
    OPTION_MP4_ENCODING_IFRAME_INTERVAL = "Mp4 encoding I-Frame interval"
    OPTION_MP4_ENCODING_PRESET = "Mp4 encoding preset"
    OPTION_MP4_ENCODING_PROFILE = "Mp4 encoding profile"
    OPTION_MP4_ENCODING_RC_MODE = "Mp4 encoding RC mode"
    OPTION_MP4_ENCODING_RC_TARGET_QUALITY = "Mp4 encoding RC target quality"
    OPTION_MP4_ENCODING_VIDEO_FULL_RANGE_FLAG = "Mp4 encoding video full range flag"

    EXR_COMP_METHODS = ["zips", "zip", "dwaa", "dwab", "piz", "rle", "b44", "b44a"]
    DEFAULT_EXR_COPM_METHOD = "zips"
    MP4_ENCODING_PRESETS = [
        "PRESET_DEFAULT",
        "PRESET_HP",
        "PRESET_HQ",
        "PRESET_BD",
        "PRESET_LOW_LATENCY_DEFAULT",
        "PRESET_LOW_LATENCY_HQ",
        "PRESET_LOW_LATENCY_HP",
        "PRESET_LOSSLESS_DEFAULT",
        "PRESET_LOSSLESS_HP"
    ]
    DEFAULT_MP4_ENCODING_PRESET = "PRESET_DEFAULT"
    MP4_ENCODING_PROFILES = [
        "H264_PROFILE_BASELINE",
        "H264_PROFILE_MAIN",
        "H264_PROFILE_HIGH",
        "H264_PROFILE_HIGH_444",
        "H264_PROFILE_STEREO",
        "H264_PROFILE_SVC_TEMPORAL_SCALABILITY",
        "H264_PROFILE_PROGRESSIVE_HIGH",
        "H264_PROFILE_CONSTRAINED_HIGH",
        "HEVC_PROFILE_MAIN",
        "HEVC_PROFILE_MAIN10",
        "HEVC_PROFILE_FREXT"
    ]
    DEFAULT_MP4_ENCODING_PROFILE = "H264_PROFILE_HIGH"
    MP4_ENCODING_RCMODES = [
        "RC_CONSTQP",
        "RC_VBR",
        "RC_CBR",
        "RC_CBR_LOWDELAY_HQ",
        "RC_CBR_HQ",
        "RC_VBR_HQ"
    ]
    DEFAULT_MP4_ENCODING_RCMODE = "RC_VBR"
    DEFAULT_MP4_ENCODING_BITRATE = 16777216
    DEFAULT_MP4_ENCODING_IFRAME_INTERVAL = 60
    DEFAULT_MP4_ENCODING_RC_TARGET_QUALITY = 0
    DEFAULT_MP4_ENCODING_VIDEO_FULL_RANGE_FLAG = False


    def __init__(self):
        self._internal_init()

    def _internal_init(self):
        self._file_options = {
            self.OPTION_FILE_TYPE: ".png",
            self.OPTION_COMM_SAVE_ALPHA: False,
            self.OPTION_EXR_HDR_OUTPUT: False,
            self.OPTION_EXR_COMP_METHOD: self.DEFAULT_EXR_COPM_METHOD,
            self.OPTION_MP4_ENCODING_BITRATE: self.DEFAULT_MP4_ENCODING_BITRATE,
            self.OPTION_MP4_ENCODING_IFRAME_INTERVAL: self.DEFAULT_MP4_ENCODING_IFRAME_INTERVAL,
            self.OPTION_MP4_ENCODING_PRESET: self.DEFAULT_MP4_ENCODING_PRESET,
            self.OPTION_MP4_ENCODING_PROFILE: self.DEFAULT_MP4_ENCODING_PROFILE,
            self.OPTION_MP4_ENCODING_RC_MODE: self.DEFAULT_MP4_ENCODING_RCMODE,
            self.OPTION_MP4_ENCODING_RC_TARGET_QUALITY: self.DEFAULT_MP4_ENCODING_RC_TARGET_QUALITY,
            self.OPTION_MP4_ENCODING_VIDEO_FULL_RANGE_FLAG: self.DEFAULT_MP4_ENCODING_VIDEO_FULL_RANGE_FLAG
        }

    def set_option(self, option, value):
        self._file_options[option] = value

    def get_option(self, option, default_value):
        return self._file_options.get(option, default_value)

    def get_options(self):
        return self._file_options
