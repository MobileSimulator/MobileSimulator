__all__ = ["MobileExtension"]

import gc
import carb
import omni.ext
from omni.mobile.robots.ui.ui_window import WidgetWindow


class MobileExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        carb.log_info("Pegasus Simulator is starting up")

        # Save the extension id
        self._ext_id = ext_id
        
        self._count = 0

        self._window = WidgetWindow("Mobile Simulator", width=260, height=270)

    def on_shutdown(self):
        """
        Callback called when the extension is shutdown
        """
        carb.log_info("Pegasus Isaac extension shutdown")
        
        if self._window:
            self._window.destroy()
            self._window = None

        # Call the garbage collector
        gc.collect()

