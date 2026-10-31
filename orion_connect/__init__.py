# Orion Connect — QGIS entry point.
#
# QGIS loads a plugin by importing this package and calling classFactory(iface).
# Kept import-light (no qgis.PyQt/qgis.core imports at module scope beyond what
# the factory function itself needs) so metadata inspection and packaging
# tools that import this file outside a running QGIS process don't fail.


def classFactory(iface):  # noqa: N802 — QGIS's own required entry-point name
    from .orion_connect_plugin import OrionConnectPlugin

    return OrionConnectPlugin(iface)
