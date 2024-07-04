# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import asyncio
import webbrowser
from enum import IntEnum
from typing import Optional

import carb
import carb.settings
import omni.ui as ui
from omni.kit.window.popup_dialog import MessageDialog
from omni.services.client import AsyncClient

FRAME_SPACING = 5
RIGHT_SPACING = 12


class FarmStatusWidget(ui.Widget):
    """UI Widget to expose Omniverse Farm Queue's status and provide Users access to its feature."""

    class FarmStatus(IntEnum):
        """Farm Queue status values."""
        DOWN = 0
        UP = 1
        CHECKING = 2

    def __init__(self) -> None:
        super().__init__()
        self._farm_status: FarmStatusWidget.FarmStatus = FarmStatusWidget.FarmStatus.CHECKING
        self._farm_url: Optional[str] = None
        self._farm_services_client: Optional[AsyncClient] = None
        self._farm_ping_future: Optional[asyncio.Task] = None
        self._open_farm_queue_button: Optional[ui.Button] = None
        self._health_check_label: str = "Checking Queue status..."
        self._dashboard_page = ""

        settings = carb.settings.get_settings()
        self._queue_management_endpoint_prefix: str = settings.get_as_string("exts/omni.kit.window.movie_capture/queue_management_endpoint_prefix")

        self._build_ui()

    def destroy(self) -> None:
        if self._farm_ping_future:
            self._farm_ping_future.cancel()
            self._farm_ping_future = None

    @ui.Widget.visible.getter
    def visible(self) -> bool:
        return self._open_farm_queue_button.visible

    @visible.setter
    def visible(self, value: bool) -> None:
        self._open_farm_queue_button.visible = value

    def _build_ui(self) -> None:
        self._open_farm_queue_button = ui.Button(
            text=self._health_check_label,
            enabled=False,
            clicked_fn=self._handle_click,
            width=160,
            height=22,
            style={
                "Button": {
                    "margin": 0,
                    "padding": 0,
                },
            },
            identifier="farm_setting_id_button_open_farm_queue",
        )

    def set_farm_url(self, farm_url: str) -> None:
        """
        Set the URL of Farm Queue where to direct the User when clicking the "Open Dashboard" button.

        Args:
            farm_url (str): URL of Farm Queue where to direct the User when clicking the "Open Dashboard" button.

        Returns:
            None

        """
        self._farm_url = farm_url
        self._farm_ping_future = asyncio.ensure_future(self._check_farm_queue_status())

    async def _has_dashboard_page(self) -> bool:
        if self._farm_services_client:
            try:
                await self._farm_services_client.dashboard.get()
                carb.log_info(f"Farm Queue {self._farm_url} supports /dashboard as its queue management page.")
                self._dashboard_page = "/dashboard"
                return True
            except Exception as exc:
                carb.log_info(f"Farm Queue {self._farm_url} does not support /dashboard as its queue management page.")
                return False
        return False

    async def _check_farm_queue_status(self) -> None:
        """Ping Farm Queue to establish whether it is available for User commands or not."""
        if not self._open_farm_queue_button:
            return

        self._farm_status = FarmStatusWidget.FarmStatus.CHECKING
        self._open_farm_queue_button.enabled = True
        self._open_farm_queue_button.text = self._health_check_label
        self._open_farm_queue_button.set_tooltip("Checking availability of the Omniverse Farm Queue Management Dashboard")
        self._open_farm_queue_button.enabled = False

        try:
            if self._farm_services_client:
                await self._farm_services_client.stop_async()
            self._farm_services_client = AsyncClient(uri=f"{self._farm_url}{self._queue_management_endpoint_prefix}")

            # Query the Omniverse Farm Management Dashboard UI, as this is the location Users would be redirected to
            # were they to click on the "Open Dashboard" button, but also because it only hits static services, and does
            # not take away processing or network resources if as querying a database API would:
            has_dashboard = await self._has_dashboard_page()
            if not has_dashboard:
                await self._farm_services_client.ui.get()
                self._dashboard_page = "/ui"

            self._farm_status = FarmStatusWidget.FarmStatus.UP
            self._open_farm_queue_button.text = f"Open Dashboard   {ui.get_custom_glyph_code('${glyphs}/external_link.svg')}"
            self._open_farm_queue_button.set_tooltip(
                tooltip_label=f"Task progress information is available at: {self._get_farm_management_url()}"
            )
        except Exception as exc:
            carb.log_info(f"Unable to connect to Omniverse Farm Queue at \"{self._farm_url}\": {str(exc)}")
            self._farm_status = FarmStatusWidget.FarmStatus.DOWN
            self._open_farm_queue_button.text = "Set up Queue"
            self._open_farm_queue_button.set_tooltip(
                tooltip_label="\n".join([
                    "No Farm Queue instance could be reached at the given address.",
                    "Click to learn more about Omniverse Farm Queue.",
                ])
            )
        finally:
            self._open_farm_queue_button.enabled = True

    def _handle_click(self) -> None:
        """Callback function executed upon clicking the button widget."""
        if self._farm_status == FarmStatusWidget.FarmStatus.UP:
            self._open_farm_dashboard()
        elif self._farm_status == FarmStatusWidget.FarmStatus.DOWN:
            self._show_farm_setup_instructions()

    def _show_farm_setup_instructions(self) -> None:
        """Callback executed upon clicking the "Set up Farm Queue" button."""
        dialog = MessageDialog(
            title="Set up Omniverse Farm Queue",
            message="\n".join([
                ("Omniverse Farm Queue and Omniverse Farm Agent allow you to run tasks in the background, and to "
                    "execute automated workflows defined by you or others. These can be configured to run locally, "
                    "or distributed across a compute cluster to best tailor to your needs."),
                "",
                ("Farm Queue and Farm Agent can be used for a number of different use cases, including executing "
                    "manual or time-consuming tasks such as:"),
                "   * Rendering frames or movie clips",
                "   * Converting materials",
                "   * Simulating physics, or baking animation caches",
                "   * Training machine learning models",
                "",
                "",
                "Click the \"Learn more\" button to get started.",
                "",
                "",  # Ensure there is sufficient space between the end of the text and the Dialog buttons.
            ]),
            ok_handler=lambda _: self._open_farm_documentation(),
            ok_label=f"Learn more  {ui.get_custom_glyph_code('${glyphs}/external_link.svg')}",
            cancel_label="Close",
            width=500,
        )
        dialog.show()

    def _open_farm_dashboard(self) -> None:
        """Callback executed upon clicking the "Open Dashboard" button."""
        webbrowser.open(url=self._get_farm_management_url())

    def _open_farm_documentation(self) -> None:
        """Callback executed upon clicking the "Learn more" button."""
        webbrowser.open(url=self._get_farm_documentation_url())

    def _get_farm_management_url(self) -> str:
        """
        Return the URL of the Omniverse Queue Management Dashboard.

        Args:
            None

        Returns:
            str: The URL of the Omniverse Farm Queue Management Dashboard.

        """
        return f"{self._farm_url}{self._queue_management_endpoint_prefix}{self._dashboard_page}"

    def _get_farm_documentation_url(self) -> str:
        """
        Return the URL of the Omniverse Farm Queue documentation page.

        Args:
            None

        Returns:
            str: The URL of the Omniverse Farm Queue documentation page.

        """
        # TODO: Move this URL into a setting when migrating to a Queue-owned widget library exposed as an Extension.
        return "https://docs.omniverse.nvidia.com/app_farm/app_farm/queue.html"

    def get_farm_status(self) -> "FarmStatusWidget.FarmStatus":
        """
        Return the status of the connection with Farm Queue.

        Args:
            None

        Returns:
            FarmStatusWidget.FarmStatus: The status of the connection with Farm Queue.

        """
        return self._farm_status
