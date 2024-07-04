# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from pathlib import Path
from .singleton import Singleton
import carb


@Singleton
class MovieCaptureIcons:
    """A singleton that scans the icon folder and returns the icon depending on the type"""

    def __init__(self):
        import carb.settings

        self._current_path = Path(__file__).parent
        self._icon_path = self._current_path.parent.parent.joinpath("assets", "icons")

        # Read all the svg files in the directory
        self._style = carb.settings.get_settings().get_as_string("/persistent/app/window/uiStyle") or "NvidiaDark"
        self._icons = {icon.stem: icon for icon in self._icon_path.joinpath(self._style).glob("*.svg")}
        # Read all png files too
        self._pngs = {png.stem: png for png in self._icon_path.joinpath(self._style).glob("*.png")}

    def get(self, prim_type, default=None):
        """Checks the icon cache and returns the icon if exists"""
        found = self._icons.get(prim_type)
        if not found and default:
            found = self._icons.get(default)

        if found:
            return str(found)

        return default

    def get_png(self, png_name, default=None):
        """Checks the icon cache and returns the icon if exists"""
        found = self._pngs.get(png_name)
        if not found and default:
            found = self._pngs.get(default)

        if found:
            return str(found)

        return default
