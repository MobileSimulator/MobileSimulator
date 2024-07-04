# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import os
import sys
import carb
import omni.kit
import omni.ui as ui
from enum import IntEnum

GLYPH_CODE_UP = omni.kit.ui.get_custom_glyph_code("${glyphs}/arrow_up.svg")
GLYPH_CODE_DOWN = omni.kit.ui.get_custom_glyph_code("${glyphs}/arrow_down.svg")
TUNE_ARROW_SIZE = 8
FRAME_SPACE = 5


class QuickNumberInputType(IntEnum):
    INT = (0,)
    FLOAT = 1


class MouseDraggingStatus(IntEnum):
    NONE = (0,)
    READY = (1,)
    DRAGGING = 2


QUICK_NUM_INPUT_DEFAULT_STYLE = {
    "Rectangle::qni_input_area": {
        "background_color": 0xFF24211F,
        "pressed": 0xFF383838,
        "padding": 0,
        "border_radius": 2,
    }
}
QUICK_NUM_INPTU_SPINNER_TRASPARENT = {
    "Triangle::qni_spinner_up": {"background_color": 0x0},
    "Triangle::qni_spinner_down": {"background_color": 0x0},
}
QUICK_NUM_INPTU_SPINNER_NORMAL = {
    "Triangle::qni_spinner_up": {"background_color": 0xFF666666},
    "Triangle::qni_spinner_down": {"background_color": 0xFF666666},
}


class QuickNumberInput:
    # Add these class-level status to resolve the issue that when you drag to change an input field and
    # stop on another input field,the status of the spinners of the input fields is not correct
    someone_is_editing = False
    hovering_on_others = False
    hovering_input = None

    def __init__(
        self,
        width=-1,
        input_type=QuickNumberInputType.INT,
        init_value=1,
        step=1,
        beginning_text="",
        ending_text="",
        style="",
        max_value=32767,
        min_value=-32768,
        value_changed_fn=None,
        identifier="",
        tooltip=""
    ):
        self._input_type = input_type
        self._step = step
        self._max_value = max_value
        self._include_max = True
        self._min_value = min_value
        self._include_min = True
        self._value_changed_fn = value_changed_fn
        self._value_changed_fn_id = None
        self._mouse_dragging_status = MouseDraggingStatus.NONE
        self._mouse_x = 0
        self._mouse_y = 0
        self._is_editing = False
        self._is_hovered = False
        self._identifier = identifier
        self._tooltip = tooltip
        self._build_input_widget(width, init_value, beginning_text, ending_text, style)
        self._update_spinner_status(False)

    @property
    def value(self):
        return self._get_input_value()

    @value.setter
    def value(self, value):
        self._set_input_value(value)

    @property
    def min(self):
        return self._min_value

    @min.setter
    def min(self, value):
        self._min_value = value
        self._ui_input_field.min = value

    @property
    def max(self):
        return self._max_value

    @max.setter
    def max(self, value):
        self._max_value = value
        self._ui_input_field.max = value

    @property
    def step(self):
        return self._step

    @step.setter
    def step(self, value):
        self._step = value
        self._ui_input_field.step = value

    @property
    def value_changed_fn(self):
        return self._value_changed_fn

    @value_changed_fn.setter
    def value_changed_fn(self, value):
        if self._value_changed_fn_id != None:
            self._ui_input_field.model.remove_value_changed_fn(self._value_changed_fn_id)
            self._value_changed_fn_id = None
        self._value_changed_fn = value
        if self._value_changed_fn != None:
            self._value_changed_fn_id = self._ui_input_field.model.add_value_changed_fn(self._value_changed_fn)

    def _build_input_widget(self, width, init_value, beginning_text, ending_text, style):
        input_style = style
        if len(input_style) < 1:
            input_style = QUICK_NUM_INPUT_DEFAULT_STYLE
        with ui.VStack():
            ui.Spacer(height=FRAME_SPACE)
            if width == -1:
                self._qni_hstack = ui.HStack(name="qni_hstack", style=input_style)
            else:
                self._qni_hstack = ui.HStack(name="qni_hstack", width=width, style=input_style)
            with self._qni_hstack:
                if len(beginning_text) > 0:
                    ui.Label(beginning_text, name="qni_beginning_text", width=0)

                with ui.ZStack():
                    # self._ui_input_rect = ui.Rectangle(name="combobox")
                    self._ui_input_rect = ui.Rectangle(name="qni_input_area")
                    self._ui_input_rect.set_mouse_hovered_fn(self._on_input_area_hovered)
                    with ui.HStack():
                        with ui.VStack():
                            if self._is_int_input():
                                self._ui_input_field = ui.IntDrag(
                                    min=self._min_value, max=self._max_value, step=self._step
                                )
                            else:
                                self._ui_input_field = ui.FloatDrag(
                                    min=self._min_value, max=self._max_value, step=self._step
                                )
                            self._ui_input_field.model.set_value(init_value)
                            if self._value_changed_fn is not None:
                                self._value_changed_fn_id = self._ui_input_field.model.add_value_changed_fn(
                                    self._value_changed_fn
                                )
                            else:
                                self._value_changed_fn_id = self._ui_input_field.model.add_value_changed_fn(
                                    self._on_input_value_changed
                                )
                            self._ui_input_field.model.add_begin_edit_fn(self._on_input_begin_edit)
                            self._ui_input_field.model.add_end_edit_fn(self._on_input_end_edit)
                            self._ui_input_field.identifier = self._identifier
                        self._ui_input_spinners, self._ui_input_spinner_up, self._ui_input_spinner_down = (
                            self._buid_ui_spinner_buttons()
                        )
                        self._ui_input_spinner_up.set_mouse_pressed_fn(lambda x, y, b, _: self._increase_value())
                        self._ui_input_spinner_down.set_mouse_pressed_fn(lambda x, y, b, _: self._decrease_value())

                if len(ending_text) > 0:
                    ui.Label(ending_text, name="qni_ending_text", width=0)
                if len(self._tooltip) > 0:
                    self._qni_hstack.set_tooltip(self._tooltip)
            ui.Spacer(height=FRAME_SPACE)

    def _on_input_begin_edit(self, model):
        self._is_editing = True
        QuickNumberInput.someone_is_editing = True
        self._update_spinner_status(True)

    def _on_input_end_edit(self, model):
        self._is_editing = False
        QuickNumberInput.someone_is_editing = False
        if self._is_hovered == False:
            self._update_spinner_status(False)
        if QuickNumberInput.hovering_on_others == True:
            if QuickNumberInput.hovering_input is not None:
                QuickNumberInput.hovering_input._update_spinner_status(True)

    def _buid_ui_spinners(self, visible=False):
        spinners = ui.VStack(width=0, height=TUNE_ARROW_SIZE * 2)
        with spinners:
            label_up = ui.Label(f"{GLYPH_CODE_UP}", width=TUNE_ARROW_SIZE, height=TUNE_ARROW_SIZE)
            label_down = ui.Label(f"{GLYPH_CODE_DOWN}", width=TUNE_ARROW_SIZE, height=TUNE_ARROW_SIZE)
        spinners.visible = visible
        return spinners, label_up, label_down

    def _update_spinner_status(self, visible):
        if visible:
            self._ui_input_spinner_up.set_style(QUICK_NUM_INPTU_SPINNER_NORMAL)
            self._ui_input_spinner_down.set_style(QUICK_NUM_INPTU_SPINNER_NORMAL)
        else:
            self._ui_input_spinner_up.set_style(QUICK_NUM_INPTU_SPINNER_TRASPARENT)
            self._ui_input_spinner_down.set_style(QUICK_NUM_INPTU_SPINNER_TRASPARENT)
        self._spinners_useable = visible

    def _buid_ui_spinner_buttons(self, visible=False):
        spinners = ui.VStack(width=0, height=0)
        with spinners:
            ui.Spacer()
            up = ui.Triangle(
                name="qni_spinner_up",
                alignment=ui.Alignment.CENTER_TOP,
                width=TUNE_ARROW_SIZE,
                height=TUNE_ARROW_SIZE,
                style=QUICK_NUM_INPTU_SPINNER_NORMAL,
            )
            ui.Spacer(height=2)
            down = ui.Triangle(
                name="qni_spinner_down",
                alignment=ui.Alignment.CENTER_BOTTOM,
                width=TUNE_ARROW_SIZE,
                height=TUNE_ARROW_SIZE,
                style=QUICK_NUM_INPTU_SPINNER_NORMAL,
            )
            ui.Spacer()
        return spinners, up, down

    def _is_int_input(self):
        return self._input_type == QuickNumberInputType.INT

    def _get_input_value(self):
        if self._is_int_input():
            return self._ui_input_field.model.as_int
        else:
            return self._ui_input_field.model.as_float

    def _set_input_value(self, value):
        self._ui_input_field.model.set_value(value)

    def _is_valid_max_value(self, value):
        if self._include_max:
            return value <= self._max_value
        else:
            return value < self._max_value

    def _is_valid_min_value(self, value):
        if self._include_min:
            return value >= self._min_value
        else:
            return value > self._min_value

    def _on_input_value_changed(self, model):
        value = self._get_input_value()
        if not self._is_valid_max_value(value):
            value = self._max_value
        elif not self._is_valid_min_value(value):
            value = self._min_value
        self._set_input_value(value)

    def _on_input_area_hovered(self, is_hovered):
        self._is_hovered = is_hovered
        QuickNumberInput.hovering_on_others = False
        QuickNumberInput.hovering_input = None
        if is_hovered:
            if self._is_editing:
                self._update_spinner_status(True)
            else:
                self._update_spinner_status(not QuickNumberInput.someone_is_editing)
                if QuickNumberInput.someone_is_editing == True:
                    QuickNumberInput.hovering_on_others = True
                    QuickNumberInput.hovering_input = self
        else:
            self._update_spinner_status(self._is_editing)

    def _increase_value(self):
        value = self._get_input_value() + self._step
        if self._is_valid_max_value(value):
            self._set_input_value(value)
        else:
            carb.log_warn("max value reached")

    def _decrease_value(self):
        value = self._get_input_value() - self._step
        if self._is_valid_min_value(value):
            self._set_input_value(value)
        else:
            carb.log_warn("min value reached")
