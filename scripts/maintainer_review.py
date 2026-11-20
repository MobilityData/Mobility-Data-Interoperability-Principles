"""Where each specification's assessment stands in its review by the maintainer.

The status is not kept in data/: it lives in one GitHub issue per
specification, labelled `maintainer-review`, so the team changes it on GitHub
with no commit and no pull request.

- The status is the issue's `review: ...` label (see REVIEW_STATUS).
- The issue body holds only the specification id and the date of the last
  status change. The redeploy workflow rewrites that date whenever a status
  label is added, so nobody edits the body by hand:

      ### Specification id

      gbfs

      ### Review date

      2026-10-24

Trust: only issues carrying the `maintainer-review` label are read, and only
people with triage access can add labels, so a visitor cannot publish a status.

`load()` is called once per build. It never fails the build: when GitHub cannot
be reached it logs a warning and the pages simply show no review status.

    MDIP_REVIEWS=off          skip the lookup (offline builds)
    MDIP_REVIEWS_FILE=path    read issues from a JSON file instead of GitHub,
                              in the shape the GitHub issues API returns
    GITHUB_TOKEN              optional; raises the API rate limit
"""

from __future__ import annotations

import json
import logging
import os
import re
import urllib.request
from collections import OrderedDict

LABEL = "maintainer-review"
API = "https://api.github.com/repos/%s/issues?labels=%s&state=all&per_page=100&page=%d"
MAX_PAGES = 5

# key: GitHub label, text on the page, tone, whether the date is shown.
REVIEW_STATUS = OrderedDict([
    ("requested", {"github_label": "review: requested",
                   "label": "Assessment review requested", "tone": "warn", "dated": True}),
    ("in_progress", {"github_label": "review: in progress",
                     "label": "Assessment under review by maintainer", "tone": "warn",
                     "dated": True}),
    ("no_answer", {"github_label": "review: no answer",
                   "label": "Assessment review requested", "tone": "warn", "dated": False}),
    ("reviewed", {"github_label": "review: reviewed",
                  "label": "Assessment reviewed by maintainer", "tone": "pass", "dated": True}),
])
BY_GITHUB_LABEL = {v["github_label"]: k for k, v in REVIEW_STATUS.items()}

_HEADING_RE = re.compile(r"^###\s+(.+?)\s*$", re.M)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_NO_RESPONSE = "_no response_"

log = logging.getLogger("mkdocs.hooks.maintainer_review")


def parse_body(body):
    """{field heading (lowercase): answer} from an issue form body."""
    fields = {}
    parts = _HEADING_RE.split(body or "")
    for i in range(1, len(parts) - 1, 2):
        value = parts[i + 1].strip()
        fields[parts[i].strip().lower()] = "" if value.lower() == _NO_RESPONSE else value
    return fields


def make_body(spec_id, date):
    return "### Specification id\n\n%s\n\n### Review date\n\n%s\n" % (spec_id, date or "_No response_")


def review_from_issue(issue):
    """The published review record for one issue, or (None, reason)."""
    fields = parse_body(issue.get("body"))
    sid = fields.get("specification id", "").strip()
    if not sid:
        return None, "no specification id"
    names = [l["name"] if isinstance(l, dict) else l for l in issue.get("labels") or []]
    statuses = [BY_GITHUB_LABEL[n] for n in names if n in BY_GITHUB_LABEL]
    if len(statuses) != 1:
        return None, "%d review labels instead of 1" % len(statuses)
    status = statuses[0]
    meta = REVIEW_STATUS[status]
    date = fields.get("review date", "").strip()
    if date and not _DATE_RE.match(date):
        return None, "review date is not YYYY-MM-DD"
    return {
        "spec_id": sid,
        "status": status,
        "status_label": meta["label"],
        "status_tone": meta["tone"],
        "date": (date or None) if meta["dated"] else None,
        "_updated": issue.get("updated_at") or "",
    }, None


def _fetch(repo):
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "mdip-registry-build"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    issues = []
    for page in range(1, MAX_PAGES + 1):
        req = urllib.request.Request(API % (repo, LABEL, page), headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            batch = json.load(resp)
        issues.extend(batch)
        if len(batch) < 100:
            break
    return issues


def _read_issues(repo):
    path = os.environ.get("MDIP_REVIEWS_FILE")
    if path:
        with open(path) as fh:
            return json.load(fh)
    return _fetch(repo)


def load(repo, known_ids):
    """{spec id: review record} for every specification with a review issue."""
    if os.environ.get("MDIP_REVIEWS", "").lower() in ("off", "0", "false", "no"):
        return {}
    try:
        issues = _read_issues(repo)
    except Exception as exc:  # network, rate limit, bad JSON: never fail the build
        log.warning("maintainer review: issues not read, no status shown (%s)", exc)
        return {}

    reviews = {}
    for issue in issues:
        if "pull_request" in issue:
            continue
        record, reason = review_from_issue(issue)
        where = "issue #%s" % issue.get("number", "?")
        if record is None:
            log.warning("maintainer review: %s skipped: %s", where, reason)
            continue
        if record["spec_id"] not in known_ids:
            log.warning("maintainer review: %s names unknown specification %r",
                        where, record["spec_id"])
            continue
        # Several issues for one specification: the most recently updated wins.
        previous = reviews.get(record["spec_id"])
        if previous is None or record["_updated"] > previous["_updated"]:
            reviews[record["spec_id"]] = record
    for record in reviews.values():
        record.pop("_updated", None)
    return reviews


def api_record(review):
    """The review as the JSON API publishes it, or None."""
    if not review:
        return None
    return {"status": {"id": review["status"], "label": review["status_label"]},
            "date": review["date"]}
