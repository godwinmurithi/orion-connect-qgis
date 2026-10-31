# Orion Connect for QGIS

Orion Connect links QGIS Desktop to [OrionGIS](https://orionterrametrics.com), the AI-native cloud GIS.

- **Search** the datasets hosted on OrionGIS from inside QGIS.
- **Add** any of them to your project as a live **WMS** (raster) or **WFS** (vector) layer in one click.
- **Upload** a layer from your project into your OrionGIS workspace.
- **Open** your OrionInsights dashboards in the browser.

Browsing and adding public layers needs no account. Uploading needs a free OrionGIS account.

- Product page: https://orionterrametrics.com/product/orion-connect
- User guide: https://orionterrametrics.com/docs/connect/qgis-plugin
- Licence: GPL-2.0-or-later (see `LICENSE`)

## Requirements

- QGIS 3.22 or newer (QGIS 4 / Qt6 supported).
- No extra Python packages: the plugin uses only the Python standard library and PyQGIS.

## Install

### From the OrionGIS plugin repository (recommended, updates automatically)

1. In QGIS open **Plugins → Manage and Install Plugins… → Settings**.
2. Under **Plugin repositories** click **Add…**, name it `OrionGIS`, set the URL to
   `https://orionterrametrics.com/qgis/plugins.xml`, and click **OK**.
3. Tick **Show also experimental plugins** (Orion Connect is marked experimental while it is below 1.0).
4. Go to **All**, search for **Orion Connect** and click **Install Plugin**.

### From a ZIP file

1. Download `orion_connect.<version>.zip` from https://orionterrametrics.com/product/orion-connect.
2. In QGIS open **Plugins → Manage and Install Plugins… → Install from ZIP**, choose the file and click **Install Plugin**.

## Use

After installing, an **Orion Connect** toolbar and a **Web → Orion Connect** menu appear.

| Action | What it does |
| --- | --- |
| Sign In… | Enter your OrionGIS URL, username and password. Only needed for uploads. |
| Browse Catalogue / Add Layer… | Search datasets and add the selected one as WMS or WFS. |
| Upload Layer to OrionGIS… | Upload a file (GeoPackage, zipped Shapefile, GeoJSON, GeoTIFF…) to your workspace. |
| Open OrionInsights Dashboards | Opens your dashboards in the browser. |
| Help | Opens the online user guide. |

## Privacy and security

- The plugin talks only to the OrionGIS server you enter (default `https://orionterrametrics.com`), over HTTPS.
- Your password is kept in memory for the QGIS session only. The server URL and username are remembered in QGIS settings; the password is never written to disk.
- No analytics, no third-party services.

## Develop

```bash
git clone https://github.com/godwinmurithi/orion-connect-qgis.git
# Link the package into your QGIS profile for live editing (Linux path shown):
ln -s "$PWD/orion-connect-qgis/orion_connect" ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/orion_connect
```

Use the **Plugin Reloader** plugin to reload after edits.

Layout:

```
orion_connect/            the plugin package (this folder is what QGIS installs)
  metadata.txt            QGIS plugin metadata, including changelog
  __init__.py             classFactory(iface)
  orion_connect_plugin.py initGui()/unload(), toolbar and menu actions
  api_client.py           OrionGIS REST API + OGC layer URIs (standard library only)
  browse_dialog.py        search and add-layer dialog
  login_dialog.py         sign-in dialog
  upload_dialog.py        upload flow with import-status polling
  icon.png, LICENSE
scripts/package.sh        builds dist/orion_connect.<version>.zip
scripts/plugins_xml.py    writes the plugins.xml served by the OrionGIS plugin repository
CHANGELOG.md
```

## Release checklist

Follows the [QGIS plugin repository rules](https://plugins.qgis.org/publish/):

1. Bump `version=` and add a `changelog=` entry in `orion_connect/metadata.txt`; mirror it in `CHANGELOG.md`.
2. `./scripts/package.sh` → `dist/orion_connect.<version>.zip` (single top-level `orion_connect/` folder, `metadata.txt` and `LICENSE` inside, no `__pycache__`/`.pyc`).
3. `python3 scripts/plugins_xml.py > dist/plugins.xml`.
4. Tag `vX.Y.Z`, push, and attach the zip to the GitHub release.
5. Publish the zip and `plugins.xml` on OrionGIS (`app/public/downloads/orion-connect/` and `app/public/qgis/plugins.xml` in the OrionGIS repo).
6. Upload the zip at https://plugins.qgis.org/plugins/add/ (needs an OSGeo account and a public repository).

## Support

Issues: https://github.com/godwinmurithi/orion-connect-qgis/issues · Email: info@orionterrametrics.com
