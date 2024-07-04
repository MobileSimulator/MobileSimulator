# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import omni.ui as ui
import carb

class ImageButton:
    STYLE = {
        "Rectangle::image_button": {"background_color": 0x0, "border_width": 0, "border_radius": 2.0},
        "Rectangle::image_button:hovered": {
            "background_color": 0xFFB8B8B8,
            "border_width": 0,
            "border_radius": 2.0,
        },
        "Rectangle::image_button:selected": {
            "background_color": 0x0,
            "border_width": 1,
            "border_color": 0xFFC5911A,
            "border_radius": 2.0,
        },
    }

    def __init__(self, name, image, width, height, on_clicked_fn: callable=None, tooltip=None, identifier=""):
        self._on_clicked_fn = on_clicked_fn
        self._id = name
        self._selected = False
        self._identifier = identifier
        with ui.ZStack(width=0, height=0, spacing=0):
            with ui.Placer(offset_x=0, offset_y=0):
                self._rect = ui.Rectangle(name="image_button", width=width, height=height, style=ImageButton.STYLE, identifier=self._identifier)
            with ui.Placer(offset_x=1, offset_y=1):
                self._image = ui.Image(
                    image, name="image_button", width=width - 2, height=height - 2, fill_policy=ui.FillPolicy.STRETCH
                )
            self._rect.set_mouse_pressed_fn(lambda x, y, btn, a: self._on_mouse_pressed(btn))
            if tooltip:
                self._rect.set_tooltip(tooltip)

    def __del__(self):
        # set ui.Image objects to None explicitly to avoid this error:
        # Client omni.ui Failed to acquire interface [omni::kit::renderer::IGpuFoundation v0.2] while unloading all plugins
        self._image = None

    def set_mouse_pressed_fn(self, on_clicked_fn: callable):
        self._on_clicked_fn = on_clicked_fn

    def _on_mouse_pressed(self, key):
        # 0 is for mouse left button
        if key == 0 and self._on_clicked_fn:
            self._on_clicked_fn(self._id)

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, value):
        self._selected = value
        self._rect.selected = value
