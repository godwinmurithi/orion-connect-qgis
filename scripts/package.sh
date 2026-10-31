#!/usr/bin/env bash
# Build the plugin zip the way the QGIS Plugin Repository expects it:
# one top-level folder named after the package (orion_connect/), metadata.txt
# and LICENSE inside it, no __pycache__/.pyc, no VCS files, no binaries
# other than the icon. Output: dist/orion_connect.<version>.zip
set -euo pipefail
cd "$(dirname "$0")/.."
version=$(sed -n 's/^version=//p' orion_connect/metadata.txt)
mkdir -p dist
out="dist/orion_connect.${version}.zip"
rm -f "$out"
find orion_connect -name '__pycache__' -prune -exec rm -rf {} +
python3 - "$out" <<'PY'
import os, sys, zipfile
out = sys.argv[1]
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk("orion_connect"):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for f in sorted(files):
            if f.endswith(".pyc") or f == ".DS_Store":
                continue
            z.write(os.path.join(root, f))
PY
echo "$out"
