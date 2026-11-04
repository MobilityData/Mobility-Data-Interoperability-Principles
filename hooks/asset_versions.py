"""Give the site's own stylesheets and scripts a version in their URL.

The server tells browsers they may keep a CSS or JS file for hours without
asking again. The files keep the same name from one deploy to the next, so
after a change a returning visitor gets the new HTML with the old script or
stylesheet, and a page that needs the new one breaks until the copy expires.

Every local entry in `extra_css` and `extra_javascript` is linked as
`<path>?v=<hash of the file>` instead. The hash only changes when the file
does, so browsers keep using their copy until there is a new one, and fetch
it as soon as there is. Visitors never see the suffix; the file served is the
same with or without it.

Material's own bundle is not touched: its file names already carry a hash.
"""

from __future__ import annotations

import hashlib
import os


def _version(path, dirs):
    for base in dirs:
        full = os.path.join(base, path)
        if os.path.isfile(full):
            with open(full, "rb") as fh:
                return hashlib.sha256(fh.read()).hexdigest()[:10]
    return None


def _versioned(path, dirs):
    path = path.split("?v=", 1)[0]          # the config may be reused by `serve`
    if "://" in path or path.startswith("//"):
        return path
    version = _version(path, dirs)
    return "%s?v=%s" % (path, version) if version else path


def on_config(config):
    dirs = [config["docs_dir"]] + list(config["theme"].dirs)
    config["extra_css"] = [_versioned(p, dirs) for p in config["extra_css"]]
    scripts = config["extra_javascript"]
    for n, script in enumerate(scripts):
        if isinstance(script, str):
            scripts[n] = _versioned(script, dirs)
        else:                                # ExtraScriptValue
            script.path = _versioned(script.path, dirs)
    return config
