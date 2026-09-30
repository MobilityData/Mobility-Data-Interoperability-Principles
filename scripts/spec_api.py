"""The registry's read-only JSON API, written as static files at build time.

`build_api` takes the joined dataset from spec_data.build_dataset() and
returns {published path: text}. The MkDocs hook publishes those files under
/api/, and `make specs-export` writes the same files to a local folder.

    api/index.json                   what is here, and the vocabularies
    api/catalogue.json               one short record per specification
    api/specifications.json          every specification, fully joined
    api/specifications/<id>.json     one specification
    api/organizations.json           organizations and what they maintain
    api/principles.json              the assessment criteria and their rules
    api/licences.json                the licence list
    api/export.csv                   every specification as one flat table
    api/openapi.json                 OpenAPI 3 description of all of the above
    api/docs/                        Swagger UI page for openapi.json (not indexed)

The ranking score is deliberately not published: it only orders the listing.
"""

from __future__ import annotations

import csv
import datetime as _dt
import io
import json

import spec_data

API_DIR = "api"
API_VERSION = 1


def _page(site_url, spec):
    return "%sspecifications/%s/" % (site_url, spec["slug"])


def _api(site_url, path):
    return "%s%s/%s" % (site_url, API_DIR, path)


def _source(path):
    return spec_data.github_url("blob", path)


def _org_ref(org):
    return {"id": org["id"], "name": org["name"], "short_name": org["short"]}


def full_record(spec, site_url):
    return {
        "id": spec["id"],
        "short_name": spec["short_name"],
        "full_name": spec["full_name"] or None,
        "description": spec["description"] or None,
        "homepage_url": spec["homepage_url"],
        "status": {"id": spec["status"], "label": spec["status_label"]},
        "modes": spec["mode_ids"],
        "maintainers": [dict(_org_ref(o), type=o["type"], url=o["url"])
                        for o in spec["maintainers"]],
        "licences": [{"id": l["id"], "name": l["name"], "category": l["category"],
                      "url": l["url"], "scopes": l["scopes"]} for l in spec["licences"]],
        "licence_evidence_urls": spec["licence_evidence"],
        "first_release_year": spec["first_release_year"],
        "adoption": {
            "lifecycle": spec["lifecycle"],
            "tier": spec["adoption_tier"],
            "adopters_count": spec["adopters_count"],
            "adopters_count_updated": spec["adopters_count_updated"],
            "adopters_registry_url": spec["adopters_registry"],
            "confirmed_by_maintainer": {"yes": True, "no": False}.get(spec["confirmed"]),
        },
        "principles": [{"id": c["key"], "name": c["label"], "verdict": c["verdict"],
                        "rationale": c["rationale"] or None,
                        "evidence_url": c["evidence_url"]} for c in spec["criteria"]],
        "principles_met": spec["criteria_met"],
        "page_url": _page(site_url, spec),
        "source_url": _source(spec["source_path"]),
    }


def catalogue_record(spec, site_url):
    return {
        "id": spec["id"],
        "short_name": spec["short_name"],
        "full_name": spec["full_name"] or None,
        "summary": spec["function"] or None,
        "status": spec["status"],
        "modes": spec["mode_ids"],
        "maintainers": [_org_ref(o) for o in spec["maintainers"]],
        "licences": [l["id"] for l in spec["licences"]],
        "lifecycle": spec["lifecycle"],
        "adoption_tier": spec["adoption_tier"],
        "adopters_count": spec["adopters_count"],
        "page_url": _page(site_url, spec),
        "detail_url": _api(site_url, "specifications/%s.json" % spec["id"]),
    }


def export_csv(records):
    """One row per specification; lists are joined with "; "."""
    cols = ["id", "short_name", "full_name", "status", "modes", "maintainer_ids",
            "maintainer_names", "licences", "homepage_url", "first_release_year",
            "lifecycle", "adoption_tier", "adopters_count", "adopters_count_updated",
            "adopters_registry_url", "confirmed_by_maintainer"]
    principle_ids = [p["id"] for p in records[0]["principles"]] if records else []
    for pid in principle_ids:
        cols += [pid + "_verdict", pid + "_rationale", pid + "_evidence_url"]
    cols += ["description", "page_url", "source_url"]

    buf = io.StringIO()
    w = csv.DictWriter(buf, cols, lineterminator="\n")
    w.writeheader()
    for r in records:
        a = r["adoption"]
        row = {
            "id": r["id"], "short_name": r["short_name"], "full_name": r["full_name"],
            "status": r["status"]["id"], "modes": "; ".join(r["modes"]),
            "maintainer_ids": "; ".join(m["id"] for m in r["maintainers"]),
            "maintainer_names": "; ".join(m["name"] for m in r["maintainers"]),
            "licences": "; ".join(
                l["id"] + (" (%s)" % ", ".join(l["scopes"]) if l["scopes"] else "")
                for l in r["licences"] if l["id"] != "Unspecified"),
            "homepage_url": r["homepage_url"], "first_release_year": r["first_release_year"],
            "lifecycle": a["lifecycle"], "adoption_tier": a["tier"],
            "adopters_count": a["adopters_count"],
            "adopters_count_updated": a["adopters_count_updated"],
            "adopters_registry_url": a["adopters_registry_url"],
            "confirmed_by_maintainer": {True: "yes", False: "no"}.get(
                a["confirmed_by_maintainer"], "unknown"),
            "description": r["description"], "page_url": r["page_url"],
            "source_url": r["source_url"],
        }
        for p in r["principles"]:
            row[p["id"] + "_verdict"] = p["verdict"]
            row[p["id"] + "_rationale"] = p["rationale"]
            row[p["id"] + "_evidence_url"] = p["evidence_url"]
        w.writerow(row)
    return buf.getvalue()


def _enum(vocab):
    return {"type": "string", "enum": list(vocab)}


def _nullable(schema):
    return dict(schema, nullable=True)


def openapi(site_url):
    """OpenAPI 3.0 description of the files build_api publishes.

    Enums are read from the vocabularies in spec_data, so the documentation
    cannot drift from what the validator accepts.
    """
    V = spec_data
    s, i, url = {"type": "string"}, {"type": "integer"}, {"type": "string", "format": "uri"}
    ref = lambda name: {"$ref": "#/components/schemas/" + name}                  # noqa: E731
    arr = lambda item: {"type": "array", "items": item}                          # noqa: E731
    envelope = {"api_version": i, "generated": dict(s, format="date")}

    def obj(props, required=()):
        out = {"type": "object", "properties": props}
        if required:
            out["required"] = list(required)
        return out

    schemas = {
        "OrganizationRef": obj({"id": s, "name": s, "short_name": s}, ("id", "name")),
        "Licence": obj({"id": s, "name": s, "category": _enum(V.LICENCE_CATEGORIES),
                        "url": _nullable(url), "note": _nullable(s)}, ("id", "name", "category")),
        "SpecificationLicence": obj({"id": s, "name": s, "category": _enum(V.LICENCE_CATEGORIES),
                                     "url": _nullable(url),
                                     "scopes": arr(_enum(V.LICENCE_SCOPES))}),
        "PrincipleVerdict": obj({"id": s, "name": s, "verdict": _enum(V.VERDICT),
                                 "rationale": _nullable(s), "evidence_url": _nullable(url)},
                                ("id", "verdict")),
        "Adoption": obj({
            "lifecycle": _nullable(_enum(V.LIFECYCLE)),
            "tier": _nullable(_enum(V.ADOPTION_TIER)),
            "adopters_count": _nullable(i),
            "adopters_count_updated": _nullable(dict(s, format="date")),
            "adopters_registry_url": _nullable(url),
            "confirmed_by_maintainer": _nullable({"type": "boolean"}),
        }),
        "CatalogueRecord": obj({
            "id": s, "short_name": s, "full_name": _nullable(s), "summary": _nullable(s),
            "status": _enum(V.STATUS), "modes": arr(_enum(V.MODES)),
            "maintainers": arr(ref("OrganizationRef")), "licences": arr(s),
            "lifecycle": _nullable(_enum(V.LIFECYCLE)),
            "adoption_tier": _nullable(_enum(V.ADOPTION_TIER)),
            "adopters_count": _nullable(i), "page_url": url, "detail_url": url,
        }, ("id", "short_name", "status")),
        "Specification": obj({
            "id": s, "short_name": s, "full_name": _nullable(s),
            "description": dict(_nullable(s), description="Markdown."),
            "homepage_url": _nullable(url),
            "status": obj({"id": _enum(V.STATUS), "label": s}),
            "modes": arr(_enum(V.MODES)),
            "maintainers": arr(obj({"id": s, "name": s, "short_name": s,
                                    "type": _enum(V.ORG_TYPES), "url": _nullable(url)})),
            "licences": arr(ref("SpecificationLicence")),
            "licence_evidence_urls": arr(url),
            "first_release_year": _nullable(i),
            "adoption": ref("Adoption"),
            "principles": arr(ref("PrincipleVerdict")),
            "principles_met": i,
            "page_url": url,
            "source_url": dict(url, description="The entry's file on GitHub."),
        }, ("id", "short_name", "status", "principles")),
        "Organization": obj({
            "id": s, "name": s, "short_name": s, "type": _enum(V.ORG_TYPES),
            "roles": arr(_enum(V.ORG_ROLES)), "url": _nullable(url), "logo_url": _nullable(url),
            "description": _nullable(s), "specifications": arr(s), "source_url": url,
        }, ("id", "name", "type")),
        "Principle": obj({"id": s, "order": i, "name": s, "definition": s,
                          "compliant_when": s, "partially_compliant_when": s,
                          "not_compliant_when": s}, ("id", "name")),
    }

    def get(summary, description, schema, tag, media="application/json", params=None):
        op = {"summary": summary, "description": description, "tags": [tag],
              "responses": {"200": {"description": "OK",
                                    "content": {media: {"schema": schema}}}}}
        if params:
            op["parameters"] = params
        return {"get": op}

    order = "Specifications are listed in the registry's display order: most known adopters first."
    paths = {
        "/index.json": get("Endpoints and vocabularies",
                           "Every endpoint, and each vocabulary with its labels.",
                           obj(dict(envelope, description=s, order=s,
                                    endpoints={"type": "object", "additionalProperties": url},
                                    vocabularies={"type": "object"})), "Registry"),
        "/catalogue.json": get("Catalogue", "One short record per specification. " + order,
                               obj(dict(envelope, count=i,
                                        specifications=arr(ref("CatalogueRecord")))),
                               "Specifications"),
        "/specifications.json": get("All specifications",
                                    "Every specification with its organizations, licences and "
                                    "verdicts joined in. " + order,
                                    obj(dict(envelope, count=i,
                                             specifications=arr(ref("Specification")))),
                                    "Specifications"),
        "/specifications/{id}.json": get(
            "One specification", "A single specification, fully joined.",
            obj(dict(envelope, specification=ref("Specification"))), "Specifications",
            params=[{"name": "id", "in": "path", "required": True, "schema": s,
                     "description": "Specification id, for example gtfs-schedule.",
                     "example": "gtfs-schedule"}]),
        "/organizations.json": get("Organizations",
                                   "Organizations, with the ids of the specifications each one "
                                   "maintains.",
                                   obj(dict(envelope, organizations=arr(ref("Organization")))),
                                   "Organizations"),
        "/principles.json": get("Principles", "The MDIP criteria and what earns each verdict.",
                                obj(dict(envelope, principles=arr(ref("Principle")))),
                                "Methodology"),
        "/licences.json": get("Licences", "The licences specifications may be released under.",
                              obj(dict(envelope, licences=arr(ref("Licence")))), "Methodology"),
        "/export.csv": get("Full export (CSV)",
                           "Every specification as one flat table, one row per specification. "
                           "Lists are joined with \"; \". " + order,
                           dict(s, format="csv"), "Specifications", media="text/csv"),
    }

    return {
        "openapi": "3.0.3",
        "info": {
            "title": "MDIP specification registry API",
            "version": str(API_VERSION),
            "description": (
                "Read-only, static API of the MDIP specification registry. Every file is "
                "regenerated from the registry's source files on GitHub at each build of the "
                "site; there is no authentication and no rate limit. To change the data, edit "
                "the source files: %s" % spec_data.github_url("tree", "data")),
        },
        "externalDocs": {"description": "Data format and contribution guide",
                         "url": spec_data.github_url("blob", "data/README.md")},
        "servers": [{"url": site_url + API_DIR}],
        "tags": [{"name": n} for n in ("Specifications", "Organizations", "Methodology",
                                       "Registry")],
        "paths": paths,
        "components": {"schemas": schemas},
    }


# Swagger UI for openapi.json. A standalone page rather than a site page, so
# the explorer gets the full width; it asks search engines not to index it,
# like the rest of the registry while it is unlisted.
DOCS_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>MDIP specification registry API</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
<style>
  body { margin: 0; background: #fff; }
  .mdip-api-bar { padding: 12px 20px; background: #1b58a4; font: 600 14px/1.4 system-ui, sans-serif; }
  .mdip-api-bar a { color: #fff; text-decoration: none; }
</style>
</head>
<body>
<div class="mdip-api-bar"><a href="../../specifications/">&larr; MDIP specification registry</a></div>
<div id="swagger-ui"></div>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
  window.ui = SwaggerUIBundle({
    url: "../openapi.json",
    dom_id: "#swagger-ui",
    deepLinking: true,
    tryItOutEnabled: true
  });
</script>
</body>
</html>
"""


def _json(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


def build_api(data, site_url):
    """Return {published path: text} for every API file."""
    site_url = (site_url or "/").rstrip("/") + "/"
    specs = data["specs"]
    records = [full_record(s, site_url) for s in specs]
    generated = _dt.date.today().isoformat()
    envelope = {"api_version": API_VERSION, "generated": generated}

    maintained = {}
    for s in specs:
        for mid in s["maintainer_ids"]:
            maintained.setdefault(mid, []).append(s["id"])

    files = {}
    files["catalogue.json"] = _json(dict(envelope, count=len(specs), specifications=[
        catalogue_record(s, site_url) for s in specs]))
    files["specifications.json"] = _json(dict(envelope, count=len(records),
                                              specifications=records))
    for r in records:
        files["specifications/%s.json" % r["id"]] = _json(dict(envelope, specification=r))
    files["organizations.json"] = _json(dict(envelope, organizations=[{
        "id": o["id"], "name": o["name"], "short_name": o["short"], "type": o["type"],
        "roles": o["roles"], "url": o["url"], "logo_url": o["logo_url"],
        "description": o["description"] or None,
        "specifications": maintained.get(o["id"], []),
        "source_url": _source(o["source_path"]),
    } for o in data["organizations"].values()]))
    files["principles.json"] = _json(dict(envelope, principles=[{
        "id": p["key"], "order": p["order"], "name": p["label"], "definition": p["blurb"],
        "compliant_when": p["when"]["compliant"],
        "partially_compliant_when": p["when"]["partially_compliant"],
        "not_compliant_when": p["when"]["not_compliant"],
    } for p in data["criteria"]]))
    files["licences.json"] = _json(dict(envelope, licences=list(data["licences"].values())))
    files["export.csv"] = export_csv(records)
    files["openapi.json"] = _json(openapi(site_url))

    files["index.json"] = _json(dict(envelope, description=(
        "Read-only API of the MDIP specification registry. Generated from the files in "
        "%s on every build." % spec_data.github_url("tree", "data")),
        order="catalogue.json and specifications.json list specifications in the "
              "registry's display order: most known adopters first.",
        endpoints=dict((path, _api(site_url, path)) for path in sorted(files)
                       if not path.startswith("specifications/")),
        documentation=_api(site_url, "docs/"),
        vocabularies={
            "status": dict((k, v["label"]) for k, v in spec_data.STATUS.items()),
            "verdict": dict((k, v["label"]) for k, v in spec_data.VERDICT.items()),
            "modes": dict(spec_data.MODES),
            "lifecycle": dict((k, v["label"]) for k, v in spec_data.LIFECYCLE.items()),
            "adoption_tier": dict((k, v["label"]) for k, v in spec_data.ADOPTION_TIER.items()),
            "organization_type": dict(spec_data.ORG_TYPES),
            "organization_role": dict(spec_data.ORG_ROLES),
            "licence_category": dict(spec_data.LICENCE_CATEGORIES),
            "licence_scope": dict(spec_data.LICENCE_SCOPES),
        }))
    files["docs/index.html"] = DOCS_HTML
    return dict((API_DIR + "/" + k, v) for k, v in files.items())
