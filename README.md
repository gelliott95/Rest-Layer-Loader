# Rest-Layer-Loader
The REST Loader plugin lets you quickly load Esri MapServer and FeatureServer layers into QGIS with vector or raster options, apply consistent symbology, and manage your service URLs from a simple menu.
REST Loader Plugin for QGIS
Overview
The REST Loader plugin lets you quickly load Esri MapServer and FeatureServer layers into QGIS with vector or raster options, apply consistent symbology, and manage your service URLs from a simple menu.
Features
• Load MapServer layers as vector or raster (toggle in dialog)
• Native FeatureServer and GeoJSON/OGR support with memory-layer fallback
• Single summary popup showing loaded, no-data, and failed layers
• Automatic QML style application from a styles/ folder
• One-click menu items to edit your layer URLs, refresh the URL list, open the styles folder, and view Help/About
Installation
- Clone or download this repository into your QGIS plugins folder. For example:
~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/rest_loader
- Restart QGIS or open Plugins ▶ Manage and Install Plugins… ▶ Installed ▶ Refresh.
- Enable “REST Loader” in the plugin list.
Usage
- Click the REST Loader toolbar icon or choose Plugins ▶ REST Loader ▶ Load REST Layers.
- In the dialog:
- Choose your spatial filter (all, current map extent, or selected polygon).
- Check “Load as Raster” if you prefer raster loading (uncheck for vector first).
- Check the services you want to load. URLs are displayed after each title.
- Click OK.
- A summary popup will report how many layers loaded successfully, which had no data, and any failures.
Adding New URLs
- In QGIS select Plugins ▶ REST Loader ▶ Edit Layer URLs…
- In the file config/layer_urls.txt add or remove URLs. Example entries:
https://server.example.com/MapServer/2
https://server.example.com/FeatureServer/0
- Save the file.
- In QGIS select Plugins ▶ REST Loader ▶ Refresh URLs, then reopen the loader dialog to see updates.
Applying Styles
- Place your QML style files in the plugin’s styles/ folder.
- Name each file to match the cleaned layer title:
- Remove any trailing underscore and digits
- Replace underscores with spaces
For example, for a service named Crude_Oil_Trunk_Pipelines_1, name the QML file
Crude Oil Trunk Pipelines.qml
- When the layer loads, the plugin automatically applies the matching QML style.
Help & About
Use Plugins ▶ REST Loader ▶ Help / About to view plugin metadata—name, version, author, description, documentation and repository links—pulled from metadata.txt.
Development & Contributing
• metadata.txt holds plugin information (name, version, author, homepage, repository, description).
• rest_loader_dialog.py implements the URL list and options dialog.
• rest_loader.py contains the core logic for loading, styling, and menu actions.
Feel free to submit issues or pull requests on GitHub.

