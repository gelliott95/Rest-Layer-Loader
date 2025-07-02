# rest_loader.py

import os
import re
import json
import requests
import shutil
from urllib.parse import urlencode

from PyQt5.QtWidgets import QAction, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

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
    """ strip trailing _digits, replace underscores with spaces """
    no_num = re.sub(r'_\d+$', '', raw)
    return no_num.replace('_', ' ')

def _get_urls_path(self):
    tpl = os.path.join(self.plugin_dir, "config", "layer_urls.txt")
    local = os.path.join(self.plugin_dir, "config", "layer_urls.local.txt")
    if not os.path.exists(local):
        shutil.copy(tpl, local)
    return local

def _read_layer_urls(self):
    path = self._get_urls_path()
    with open(path, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f
                if ln.strip() and not ln.startswith("#")]

class RestLoader:
    def __init__(self, iface):
        self.iface = iface
        base = os.path.dirname(__file__)
        icon = QIcon(os.path.join(base, "icon.png"))
        
        #self.meta = self._load_metadata()

        # 1) Load REST Layers (used for both toolbar and menu)
        self.action_load = QAction(icon, "Load REST Layers", iface.mainWindow())
        self.action_load.triggered.connect(self.run)

        # 2) Edit Layer URLs
        self.action_edit_urls = QAction("Edit Layer URLs…", iface.mainWindow())
        self.action_edit_urls.triggered.connect(self.open_layer_urls)

        # 3) Refresh URLs
        self.action_refresh = QAction("Refresh URLs", iface.mainWindow())
        self.action_refresh.triggered.connect(self.refresh_urls)

        # 4) Open Styles Folder
        self.action_styles = QAction("Open Styles Folder…", iface.mainWindow())
        self.action_styles.triggered.connect(self.open_styles_folder)

        # 5) Help / About
        self.action_help = QAction("Help / About", iface.mainWindow())
        self.action_help.triggered.connect(self.show_about)

    def initGui(self):
        # Toolbar: icon only
        self.iface.addToolBarIcon(self.action_load)

        # Plugins menu: all actions with labels
        for act in (
            self.action_load,
            self.action_edit_urls,
            self.action_refresh,
            self.action_styles,
            self.action_help
        ):
            self.iface.addPluginToMenu("&REST Loader", act)

    def unload(self):
        # Clean up toolbar
        self.iface.removeToolBarIcon(self.action_load)

        # Clean up menu
        for act in (
            self.action_load,
            self.action_edit_urls,
            self.action_refresh,
            self.action_styles,
            self.action_help
        ):
            self.iface.removePluginMenu("&REST Loader", act)
            
    def open_layer_urls(self):
        path = os.path.join(os.path.dirname(__file__), "config", "layer_urls.local.txt")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            open(path, "a").close()
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def refresh_urls(self):
        # Since the dialog always re-reads the file, just notify the user.
        QgsMessageLog.logMessage("Layer URLs refreshed from disk", "RestLoader", Qgis.Info)
        QMessageBox.information(
            self.iface.mainWindow(),
            "REST Loader",
            "Layer URLs have been refreshed. Open the loader to see updates."
        )

    def open_styles_folder(self):
        path = os.path.join(os.path.dirname(__file__), "styles")
        os.makedirs(path, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def show_about(self):
        text = (
            "<b>REST Loader</b><br/>"
            "Version 0.0.1<br/>"
            "Load Esri MapServer & FeatureServer layers into QGIS<br/>"
            "By Grant Elliott<br/>"
            "<a href='https://github.com/gelliott95/Rest-Layer-Loader'>Documentation</a>"
        )
        QMessageBox.information(self.iface.mainWindow(), "REST Loader — About", text)


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
                QMessageBox.warning(self.iface.mainWindow(), "REST Loader", "No polygon selected.")
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
                    status, title = self.load_mapserver_layer(url, bbox, as_vector)
            except Exception as e:
                status, title = "error", url
                QgsMessageLog.logMessage(f"Exception loading {url}: {e}", "RestLoader", Qgis.Critical)

            if status == "loaded":
                loaded += 1
            elif status == "no_data":
                no_data.append(title)
            else:
                errors.append(title)

        msg = f"Loaded {loaded}/{total} layers."
        if no_data:
            msg += "\nNo data found in the selected area for: " + ", ".join(no_data)
        if errors:
            msg += "\nFailed to load: " + ", ".join(errors)
        QMessageBox.information(self.iface.mainWindow(), "REST Loader Summary", msg)

    def apply_style(self, layer):
        plugin_dir = os.path.dirname(__file__)
        style_name = clean_title(layer.name())
        style_path = os.path.join(plugin_dir, "styles", f"{style_name}.qml")
        if os.path.exists(style_path):
            layer.loadNamedStyle(style_path)
            layer.triggerRepaint()
    def load_mapserver_layer(self, url, bbox=None, as_vector=False):
        parts = url.rstrip("/").split("/")
        base, idx = "/".join(parts[:-1]), parts[-1]
        if not idx.isdigit():
            return "error", url

        # metadata
        try:
            meta = requests.get(f"{base}/{idx}?f=json", timeout=5).json()
            raw = meta.get("name", f"{parts[-2]}_{idx}")
            caps = meta.get("capabilities", "")
        except Exception:
            raw, caps = f"{parts[-2]}_{idx}", ""

        title = clean_title(raw)

        # vector path
        if as_vector:
            if "Query" not in caps:
                return "error", title

            qurl = f"{base}/{idx}/query"
            params = {"f": "geojson", "where": "1=1", "outFields": "*", "outSR": 4326}
            if bbox:
                src = iface.mapCanvas().mapSettings().destinationCrs()
                dst = QgsCoordinateReferenceSystem(4326)
                xform = QgsCoordinateTransform(src, dst, QgsProject.instance())
                e = xform.transform(bbox)
                params.update({
                    "geometry": json.dumps({
                        "xmin": e.xMinimum(),
                        "ymin": e.yMinimum(),
                        "xmax": e.xMaximum(),
                        "ymax": e.yMaximum(),
                        "spatialReference": {"wkid": 4326}
                    }),
                    "geometryType": "esriGeometryEnvelope",
                    "inSR": 4326,
                    "spatialRel": "esriSpatialRelIntersects"
                })

            uri = f"{qurl}?{urlencode(params)}"
            layer = QgsVectorLayer(uri, title, "ogr")
            if layer.isValid() and layer.wkbType() != QgsWkbTypes.NoGeometry:
                QgsProject.instance().addMapLayer(layer)
                self.apply_style(layer)
                return "loaded", title
            else:
                return "no_data", title

        # raster path
        arc_uri = f"url={base}/{idx}"
        raster = QgsRasterLayer(arc_uri, title, "arcgismapserver")
        if raster.isValid():
            QgsProject.instance().addMapLayer(raster)
            self.apply_style(raster)
            return "loaded", title

        # WMS fallback
        services = base.replace("/rest/services", "/services")
        wms_url = f"{services}/WMSServer?service=WMS&request=GetMap&version=1.3.0"
        wms_params = {
            "layers": idx,
            "styles": "",
            "format": "image/png",
            "transparent": "true",
            "crs": "EPSG:3857"
        }
        wms_uri = f"url={wms_url}&" + "&".join(f"{k}={v}" for k, v in wms_params.items())
        wms = QgsRasterLayer(wms_uri, title, "wms")
        if wms.isValid():
            QgsProject.instance().addMapLayer(wms)
            self.apply_style(wms)
            return "loaded", title

        # XYZ fallback
        tile_url = f"{base}/{idx}/tile/{{z}}/{{y}}/{{x}}"
        xyz = QgsRasterLayer(f"type=xyz&url={tile_url}", title, "xyz")
        if xyz.isValid():
            QgsProject.instance().addMapLayer(xyz)
            self.apply_style(xyz)
            return "loaded", title

        return "error", title

    def load_featureserver_layer(self, url, bbox=None):
        parts = url.rstrip("/").split("/")
        idx = parts[-1]
        service_base = "/".join(parts[:-1])
        if not idx.isdigit():
            return "error", url

        # fetch name
        try:
            meta = requests.get(f"{service_base}/{idx}?f=json", timeout=5).json()
            raw = meta.get("name", meta.get("serviceDescription", f"{parts[-2]}_{idx}"))
        except Exception:
            raw = f"{parts[-2]}_{idx}"

        title = clean_title(raw)

        # native provider
        layer = QgsVectorLayer(url, title, "arcgisfeatureserver")
        if layer.isValid() and layer.wkbType() != QgsWkbTypes.NoGeometry:
            QgsProject.instance().addMapLayer(layer)
            self.apply_style(layer)
            return "loaded", title

        # OGR GeoJSON
        query_url = f"{service_base}/{idx}/query"
        params = {
            "f": "geojson",
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": 4326
        }
        if bbox:
            src = iface.mapCanvas().mapSettings().destinationCrs()
            dst = QgsCoordinateReferenceSystem(4326)
            xform = QgsCoordinateTransform(src, dst, QgsProject.instance())
            e = xform.transform(bbox)
            params.update({
                "geometry": json.dumps({
                    "xmin": e.xMinimum(),
                    "ymin": e.yMinimum(),
                    "xmax": e.xMaximum(),
                    "ymax": e.yMaximum(),
                    "spatialReference": {"wkid": 4326}
                }),
                "geometryType": "esriGeometryEnvelope",
                "inSR": 4326,
                "spatialRel": "esriSpatialRelIntersects"
            })

        geojson_uri = f"{query_url}?{urlencode(params)}"
        layer = QgsVectorLayer(geojson_uri, title, "ogr")
        if layer.isValid() and layer.wkbType() != QgsWkbTypes.NoGeometry:
            QgsProject.instance().addMapLayer(layer)
            self.apply_style(layer)
            return "loaded", title

        # manual fallback
        resp = requests.get(query_url, params=params, timeout=30)
        resp.raise_for_status()
        feats = resp.json().get("features", [])

        if not feats:
            return "no_data", title

        # determine geometry
        g0 = feats[0].get("geometry", {})
        if "x" in g0 and "y" in g0:
            geom_type = "Point"
        elif "paths" in g0:
            geom_type = "LineString"
        elif "rings" in g0:
            geom_type = "Polygon"
        else:
            return "error", title

        mem = QgsVectorLayer(f"{geom_type}?crs=EPSG:4326", title, "memory")
        dp = mem.dataProvider()
        attrs = feats[0].get("attributes", {})
        dp.addAttributes([QgsField(k, QVariant.String) for k in attrs.keys()])
        mem.updateFields()

        to_add = []
        for feat_json in feats:
            feat = QgsFeature(mem.fields())
            for k, v in feat_json.get("attributes", {}).items():
                feat[k] = str(v)
            geom = feat_json.get("geometry", {})
            if geom_type == "Point":
                feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(geom["x"], geom["y"])))
            elif geom_type == "LineString":
                pts = [QgsPointXY(x, y) for part in geom["paths"] for x, y in part]
                feat.setGeometry(QgsGeometry.fromPolylineXY(pts))
            else:
                rings = [[QgsPointXY(x, y) for x, y in ring] for ring in geom["rings"]]
                feat.setGeometry(QgsGeometry.fromPolygonXY(rings))
            to_add.append(feat)

        dp.addFeatures(to_add)
        QgsProject.instance().addMapLayer(mem)
        self.apply_style(mem)
        return "loaded", title
