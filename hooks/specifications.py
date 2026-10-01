"""Generate /specifications and one page per specification at build time.

The pages are produced with `File.generated`, so nothing is written into
docs/en and there are no generated Markdown files to keep in sync in git. The
single source of truth is the set of CSV files in data/, which are reviewed
and changed on GitHub; `scripts/spec_data.py` validates and joins them, and
`scripts/spec_api.py` turns the result into the static JSON API under /api/.

The section is deliberately unlisted for now: it is left out of the nav bar,
the site search and the sitemap, and every page asks search engines not to
index it (see INDEX_META and overrides/main.html).

Everything the listing page needs is rendered server-side: every row and every
filter control exists in the HTML, and the JavaScript only hides, sorts and
counts them. With JavaScript off the page is still a complete, readable list.

Specifications still under review are rendered into a collapsed section after
the main list: they carry no finding yet, so they would only add noise to the
default view.

Icons are read out of the Material theme's own bundled Material Design Icons
set and inlined, so there are no emoji and no icon font to load.
"""

from __future__ import annotations

import json
import os
import re
import sys
from html import escape
from urllib.parse import quote

from mkdocs.structure.files import File

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import spec_api  # noqa: E402  (path set above)
import spec_data  # noqa: E402

SECTION = "specifications"

_ICON_CACHE = {}


def icon(name, cls="", title=None):
    """Inline one Material Design Icon from the theme's bundled set."""
    if name not in _ICON_CACHE:
        import material
        path = os.path.join(
            os.path.dirname(material.__file__), "templates", ".icons", "material", name + ".svg"
        )
        with open(path) as fh:
            _ICON_CACHE[name] = fh.read().strip()
    svg = _ICON_CACHE[name]
    attrs = ' class="mdip-i %s" aria-hidden="true" focusable="false"' % escape(cls or "")
    if title:
        attrs = (' class="mdip-i %s" role="img" aria-label="%s" focusable="false"'
                 % (escape(cls or ""), escape(title)))
    return svg.replace("<svg ", "<svg" + attrs + " ", 1)


TONE_ICON = {
    "pass": "check-circle",
    "warn": "alert-circle",
    "fail": "close-circle",
    "info": "progress-clock",
    "muted": "help-circle",
}

FACET_ICON = {
    "mode": "routes",
    "status": "shield-check",
    "confirmed": "account-check",
    "lifecycle": "chart-timeline-variant",
    "adoption_tier": "account-group",
    "licence": "scale-balance",
    "licence_category": "lock-open-variant-outline",
    "maintainer": "domain",
    "maintainer_type": "office-building-outline",
    "decade": "calendar-blank",
}

# Facets shown expanded on arrival. None: every filter starts folded, so the
# whole set reads as one short list of headings.
OPEN_BY_DEFAULT = ()

FACET_ORDER = [
    "mode",
    "status",
    "confirmed",
    "lifecycle",
    "adoption_tier",
    "licence",
    "licence_category",
    "maintainer",
    "maintainer_type",
    "decade",
]

# The first entry is the default and matches the server-rendered order.
SORTS = [
    ("default", "Most adopted"),
    ("criteria", "Criteria met"),
    ("name", "Name (A-Z)"),
    ("newest", "Newest first"),
    ("oldest", "Oldest first"),
]
DEFAULT_SORT = SORTS[0][0]

# Statuses held back in the collapsed section under the main list.
DEFERRED_STATUSES = ("under_review",)


def org_logo(org, base):
    """The organization's logo from `logo_url`, over a generated monogram.

    Logos are linked from the organization's own site, not copied into the
    repository. The monogram is always rendered and the image is drawn on top
    of it, so a logo that is missing, moved or blocked falls back on its own:
    the image removes itself on error and the monogram shows through.
    """
    mono = ('<span class="org-logo org-logo--mono" style="--org-hue:%d" aria-hidden="true">'
            "%s</span>" % (org_hue(org["id"]), escape(monogram(org.get("short") or org["name"]))))
    if not org.get("logo_url"):
        return mono
    return ('<span class="org-logo org-logo--stack">%s<img class="org-logo__img" src="%s" '
            'alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer" '
            'onerror="this.remove()"></span>' % (mono, escape(org["logo_url"])))


def org_hue(key):
    h = 0
    for ch in key:
        h = (h * 31 + ord(ch)) % 360
    return h


def monogram(name):
    words = [w for w in name.replace("-", " ").split() if w[:1].isalnum()]
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][:1] + words[1][:1]).upper()


def pill(tone, label, icon_name=None, cls=""):
    return ('<span class="pill pill--%s %s">%s<span>%s</span></span>'
            % (escape(tone), escape(cls), icon(icon_name or TONE_ICON.get(tone, "help-circle")),
               escape(label)))


def meter(met, total):
    dots = []
    for i in range(total):
        dots.append('<i class="%s"></i>' % ("on" if i < met else "off"))
    return ('<span class="meter" role="img" aria-label="%d of %d MDIP criteria met">%s</span>'
            % (met, total, "".join(dots)))


def ext_link(url, label, icon_name="open-in-new", cls=""):
    return ('<a class="srclink %s" href="%s" rel="noopener">%s<span>%s</span>%s</a>'
            % (escape(cls), escape(url), icon("link-variant"), escape(label),
               icon(icon_name)))


# --------------------------------------------------------------------------
# Contributing on GitHub
# --------------------------------------------------------------------------

ISSUE_TEMPLATE = "specification-change.yml"

# What "Propose a specification" opens in GitHub's editor: a new file in
# data/specifications/ with every field already laid out.
NEW_SPEC_TEMPLATE = """---
short_name:
full_name:
homepage_url:
status: under_review
modes: []
maintainers: []
licences:
- id:
  scopes: [specification]
first_release_year:
adoption:
  lifecycle:
  tier:
principles:
%s---

# Description

What the specification is for, in a sentence or two.
"""


def issue_url(spec=None):
    """A new issue from the change-request form, pre-filled where possible."""
    params = [("template", ISSUE_TEMPLATE)]
    if spec:
        params += [("title", "Change request: %s" % spec["short_name"]), ("spec_id", spec["id"])]
    return spec_data.github_url("issues/new") + "?" + "&".join(
        "%s=%s" % (k, quote(v)) for k, v in params)


def new_spec_url(data):
    blocks = "".join("  %s:\n    verdict: not_assessed\n    rationale:\n    evidence_url:\n"
                     % c["key"] for c in data["criteria"])
    return "%s?filename=%s&value=%s" % (
        spec_data.github_url("new", "data/" + spec_data.SPECS_DIR),
        quote("new-specification-id.md"), quote(NEW_SPEC_TEMPLATE % blocks))


def render_contribute(data, spec=None):
    """Where to change what the page shows.

    On a specification page, "Suggest a change" opens that specification's
    own file in GitHub's editor. Someone without write access is offered a
    fork and a pull request, so every change is proposed and reviewed in
    public.
    """
    if spec:
        title = "Something to update about %s?" % spec["short_name"]
        text = ("If any information on this page is missing, outdated or incorrect, "
                "suggest an edit on GitHub. The coalition reviews every change in public "
                "before it appears here.")
        primary = (spec_data.github_url("edit", spec["source_path"]), "pencil-outline",
                   "Suggest a change")
        secondary = (issue_url(spec), "message-alert-outline", "Report an issue")
    else:
        title = "Help keep this registry accurate"
        text = ("Every specification and organization on this page is a file kept in the "
                "open on GitHub. Anyone can suggest a change, or propose a specification "
                "that is missing.")
        primary = (new_spec_url(data), "plus", "Propose a specification")
        secondary = (spec_data.github_url("tree", "data"), "database-outline", "Browse the data")
    return ('<section class="contribute">%s<div class="contribute__t"><h2>%s</h2><p>%s</p></div>'
            '<div class="contribute__a">'
            '<a class="btn btn--primary" href="%s" rel="noopener">%s<span>%s</span></a>'
            '<a class="btn" href="%s" rel="noopener">%s<span>%s</span></a>'
            "</div></section>"
            % (icon("github", "contribute__ico"), escape(title), escape(text),
               escape(primary[0]), icon(primary[1]), escape(primary[2]),
               escape(secondary[0]), icon(secondary[1]), escape(secondary[2])))


# --------------------------------------------------------------------------
# Listing page
# --------------------------------------------------------------------------

def render_row(spec, base):
    """One row of the registry list.

    A row, not a card: the listing is a long inventory that people scan down a
    single column, comparing one specification's status against the next, and
    rows put those values in the same place on every line. Nothing here is
    tinted by status -- the verdict is carried by the icon and the pill, which
    is enough, and a coloured edge on 55 rows reads as decoration.
    """
    parts = ['<li class="spec-row" data-spec="%s" data-status="%s">'
             % (escape(spec["id"]), escape(spec["status"]))]
    parts.append('<a class="spec-row__link" href="%s/">' % escape(spec["slug"]))

    parts.append('<span class="spec-row__main">')
    parts.append('<span class="spec-row__head"><span class="spec-row__name">%s</span>'
                 % escape(spec["short_name"]))
    if spec["full_name"] and spec["full_name"] != spec["short_name"]:
        parts.append('<span class="spec-row__full">%s</span>' % escape(spec["full_name"]))
    parts.append("</span>")

    if spec["function"]:
        parts.append('<span class="spec-row__fn">%s</span>' % escape(spec["function"]))

    parts.append('<span class="spec-row__meta">')
    if spec["maintainers"]:
        for org in spec["maintainers"][:2]:
            parts.append('<span class="org-chip">%s<span>%s</span></span>'
                         % (org_logo(org, base), escape(org["short"])))
        if len(spec["maintainers"]) > 2:
            parts.append('<span class="tag tag--more">+%d</span>'
                         % (len(spec["maintainers"]) - 2))
    else:
        parts.append('<span class="org-chip org-chip--none">%s<span>No maintainer recorded'
                     "</span></span>" % icon("help-circle"))
    for mode in spec["modes"]:
        parts.append('<span class="tag tag--mode">%s</span>' % escape(mode))
    for lic in spec["licences"]:
        parts.append('<span class="tag tag--lic tag--lic-%s">%s</span>'
                     % (escape(lic["category"]),
                        escape(lic["id"] if lic["id"] != "Other" else lic["name"][:28])))
    parts.append("</span></span>")

    parts.append('<span class="spec-row__side">')
    parts.append(pill(spec["status_tone"], spec["status_label"]))
    facts = []
    if spec["adopters_count"]:
        facts.append("%d adopters" % spec["adopters_count"])
    elif spec["adoption_tier_label"]:
        facts.append(spec["adoption_tier_label"])
    if spec["first_release_year"]:
        facts.append("since %d" % spec["first_release_year"])
    if facts:
        parts.append('<span class="spec-row__facts">%s</span>' % escape(" · ".join(facts)))
    parts.append("</span>")

    parts.append('<span class="spec-row__go">%s</span>' % icon("chevron-right"))
    parts.append("</a></li>")
    return "".join(parts)


def render_facet(key, facet, base, organizations):
    if not facet["options"]:
        return ""
    out = ['<details class="facet" data-facet="%s"%s>'
           % (escape(key), " open" if key in OPEN_BY_DEFAULT else "")]
    out.append('<summary class="facet__head"%s>'
               % (' title="%s"' % escape(facet["hint"]) if facet.get("hint") else ""))
    out.append(icon(FACET_ICON.get(key, "tune-variant"), "facet__icon"))
    out.append('<span class="facet__label">%s</span>' % escape(facet["label"]))
    out.append('<span class="facet__badge" data-facet-count hidden></span>')
    out.append(icon("chevron-down", "facet__chev"))
    out.append("</summary>")
    out.append('<div class="facet__body">')
    if facet.get("searchable"):
        out.append('<label class="facet__find"><span class="u-sr">Search %s</span>%s'
                   '<input type="search" data-facet-search placeholder="Search %s"'
                   ' autocomplete="off"></label>'
                   % (escape(facet["label"].lower()), icon("magnify"),
                      escape(facet["label"].lower())))
    out.append('<ul class="facet__list">')
    for opt in facet["options"]:
        oid = "f-%s-%s" % (key, opt["value"])
        logo = ""
        if key == "maintainer":
            org = organizations.get(opt["value"])
            if org:
                logo = org_logo(org, base)
        out.append('<li class="facet__item">')
        out.append('<input type="checkbox" id="%s" name="%s" value="%s">'
                   % (escape(oid), escape(key), escape(opt["value"])))
        out.append('<label for="%s">%s<span class="facet__name">%s</span>'
                   '<span class="facet__n">%d</span></label>'
                   % (escape(oid), logo, escape(opt["label"]), opt["count"]))
        out.append("</li>")
    out.append("</ul>")
    out.append('<p class="facet__none" hidden>No match.</p>')
    out.append("</div></details>")
    return "".join(out)


def render_index(data, base):
    m = data["meta"]
    specs = data["specs"]
    o = []

    o.append('<div class="mdip-specs" data-specs-root>')

    o.append('<p class="specs-notice" role="note">%s<span>The evaluation of the specifications '
             'listed here is a work in progress. Findings may change as assessments are '
             'reviewed.</span></p>' % icon("progress-wrench"))

    # ---- hero
    o.append('<header class="specs-hero">')
    o.append('<div class="specs-hero__glow" aria-hidden="true"></div>')
    o.append('<div class="specs-hero__in">')
    o.append('<p class="specs-hero__eyebrow">%s<span>MDIP registry</span></p>'
             % icon("clipboard-text-search-outline"))
    o.append("<h1>Mobility specifications</h1>")
    o.append('<p class="specs-hero__lede">Every specification the coalition has assessed against '
             'the %d MDIP openness criteria: what it covers, who maintains it, how it is '
             'licensed, and where the evidence for each finding comes from.</p>'
             % len(data["criteria"]))
    o.append('<ul class="specs-stats">')
    for value, label, ico in (
        (m["count"], "assessed", "table-search"),
        (m["compliant_count"], "MDIP compliant", "shield-check"),
        (m["confirmed_count"], "maintainer-confirmed", "account-check"),
        (m["organization_count"], "organizations", "domain"),
    ):
        o.append('<li class="stat"><span class="stat__ico">%s</span>'
                 '<span class="stat__v">%s</span><span class="stat__l">%s</span></li>'
                 % (icon(ico), value, escape(label)))
    o.append("</ul>")
    o.append("</div></header>")

    # ---- layout
    o.append('<div class="specs-layout">')

    o.append('<button class="specs-drawer-btn" type="button" data-drawer-open>'
             '%s<span>Filters</span><span class="specs-drawer-btn__n" data-active-count hidden>'
             '</span></button>' % icon("filter-variant"))

    o.append('<form class="specs-panel" data-panel id="specs-filters" '
             'aria-label="Filter specifications">')
    o.append('<div class="specs-panel__head">')
    o.append('<h2>%s<span>Filters</span></h2>' % icon("filter-variant"))
    o.append('<button type="button" class="ghost" data-clear-all hidden>%s<span>Clear</span>'
             "</button>" % icon("close"))
    o.append('<button type="button" class="specs-panel__close" data-drawer-close '
             'aria-label="Close filters">%s</button>' % icon("close"))
    o.append("</div>")

    o.append('<label class="specs-find"><span class="u-sr">Search specifications</span>%s'
             '<input type="search" data-q placeholder="Search name, function, maintainer"'
             ' autocomplete="off"></label>' % icon("magnify"))

    o.append('<div class="specs-panel__scroll">')
    for key in FACET_ORDER:
        if key in data["facets"]:
            o.append(render_facet(key, data["facets"][key], base, data["organizations"]))

    o.append('<div class="facet-group">')
    o.append('<p class="facet-group__title">%s<span>By individual criterion</span></p>'
             % icon("shield-check"))
    for c in data["criteria"]:
        key = "criterion_" + c["key"]
        if key in data["facets"]:
            o.append(render_facet(key, data["facets"][key], base, data["organizations"]))
    o.append("</div>")
    o.append("</div></form>")

    # ---- results
    deferred = [sp for sp in specs if sp["status"] in DEFERRED_STATUSES]
    main = [sp for sp in specs if sp["status"] not in DEFERRED_STATUSES]

    o.append('<section class="specs-results" aria-live="polite">')
    o.append('<div class="specs-toolbar">')
    o.append('<p class="specs-count"><strong data-shown>%d</strong><span>of %d'
             "</span></p>" % (len(main), len(specs)))
    o.append('<label class="specs-sort">%s<span class="u-sr">Sort by</span>'
             '<select data-sort>' % icon("sort-variant"))
    for value, label in SORTS:
        o.append('<option value="%s"%s>%s</option>'
                 % (escape(value), " selected" if value == DEFAULT_SORT else "",
                    escape(label)))
    o.append("</select></label>")
    o.append("</div>")
    o.append('<div class="specs-chips" data-chips hidden></div>')

    o.append('<ol class="specs-list" data-grid>')
    for spec in main:
        o.append(render_row(spec, base))
    o.append("</ol>")

    if deferred:
        o.append('<details class="specs-defer" data-defer>')
        o.append('<summary class="specs-defer__head">%s'
                 '<span class="specs-defer__t">Not yet assessed</span>'
                 '<span class="specs-defer__n" data-defer-count>%d</span>%s</summary>'
                 % (icon("progress-clock"), len(deferred), icon("chevron-down")))
        o.append('<p class="specs-defer__note">These specifications are in the registry but '
                 'the coalition has not finished reviewing them against the MDIP criteria, so '
                 'no finding is published yet.</p>')
        o.append('<ol class="specs-list specs-list--defer" data-grid-defer>')
        for spec in deferred:
            o.append(render_row(spec, base))
        o.append("</ol>")
        o.append("</details>")

    o.append('<div class="specs-empty" data-empty hidden>%s'
             "<h2>Nothing matches those filters</h2>"
             "<p>Try removing a filter, or clear them all to see the full registry.</p>"
             '<button type="button" class="btn" data-clear-all>Clear all filters</button></div>'
             % icon("text-box-search-outline"))
    o.append(render_contribute(data))
    o.append('<p class="specs-foot">%s<span>Reuse this data: <a href="%sapi/docs/">API '
             'documentation</a> &middot; <a href="%sapi/catalogue.json">catalogue (JSON)</a> '
             '&middot; <a href="%sapi/export.csv">full export (CSV)</a></span></p>'
             % (icon("api"), base, base, base))
    o.append("</section>")

    o.append("</div>")  # layout

    o.append('<script type="application/json" data-specs-json>%s</script>'
             % json.dumps(compact(data), separators=(",", ":")).replace("</", "<\\/"))
    o.append("</div>")
    return "\n".join(o)


def render_rules(data):
    """What earns each verdict, from data/principles.csv.

    Shown under the criteria on every specification page, so the reasoning
    behind a verdict sits next to the rule it was judged against. Only the
    principles are listed: the bonus and adoption rows of principles.csv
    feed the ordering of the registry, which is documented in data/README.md
    rather than presented on the page.
    """
    o = ['<details class="disclosure method" id="methodology">']
    o.append('<summary>%s<span>How each criterion is assessed</span></summary>'
             % icon("book-open-outline"))
    o.append('<div class="method__body"><div class="method__scroll"><table class="method__t">'
             "<thead><tr><th>Criterion</th><th>Compliant</th><th>Partially compliant</th>"
             "<th>Not compliant</th></tr></thead><tbody>")
    for r in data["criteria"]:
        o.append('<tr><th scope="row"><span class="method__name">%s</span>'
                 '<span class="method__def">%s</span></th>'
                 % (escape(r["label"]), escape(r["blurb"])))
        for outcome in spec_data.OUTCOMES:
            o.append("<td>%s</td>" % escape(r["when"].get(outcome) or ""))
        o.append("</tr>")
    o.append('</tbody></table></div><p class="method__src">The rules are kept in '
             '<a href="%s" rel="noopener">principles.csv</a> on GitHub.</p></div></details>'
             % escape(spec_data.github_url("blob", "data/" + spec_data.PRINCIPLES_CSV)))
    return "".join(o)


def compact(data):
    """Small record per spec for client-side filtering, sorting and search."""
    out = []
    for s in data["specs"]:
        text = " ".join(filter(None, [
            s["short_name"], s["full_name"], s["function"], s["id"],
            " ".join(m["name"] for m in s["maintainers"]),
            " ".join(m["short"] for m in s["maintainers"]),
            " ".join(l["name"] for l in s["licences"]),
            " ".join(l["id"] for l in s["licences"]),
            " ".join(s["modes"]),
        ])).lower()
        rec = {
            "id": s["id"],
            "mode": s["modes"],
            "status": [s["status"]],
            "confirmed": [s["confirmed"]],
            "lifecycle": [s["lifecycle"]] if s["lifecycle"] else [],
            "adoption_tier": [s["adoption_tier"]] if s["adoption_tier"] else [],
            "licence": sorted(set(s["licence_ids"])),
            "licence_category": sorted(set(l["category"] for l in s["licences"])),
            "maintainer": s["maintainer_ids"],
            "maintainer_type": s["maintainer_types"],
            "decade": ([str(s["first_release_year"] // 10 * 10) + "s"]
                       if s["first_release_year"] else []),
            "t": text,
            "sort": {
                # Mirrors spec_data.default_order so the client re-sort lands
                # back on exactly the server-rendered order.
                "default": [1 if s["adopters_count"] is None else 0, -(s["adopters_count"] or 0),
                            -(s["score"] if s["score"] is not None else -999),
                            s["status_rank"], s["short_name"].lower()],
                "criteria": [-s["criteria_met"], s["status_rank"]],
                "name": [s["short_name"].lower()],
                "newest": [-(s["first_release_year"] or 0)],
                "oldest": [s["first_release_year"] or 9999],
            },
        }
        for c in s["criteria"]:
            rec["criterion_" + c["key"]] = [c["verdict"]]
        out.append(rec)
    return {"specs": out}


# --------------------------------------------------------------------------
# Detail page
# --------------------------------------------------------------------------

def paras(text, cls=""):
    """Turn the registry's free text into paragraphs, keeping its line breaks."""
    blocks = [b.strip() for b in (text or "").replace("\r\n", "\n").split("\n\n") if b.strip()]
    if not blocks:
        return ""
    return "".join(
        '<p class="%s">%s</p>' % (escape(cls), escape(b).replace("\n", "<br>"))
        for b in blocks
    )


# Rationales that only restate the verdict. A quarter of the cells in the
# registry are one of these, and "Compliant -- because: Yes" is worth neither a
# paragraph nor a disclosure to open.
_RESTATEMENTS = {
    "yes", "no", "n a", "na", "none", "tbd", "unknown", "partial", "partially",
    "compliant", "not compliant", "not assessed", "yes yes", "no no",
}


def is_restatement(rationale):
    folded = " ".join(re.sub(r"[^a-z0-9]+", " ", (rationale or "").lower()).split())
    return not folded or folded in _RESTATEMENTS


def description_html(text):
    """The entry's `# Description` section, rendered as Markdown.

    Contributors write it on GitHub, so raw HTML in it is escaped rather than
    passed through: the page renders what GitHub previews, and nothing else.
    """
    import markdown
    return markdown.markdown(escape(text, quote=False), extensions=["sane_lists"])


def dl_row(ico, label, value_html):
    return ('<div class="glance__row"><dt>%s<span>%s</span></dt><dd>%s</dd></div>'
            % (icon(ico), escape(label), value_html))


def render_detail(spec, data, base):
    o = ['<div class="mdip-spec">']

    o.append('<a class="spec-back" href="%s">%s<span>All specifications</span></a>'
             % (escape(base + SECTION + "/"), icon("arrow-left")))

    # ---- hero
    o.append('<header class="spec-hero spec-hero--%s">' % escape(spec["status_tone"]))
    o.append('<div class="spec-hero__glow" aria-hidden="true"></div>')
    o.append('<div class="spec-hero__in">')
    o.append('<div class="spec-hero__top">%s%s</div>'
             % (pill(spec["status_tone"], spec["status_label"]),
                meter(spec["criteria_met"], spec["criteria_total"])))
    o.append("<h1>%s</h1>" % escape(spec["short_name"]))
    if spec["full_name"] and spec["full_name"] != spec["short_name"]:
        o.append('<p class="spec-hero__full">%s</p>' % escape(spec["full_name"]))
    if spec["description"]:
        o.append('<div class="spec-hero__lede">%s</div>' % description_html(spec["description"]))

    o.append('<div class="spec-hero__actions">')
    if spec["homepage_url"]:
        o.append('<a class="btn btn--primary" href="%s" rel="noopener">%s<span>Specification '
                 "homepage</span>%s</a>"
                 % (escape(spec["homepage_url"]), icon("web"), icon("open-in-new")))
    if spec["adopters_registry"]:
        o.append('<a class="btn" href="%s" rel="noopener">%s<span>Adopters registry</span>%s</a>'
                 % (escape(spec["adopters_registry"]), icon("account-group"), icon("open-in-new")))
    o.append("</div>")

    if spec["maintainers"]:
        o.append('<div class="spec-hero__orgs"><span class="spec-hero__orgs-l">Maintained by'
                 "</span>")
        for org in spec["maintainers"]:
            o.append('<span class="org-chip org-chip--lg">%s<span>%s</span></span>'
                     % (org_logo(org, base), escape(org["name"])))
        o.append("</div>")
    o.append("</div></header>")

    # ---- in-page nav
    sections = [("glance", "At a glance", "information-outline"),
                ("criteria", "MDIP criteria", "shield-check"),
                ("licensing", "Licensing", "scale-balance")]
    if spec["adoption_tier_label"] or spec["adopters_count"] or spec["adopters_registry"]:
        sections.append(("adoption", "Adoption", "account-group"))
    if spec["maintainers"]:
        sections.append(("maintainers", "Maintainers", "domain"))
    o.append('<nav class="spec-nav" aria-label="On this page"><ul>')
    for sid, label, ico in sections:
        o.append('<li><a href="#%s">%s<span>%s</span></a></li>' % (sid, icon(ico), escape(label)))
    o.append("</ul></nav>")

    o.append('<div class="spec-body">')

    # ---- at a glance
    o.append('<section class="spec-section" id="glance">')
    o.append('<h2 class="spec-h2">%s<span>At a glance</span></h2>' % icon("information-outline"))
    o.append('<dl class="glance">')
    o.append(dl_row("routes", "Mode", " ".join(
        '<span class="tag tag--mode">%s</span>' % escape(m) for m in spec["modes"])))
    o.append(dl_row("shield-check", "MDIP status",
                    pill(spec["status_tone"], spec["status_label"])
                    + '<span class="glance__note">%d of %d criteria met</span>'
                      % (spec["criteria_met"], spec["criteria_total"])))
    o.append(dl_row("account-check", "Adoption confirmed by maintainer",
                    pill(spec["confirmed_tone"], spec["confirmed_label"])))
    if spec["lifecycle_label"]:
        o.append(dl_row("chart-timeline-variant", "Lifecycle",
                        '<span class="tag">%s</span><span class="glance__note">%s</span>'
                        % (escape(spec["lifecycle_label"]), escape(spec["lifecycle_hint"] or ""))))
    if spec["adoption_tier_label"]:
        o.append(dl_row("account-group", "Adoption",
                        '<span class="tag">%s</span>' % escape(spec["adoption_tier_label"])))
    if spec["first_release_year"]:
        o.append(dl_row("calendar-blank", "First release",
                        "<strong>%d</strong>" % spec["first_release_year"]))
    o.append(dl_row("scale-balance", "Licence", " ".join(
        '<span class="tag tag--lic tag--lic-%s">%s</span>'
        % (escape(l["category"]), escape(l["id"] if l["id"] != "Other" else l["name"]))
        for l in spec["licences"])))
    if spec["homepage_url"]:
        o.append(dl_row("web", "Homepage",
                        '<a href="%s" rel="noopener">%s%s</a>'
                        % (escape(spec["homepage_url"]), escape(spec["homepage_url"]),
                           icon("open-in-new"))))
    o.append('<div class="glance__row"><dt>%s<span>Registry id</span></dt>'
             '<dd><code>%s</code></dd></div>' % (icon("tag-outline"), escape(spec["id"])))
    o.append("</dl></section>")

    # ---- criteria
    o.append('<section class="spec-section" id="criteria">')
    o.append('<h2 class="spec-h2">%s<span>MDIP criteria</span><span class="spec-h2__n">%s</span>'
             "</h2>" % (icon("shield-check"),
                        meter(spec["criteria_met"], spec["criteria_total"])))
    o.append('<div class="crits">')
    for c in spec["criteria"]:
        # Reasoning worth reading is folded away, because five open rationales
        # is a wall of text and the verdict alone answers the question most
        # readers arrive with. A rationale that only restates the verdict is
        # dropped instead of folded, so a row never offers a disclosure that
        # opens onto the word "Yes"; its evidence link sits in the row.
        reasoning = "" if is_restatement(c["rationale"]) else c["rationale"]
        foldable = bool(reasoning)
        o.append('<%s class="crit crit--%s">'
                 % ("details" if foldable else "div", escape(c["tone"])))
        o.append('<%s class="crit__head">' % ("summary" if foldable else "div"))
        o.append('<span class="crit__icon">%s</span>'
                 % icon(TONE_ICON.get(c["tone"], "help-circle")))
        o.append('<span class="crit__title"><span class="crit__label">%s</span>'
                 '<span class="crit__blurb">%s</span></span>'
                 % (escape(c["label"]), escape(c["blurb"])))
        o.append('<span class="crit__verdict">%s</span>' % pill(c["tone"], c["verdict_label"]))
        if foldable:
            o.append('<span class="crit__chev">%s</span>' % icon("chevron-down"))
        elif c["evidence_url"]:
            o.append('<span class="crit__src">%s</span>'
                     % ext_link(c["evidence_url"], "Source", cls="srclink--crit"))
        o.append("</%s>" % ("summary" if foldable else "div"))
        if foldable:
            o.append('<div class="crit__body">')
            o.append(paras(reasoning, "crit__rationale"))
            if c["evidence_url"]:
                o.append(ext_link(c["evidence_url"], "Source", cls="srclink--crit"))
            o.append("</div>")
        o.append("</%s>" % ("details" if foldable else "div"))
    o.append("</div>")
    o.append(render_rules(data))
    o.append("</section>")

    # ---- licensing
    o.append('<section class="spec-section" id="licensing">')
    o.append('<h2 class="spec-h2">%s<span>Licensing</span></h2>' % icon("scale-balance"))
    o.append('<div class="lics">')
    for lic in spec["licences"]:
        o.append('<article class="lic lic--%s">' % escape(lic["category"]))
        o.append('<div class="lic__head">')
        # Short id as the heading, full name underneath: the ids are what the
        # cards and the licence filter use, and a long CC name would otherwise
        # wrap and strand the external-link icon on its own line.
        short = lic["id"] if lic["id"] != "Other" else lic["name"]
        if lic["url"]:
            o.append('<h3><a href="%s" rel="noopener"><span>%s</span>%s</a></h3>'
                     % (escape(lic["url"]), escape(short), icon("open-in-new")))
        else:
            o.append("<h3><span>%s</span></h3>" % escape(short))
        if lic["scopes"]:
            o.append('<span class="lic__scopes">%s</span>' % " ".join(
                '<span class="tag tag--scope">%s</span>' % escape(SCOPE_LABEL[s])
                for s in lic["scopes"]))
        o.append("</div>")
        if lic["name"] != short:
            o.append('<p class="lic__name">%s</p>' % escape(lic["name"]))
        if lic["note"]:
            o.append('<p class="lic__note">%s%s</p>'
                     % (icon("information-outline"), escape(lic["note"])))
        o.append("</article>")
    o.append("</div>")
    for url in spec["licence_evidence"]:
        o.append('<p class="lic__evidence">%s</p>' % ext_link(url, "Licence text"))
    o.append("</section>")

    # ---- adoption
    if spec["adoption_tier_label"] or spec["adopters_count"] or spec["adopters_registry"]:
        o.append('<section class="spec-section" id="adoption">')
        o.append('<h2 class="spec-h2">%s<span>Adoption</span></h2>' % icon("account-group"))
        o.append('<dl class="glance">')
        if spec["adoption_tier_label"]:
            o.append(dl_row("counter", "Adoption tier",
                            '<span class="tag">%s</span>' % escape(spec["adoption_tier_label"])))
        o.append(dl_row("account-check", "Confirmed by maintainer",
                        pill(spec["confirmed_tone"], spec["confirmed_label"])))
        if spec["adopters_count"]:
            note = ""
            if spec["adopters_count_updated"]:
                note = ('<span class="glance__note">as of %s</span>'
                        % escape(spec["adopters_count_updated"]))
            o.append(dl_row("counter", "Known adopters",
                            "<strong>%d</strong>%s" % (spec["adopters_count"], note)))
        if spec["adopters_registry"]:
            o.append(dl_row("database-outline", "Adopters registry",
                            ext_link(spec["adopters_registry"], "Open registry")))
        o.append("</dl></section>")

    # ---- maintainers
    if spec["maintainers"]:
        o.append('<section class="spec-section" id="maintainers">')
        o.append('<h2 class="spec-h2">%s<span>Maintainers</span></h2>' % icon("domain"))
        o.append('<div class="orgs">')
        for org in spec["maintainers"]:
            o.append('<article class="orgcard">%s<div class="orgcard__t">'
                     "<h3>%s</h3><p>%s</p>" % (org_logo(org, base), escape(org["name"]),
                                               escape(org["type_label"])))
            if org["url"]:
                o.append('<a href="%s" rel="noopener">%s%s</a>'
                         % (escape(org["url"]), escape(short_url(org["url"])),
                            icon("open-in-new")))
            o.append("</div></article>")
        o.append("</div>")

        related = [s for s in data["specs"]
                   if s["id"] != spec["id"]
                   and set(s["maintainer_ids"]) & set(spec["maintainer_ids"])]
        if related:
            o.append('<div class="related"><h3>%s<span>Also maintained by these organizations'
                     "</span></h3><ul>" % icon("source-branch"))
            for r in sorted(related, key=lambda s: s["short_name"].lower()):
                o.append('<li><a href="%s">%s%s<span>%s</span></a></li>'
                         % (escape("../" + r["slug"] + "/"),
                            icon(TONE_ICON.get(r["status_tone"], "help-circle"),
                                 "related__i related__i--" + r["status_tone"]),
                            "", escape(r["short_name"])))
            o.append("</ul></div>")
        o.append("</section>")

    o.append("</div>")  # body

    o.append(render_contribute(data, spec))

    o.append("</div>")
    return "\n".join(o)


SCOPE_LABEL = spec_data.LICENCE_SCOPES


def short_url(url):
    u = url.split("://", 1)[-1]
    return u[:-1] if u.endswith("/") else u


# --------------------------------------------------------------------------
# MkDocs entry point
# --------------------------------------------------------------------------

INDEX_META = """---
title: Specifications
description: >-
  Open mobility specifications assessed by the MDIP coalition against five
  criteria for openness: cost, documentation, maintainer independence,
  governance and release process.
robots: noindex
search:
  exclude: true
hide:
  - navigation
  - toc
---

"""

DETAIL_META = """---
title: %(title)s
description: %(description)s
robots: noindex
search:
  exclude: true
hide:
  - navigation
  - toc
---

"""


def _one_line(text):
    return " ".join((text or "").split())


def _collapse(html):
    """Keep the payload free of blank lines.

    Python-Markdown ends a raw HTML block at the first blank line, so a stray
    "\\n\\n" inside a value from the CSV would make the rest of
    the page render as escaped markup.
    """
    out = []
    for line in html.split("\n"):
        if line.strip():
            out.append(line)
    return "\n".join(out)


def on_files(files, config):
    data = spec_data.build_dataset()

    for issue in data["issues"]:
        log("specifications: %s in %s: %s"
            % (issue["level"], issue["where"], issue["detail"][:160]))

    index = INDEX_META + _collapse(render_index(data, "../"))
    files.append(File.generated(config, SECTION + "/index.md", content=index))

    for spec in data["specs"]:
        title = spec["short_name"]
        desc = _one_line(spec["function"] or spec["full_name"] or title)
        if len(desc) > 300:
            desc = desc[:297].rstrip() + "..."
        head = DETAIL_META % {
            "title": json.dumps(title),
            "description": json.dumps(desc),
        }
        body = _collapse(render_detail(spec, data, "../../"))
        files.append(File.generated(
            config, "%s/%s.md" % (SECTION, spec["slug"]), content=head + body))

    for path, text in spec_api.build_api(data, config.get("site_url")).items():
        files.append(File.generated(config, path, content=text))

    return files


def log(message):
    import logging
    logging.getLogger("mkdocs.hooks.specifications").warning(message)
