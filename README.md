Rest-Layer-Loader
The REST Loader plugin for QGIS lets you quickly load Esri MapServer and FeatureServer layers into QGIS with vector or raster options, apply consistent symbology, and manage your service URLs from a simple menu.
Features:
- Load MapServer layers as vector or raster (toggle in dialog)
- Native FeatureServer and GeoJSON/OGR support with memory-layer fallback
- Single summary popup showing loaded, no-data, and failed layers
- Automatic QML style application from a styles/ folder
- One-click menu items to edit your layer URLs, refresh the URL list, open the styles folder, and view Help/About
Installation:
- Clone or download this repository into your QGIS plugins folder. For example: ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/rest_loader
- Restart QGIS or open Plugins > Manage and Install Plugins… > Installed > Refresh
- Enable REST Loader in the plugin list
Usage:
- Click the REST Loader toolbar icon or choose Plugins > REST Loader > Load REST Layers
- In the dialog:
- Choose your spatial filter (All, Current Map Extent, or Selected Polygon)
- Check Load as Raster if you prefer raster loading (uncheck for vector first)
- Select the services you want to load. URLs appear below each title
- Click OK
- A summary popup reports how many layers loaded successfully, which had no data, and any failures
Adding New URLs:
- Select Plugins > REST Loader > Edit Layer URLs… in QGIS
- In config/layer_urls.txt add or remove service endpoints. Example entries: https://server.example.com/MapServer/2 https://server.example.com/FeatureServer/0
- Save the file
- Select Plugins > REST Loader > Refresh URLs, then reopen the loader dialog to see your updates
Naming & Styling Layers: When your services load, QGIS names each layer based on the URL endpoint’s last path segment, cleaned by:
- Stripping any trailing _digits
- Replacing all underscores (_) with spaces
Example: URL: https://server.example.com/MapServer/Crude_Oil_Trunk_Pipelines_1 becomes layer name: Crude Oil Trunk Pipelines
To apply a custom QML style:
- Place your QML files in the plugin’s styles/ folder
- Name each QML file to match the cleaned layer name exactly, plus the .qml extension For the example above, the style file must be named: Crude Oil Trunk Pipelines.qml
- On load, the plugin searches styles/ for a QML file matching the layer’s cleaned title and applies it automatically
Help & About: Use Plugins > REST Loader > Help / About to view plugin metadata—name, version, author, description, documentation, and repository links—pulled from metadata.txt
Development & Contributing: metadata.txt holds plugin information (name, version, author, homepage, repository, description) rest_loader_dialog.py implements the URL list and options dialog rest_loader.py contains the core logic for loading, styling, and menu actions
Feel free to submit issues or pull requests on GitHub!
