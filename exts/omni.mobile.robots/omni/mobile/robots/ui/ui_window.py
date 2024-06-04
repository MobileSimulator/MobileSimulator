__all__ = ["WidgetWindow"]

import numpy as np

# Omniverse general API
import carb
import omni.ui as ui
from omni.ui import color as cl


class WidgetWindow(ui.Window):
    # Design constants for the widgets
    LABEL_PADDING = 120
    BUTTON_HEIGHT = 50
    GENERAL_SPACING = 5

    WINDOW_WIDTH = 325
    WINDOW_HEIGHT = 850
    
    