# Rest-Layer-Loader

**REST Loader** is a QGIS plugin that lets you quickly load Esri MapServer and FeatureServer layers into QGIS with vector or raster options, apply consistent symbology, and manage your service URLs from a simple menu.

---

## 🔧 Features

- Load MapServer layers as **vector** or **raster** (toggle in dialog)
- Native FeatureServer & GeoJSON/OGR support with memory-layer fallback
- Summary popup reporting:
  - Loaded layers
  - No-data layers
  - Load failures
- Automatic QML style application from a `styles/` folder
- One-click menu actions:
  - Edit your layer URLs
  - Refresh the URL list
  - Open the styles folder
  - View Help/About

---

## 🛠 Installation

1. Clone or download this repository into your QGIS plugins folder:  
   `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/rest_loader`

2. Restart QGIS, or go to:  
   `Plugins > Manage and Install Plugins… > Installed > Refresh`

3. Enable **REST Loader** in the plugin list.

---

## 🚀 Usage

- Click the **REST Loader** toolbar icon  
  **OR**  
  Use the menu: `Plugins > REST Loader > Load REST Layers`

### In the dialog:

- Choose a spatial filter:
  - All
  - Current Map Extent
  - Selected Polygon
- Toggle “Load as Raster” to switch between raster/vector
- Tick the services you want to load (URLs shown under each title)
- Click **OK**
- A summary popup will report:
  - Successfully loaded layers
  - No-data layers
  - Failed loads

---

## ➕ Adding New URLs

1. Go to: `Plugins > REST Loader > Edit Layer URLs…`

2. Edit the file: `config/layer_urls.txt`  
   Example: https://server.example.com/MapServer/2
https://server.example.com/FeatureServer/0


3. Save the file

4. Go to: `Plugins > REST Loader > Refresh URLs`  
Then reopen the loader dialog

---

## 🎨 Naming & Styling Layers

When loading, the plugin:

- Extracts the last path segment from the URL (e.g., `Crude_Oil_Trunk_Pipelines_1`)
- Cleans it by:
- Removing trailing `_digits`
- Replacing underscores with spaces
- Applies a matching `.qml` style file from the `styles/` folder

**Example:**

| URL Segment                  | Layer Name                 | Style File                              |
|-----------------------------|----------------------------|-----------------------------------------|
| Crude_Oil_Trunk_Pipelines_1 | Crude Oil Trunk Pipelines  | styles/Crude Oil Trunk Pipelines.qml    |

---

## ❓ Help & About

Use the menu:  
`Plugins > REST Loader > Help / About`

Displays plugin metadata from `metadata.txt`, including:

- Plugin name and version
- Author
- Description
- Documentation and repo links

---

## 🧑‍💻 Development & Contributing

- `metadata.txt` – Plugin info (name, version, author, description, links)
- `rest_loader_dialog.py` – URL list and options dialog
- `rest_loader.py` – Core logic for loading, styling, and menu actions

Feel free to open issues or submit pull requests on GitHub!

