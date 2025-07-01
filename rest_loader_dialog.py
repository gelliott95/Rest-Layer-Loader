# rest_loader_dialog.py

import os
import re
import json
import requests
from urllib.parse import urlencode

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QDialogButtonBox
)
from PyQt5.QtCore import Qt
from qgis.core import QgsProject, QgsMessageLog, Qgis
from qgis.utils import iface


def clean_title(raw: str) -> str:
    """
    Strip any trailing '_<digits>' and replace underscores with spaces.
    E.g. 'Crude_Oil_Trunk_Pipelines_1' -> 'Crude Oil Trunk Pipelines'
    """
    no_num = re.sub(r'_\d+$', '', raw)
    return no_num.replace('_', ' ')


class RestLoaderDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Load REST Layers")
        self.layout = QVBoxLayout(self)

        # 1) Spatial filter dropdown
        self.layout.addWidget(QLabel("Load layers from:"))
        self.combo = QComboBox()
        self.combo.addItem("All Layers", "all")
        self.combo.addItem("Current Map Extent", "extent")
        self.combo.addItem("Selected Polygon", "polygon")
        self.layout.addWidget(self.combo)

        # 2) Raster‐toggle (default unchecked = vector by default)
        self.chk_raster = QCheckBox("Load as Raster")
        self.chk_raster.setToolTip("When unchecked (default), attempts vector first")
        self.layout.addWidget(self.chk_raster)

        # 3) Select All checkbox
        self.chk_select_all = QCheckBox("Select All")
        self.chk_select_all.stateChanged.connect(self._on_select_all)
        self.layout.addWidget(self.chk_select_all)

        # 4) Service selection list
        self.listWidget = QListWidget()
        for url in self._load_urls_from_file():
            raw = self._fetch_layer_name(url)
            title = clean_title(raw)
            label = f"{title}  —  {url}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, url)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)  # start unchecked
            self.listWidget.addItem(item)
        self.layout.addWidget(self.listWidget)

        # 5) OK / Cancel buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def _on_select_all(self, state):
        check = Qt.Checked if state == Qt.Checked else Qt.Unchecked
        for i in range(self.listWidget.count()):
            self.listWidget.item(i).setCheckState(check)

    def _fetch_layer_name(self, url: str) -> str:
        try:
            parts = url.rstrip("/").split("/")
            if not parts[-1].isdigit():
                return "Map Service"
            r = requests.get(f"{url}?f=json", timeout=5)
            js = r.json() if r.ok else {}
            return js.get("name", url)
        except Exception:
            return url

    def extent_method(self) -> str:
        return self.combo.currentData()

    def load_as_raster(self) -> bool:
        return self.chk_raster.isChecked()

    def selected_urls(self) -> list:
        urls = []
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            if item.checkState() == Qt.Checked:
                urls.append(item.data(Qt.UserRole))
        return urls

    def selected_polygon_layer(self):
        for lyr in QgsProject.instance().mapLayers().values():
            if hasattr(lyr, "selectedFeatureCount") and lyr.selectedFeatureCount() > 0:
                return lyr
        return None

    def _config_file_path(self) -> str:
        d = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(d, "config", "layer_urls.txt")

    def _load_urls_from_file(self) -> list:
        path = self._config_file_path()
        if not os.path.exists(path):
            QgsMessageLog.logMessage(f"Config not found: {path}", "RestLoader", Qgis.Warning)
            return []
        with open(path, "r", encoding="utf-8") as f:
            return [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]