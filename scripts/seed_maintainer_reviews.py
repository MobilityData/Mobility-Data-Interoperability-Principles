"""Set up one `maintainer-review` issue per specification from the tracking sheet.

One-off helper. Only three columns of the private sheet are read
(Specification, Review Status, Review Date): contact details, evidence links
and comments are never read, so they cannot end up in an issue.

Each issue gets the `maintainer-review` label, one `review: ...` status label,
and a body holding only the specification id and the review date.

    python3 scripts/seed_maintainer_reviews.py SHEET.csv
        Print what each issue would carry. Changes nothing.

    python3 scripts/seed_maintainer_reviews.py SHEET.csv --json issues.json
        Also write the issues in the GitHub API's shape, for a local preview:
        MDIP_REVIEWS_FILE=issues.json make serve

    python3 scripts/seed_maintainer_reviews.py SHEET.csv --apply
        Open the missing issues on GitHub with `gh`, and bring the existing
        ones (body and status label) in line with the sheet.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import maintainer_review as mr  # noqa: E402
import spec_data  # noqa: E402

COLUMNS = ("Specification", "Review Status", "Review Date")

SHEET_STATUS = {
    "asked": "requested",
    "review in progress": "in_progress",
    "no answer": "no_answer",
    "reviewed": "reviewed",
}

# Sheet name -> registry id. None: not published (no file in
# data/specifications/ yet, or a row superseded by another one).
SHEET_IDS = {
    "GTFS Schedule": "gtfs-schedule",
    "GTFS Realtime": "gtfs-realtime",
    "GBFS (General Bikeshare Feed)": "gbfs",
    "MDS (Mobility Data Specification)": None,  # superseded by the row below
    "MDS - Mobility Data Specification": "mds",
    "NeTEx Profile - Regional Rail": None,
    "CDS (Curb Data Specification)": "cds",
    "CDS-M (City Data Standard - Mobility)": "cds-m",
    "TODS (Transit Operational Data)": "tods",
    "TIDES (Transit Integrated Exchange)": "tides",
    "Transmodel": None,
    "NeTEx (Network & Timetable Exchange)": "netex",
    "SIRI (Real Time Information)": "siri",
    "OpRa (Operating Raw Data)": "opra",
    "OJP (Open Journey Planner)": "ojp",
    "ITxPT Architecture": "itxpt",
    "GTNS (General Travel Network)": "gtns",
    "GMNS (General Modeling Network)": "gmns",
    "VDV / VDV-KA": "vdv",
    "TransXChange (TXC)": "transxchange",
    "GOFS (General On-Demand Feed)": "gofs",
    "GTFS Flex": "gtfs-flex",
    "TOMP API": "tomp-api",
    "ISO 7874": "iso-7874",
    "NEMTAC 1000": "nemtac-1000",
    "Overture Maps Transportation": "overture-maps",
    "OpenStreetMap (OSM) Pedestrian": "osm",
    "OSM BNA Guide": "osm-bna-guide",
    "OpenSidewalks Exchange": "opensidewalks",
    "Connect-OS": "connect-os",
    "OSM US Ped WG": "osm-us-pedestrian-wg",
    "GATIS": "gatis",
    "IMDF": "imdf",
    "shared-row": "shared-row",
    "Statewide Trails Standard (MA)": "statewide-trails-data-standard-ma",
    "ISO GDF 5.1": "iso-20524-2",
    "SAE J2735": "sae-j2735",
    "NCHRP 08-177": "nchrp-08-177",
    "NCHRP 07-31": "nchrp-07-31",
    "MAT": "mat",
    "OpenTrails": "opentrails",
    "Cyclables Data Schema (FR)": "schema-amenagements-cyclables",
    "Bike Parking Schema (FR)": "schema-stationnement-cyclable",
    "APDS": "apds",
    "IXSI": "ixsi",
    "CurbLR": "curblr",
    "ASAM OpenDRIVE": "asam-opendrive",
}


def read_sheet(path):
    """The sheet's rows, reduced to COLUMNS. The header row is found by name."""
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))
    for n, row in enumerate(rows):
        cells = [c.strip() for c in row]
        if "Specification" in cells and "Review Status" in cells:
            index = {c: cells.index(c) for c in COLUMNS if c in cells}
            break
    else:
        sys.exit("No header row with 'Specification' and 'Review Status' in %s" % path)
    out = []
    for row in rows[n + 1:]:
        rec = {c: (row[i].strip() if i < len(row) else "") for c, i in index.items()}
        if rec.get("Specification"):
            out.append(rec)
    return out


def plan(sheet, specs):
    """(issues, notes) after checking every row against data/."""
    by_id = {s["id"]: s for s in specs}
    seen, issues, notes = {}, [], []
    for rec in sheet:
        name = rec["Specification"]
        if name not in SHEET_IDS:
            notes.append("%s: not mapped to a registry id, skipped" % name)
            continue
        sid = SHEET_IDS[name]
        if sid is None:
            notes.append("%s: not published, skipped" % name)
            continue
        seen.setdefault(sid, []).append(rec)
    for sid, recs in seen.items():
        if len(recs) > 1:
            notes.append("%s: %d rows in the sheet, skipped until one is kept" % (sid, len(recs)))
            continue
        rec = recs[0]
        status = SHEET_STATUS.get(rec["Review Status"].lower())
        if not status:
            notes.append("%s: unknown review status, skipped" % sid)
            continue
        issues.append({
            "id": sid,
            "title": "Maintainer review: %s" % by_id[sid]["short_name"],
            "body": mr.make_body(sid, rec.get("Review Date")),
            "labels": [mr.LABEL, mr.REVIEW_STATUS[status]["github_label"]],
        })
    for sid in sorted(set(by_id) - set(seen)):
        notes.append("%s: not in the sheet, no status shown" % sid)
    return issues, notes


def gh(*args):
    return subprocess.run(["gh", *args, "--repo", spec_data.GITHUB_REPO],
                          check=True, capture_output=True, text=True).stdout


def ensure_labels():
    have = {l["name"] for l in json.loads(gh("label", "list", "--limit", "200", "--json", "name"))}
    colours = {"reviewed": "0E8A16"}
    for key, meta in mr.REVIEW_STATUS.items():
        if meta["github_label"] not in have:
            gh("label", "create", meta["github_label"], "--color", colours.get(key, "FBCA04"))
            print("label created: %s" % meta["github_label"])


def apply(issues):
    ensure_labels()
    existing = {}
    for i in json.loads(gh("issue", "list", "--label", mr.LABEL, "--state", "all",
                           "--limit", "500", "--json", "number,body,labels")):
        existing[mr.parse_body(i["body"]).get("specification id", "")] = i
    for want in issues:
        have = existing.get(want["id"])
        if have is None:
            args = ["issue", "create", "--title", want["title"], "--body", want["body"]]
            for l in want["labels"]:
                args += ["--label", l]
            print("created %s: %s" % (want["id"], gh(*args).strip()))
            continue
        num = str(have["number"])
        current = {l["name"] for l in have["labels"]}
        args = ["issue", "edit", num, "--body", want["body"]]
        for l in sorted(current - set(want["labels"])):
            if l.startswith("review: "):
                args += ["--remove-label", l]
        for l in want["labels"]:
            if l not in current:
                args += ["--add-label", l]
        gh(*args)
        print("updated %s: #%s" % (want["id"], num))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("sheet")
    ap.add_argument("--json", help="write the issues as GitHub API JSON for a local preview")
    ap.add_argument("--apply", action="store_true", help="create or update the issues on GitHub")
    args = ap.parse_args()

    data = spec_data.build_dataset()
    issues, notes = plan(read_sheet(args.sheet), data["specs"])

    for i in sorted(issues, key=lambda i: i["id"]):
        rec, _ = mr.review_from_issue({"body": i["body"], "labels": i["labels"]})
        print("%-36s %-40s %s" % (i["id"], rec["status_label"], rec["date"] or ""))
    print("\n%d issues." % len(issues))
    for n in notes:
        print("note: " + n)

    if args.json:
        with open(args.json, "w") as fh:
            json.dump([{"number": n + 1, "title": i["title"], "body": i["body"], "updated_at": "",
                        "labels": [{"name": l} for l in i["labels"]]}
                       for n, i in enumerate(issues)], fh, indent=1)
        print("wrote %s" % args.json)

    if args.apply:
        apply(issues)


if __name__ == "__main__":
    main()
