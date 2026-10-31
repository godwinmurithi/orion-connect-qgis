# Sign-in dialog — collects the user's own OrionGIS username/password for
# Basic Auth (see api_client.py's module docstring for why: this is a public
# distributed plugin, so it authenticates as the *user*, not a shared secret).
# Credentials are kept only in QSettings for this machine/profile, the same
# place QGIS itself stores plugin-scoped preferences — never sent anywhere
# except the Authorization header on requests to base_url.

from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QLabel

SETTINGS_GROUP = "OrionConnect"


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sign in to OrionGIS")
        settings = QSettings()

        self.base_url_edit = QLineEdit(settings.value(f"{SETTINGS_GROUP}/base_url", "https://orionterrametrics.com"))
        self.username_edit = QLineEdit(settings.value(f"{SETTINGS_GROUP}/username", ""))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

        form = QFormLayout(self)
        form.addRow(QLabel("Sign in with your OrionGIS account. Nothing is shared with third parties."))
        form.addRow("OrionGIS URL", self.base_url_edit)
        form.addRow("Username", self.username_edit)
        form.addRow("Password", self.password_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def credentials(self) -> tuple[str, str, str]:
        return (
            self.base_url_edit.text().strip().rstrip("/"),
            self.username_edit.text().strip(),
            self.password_edit.text(),
        )

    def save_non_sensitive(self):
        """Remember the URL/username for next time — never the password."""
        settings = QSettings()
        settings.setValue(f"{SETTINGS_GROUP}/base_url", self.base_url_edit.text().strip())
        settings.setValue(f"{SETTINGS_GROUP}/username", self.username_edit.text().strip())
