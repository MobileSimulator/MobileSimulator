# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from typing import Any, Dict, Optional

import carb

from omni.services.client import AsyncClient


ADVANCED_RENDERING_FEATURES_SETTINGS_KEY = "advanced_rendering_features"
"""Key used to detect if the selected Farm Queue supports advanced rendering features."""


async def get_farm_queue_settings(farm_queue_server_url: str) -> Dict[str, Any]:
    """
    Return the settings from the selected Farm Queue.

    Args:
        farm_queue_server_url(str): Server URL of the selected Farm Queue.

    Returns:
        Dict[str, Any]: Settings exposed by the selected Farm Queue.

    """
    try:
        client = AsyncClient(uri=farm_queue_server_url)
        settings_response = await client.queue.settings.get()
        return settings_response["settings"]
    except Exception as exc:
        carb.log_warn(f"Failed to read farm queue settings: {exc}")
        return {}

async def farm_queue_supports_advanced_features(farm_queue_server_url: str) -> bool:
    """
    Check if the Farm Queue at the given URL supports advanced rendering features.

    Args:
        farm_queue_server_url(str): Server URL of the Farm Queue to query for advanced rendering features.

    Returns:
        bool: A flag indicating whether the Farm Queue at the given server URL supports advanced rendering features.

    """
    queue_settings = await get_farm_queue_settings(farm_queue_server_url=farm_queue_server_url)
    return ADVANCED_RENDERING_FEATURES_SETTINGS_KEY in queue_settings

def get_ovc_available_farm_queues(settings: Dict[str, Any]) -> Dict[str,str]:
    render_settings = settings.get("advanced_rendering_features", {})
    if "default_farm_queue" in render_settings:
        return { "default_farm_queue": render_settings["default_farm_queue"] }
    else:
        return {}

def get_farm_utilities_server(settings: Dict[str, Any]) -> Optional[str]:
    return ADVANCED_RENDERING_FEATURES_SETTINGS_KEY in settings \
        and settings[ADVANCED_RENDERING_FEATURES_SETTINGS_KEY]["farm_utilities_server"]

def get_farm_ingress_bucket(settings: Dict[str, Any]) -> Optional[str]:
    return ADVANCED_RENDERING_FEATURES_SETTINGS_KEY in settings \
        and settings[ADVANCED_RENDERING_FEATURES_SETTINGS_KEY]["ingress_bucket"]

def get_farm_ingress_bucket_url(settings: Dict[str, Any]) -> Optional[str]:
    return ADVANCED_RENDERING_FEATURES_SETTINGS_KEY in settings \
        and settings[ADVANCED_RENDERING_FEATURES_SETTINGS_KEY]["ingress_bucket_url"]

def get_farm_egress_bucket(settings: Dict[str, Any]) -> Optional[str]:
    return ADVANCED_RENDERING_FEATURES_SETTINGS_KEY in settings \
        and settings[ADVANCED_RENDERING_FEATURES_SETTINGS_KEY]["egress_bucket"]

def get_farm_egress_archive_bucket(settings: Dict[str, Any]) -> Optional[str]:
    return ADVANCED_RENDERING_FEATURES_SETTINGS_KEY in settings \
        and settings[ADVANCED_RENDERING_FEATURES_SETTINGS_KEY]["egress_archive_bucket"]

def get_farm_aws_profile(settings: Dict[str, Any]) -> Optional[str]:
    return ADVANCED_RENDERING_FEATURES_SETTINGS_KEY in settings \
        and settings[ADVANCED_RENDERING_FEATURES_SETTINGS_KEY]["aws_profile"]

def _supports_advanced_feature(settings: Dict[str, Any], feature_key: str) -> bool:
    return ADVANCED_RENDERING_FEATURES_SETTINGS_KEY in settings \
        and feature_key in settings[ADVANCED_RENDERING_FEATURES_SETTINGS_KEY]

def _has_advanced_feature(settings: Dict[str, Any], feature_key: str) -> bool:
    return _supports_advanced_feature(settings=settings, feature_key=feature_key) \
        and settings[ADVANCED_RENDERING_FEATURES_SETTINGS_KEY][feature_key] == "true"

def supports_ui_should_upload(settings: Dict[str, Any]) -> bool:
    return _supports_advanced_feature(settings=settings, feature_key="ui_should_upload")

def get_ui_should_upload(settings: Dict[str, Any]) -> bool:
    return _has_advanced_feature(settings=settings, feature_key="ui_should_upload")

def supports_ui_skip_upload_to_s3(settings: Dict[str, Any]) -> bool:
    return _supports_advanced_feature(settings=settings, feature_key="skip_upload_to_s3")

def get_ui_skip_upload_to_s3(settings: Dict[str, Any]) -> bool:
    return _has_advanced_feature(settings=settings, feature_key="skip_upload_to_s3")

def supports_ui_task_extensions(settings: Dict[str, Any]) -> bool:
    return _supports_advanced_feature(settings=settings, feature_key="task_extensions")

def get_ui_task_extensions(settings: Dict[str, Any]) -> bool:
    return _has_advanced_feature(settings=settings, feature_key="task_extensions")

def supports_ui_task_registries(settings: Dict[str, Any]) -> bool:
    return _supports_advanced_feature(settings=settings, feature_key="task_registries")

def get_ui_task_registries(settings: Dict[str, Any]) -> bool:
    return _has_advanced_feature(settings=settings, feature_key="task_registries")

def supports_ui_generate_shader_cache(settings: Dict[str, Any]) -> bool:
    return _supports_advanced_feature(settings=settings, feature_key="generate_shader_cache")

def get_ui_generate_shader_cache(settings: Dict[str, Any]) -> bool:
    return _has_advanced_feature(settings=settings, feature_key="generate_shader_cache")
