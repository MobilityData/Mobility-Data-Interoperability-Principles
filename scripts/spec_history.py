"""Past values of the registry, read from the repository's git history.

Every change to a file in data/ is a commit, so the history of a value needs
no extra bookkeeping: each revision of a specification file is read back and
parsed like the current one. Only the known adopters count is tracked today,
for the chart in the Adoption section of each specification page.

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


def _adopters(text):
    try:
        front, _sections = spec_data.parse_entry(text)
    except Exception:       # a broken revision is skipped, not fatal
        return None, None
    adoption = front.get("adoption") if isinstance(front, dict) else None
    if not isinstance(adoption, dict):
        return None, None
    count = adoption.get("adopters_count")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        return None, None
    return count, spec_data.as_text(adoption.get("adopters_count_updated")) or None


def _committed_counts():
    """{path: [(count, count date or None, commit date), ...]} from git.

    A revision that leaves the count and its date as they were (any other edit
    to the file) is not a new count, so it is skipped.
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
                count, updated = _adopters(text) if text else (None, None)
                seen = counts.setdefault(path, [])
                if count is not None and (not seen or seen[-1][:2] != (count, updated)):
                    seen.append((count, updated, date))
        _CACHE.clear()
        _CACHE[head] = counts
    return _CACHE[head]


def adopters_series(spec, today=None):
    """Known adopters over time for one specification, oldest first.

    One point per date: the date the count was taken (`adopters_count_updated`)
    when the file gives one, otherwise the date of the commit that recorded
    it. The file as it is now is the last point, so a local edit shows up in a
    preview before it is committed. A later value for the same date replaces
    the earlier one, because that is a correction rather than a new count.
    """
    committed = _committed_counts().get(spec["source_path"], [])
    points = dict((updated or date, count) for count, updated, date in committed)
    current = (spec["adopters_count"], spec["adopters_count_updated"])
    if current[0] is not None and (not committed or committed[-1][:2] != current):
        import datetime
        points[current[1] or today or datetime.date.today().isoformat()] = current[0]
    return [{"date": d, "count": points[d]} for d in sorted(points)]
