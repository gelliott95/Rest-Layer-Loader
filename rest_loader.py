# rest_loader.py

import os
import re
import json
import requests
from urllib.parse import urlencode

from PyQt5.QtWidgets import QAction, QMessageBox
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtCore import QUrl

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsMessageLog,
    Qgis,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsWkbTypes,
    QgsPointXY
)
from qgis.PyQt.QtCore import QVariant
from qgis.utils import iface

from .rest_loader_dialog import RestLoaderDialog


def clean_title(raw):
    no_num = re.sub(r'_\d+$', '', raw)
    return no_num.replace('_', ' ')


class RestLoader:
    def __init__(self, iface):
        self.iface = iface
        plugin_dir = os.path.dirname(__file__)
        self.icon = QIcon(os.path.join(plugin_dir, "icon.png"))
        self.meta = self._load_metadata()

        # toolbar-only action (icon, no text)
        self.action_load_toolbar = QAction(self.icon, "", iface.mainWindow())
        self.action_load_toolbar.setToolTip(self.meta.get("name", "Load REST Layers"))
        self.action_load_toolbar.triggered.connect(self.run)

        # menu action – Load REST Layers with icon
        self.action_load_menu = QAction(self.icon,
                                        self.meta.get("name", "Load REST Layers"),
                                        iface.mainWindow())
        self.action_load_menu.triggered.connect(self.run)

        # other menu actions: text only
        self.action_edit_urls = QAction("Edit Layer URLs…", iface.mainWindow())
        self.action_edit_urls.triggered.connect(self.open_layer_urls)

        self.action_refresh = QAction("Refresh URLs", iface.mainWindow())
        self.action_refresh.triggered.connect(self.refresh_urls)

        self.action_styles = QAction("Open Styles Folder…", iface.mainWindow())
        self.action_styles.triggered.connect(self.open_styles_folder)

        self.action_help = QAction("Help / About", iface.mainWindow())
        self.action_help.triggered.connect(self.show_about)

    def initGui(self):
        self.iface.addToolBarIcon(self.action_load_toolbar)
        for act in (
            self.action_load_menu,
            self.action_edit_urls,
            self.action_refresh,
            self.action_styles,
            self.action_help,
        ):
            self.iface.addPluginToMenu("&REST Loader", act)

    def unload(self):
        self.iface.removeToolBarIcon(self.action_load_toolbar)
        for act in (
            self.action_load_menu,
            self.action_edit_urls,
            self.action_refresh,
            self.action_styles,
            self.action_help,
        ):
            self.iface.removePluginMenu("&REST Loader", act)

    def _load_metadata(self):
        """Parse metadata.txt for plugin info."""
        meta = {}
        path = os.path.join(os.path.dirname(__file__), "metadata.txt")
        if not os.path.exists(path):
            return meta
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                meta[key.strip()] = val.strip()
        return meta

    def open_layer_urls(self):
        path = os.path.join(os.path.dirname(__file__),
                            "config", "layer_urls.txt")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            open(path, "a").close()
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def refresh_urls(self):
        QgsMessageLog.logMessage("Layer URLs refreshed from disk",
                                 "RestLoader", Qgis.Info)
        QMessageBox.information(
            self.iface.mainWindow(),
            self.meta.get("name", "REST Loader"),
            "Layer URLs have been refreshed. Reopen the loader to see updates."
        )

    def open_styles_folder(self):
        path = os.path.join(os.path.dirname(__file__), "styles")
        os.makedirs(path, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def show_about(self):
        name = self.meta.get("name", "REST Loader")
        version = self.meta.get("version", "")
        author = self.meta.get("author", "")
        desc = self.meta.get("description", "")
        homepage = self.meta.get("homepage", "")
        repo = self.meta.get("repository", "")  # pulled from metadata.txt

        html = f"<b>{name}</b><br/>"
        if version:
            html += f"Version {version}<br/>"
        if author:
            html += f"By {author}<br/><br/>"
        if desc:
            html += f"{desc}<br/><br/>"
        if homepage:
            html += f"<a href='{homepage}'>Documentation</a><br/>"
        if repo:
            html += f"<a href='{repo}'>Repository</a>"

        QMessageBox.information(self.iface.mainWindow(),
                                f"{name} — About",
                                html)

    def run(self):
        dlg = RestLoaderDialog()
        if dlg.exec_() != dlg.Accepted:
            return

        method = dlg.extent_method()
        bbox = None
        if method == "extent":
            bbox = iface.mapCanvas().extent()
        elif method == "polygon":
            poly = dlg.selected_polygon_layer()
            if not poly:
                QMessageBox.warning(
                    self.iface.mainWindow(),
                    self.meta.get("name", "REST Loader"),
                    "No polygon selected."
                )
                return
            bbox = poly.selectedFeatures()[0].geometry().boundingBox()

        as_raster = dlg.load_as_raster()
        as_vector = not as_raster

        urls = dlg.selected_urls()
        total = len(urls)
        loaded = 0
        no_data = []
        errors = []

        for url in urls:
            try:
                if "featureserver" in url.lower():
                    status, title = self.load_featureserver_layer(url, bbox)
                else:
                    status, title = self.load_mapserver_layer(url, bbox,
                                                              as_vector)
            except Exception as e:
                status, title = "error", url
                QgsMessageLog.logMessage(
                    f"Exception loading {url}: {e}",
                    "RestLoader", Qgis.Critical)

            if status == "loaded":
                loaded += 1
            elif status == "no_data":
                no_data.append(title)
            else:
                errors.append(title)

        msg = f"Loaded {loaded}/{total} layers."
        if no_data:
            msg += ("\nNo data found in the selected area for: "
                    + ", ".join(no_data))
        if errors:
            msg += "\nFailed to load: " + ", ".join(errors)

        QMessageBox.information(
            self.iface.mainWindow(),
            self.meta.get("name", "REST Loader"),
            msg
        )

    # load_mapserver_layer() and load_featureserver_layer()
    # remain unchanged, returning (status, title) tuples.