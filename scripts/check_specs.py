"""Validate the specification registry in data/ and summarise it.

Run with `make specs-check`; the pull request workflow runs it too. Errors
(an unknown vocabulary value or key, a maintainer with no organization file,
a malformed URL) exit with status 1. Warnings are printed but do not fail:
they point at data that is valid but worth a second look, such as a recorded
status the verdicts do not support.

`--export DIR` also writes the API files (see spec_api.py) into DIR, which is
how to get the full export without building the site.
"""

from __future__ import annotations

import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import spec_api  # noqa: E402
import spec_data  # noqa: E402

SITE_URL = "https://interoperablemobility.org/"


def main(argv):
    data = spec_data.build_dataset()
    specs = data["specs"]

    print("%d specifications, %d organizations, %d principles"
          % (len(specs), len(data["organizations"]), len(data["criteria"])))
    for label, n in Counter(s["status_label"] for s in specs).most_common():
        print("  %-22s %d" % (label, n))

    print("\nDisplay order (known adopters first, then ranking score):")
    for s in specs:
        score = "-" if s["score"] is None else "%+d" % s["score"]
        count = "" if s["adopters_count"] is None else "%d adopters" % s["adopters_count"]
        print("  %4s  %-36s %-20s %s" % (score, s["short_name"][:36], s["status_label"], count))

    for key in sorted(k for k in data["organizations"]
                      if not any(k in s["maintainer_ids"] for s in specs)):
        data["issues"].append({"level": "warning",
                               "where": spec_data.entry_path(spec_data.ORGS_DIR, key),
                               "detail": "not referenced by any specification"})

    if "--export" in argv:
        out = argv[argv.index("--export") + 1]
        files = spec_api.build_api(data, SITE_URL)
        for path, text in files.items():
            dest = os.path.join(out, path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write(text)
        print("\nWrote %d API files to %s" % (len(files), os.path.join(out, spec_api.API_DIR)))

    errors = [i for i in data["issues"] if i["level"] == "error"]
    warnings = [i for i in data["issues"] if i["level"] == "warning"]
    for title, items in (("WARNINGS", warnings), ("ERRORS", errors)):
        if items:
            print("\n%s (%d)" % (title, len(items)))
            for i in items:
                print("  %s: %s" % (i["where"], i["detail"]))

    if errors:
        print("\nFix the errors above; data/README.md lists the allowed values.")
        return 1
    print("\nOK: no errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
