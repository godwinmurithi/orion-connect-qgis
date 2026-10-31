#!/usr/bin/env python3
"""Write the plugins.xml for the OrionGIS QGIS plugin repository
(https://orionterrametrics.com/qgis/plugins.xml) from orion_connect/metadata.txt,
in the format QGIS's Plugin Manager reads for custom repositories."""
import configparser
import datetime
import os
import sys
from xml.sax.saxutils import escape

BASE = "https://orionterrametrics.com"
here = os.path.dirname(os.path.abspath(__file__))
cfg = configparser.ConfigParser(interpolation=None)
cfg.read(os.path.join(here, "..", "orion_connect", "metadata.txt"), encoding="utf-8")
m = cfg["general"]
version = m["version"]
zip_name = f"orion_connect.{version}.zip"
today = datetime.date.today().isoformat()


def el(tag: str, value: str) -> str:
    return f"    <{tag}>{escape(value)}</{tag}>"


rows = [
    f'  <pyqgis_plugin name="{escape(m["name"])}" version="{version}" plugin_id="orion_connect">',
    el("description", m["description"]),
    el("about", m["about"]),
    el("version", version),
    el("trusted", "False"),
    el("qgis_minimum_version", m["qgisMinimumVersion"]),
    el("qgis_maximum_version", "4.99.0"),
    el("homepage", m["homepage"]),
    el("file_name", zip_name),
    el("icon", f"{BASE}/downloads/orion-connect/icon.png"),
    el("author_name", m["author"]),
    el("download_url", f"{BASE}/downloads/orion-connect/{zip_name}"),
    el("uploaded_by", "oriongis"),
    el("create_date", "2026-09-13"),
    el("update_date", today),
    el("experimental", m.get("experimental", "False")),
    el("deprecated", m.get("deprecated", "False")),
    el("tracker", m["tracker"]),
    el("repository", m["repository"]),
    el("tags", m["tags"]),
    el("downloads", "0"),
    el("average_vote", "0"),
    el("rating_votes", "0"),
    el("external_dependencies", ""),
    el("server", m.get("server", "False")),
    "  </pyqgis_plugin>",
]
sys.stdout.write('<?xml version="1.0" encoding="UTF-8"?>\n<plugins>\n' + "\n".join(rows) + "\n</plugins>\n")
