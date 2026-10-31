# Minimal "upload a local layer to OrionGIS" flow — picks a file, uploads via
# the real importer API (api_client.upload_file), then polls the same
# execution-request endpoint the OrionGIS portal itself polls.

from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox

from .api_client import OrionApiClient, OrionApiError

POLL_INTERVAL_MS = 3000
POLL_TIMEOUT_MS = 120_000


def run_upload_flow(client: OrionApiClient, parent_widget) -> None:
    file_path, _ = QFileDialog.getOpenFileName(
        parent_widget,
        "Choose a file to upload to OrionGIS",
        "",
        "Geospatial files (*.zip *.geojson *.json *.gpkg *.shp *.tif *.tiff);;All files (*)",
    )
    if not file_path:
        return

    try:
        execution_id = client.upload_file(file_path)
    except OrionApiError as e:
        QMessageBox.warning(parent_widget, "Orion Connect", f"Upload failed: {e}")
        return

    elapsed = {"ms": 0}

    def poll():
        try:
            status = client.get_upload_status(execution_id)
        except OrionApiError as e:
            timer.stop()
            QMessageBox.warning(parent_widget, "Orion Connect", f"Could not check upload status: {e}")
            return

        state = status.get("status")
        if state == "finished":
            timer.stop()
            dataset_id = status.get("geonode_resource")
            QMessageBox.information(
                parent_widget,
                "Orion Connect",
                f"Upload complete — published to your OrionGIS catalogue (dataset id {dataset_id}).",
            )
            return
        if state == "failed":
            timer.stop()
            QMessageBox.warning(parent_widget, "Orion Connect", f"Import failed: {status.get('log', 'unknown error')}")
            return

        elapsed["ms"] += POLL_INTERVAL_MS
        if elapsed["ms"] >= POLL_TIMEOUT_MS:
            timer.stop()
            QMessageBox.information(
                parent_widget,
                "Orion Connect",
                "Still processing on the server — check your OrionGIS workspace in a few minutes.",
            )

    timer = QTimer(parent_widget)
    timer.timeout.connect(poll)
    timer.start(POLL_INTERVAL_MS)
