__all__ = ["EnvComboboxWidget", "RobotComboboxWidget", "RecordEnvComboboxWidget"]

import omni
import carb
import logging
import omni.ui as ui
from typing import List, Optional
from omni.mobile.robots.params import WORLD_ICON, ROBOT_ICON, WORLD_THUMBNAILS, SIMULATION_ENVIRONMENTS, _asset_server
from omni.mobile.robots.ui.widgets import custom_multifield_widget


class EnvComboboxWidget(object):
    """A customized combobox widget"""

    def __init__(self,
                 model: ui.AbstractItemModel = None,
                 options: List[str] = None,
                 default_value=0,
                 on_restore_fn: callable = None,
                 **kwargs):
        """
        Set up the take type combo box widget
        ::params:
            :on_restore_fn: call when write/restore the widget
        """
        self.__default_val = default_value
        self.__options = options or ["1", "2", "3"]
        self.__combobox_widget = None
        self.on_restore_fn = on_restore_fn
        
        self._env_name = None
        self._world_thumbnail = None

        # Call at the end, rather than start, so build_fn runs after all the init stuff
        # CustomBaseWidget.__init__(self, model=model, **kwargs)

        self.existing_model: Optional[ui.AbstractItemModel] = kwargs.pop("model", None)
        self.revert_img = None
        self.__attr_label: Optional[str] = kwargs.pop("label", "")
        self.__frame = ui.Frame()
        with self.__frame:
            self._build_fn()

    def destroy(self):
        self.existing_model = None
        self.revert_img = None
        self.__attr_label = None
        self.__frame = None
        self.__options = None
        self.__combobox_widget = None

    @property
    def model(self) -> Optional[ui.AbstractItemModel]:
        """The widget's model"""
        if self.__combobox_widget:
            return self.__combobox_widget.model

    @model.setter
    def model(self, value: ui.AbstractItemModel):
        """The widget's model"""
        self.__combobox_widget.model = value

    def _on_value_changed(self, *args):
        """Set revert_img to correct state."""
        model = self.__combobox_widget.model
        index = model.get_item_value_model().get_value_as_int()
        
        cur_env_name = SIMULATION_ENVIRONMENTS[model.get_item_value_model().get_value_as_int()]
        self._env_name = _asset_server("/Isaac/Environments/" + f"{cur_env_name}")
        carb.log_info(f"Environment {self._env_name} has been selected")
        print(f"Environment {self._env_name} has been selected")
        
        self.revert_img.enabled = self.__default_val != index


    def _restore_default(self):
        """Restore the default value."""
        if self.revert_img.enabled:
            # self.__combobox_widget.model.get_item_value_model().set_value(
            #     self.__default_val)
            self.revert_img.enabled = False
            if self.on_restore_fn:
                self.on_restore_fn(True)
        else:
            self.revert_img.enabled = True
            if self.on_restore_fn:
                self.on_restore_fn(False)
    

    def _build_body(self):
        """Main meat of the widget.  Draw the Rectangle, Combobox, and
        set up callbacks to keep them updated.
        """
        with ui.HStack(width=220):  # width : 위치 조정
            with ui.ZStack(width=220): # width : 길이 조정
                # TODO: Simplify when borders on ComboBoxes work in Kit!
                # and remove style rule for "combobox" Rect

                # Use the outline from the Rectangle for the Combobox
                ui.Rectangle(name="combobox", height=22)

                option_list = list(self.__options)
                self.__combobox_widget = ui.ComboBox(
                    0, *option_list,
                    name="dropdown_menu",
                    # Abnormal height because this "transparent" combobox
                    # has to fit inside the Rectangle behind it
                    height=10
                )

                # Swap for  different dropdown arrow image over current one
                with ui.HStack():
                    ui.Spacer()  # Keep it on the right side
                    with ui.VStack(width=0):  # Need width=0 to keep right-aligned
                        ui.Spacer(height=5)
                        with ui.ZStack():
                            ui.Rectangle(width=15, height=15, name="combobox_icon_cover")
                            ui.Image(name="collapsable_closed", width=12, height=12)
                    ui.Spacer(width=2)  # Right margin

            ui.Spacer(width=ui.Percent(5))
        self.__combobox_widget.model.add_item_changed_fn(self._on_value_changed)

    def _build_head(self):
        """Build the left-most piece of the widget line (label in this case)"""
        ui.Label(self.__attr_label, width=80, style = {"color": "lightsteelblue", "margin_height": 2, "alignment": ui.Alignment.RIGHT_TOP})
        ui.Image(WORLD_ICON, width=20, height=20)
        ui.Label("): ", height=20)

    def _build_tail(self):
        """Build the right-most piece of the widget line. In this case,
        we have a Revert Arrow button at the end of each widget line.
        """
        with ui.HStack(width=0):
            # ui.Spacer(width=5)
            with ui.VStack(height=0):
                ui.Spacer(height=3)
                self.revert_img = ui.Image(
                    name="revert_arrow_task_type",
                    fill_policy=ui.FillPolicy.PRESERVE_ASPECT_FIT,
                    width=12,
                    height=13,
                    enabled=False,
                    tooltip="randomly fill (or reset) task type, object id, and house id."
                )
            ui.Spacer(width=5)

        # call back for revert_img click, to restore the default value
        self.revert_img.set_mouse_pressed_fn(
            lambda x, y, b, m: self._restore_default())

    def _build_fn(self):
        """Puts the 3 pieces together."""
        with ui.HStack():
            self._build_head()
            self._build_body()
            self._build_tail()


"""Robot ComboBox"""
class RobotComboboxWidget():
    """A customized combobox widget"""

    def __init__(self,
                 model: ui.AbstractItemModel = None,
                 options: List[str] = None,
                 default_value=0,
                 on_restore_fn: callable = None,
                 **kwargs):
        """
        Set up the take type combo box widget
        ::params:
            :on_restore_fn: call when write/restore the widget
        """
        self.__default_val = default_value
        self.__options = options or ["1", "2", "3"]
        self.__combobox_widget = None
        self.on_restore_fn = on_restore_fn

        # Call at the end, rather than start, so build_fn runs after all the init stuff
        # CustomBaseWidget.__init__(self, model=model, **kwargs)

        self.existing_model: Optional[ui.AbstractItemModel] = kwargs.pop("model", None)
        self.revert_img = None
        self.__attr_label: Optional[str] = kwargs.pop("label", "")
        self.__frame = ui.Frame()
        with self.__frame:
            self._build_fn()

    def destroy(self):
        self.existing_model = None
        self.revert_img = None
        self.__attr_label = None
        self.__frame = None
        self.__options = None
        self.__combobox_widget = None

    @property
    def model(self) -> Optional[ui.AbstractItemModel]:
        """The widget's model"""
        if self.__combobox_widget:
            return self.__combobox_widget.model

    @model.setter
    def model(self, value: ui.AbstractItemModel):
        """The widget's model"""
        self.__combobox_widget.model = value

    def _on_value_changed(self, *args):
        """Set revert_img to correct state."""
        model = self.__combobox_widget.model
        index = model.get_item_value_model().get_value_as_int()
        self.revert_img.enabled = self.__default_val != index

    def _restore_default(self):
        """Restore the default value."""
        if self.revert_img.enabled:
            # self.__combobox_widget.model.get_item_value_model().set_value(
            #     self.__default_val)
            self.revert_img.enabled = False
            if self.on_restore_fn:
                self.on_restore_fn(True)
        else:
            self.revert_img.enabled = True
            if self.on_restore_fn:
                self.on_restore_fn(False)
    

    def _build_body(self):
        """Main meat of the widget.  Draw the Rectangle, Combobox, and
        set up callbacks to keep them updated.
        """
        with ui.HStack():
            with ui.ZStack():
                # TODO: Simplify when borders on ComboBoxes work in Kit!
                # and remove style rule for "combobox" Rect

                # Use the outline from the Rectangle for the Combobox
                ui.Rectangle(name="combobox",
                             height=22)

                option_list = list(self.__options)
                self.__combobox_widget = ui.ComboBox(
                    0, *option_list,
                    name="dropdown_menu",
                    # Abnormal height because this "transparent" combobox
                    # has to fit inside the Rectangle behind it
                    height=10
                )

                # Swap for  different dropdown arrow image over current one
                with ui.HStack():
                    ui.Spacer()  # Keep it on the right side
                    with ui.VStack(width=0):  # Need width=0 to keep right-aligned
                        ui.Spacer(height=5)
                        with ui.ZStack():
                            ui.Rectangle(width=15, height=15, name="combobox_icon_cover")
                            ui.Image(name="collapsable_closed", width=12, height=12)
                    ui.Spacer(width=2)  # Right margin

            ui.Spacer(width=ui.Percent(5))

        self.__combobox_widget.model.add_item_changed_fn(self._on_value_changed)

    def _build_head(self):
        """Build the left-most piece of the widget line (label in this case)"""
        ui.Label(
            self.__attr_label,
            width=45,
            style = {"color": "lightsteelblue", "margin_height": 2, "alignment": ui.Alignment.RIGHT_TOP}
        )
        
        ui.Image(ROBOT_ICON, width=20, height=20)
        ui.Label("): \t", height=20)

    def _build_tail(self):
        """Build the right-most piece of the widget line. In this case,
        we have a Revert Arrow button at the end of each widget line.
        """
        with ui.HStack(width=0):
            # ui.Spacer(width=5)
            with ui.VStack(height=0):
                ui.Spacer(height=3)
                self.revert_img = ui.Image(
                    name="revert_arrow_task_type",
                    fill_policy=ui.FillPolicy.PRESERVE_ASPECT_FIT,
                    width=12,
                    height=13,
                    enabled=False,
                    tooltip="randomly fill (or reset) task type, object id, and house id."
                )
            ui.Spacer(width=5)

        # call back for revert_img click, to restore the default value
        self.revert_img.set_mouse_pressed_fn(
            lambda x, y, b, m: self._restore_default())

    def _build_fn(self):
        """Puts the 3 pieces together."""
        with ui.HStack():
            self._build_head()
            self._build_body()
            self._build_tail()


class RecordEnvComboboxWidget():
    """A customized combobox widget"""

    def __init__(self,
                 model: ui.AbstractItemModel = None,
                 options: List[str] = None,
                 default_value=0,
                 on_restore_fn: callable = None,
                 **kwargs):
        """
        Set up the take type combo box widget
        ::params:
            :on_restore_fn: call when write/restore the widget
        """
        self.__default_val = default_value
        self.__options = options or ["1", "2", "3"]
        self.__combobox_widget = None
        self.on_restore_fn = on_restore_fn

        # Call at the end, rather than start, so build_fn runs after all the init stuff
        # CustomBaseWidget.__init__(self, model=model, **kwargs)

        self.existing_model: Optional[ui.AbstractItemModel] = kwargs.pop("model", None)
        self.revert_img = None
        self.__attr_label: Optional[str] = kwargs.pop("label", "")
        self.__frame = ui.Frame()
        with self.__frame:
            self._build_fn()

    def destroy(self):
        self.existing_model = None
        self.revert_img = None
        self.__attr_label = None
        self.__frame = None
        self.__options = None
        self.__combobox_widget = None

    @property
    def model(self) -> Optional[ui.AbstractItemModel]:
        """The widget's model"""
        if self.__combobox_widget:
            return self.__combobox_widget.model

    @model.setter
    def model(self, value: ui.AbstractItemModel):
        """The widget's model"""
        self.__combobox_widget.model = value

    def _on_value_changed(self, *args):
        """Set revert_img to correct state."""
        model = self.__combobox_widget.model
        index = model.get_item_value_model().get_value_as_int()
        self.revert_img.enabled = self.__default_val != index

    def _restore_default(self):
        """Restore the default value."""
        if self.revert_img.enabled:
            # self.__combobox_widget.model.get_item_value_model().set_value(
            #     self.__default_val)
            self.revert_img.enabled = False
            if self.on_restore_fn:
                self.on_restore_fn(True)
        else:
            self.revert_img.enabled = True
            if self.on_restore_fn:
                self.on_restore_fn(False)
    

    def _build_body(self):
        """Main meat of the widget.  Draw the Rectangle, Combobox, and
        set up callbacks to keep them updated.
        """
        with ui.HStack():
            with ui.ZStack():
                # TODO: Simplify when borders on ComboBoxes work in Kit!
                # and remove style rule for "combobox" Rect

                # Use the outline from the Rectangle for the Combobox
                ui.Rectangle(name="combobox",
                             height=22,
                             )

                option_list = list(self.__options)
                self.__combobox_widget = ui.ComboBox(
                    0, *option_list,
                    name="dropdown_menu",
                    # Abnormal height because this "transparent" combobox
                    # has to fit inside the Rectangle behind it
                    height=10
                )

                # Swap for  different dropdown arrow image over current one
                with ui.HStack():
                    ui.Spacer()  # Keep it on the right side
                    with ui.VStack(width=0):  # Need width=0 to keep right-aligned
                        ui.Spacer(height=5)
                        with ui.ZStack():
                            ui.Rectangle(width=15, height=15, name="combobox_icon_cover")
                            ui.Image(name="collapsable_closed", width=12, height=12)
                    ui.Spacer(width=2)  # Right margin

            ui.Spacer(width=ui.Percent(5))

        self.__combobox_widget.model.add_item_changed_fn(self._on_value_changed)

    def _build_head(self):
        """Build the left-most piece of the widget line (label in this case)"""
        ui.Label(
            self.__attr_label,
            width=30,
            style = {"color": "lightsteelblue", "margin_height": 2, "alignment": ui.Alignment.RIGHT_TOP}
        )
        
        # ui.Image(WORLD_ICON, width=20, height=20)
        # ui.Label("): \t", height=20)

    def _build_tail(self):
        """Build the right-most piece of the widget line. In this case,
        we have a Revert Arrow button at the end of each widget line.
        """
        with ui.HStack(width=0):
            # ui.Spacer(width=5)
            with ui.VStack(height=0):
                ui.Spacer(height=3)
                self.revert_img = ui.Image(
                    name="revert_arrow_task_type",
                    fill_policy=ui.FillPolicy.PRESERVE_ASPECT_FIT,
                    width=12,
                    height=13,
                    enabled=False,
                    tooltip="randomly fill (or reset) task type, object id, and house id."
                )
            ui.Spacer(width=5)

        # call back for revert_img click, to restore the default value
        self.revert_img.set_mouse_pressed_fn(
            lambda x, y, b, m: self._restore_default())

    def _build_fn(self):
        """Puts the 3 pieces together."""
        with ui.HStack():
            self._build_head()
            self._build_body()
            self._build_tail()