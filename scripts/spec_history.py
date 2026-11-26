"""Past values of the registry, read from the repository's git history.

Every change to a file in data/ is a commit, so the history of a value needs
no extra bookkeeping: each revision of a specification file is read back and
parsed like the current one. Only the known adopters counts (data producers
and data consumers) are tracked today, for the chart in the Adoption section
of each specification page.

The file's own `adoption.history` rows come on top: they fill in dates the
repository does not know about, and replace its value for a date they share,
so a count that was wrong when it was committed can be corrected.

Everything here is best effort. Without git, outside a clone, or in a shallow
clone the history is simply shorter or empty, and the page leaves the chart
out rather than failing the build.
"""

from __future__ import annotations

import subprocess

import spec_data

_CACHE = {}


def _git(args, stdin=None):
    return subprocess.run(["git", "-C", spec_data.ROOT] + args, input=stdin,
                          capture_output=True, check=True).stdout


def _revisions():
    """{repository path: [(commit, commit date), ...]}, oldest first."""
    log = _git(["log", "--reverse", "--format=%x00%H %cs", "--name-only", "--",
                "data/" + spec_data.SPECS_DIR]).decode("utf-8")
    out = {}
    for block in log.split("\0")[1:]:
        lines = [l for l in block.splitlines() if l.strip()]
        sha, date = lines[0].split()
        for path in lines[1:]:
            out.setdefault(path, []).append((sha, date))
    return out


def _blobs(refs):
    """Contents of many `<commit>:<path>` at once, None where a path is gone."""
    if not refs:
        return {}
    raw = _git(["cat-file", "--batch"], ("\n".join(refs) + "\n").encode("utf-8"))
    out, pos = {}, 0
    for ref in refs:
        end = raw.index(b"\n", pos)
        header = raw[pos:end].decode("utf-8")
        pos = end + 1
        if header.endswith(" missing"):
            out[ref] = None
            continue
        size = int(header.rsplit(" ", 1)[1])
        out[ref] = raw[pos:pos + size].decode("utf-8", "replace")
        pos += size + 1
    return out


def _whole(value):
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _adopters(text):
    """(producers, consumers, count date) in one revision of a file.

    Before data consumers were counted apart, the file had one
    `adopters_count`; it counted data producers, and is read as such.
    """
    try:
        front, _sections = spec_data.parse_entry(text)
    except Exception:       # a broken revision is skipped, not fatal
        return None
    adoption = front.get("adoption") if isinstance(front, dict) else None
    if not isinstance(adoption, dict):
        return None
    producers = _whole(adoption.get("data_producers_count",
                                    adoption.get("adopters_count")))
    consumers = _whole(adoption.get("data_consumers_count"))
    if producers is None and consumers is None:
        return None
    return (producers or 0, consumers or 0,
            spec_data.as_text(adoption.get("adopters_count_updated")) or None)


def _committed_counts():
    """{path: [(producers, consumers, count date or None, commit date), ...]}.

    A revision that leaves the counts and their date as they were (any other
    edit to the file) is not a new count, so it is skipped.
    """
    try:
        head = _git(["rev-parse", "HEAD"]).decode().strip()
    except (OSError, subprocess.CalledProcessError):
        return {}
    if head not in _CACHE:
        try:
            revisions = _revisions()
            refs = ["%s:%s" % (sha, path) for path, revs in revisions.items()
                    for sha, _date in revs]
            blobs = _blobs(refs)
        except (OSError, subprocess.CalledProcessError, ValueError):
            revisions, blobs = {}, {}
        counts = {}
        for path, revs in revisions.items():
            for sha, date in revs:
                text = blobs.get("%s:%s" % (sha, path))
                found = _adopters(text) if text else None
                seen = counts.setdefault(path, [])
                if found is not None and (not seen or seen[-1][:3] != found):
                    seen.append(found + (date,))
        _CACHE.clear()
        _CACHE[head] = counts
    return _CACHE[head]


def _point(date, producers, consumers, source):
    return {"date": date, "data_producers": producers, "data_consumers": consumers,
            "count": producers + consumers, "source": source}


def committed_series(spec):
    """The counts the repository's history records, one point per date.

    The date is the one the count was taken (`adopters_count_updated`) when
    the file gives one, otherwise the date of the commit that recorded it. A
    later value for the same date replaces the earlier one.
    """
    points = {}
    for producers, consumers, updated, date in _committed_counts().get(spec["source_path"], []):
        points[updated or date] = _point(updated or date, producers, consumers, "git")
    return [points[d] for d in sorted(points)]


def adopters_series(spec, today=None):
    """Known adopters over time for one specification, oldest first.

    Three layers, each replacing the one before for a date they share: the
    repository's history, the counts in the file as it is now (so a local
    edit shows up in a preview before it is committed), and the rows of the
    file's `adoption.history`.
    """
    points = dict((p["date"], p) for p in committed_series(spec))
    producers, consumers = spec["data_producers_count"], spec["data_consumers_count"]
    if producers is not None or consumers is not None:
        import datetime
        date = spec["adopters_count_updated"] or today or datetime.date.today().isoformat()
        current = _point(date, producers or 0, consumers or 0, "current")
        if date not in points or (points[date]["data_producers"], points[date]["data_consumers"]) \
                != (current["data_producers"], current["data_consumers"]):
            points[date] = current
    for row in spec.get("adopters_history") or []:
        points[row["date"]] = _point(row["date"], row["data_producers"], row["data_consumers"],
                                     "manual")
    return [points[d] for d in sorted(points)]
