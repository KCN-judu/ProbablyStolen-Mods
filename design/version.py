"""A mod's version as the tools read it, and the WIP special case.

A mod that is still being made has the version WIP in its manifest.xml. The covers then read WIP where a version
would be, and the release tools (scripts/package.sh, scripts/workshop.py, scripts/release-check.sh) refuse to
release it, so an unfinished mod cannot be published by mistake. The game's own mod validator needs a real version,
so scripts/scan.sh scans a copy of the mod with STAND_IN in place of WIP; the mod's own manifest.xml is never changed.
"""
import os
import re
from typing import Final

WIP: Final = "WIP"
STAND_IN: Final = "0.1.0"   # what the validator sees in place of WIP


def is_wip(version: str | None) -> bool:
    return version is not None and version.strip() == WIP


def read_version(folder: str) -> str | None:
    """The ModVersion of the manifest.xml in `folder`, or None when the folder has no manifest or no version."""
    path = os.path.join(folder, "manifest.xml")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        m = re.search(r"<ModVersion>\s*([^<]+?)\s*</ModVersion>", f.read())
    return m.group(1) if m else None


def version_label(version: str) -> str:
    """The text a cover shows for a version."""
    if is_wip(version):
        return WIP
    # Always the full x.y.z (1.1.0 -> V1.1.0, 1.0.1 -> V1.0.1), except a new major version x.0.0, which reads
    # Vx.0 (1.0.0 -> V1.0, 2.0.0 -> V2.0).
    parts = (version.strip().split(".") + ["0", "0"])[:3]
    if parts[1] == "0" and parts[2] == "0":
        return "V" + parts[0] + ".0"
    return "V" + ".".join(parts)
