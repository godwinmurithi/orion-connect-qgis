# Main plugin class — QGIS's required initGui()/unload() lifecycle, wiring a
# toolbar/menu entry to each of Orion Connect's four real actions: sign in,
# browse/add catalogue layers, upload a layer, and open OrionInsights.

import os
import webbrowser

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox

from .api_client import OrionApiClient
from .browse_dialog import BrowseDialog
from .login_dialog import LoginDialog
from .upload_dialog import run_upload_flow

DASHBOARDS_URL = "https://orionterrametrics.com/insights"
HELP_URL = "https://orionterrametrics.com/docs/connect/qgis-plugin"


class OrionConnectPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.actions: list[QAction] = []
        self.menu = "&Orion Connect"
        self.toolbar = None

        self.client = OrionApiClient()  # unauthenticated by default — reads work immediately

    # -- QGIS lifecycle ---------------------------------------------------

    def initGui(self):
        self.toolbar = self.iface.addToolBar("Orion Connect")
        self.toolbar.setObjectName("OrionConnectToolbar")
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

        self._add_action(icon, "Sign In…", self.show_login)
        self._add_action(icon, "Browse Catalogue / Add Layer…", self.show_browse)
        self._add_action(icon, "Upload Layer to OrionGIS…", self.show_upload)
        self._add_action(icon, "Open OrionInsights Dashboards", self.open_dashboards)
        self._add_action(QIcon(), "Help", self.open_help, toolbar=False)

    def unload(self):
        for action in self.actions:
            self.iface.removePluginWebMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)
        self.actions = []
        if self.toolbar is not None:
            self.iface.mainWindow().removeToolBar(self.toolbar)
            self.toolbar.deleteLater()
            self.toolbar = None

    def _add_action(self, icon: QIcon, text: str, callback, toolbar: bool = True):
        action = QAction(icon, text, self.iface.mainWindow())
        action.triggered.connect(callback)
        if toolbar:
            self.toolbar.addAction(action)
        self.iface.addPluginToWebMenu(self.menu, action)
        self.actions.append(action)
        return action

    # -- actions ------------------------------------------------------------

    def show_login(self):
        dialog = LoginDialog(self.iface.mainWindow())
        if dialog.exec():
            base_url, username, password = dialog.credentials()
            if not username or not password:
                QMessageBox.warning(self.iface.mainWindow(), "Orion Connect", "Username and password are required.")
                return
            dialog.save_non_sensitive()
            self.client = OrionApiClient(base_url=base_url, username=username, password=password)
            QMessageBox.information(self.iface.mainWindow(), "Orion Connect", f"Signed in as {username}.")

    def show_browse(self):
        dialog = BrowseDialog(self.client, self.iface, self.iface.mainWindow())
        dialog.exec()

    def show_upload(self):
        run_upload_flow(self.client, self.iface.mainWindow())

    def open_dashboards(self):
        webbrowser.open(DASHBOARDS_URL)

    def open_help(self):
        webbrowser.open(HELP_URL)
