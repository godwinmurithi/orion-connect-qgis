# Changelog

All notable changes to Orion Connect. Versions follow [Semantic Versioning](https://semver.org/); the same entries are in `orion_connect/metadata.txt` (`changelog=`), which QGIS shows in the Plugin Manager.

## 0.2.0 (2026-10-31)

- Ready for QGIS 4 (Qt6): fully scoped Qt enums and `exec()`; `supportsQt6=True`.
- The toolbar is created in `initGui()` and removed on `unload()`, so reloading the plugin leaves no empty toolbar.
- New **Help** menu entry linking to the online guide.
- OrionInsights link updated to `https://orionterrametrics.com/insights`.
- Fixed: search now filters by title and description (before, every dataset matched).
- New icon; GPL-2.0-or-later `LICENSE` included in the package.

## 0.1.0 (2026-09-13)

- First release: sign in, browse and search, add as WMS/WFS, upload a layer, open OrionInsights.
