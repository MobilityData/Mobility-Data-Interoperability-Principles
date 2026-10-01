"""Load, validate, join and score the MDIP specification registry.

The registry lives in this repository under data/, and GitHub is where it is
reviewed and changed:

    specifications/<id>.md  one file per specification
    organizations/<id>.md   one file per organization (maintainers, for now)
    principles.csv          the assessment methodology and the ranking scores
    licences.csv            the licence ids a specification may use

Each Markdown file is YAML front matter for the structured fields, followed by
a `# Description` section in Markdown. The file name is the id. Every value
outside the free-text fields comes from a fixed vocabulary, defined below and
documented in data/README.md. Nothing is guessed: an unknown value or key is
reported as an error by `Registry`, which `make specs-check` and the pull
request workflow run, so a mistake is caught in review instead of being
quietly reinterpreted at build time.

The score computed here only orders the listing. It is not published on the
site or in the API; data/README.md documents how it is calculated.
"""

from __future__ import annotations

import csv
import datetime as _dt
import glob
import os
import re
from collections import Counter, OrderedDict

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")

SPECS_DIR = "specifications"
ORGS_DIR = "organizations"
PRINCIPLES_CSV = "principles.csv"
LICENCES_CSV = "licences.csv"

GITHUB_REPO = "MobilityData/Mobility-Data-Interoperability-Principles"
GITHUB_BRANCH = "main"

# Keys a front matter block may contain. Anything else is reported, so a typo
# ("maintainer:" for "maintainers:") fails the check instead of vanishing.
SPEC_KEYS = ("short_name", "full_name", "homepage_url", "status", "modes", "maintainers",
             "licences", "licence_evidence_url", "first_release_year", "adoption", "principles")
ADOPTION_KEYS = ("lifecycle", "tier", "adopters_count", "adopters_count_updated",
                 "adopters_registry_url", "confirmed_by_maintainer")
PRINCIPLE_KEYS = ("verdict", "rationale", "evidence_url")
LICENCE_KEYS = ("id", "scopes")
ORG_KEYS = ("name", "short_name", "type", "roles", "url", "logo_url")

# --------------------------------------------------------------------------
# Vocabularies. The keys are what the CSV files contain.
# --------------------------------------------------------------------------

STATUS = OrderedDict([
    ("compliant", {"label": "MDIP Compliant", "tone": "pass", "rank": 0}),
    ("partially_compliant", {"label": "Partially compliant", "tone": "warn", "rank": 1}),
    ("not_compliant", {"label": "Not compliant", "tone": "fail", "rank": 2}),
    ("inactive", {"label": "Inactive project", "tone": "muted", "rank": 3}),
    ("under_review", {"label": "Under review", "tone": "info", "rank": 4}),
])

VERDICT = OrderedDict([
    ("compliant", {"label": "Compliant", "tone": "pass"}),
    ("partially_compliant", {"label": "Partially compliant", "tone": "warn"}),
    ("not_compliant", {"label": "Not compliant", "tone": "fail"}),
    ("unknown", {"label": "Unknown", "tone": "muted"}),
    ("not_assessed", {"label": "Not assessed", "tone": "muted"}),
])

# Verdicts that carry a score from principles.csv. The other two score 0.
SCORED_VERDICTS = ("compliant", "partially_compliant", "not_compliant")

LIFECYCLE = OrderedDict([
    ("active", {"label": "Active", "hint": "In active maintenance with a live user base."}),
    ("early_adoption", {"label": "Early adoption", "hint": "Published and in use by early adopters."}),
    ("pilot_adoption", {"label": "Pilot adoption", "hint": "Being trialled in a small number of deployments."}),
    ("pre_adoption", {"label": "Pre-adoption", "hint": "Published but not yet deployed in production."}),
    ("inactive", {"label": "Inactive", "hint": "No longer maintained."}),
])

# `outcome` ties each tier to a column of the adoption row in principles.csv.
ADOPTION_TIER = OrderedDict([
    ("hundred_plus", {"label": "100+ adopters", "outcome": "compliant"}),
    ("early", {"label": "Early adopters", "outcome": "partially_compliant"}),
    ("pilot", {"label": "Pilot deployments", "outcome": "partially_compliant"}),
    ("none", {"label": "No known adopters", "outcome": "not_compliant"}),
])

CONFIRMED = OrderedDict([
    ("yes", {"label": "Confirmed by maintainer", "tone": "pass"}),
    ("no", {"label": "Not confirmed", "tone": "fail"}),
    ("unknown", {"label": "Unknown", "tone": "muted"}),
])

MODES = OrderedDict([
    ("public_transport", "Public Transport"),
    ("microtransit_drt", "Microtransit/DRT"),
    ("taxi_ridehail", "Taxi/Ridehail"),
    ("bicycle", "Bicycle"),
    ("pedestrian_accessibility", "Pedestrian/Accessibility"),
    ("parking", "Parking"),
])
UNCLASSIFIED = "Unclassified"

ORG_TYPES = OrderedDict([
    ("standards-body", "Standards body"),
    ("nonprofit", "Non-profit"),
    ("government", "Government"),
    ("industry-consortium", "Industry consortium"),
    ("academic", "Academic"),
    ("company", "Company"),
    ("community", "Community"),
    ("individual", "Individual"),
])

ORG_ROLES = OrderedDict([
    ("specification_maintainer", "Specification maintainer"),
])

LICENCE_CATEGORIES = OrderedDict([
    ("open", "Open"),
    ("restricted", "Open with restrictions"),
    ("closed", "Purchase or membership required"),
    ("unknown", "Not stated"),
])

LICENCE_SCOPES = OrderedDict([
    ("specification", "Specification"),
    ("documentation", "Documentation"),
    ("code", "Code"),
    ("data", "Data"),
])

PRINCIPLE_KINDS = ("principle", "bonus", "adoption")
OUTCOMES = ("compliant", "partially_compliant", "not_compliant")

_URL_RE = re.compile(r"^https?://\S+$")
_ID_RE = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_HEADING_RE = re.compile(r"^#\s+(.+?)\s*$", re.M)


def github_url(kind, path=""):
    """Link to the repository: kind is blob, edit, new, tree or issues/new."""
    if kind == "issues/new":
        return "https://github.com/%s/issues/new" % GITHUB_REPO
    return "https://github.com/%s/%s/%s/%s" % (GITHUB_REPO, kind, GITHUB_BRANCH, path)


def entry_path(folder, key):
    """Repository path of one entry, e.g. data/specifications/gtfs-schedule.md."""
    return "data/%s/%s.md" % (folder, key)


def split(value):
    return [v.strip() for v in (value or "").split(";") if v.strip()]


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def as_text(value):
    """YAML turns 2026-09-29 into a date and 2006 into an int; want text."""
    if value is None:
        return ""
    if isinstance(value, (_dt.date, _dt.datetime)):
        return value.isoformat()
    return str(value).strip()


def read_entry(path):
    """Split one Markdown file into (front matter, sections).

    `sections` maps each top-level `# Heading` to the Markdown under it, so
    `# Description` and any section added later are read the same way.
    """
    with open(path, encoding="utf-8") as fh:
        text = fh.read().replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise ValueError("does not start with a --- front matter block")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("front matter block is not closed with ---")
    front = yaml.safe_load(text[4:end]) or {}
    if not isinstance(front, dict):
        raise ValueError("front matter is not a set of key: value pairs")
    body = text[end + 5:]
    sections = OrderedDict()
    marks = list(_HEADING_RE.finditer(body))
    for n, m in enumerate(marks):
        stop = marks[n + 1].start() if n + 1 < len(marks) else len(body)
        sections[m.group(1)] = body[m.end():stop].strip()
    return front, sections


def read_entries(folder):
    for path in sorted(glob.glob(os.path.join(DATA_DIR, folder, "*.md"))):
        yield os.path.splitext(os.path.basename(path))[0], path


def read_csv(name):
    path = os.path.join(DATA_DIR, name)
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = [dict((k, (v or "").strip()) for k, v in row.items() if k) for row in reader]
        return reader.fieldnames or [], rows


class Registry(object):
    """The four files, validated and joined."""

    def __init__(self):
        self.issues = []
        self.principles, self.bonus, self.adoption = self._load_principles()
        self.licences = self._load_licences()
        self.organizations = self._load_organizations()
        self.specs = self._load_specs()

    # -- reporting ---------------------------------------------------------
    def error(self, where, detail):
        self.issues.append({"level": "error", "where": where, "detail": detail})

    def warning(self, where, detail):
        self.issues.append({"level": "warning", "where": where, "detail": detail})

    def _url(self, where, column, value):
        if value and not _URL_RE.match(value):
            self.error(where, "%s is not an http(s) URL: %r" % (column, value))

    def _keys(self, where, block, allowed, label=""):
        if not isinstance(block, dict):
            self.error(where, "%s must be a set of key: value pairs" % (label or "block"))
            return {}
        for key in block:
            if key not in allowed:
                self.error(where, "unknown key %s%r (expected one of %s)"
                           % (label + "." if label else "", key, ", ".join(allowed)))
        return block

    def _read(self, folder, key, path):
        where = entry_path(folder, key)
        if not _ID_RE.match(key):
            self.error(where, "file name must be lower-case letters, digits and - or _")
        try:
            front, sections = read_entry(path)
        except (ValueError, yaml.YAMLError) as exc:
            self.error(where, "cannot be read: %s" % str(exc).splitlines()[0])
            return where, None, None
        for heading in sections:
            if heading != "Description":
                self.warning(where, "section %r is not published (only # Description is)"
                             % heading)
        return where, front, sections.get("Description", "")

    # -- principles.csv ----------------------------------------------------
    def _load_principles(self):
        _cols, rows = read_csv(PRINCIPLES_CSV)
        principles, bonus, adoption = [], None, None
        seen = set()
        for row in rows:
            where = "%s:%s" % (PRINCIPLES_CSV, row.get("id") or "?")
            if row["id"] in seen:
                self.error(where, "duplicate id")
            seen.add(row["id"])
            if row["kind"] not in PRINCIPLE_KINDS:
                self.error(where, "kind must be one of %s" % ", ".join(PRINCIPLE_KINDS))
                continue
            scores = {}
            for outcome in OUTCOMES:
                raw = row.get(outcome + "_score", "")
                if raw == "":
                    scores[outcome] = None
                    continue
                try:
                    scores[outcome] = int(raw)
                except ValueError:
                    self.error(where, "%s_score is not an integer: %r" % (outcome, raw))
                    scores[outcome] = 0
            try:
                order = int(row.get("order") or 0)
            except ValueError:
                self.error(where, "order is not an integer")
                order = 0
            entry = {
                "key": row["id"],
                "kind": row["kind"],
                "order": order,
                "label": row["name"],
                "blurb": row["definition"],
                "when": dict((o, row.get(o + "_when", "")) for o in OUTCOMES),
                "scores": scores,
            }
            if row["kind"] == "principle":
                principles.append(entry)
            elif row["kind"] == "bonus":
                bonus = entry
            else:
                adoption = entry
        principles.sort(key=lambda p: p["order"])
        if not principles:
            self.error(PRINCIPLES_CSV, "no principle rows")
        return principles, bonus, adoption

    # -- licences.csv ------------------------------------------------------
    def _load_licences(self):
        _cols, rows = read_csv(LICENCES_CSV)
        out = OrderedDict()
        for row in rows:
            where = "%s:%s" % (LICENCES_CSV, row.get("id") or "?")
            if row["id"] in out:
                self.error(where, "duplicate id")
            if row["category"] not in LICENCE_CATEGORIES:
                self.error(where, "category must be one of %s" % ", ".join(LICENCE_CATEGORIES))
            self._url(where, "url", row.get("url"))
            out[row["id"]] = {
                "id": row["id"],
                "name": row["name"],
                "category": row["category"],
                "url": row.get("url") or None,
                "note": row.get("note") or None,
            }
        return out

    # -- organizations/*.md -----------------------------------------------
    def _load_organizations(self):
        out = OrderedDict()
        for key, path in read_entries(ORGS_DIR):
            where, front, description = self._read(ORGS_DIR, key, path)
            if front is None:
                continue
            self._keys(where, front, ORG_KEYS)
            name = as_text(front.get("name"))
            if not name:
                self.error(where, "name is empty")
            org_type = as_text(front.get("type"))
            if org_type not in ORG_TYPES:
                self.error(where, "type must be one of %s" % ", ".join(ORG_TYPES))
            roles = [as_text(r) for r in as_list(front.get("roles"))]
            for role in roles:
                if role not in ORG_ROLES:
                    self.error(where, "roles must be among %s" % ", ".join(ORG_ROLES))
            url, logo = as_text(front.get("url")), as_text(front.get("logo_url"))
            self._url(where, "url", url)
            self._url(where, "logo_url", logo)
            out[key] = {
                "id": key,
                "name": name or key,
                "short": as_text(front.get("short_name")) or name or key,
                "url": url or None,
                "logo_url": logo or None,
                "type": org_type,
                "type_label": ORG_TYPES.get(org_type, "Other"),
                "roles": roles,
                "description": description,
                "source_path": entry_path(ORGS_DIR, key),
            }
        return out

    # -- specifications/*.md ----------------------------------------------
    def _parse_licences(self, where, entries):
        out = []
        for entry in as_list(entries):
            if isinstance(entry, str):
                entry = {"id": entry}
            entry = self._keys(where, entry, LICENCE_KEYS, "licences")
            lid = as_text(entry.get("id"))
            scopes = [as_text(x) for x in as_list(entry.get("scopes"))]
            for sc in scopes:
                if sc not in LICENCE_SCOPES:
                    self.error(where, "licence scope must be one of %s: %r"
                               % (", ".join(LICENCE_SCOPES), sc))
            meta = self.licences.get(lid)
            if meta is None:
                self.error(where, "licence %r is not in %s" % (lid, LICENCES_CSV))
                meta = {"id": lid, "name": lid, "category": "unknown", "url": None, "note": None}
            out.append(dict(meta, scopes=[x for x in scopes if x in LICENCE_SCOPES]))
        if not out:
            out.append({"id": "Unspecified", "name": "No licence stated", "category": "unknown",
                        "url": None, "note": None, "scopes": []})
        return out

    def _vocab(self, where, column, value, vocab, allow_empty=False):
        if value == "" and allow_empty:
            return None
        if value not in vocab:
            self.error(where, "%s must be one of %s, got %r"
                       % (column, ", ".join(vocab), value))
            return None
        return value

    def _load_specs(self):
        specs = []
        for key, path in read_entries(SPECS_DIR):
            where, front, description = self._read(SPECS_DIR, key, path)
            if front is not None:
                specs.append(self._clean_spec(key, where, front, description))
        specs.sort(key=default_order)
        return specs

    def _clean_spec(self, sid, where, front, description):
        self._keys(where, front, SPEC_KEYS)
        short_name = as_text(front.get("short_name"))
        if not short_name:
            self.error(where, "short_name is empty")

        status = self._vocab(where, "status", as_text(front.get("status")), STATUS) \
            or "under_review"
        status_meta = STATUS[status]

        mode_ids = []
        for m in as_list(front.get("modes")):
            if self._vocab(where, "modes", as_text(m), MODES):
                mode_ids.append(as_text(m))
        modes = [MODES[m] for m in mode_ids] or [UNCLASSIFIED]

        maintainers = []
        for key in as_list(front.get("maintainers")):
            key = as_text(key)
            org = self.organizations.get(key)
            if org is None:
                self.error(where, "maintainer %r has no file %s" % (key, entry_path(ORGS_DIR, key)))
                continue
            if "specification_maintainer" not in org["roles"]:
                self.warning(where, "maintainer %r does not have the specification_maintainer "
                                    "role" % key)
            maintainers.append(org)

        given = self._keys(where, front.get("principles") or {}, [p["key"] for p in self.principles],
                           "principles")
        criteria = []
        for p in self.principles:
            block = self._keys(where, given.get(p["key"]) or {}, PRINCIPLE_KEYS,
                               "principles." + p["key"])
            verdict = self._vocab(where, "principles.%s.verdict" % p["key"],
                                  as_text(block.get("verdict")) or "not_assessed", VERDICT) \
                or "not_assessed"
            evidence = as_text(block.get("evidence_url"))
            self._url(where, "principles.%s.evidence_url" % p["key"], evidence)
            points = p["scores"].get(verdict) if verdict in SCORED_VERDICTS else 0
            criteria.append({
                "key": p["key"],
                "label": p["label"],
                "blurb": p["blurb"],
                "verdict": verdict,
                "verdict_label": VERDICT[verdict]["label"],
                "tone": VERDICT[verdict]["tone"],
                "rationale": as_text(block.get("rationale")),
                "evidence_url": evidence or None,
                "points": points or 0,
            })

        adoption = self._keys(where, front.get("adoption") or {}, ADOPTION_KEYS, "adoption")
        lifecycle = self._vocab(where, "adoption.lifecycle", as_text(adoption.get("lifecycle")),
                                LIFECYCLE, True)
        tier = self._vocab(where, "adoption.tier", as_text(adoption.get("tier")),
                           ADOPTION_TIER, True)
        raw_confirmed = adoption.get("confirmed_by_maintainer")
        if raw_confirmed not in (None, True, False):
            self.error(where, "adoption.confirmed_by_maintainer must be true or false")
        confirmed = {True: "yes", False: "no"}.get(raw_confirmed, "unknown")

        adopters_count = adoption.get("adopters_count")
        if adopters_count is not None and (not isinstance(adopters_count, int)
                                           or isinstance(adopters_count, bool)
                                           or adopters_count < 0):
            self.error(where, "adoption.adopters_count must be a whole number")
            adopters_count = None
        updated = as_text(adoption.get("adopters_count_updated"))
        if updated and not _DATE_RE.match(updated):
            self.error(where, "adoption.adopters_count_updated must be a YYYY-MM-DD date")
        registry = as_text(adoption.get("adopters_registry_url"))
        self._url(where, "adoption.adopters_registry_url", registry)

        year = front.get("first_release_year")
        if year is not None and not (isinstance(year, int) and 1900 <= year <= 2100):
            self.error(where, "first_release_year must be a four-digit year")
            year = None

        homepage = as_text(front.get("homepage_url"))
        self._url(where, "homepage_url", homepage)
        evidence = [as_text(u) for u in as_list(front.get("licence_evidence_url"))]
        for url in evidence:
            self._url(where, "licence_evidence_url", url)

        licences = self._parse_licences(where, front.get("licences"))
        score = self.score(criteria, tier)
        met = sum(1 for c in criteria if c["verdict"] == "compliant")
        self._check_status(where, status, criteria)

        return {
            "id": sid,
            "slug": sid,
            "short_name": short_name or sid,
            "full_name": as_text(front.get("full_name")),
            "description": description,
            "function": plain_summary(description),
            "homepage_url": homepage or None,
            "modes": modes,
            "mode_ids": mode_ids,
            "status": status,
            "status_label": status_meta["label"],
            "status_tone": status_meta["tone"],
            "status_rank": status_meta["rank"],
            "criteria": criteria,
            "criteria_met": met,
            "criteria_total": len(criteria),
            "score": score["total"],
            "confirmed": confirmed,
            "confirmed_label": CONFIRMED[confirmed]["label"],
            "confirmed_tone": CONFIRMED[confirmed]["tone"],
            "lifecycle": lifecycle,
            "lifecycle_label": LIFECYCLE[lifecycle]["label"] if lifecycle else None,
            "lifecycle_hint": LIFECYCLE[lifecycle]["hint"] if lifecycle else None,
            "adoption_tier": tier,
            "adoption_tier_label": ADOPTION_TIER[tier]["label"] if tier else None,
            "adopters_registry": registry or None,
            "adopters_count": adopters_count,
            "adopters_count_updated": updated or None,
            "first_release_year": year,
            "licences": licences,
            "licence_ids": [l["id"] for l in licences],
            "licence_evidence": evidence,
            "maintainers": maintainers,
            "maintainer_ids": [m["id"] for m in maintainers],
            "maintainer_types": sorted(set(m["type"] for m in maintainers)),
            "source_path": entry_path(SPECS_DIR, sid),
        }

    def _check_status(self, where, status, criteria):
        """Flag a recorded status that the verdicts do not support.

        `status` is the coalition's decision and is published as recorded --
        "inactive" and "under_review" cannot be derived from verdicts at all.
        For the three assessed outcomes, though, the verdicts imply one answer,
        and a mismatch is worth a second look in review.
        """
        if status not in ("compliant", "partially_compliant", "not_compliant"):
            return
        verdicts = [c["verdict"] for c in criteria]
        if all(v == "compliant" for v in verdicts):
            expected = "compliant"
        elif "not_compliant" in verdicts:
            expected = "not_compliant"
        elif all(v in ("compliant", "partially_compliant") for v in verdicts):
            expected = "partially_compliant"
        else:
            return      # unknown or not assessed verdicts: no single answer
        if expected != status:
            self.warning(where, "status is %s but the principle verdicts imply %s"
                         % (status, expected))

    # -- scoring -----------------------------------------------------------
    def score(self, criteria, tier):
        """Ranking score, per principles.csv. Used for ordering only.

        Returns None when no principle has been assessed, so an unreviewed
        specification sorts after every assessed one.
        """
        parts = [{"key": c["key"], "label": c["label"], "outcome": c["verdict_label"],
                  "points": c["points"]} for c in criteria]
        assessed = any(c["verdict"] in SCORED_VERDICTS for c in criteria)
        maximum = sum(max(v for v in p["scores"].values() if v is not None)
                      for p in self.principles)

        if self.bonus:
            full = all(c["verdict"] == "compliant" for c in criteria)
            outcome = "compliant" if full else "not_compliant"
            parts.append({"key": self.bonus["key"], "label": self.bonus["label"],
                          "outcome": "Yes" if full else "No",
                          "points": self.bonus["scores"].get(outcome) or 0})
            maximum += max(v for v in self.bonus["scores"].values() if v is not None)

        if self.adoption:
            if tier:
                outcome = ADOPTION_TIER[tier]["outcome"]
                points = self.adoption["scores"].get(outcome) or 0
                label = ADOPTION_TIER[tier]["label"]
            else:
                points, label = 0, "Not recorded"
            parts.append({"key": self.adoption["key"], "label": self.adoption["label"],
                          "outcome": label, "points": points})
            maximum += max(v for v in self.adoption["scores"].values() if v is not None)

        total = sum(p["points"] for p in parts) if assessed else None
        return {"total": total, "max": maximum, "parts": parts}


def plain_summary(markdown_text):
    """First paragraph of a Markdown description, as plain text for listings."""
    first = (markdown_text or "").strip().split("\n\n", 1)[0]
    first = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", first)     # links, images
    first = re.sub(r"[*_`]+", "", first)
    return " ".join(first.split())


def default_order(spec):
    """The registry's reading order.

    Specifications with the most known adopters come first; those without a
    recorded count follow, highest score first. Status, then name, break the
    remaining ties so the order is stable between builds.
    """
    return (
        spec["adopters_count"] is None,
        -(spec["adopters_count"] or 0),
        -(spec["score"] if spec["score"] is not None else -999),
        spec["status_rank"],
        spec["short_name"].lower(),
    )


def _facet(counter, order=None, labels=None):
    items = []
    for value, count in counter.items():
        items.append({"value": value, "label": (labels or {}).get(value, value), "count": count})
    if order:
        pos = dict((v, i) for i, v in enumerate(order))
        items.sort(key=lambda i: (pos.get(i["value"], len(order)), -i["count"], i["label"].lower()))
    else:
        items.sort(key=lambda i: (-i["count"], i["label"].lower()))
    return items


def build_dataset():
    reg = Registry()
    specs = reg.specs

    counters = dict((k, Counter()) for k in (
        "mode", "status", "confirmed", "lifecycle", "adoption_tier", "licence",
        "licence_category", "maintainer", "maintainer_type", "decade"))
    for p in reg.principles:
        counters["criterion_" + p["key"]] = Counter()

    for s in specs:
        for m in s["modes"]:
            counters["mode"][m] += 1
        counters["status"][s["status"]] += 1
        counters["confirmed"][s["confirmed"]] += 1
        if s["lifecycle"]:
            counters["lifecycle"][s["lifecycle"]] += 1
        if s["adoption_tier"]:
            counters["adoption_tier"][s["adoption_tier"]] += 1
        for lid in set(s["licence_ids"]):
            counters["licence"][lid] += 1
        for cat in set(l["category"] for l in s["licences"]):
            counters["licence_category"][cat] += 1
        for mid in s["maintainer_ids"]:
            counters["maintainer"][mid] += 1
        for t in s["maintainer_types"]:
            counters["maintainer_type"][t] += 1
        if s["first_release_year"]:
            counters["decade"][str(s["first_release_year"] // 10 * 10) + "s"] += 1
        for c in s["criteria"]:
            counters["criterion_" + c["key"]][c["verdict"]] += 1

    licence_labels = dict((lid, m["name"]) for lid, m in reg.licences.items())
    licence_labels["Unspecified"] = "No licence stated"
    org_labels = dict((k, o["short"]) for k, o in reg.organizations.items())
    verdict_labels = dict((k, v["label"]) for k, v in VERDICT.items())

    facets = OrderedDict()
    facets["mode"] = {"label": "Mode", "hint": "Transport modes the specification covers.",
                      "options": _facet(counters["mode"], list(MODES.values()) + [UNCLASSIFIED])}
    facets["status"] = {"label": "MDIP status", "hint": "Overall outcome of the MDIP assessment.",
                        "options": _facet(counters["status"], list(STATUS),
                                          dict((k, v["label"]) for k, v in STATUS.items()))}
    facets["confirmed"] = {"label": "Adoption confirmed by maintainer",
                           "hint": "Whether the maintainer confirmed real-world adoption.",
                           "options": _facet(counters["confirmed"], list(CONFIRMED),
                                             dict((k, v["label"]) for k, v in CONFIRMED.items()))}
    facets["lifecycle"] = {"label": "Lifecycle", "hint": "How far along the specification is.",
                           "options": _facet(counters["lifecycle"], list(LIFECYCLE),
                                             dict((k, v["label"]) for k, v in LIFECYCLE.items()))}
    facets["adoption_tier"] = {"label": "Adoption", "hint": "Scale of known deployments.",
                               "options": _facet(counters["adoption_tier"], list(ADOPTION_TIER),
                                                 dict((k, v["label"])
                                                      for k, v in ADOPTION_TIER.items()))}
    facets["licence"] = {"label": "Licence",
                         "hint": "Licences the specification, its documentation, code or data "
                                 "are released under.",
                         "searchable": True,
                         "options": _facet(counters["licence"], None, licence_labels)}
    facets["licence_category"] = {"label": "Licence type",
                                  "hint": "Whether the licence puts any gate in front of use.",
                                  "options": _facet(counters["licence_category"],
                                                    list(LICENCE_CATEGORIES),
                                                    dict(LICENCE_CATEGORIES))}
    facets["maintainer"] = {"label": "Maintainer organization",
                            "hint": "Organization responsible for the specification.",
                            "searchable": True,
                            "options": _facet(counters["maintainer"], None, org_labels)}
    facets["maintainer_type"] = {"label": "Maintainer type",
                                 "hint": "What kind of body maintains the specification.",
                                 "options": _facet(counters["maintainer_type"], list(ORG_TYPES),
                                                   dict(ORG_TYPES))}
    for p in reg.principles:
        facets["criterion_" + p["key"]] = {
            "label": p["label"], "hint": p["blurb"], "group": "criteria",
            "options": _facet(counters["criterion_" + p["key"]], list(VERDICT), verdict_labels)}
    facets["decade"] = {"label": "First released", "hint": "Decade of the first public release.",
                        "options": _facet(counters["decade"],
                                          sorted(counters["decade"], reverse=True))}

    return {
        "meta": {
            "count": len(specs),
            "organization_count": len([k for k, v in counters["maintainer"].items() if v]),
            "compliant_count": counters["status"].get("compliant", 0),
            "confirmed_count": counters["confirmed"].get("yes", 0),
        },
        "facets": facets,
        "organizations": reg.organizations,
        "criteria": reg.principles,
        "licences": reg.licences,
        "bonus": reg.bonus,
        "adoption": reg.adoption,
        "specs": specs,
        "issues": reg.issues,
    }
