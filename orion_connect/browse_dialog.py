# Catalogue browse/search dialog — lists real OrionGIS datasets and adds the
# selected one as a live WMS or WFS layer in the current QGIS project.

from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from .api_client import Dataset, OrionApiClient, OrionApiError


class BrowseDialog(QDialog):
    def __init__(self, client: OrionApiClient, iface, parent=None):
        super().__init__(parent)
        self.client = client
        self.iface = iface
        self.setWindowTitle("Orion Connect — Catalogue")
        self.resize(560, 480)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search the OrionGIS catalogue (e.g. \"malaria\", \"roads\", \"counties\")…")
        self.search_edit.returnPressed.connect(self.run_search)

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.run_search)

        search_row = QHBoxLayout()
        search_row.addWidget(self.search_edit)
        search_row.addWidget(search_btn)

        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self._on_add_clicked)

        self.status_label = QLabel("Type a query and press Search, or press Search with an empty box to browse recent datasets.")
        self.status_label.setWordWrap(True)

        self.layer_type_combo = QComboBox()
        self.layer_type_combo.addItems(["Add as WMS (raster/rendered)", "Add as WFS (vector features)"])

        add_btn = QPushButton("Add selected layer to map")
        add_btn.clicked.connect(self._on_add_clicked)

        layout = QVBoxLayout(self)
        layout.addLayout(search_row)
        layout.addWidget(self.results_list, 1)
        layout.addWidget(self.status_label)
        layout.addWidget(self.layer_type_combo)
        layout.addWidget(add_btn)

        self._datasets: list[Dataset] = []
        self.run_search()

    def run_search(self):
        query = self.search_edit.text().strip()
        self.status_label.setText("Searching…")
        try:
            result = self.client.search_datasets(query=query, page_size=30)
        except OrionApiError as e:
            self.status_label.setText(f"Search failed: {e}")
            return

        self._datasets = result.datasets
        self.results_list.clear()
        for ds in self._datasets:
            item = QListWidgetItem(f"{ds.title}  ({ds.subtype})")
            item.setData(Qt.ItemDataRole.UserRole, ds)
            self.results_list.addItem(item)
        self.status_label.setText(f"{result.total} dataset(s) in the catalogue — showing {len(self._datasets)}.")

    def _selected_dataset(self) -> Dataset | None:
        item = self.results_list.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _on_add_clicked(self):
        dataset = self._selected_dataset()
        if dataset is None:
            QMessageBox.information(self, "Orion Connect", "Select a dataset first.")
            return

        as_wfs = self.layer_type_combo.currentIndex() == 1
        try:
            if as_wfs:
                uri = self.client.wfs_layer_uri(dataset)
                layer = QgsVectorLayer(uri, dataset.title, "WFS")
            else:
                uri = self.client.wms_layer_uri(dataset)
                layer = QgsRasterLayer(uri, dataset.title, "wms")
        except OrionApiError as e:
            QMessageBox.warning(self, "Orion Connect", f"Could not build the layer URL: {e}")
            return

        if not layer.isValid():
            QMessageBox.warning(
                self,
                "Orion Connect",
                f"QGIS could not load '{dataset.title}' as a {'WFS' if as_wfs else 'WMS'} layer. "
                "The dataset may not have a matching layer type on the server.",
            )
            return

        QgsProject.instance().addMapLayer(layer)
        self.status_label.setText(f"Added '{dataset.title}' to the map.")
