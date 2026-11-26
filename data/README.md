# MDIP specification registry data

These files are the source of truth for the `/specifications` pages of the
site and for the read-only API under `/api/`. They are kept on GitHub so that
every change is proposed, reviewed and recorded in public. Nothing under
`/specifications` or `/api` is edited by hand: both are generated from this
folder on every build.

| Path | What it holds |
| --- | --- |
| [`specifications/<id>.md`](specifications/) | One file per specification |
| [`organizations/<id>.md`](organizations/) | One file per organization |
| [`principles.csv`](principles.csv) | The assessment criteria and what earns each verdict |
| [`licences.csv`](licences.csv) | The licence ids a specification may use |

## How to contribute

- **Change an entry**: on the specification's page, "Suggest a change" makes
  the page editable. Each value gets an edit button with a control that only
  offers valid values, and values that depend on each other follow along (a
  criterion that is not compliant makes the status not compliant, for
  example). The change is sent as a pre-filled issue
  ([`specification-edit.yml`](../.github/ISSUE_TEMPLATE/specification-edit.yml))
  showing what changes and the same change as YAML for the file. It is kept
  in the browser until it is sent, so signing in or creating a GitHub account
  does not lose it. Without JavaScript, the button opens the file in GitHub's
  editor instead.
- **Add a specification**: "Propose a specification" opens
  `/specifications/new/`, a blank page in the same editor. It sends the whole
  new file, named after the registry id, as an issue.
- **Report a problem or ask a question**: open a
  [change request](https://github.com/MobilityData/Mobility-Data-Interoperability-Principles/issues/new?template=specification-change.yml).

Run `make specs-check` before pushing a change made locally; the same check
runs on every pull request and fails on any value, or any key, it does not
recognise. A change is published once it is merged into `main`.

## File format

Each entry is a Markdown file: YAML front matter between two `---` lines for
the structured fields, then a `# Description` section in Markdown.

- The file name is the id, and part of the page URL
  (`/specifications/<id>/`). Use lower case, with words joined by `-` or `_`,
  and do not rename a file without a reason.
- Leave a field out, or empty, when it is not known.
- Put a URL or a date in quotes only if your editor insists; both are read
  either way. Dates are `YYYY-MM-DD`.
- Text that spans several lines uses a YAML block (`rationale: |`) followed by
  the indented lines.

### `specifications/<id>.md`

```yaml
---
short_name: GTFS Schedule
full_name: General Transit Feed Specification Schedule
homepage_url: https://gtfs.org/
status: compliant
modes: [public_transport]
maintainers: [mobilitydata]
licences:
- id: Apache-2.0
  scopes: [specification]
- id: CC-BY-3.0
  scopes: [documentation]
first_release_year: 2006
adoption:
  lifecycle: active
  tier: hundred_plus
  data_producers_count: 2950
  data_consumers_count: 40
  adopters_count_updated: '2026-09-29'
  data_producers_registry_url: https://mobilitydatabase.org/feeds?gtfs=true
  confirmed_by_maintainer: true
  history:
  - date: '2024-01-15'
    data_producers: 2400
    data_consumers: 25
principles:
  cost_restriction_free:
    verdict: compliant
    rationale: Apache 2.0
    evidence_url: https://github.com/google/transit
  # ... one block per principle in principles.csv
---

# Description

Travel information: Transit schedules, geography, fares.
```

| Field | Values |
| --- | --- |
| `short_name` | Required. |
| `full_name` | Free text. |
| `homepage_url` | URL. |
| `status` | The coalition's overall finding: `compliant`, `partially_compliant`, `not_compliant`, `inactive` or `under_review`. |
| `modes` | Any of `public_transport`, `microtransit_drt`, `taxi_ridehail`, `bicycle`, `bikeshare`, `shared_scooter`, `carsharing`, `pedestrian_accessibility`, `parking`. Empty shows as "Unclassified". |
| `maintainers` | Organization ids: file names in `organizations/`. |
| `licences` | A list of licences, each with an `id` from `licences.csv` and optional `scopes`: `specification`, `documentation`, `code`, `data`. Empty means no licence is stated. |
| `licence_evidence_url` | URL of the licence text, when it is not the licence's own page. |
| `first_release_year` | Four-digit year. |
| `adoption.lifecycle` | `active`, `early_adoption`, `pilot_adoption`, `pre_adoption` or `inactive`. |
| `adoption.tier` | `hundred_plus`, `early`, `pilot` or `none`. |
| `adoption.data_producers_count` | Whole number of known data producers (organizations that publish data in the format). |
| `adoption.data_consumers_count` | Whole number of known data consumers (applications or organizations that use the data). Known adopters, as shown on the site, are both counts added up. |
| `adoption.adopters_count_updated` | Date the counts were taken. |
| `adoption.data_producers_registry_url` | URL of a public list of data producers. |
| `adoption.data_consumers_registry_url` | URL of a public list of data consumers. |
| `adoption.history` | Past counts that the repository's history does not record, or records wrongly: a list of rows with `date` (`YYYY-MM-DD`), `data_producers` and `data_consumers` (0 when left out). Each date appears once. See [Adoption history](#adoption-history). |
| `adoption.confirmed_by_maintainer` | `true` or `false`; leave out when unknown. |
| `principles.<id>.verdict` | One block per principle in `principles.csv`: `compliant`, `partially_compliant`, `not_compliant`, `unknown` or `not_assessed` (the default when left out). |
| `principles.<id>.rationale` | Why the verdict was given. Published as written. |
| `principles.<id>.evidence_url` | URL supporting the verdict. |
| `# Description` | What the specification is for, in Markdown. Its first paragraph is the summary in the registry list. |

### Adoption history

The chart under "Adoption" on a specification page is built from three
layers, each replacing the one before for a date they share:

1. The repository's git history: every committed change to the counts is a
   point, dated by `adopters_count_updated` (or by the commit when it is
   missing). Files written before data consumers were counted apart have one
   `adopters_count`; it is read as data producers.
2. The counts in the file as it is now.
3. The rows of `adoption.history`, to add dates the repository does not know
   about or to correct a count that was wrong when it was committed.

In the page editor, "Adopters history" opens these points as a table: type
over a value to correct it, add a row, or import a CSV file with the columns
`date,data_producers,data_consumers` (comma, semicolon or tab separated; a
single count column is read as data producers). A CSV value for a date
already in the table overwrites it. The newest row becomes the current count,
and only rows that differ from what git records are written to the file.

`make specs-check` warns, without failing, when `status` disagrees with the
verdicts: `compliant` when every principle is compliant, `not_compliant` when
any principle is not compliant, and `partially_compliant` otherwise. `status`
is still published as recorded, because it is the coalition's decision.

### `organizations/<id>.md`

```yaml
---
name: MobilityData
type: nonprofit
roles: [specification_maintainer]
url: https://mobilitydata.org/
logo_url: https://mobilitydata.org/.../logo.png
---

# Description
```

| Field | Values |
| --- | --- |
| `name` | Required. Full name. |
| `short_name` | Optional shorter name for compact places such as filters. |
| `type` | `standards-body`, `nonprofit`, `government`, `industry-consortium`, `academic`, `company`, `community` or `individual`. |
| `roles` | The organization's roles in the registry. Today only `specification_maintainer`. |
| `url` | Home page. |
| `logo_url` | Link to the organization's logo online. When it is empty, or the image does not load, the site shows the organization's initials instead. |
| `# Description` | Optional, in Markdown. |

## `principles.csv`

Each `principle` row is one criterion of an open standard in the MDIP
[definition](../docs/en/definitions.md#open_standard). Every specification
file has a `principles.<id>` block for each of them.

| Column | Meaning |
| --- | --- |
| `id` | Criterion id, used as the key under `principles:` in specification files. |
| `kind` | `principle`, `bonus` or `adoption`. The last two only feed the ranking below. |
| `order` | Display order. |
| `name`, `definition` | What the criterion is. |
| `compliant_when`, `partially_compliant_when`, `not_compliant_when` | What earns each verdict. Shown under "MDIP criteria" on every specification page. |
| `compliant_score`, `partially_compliant_score`, `not_compliant_score` | Points used by the ranking. |

## Ranking

The registry lists specifications with the most known adopters
(data producers plus data consumers) first. Those without a count follow, ordered by a
ranking score. The score only decides that order: it is not shown on the site
and not published in the API.

| Criterion | Points |
| --- | --- |
| Each of the five principles | +1 compliant, 0 partially compliant, -1 not compliant. `unknown` and `not_assessed` count 0. |
| Fully compliant | +1 when all five principles are compliant, otherwise 0. |
| Adoption | +1 for `hundred_plus`, 0 for `early` or `pilot`, -1 for `none`. No tier counts 0. |

The maximum is 7. A specification with no assessed principle sorts after
every assessed one. Ties are broken by status, then by name.
`make specs-check` prints the resulting order with each score.

## `licences.csv`

| Column | Values |
| --- | --- |
| `id` | Licence id, used in specification files. Use the [SPDX id](https://spdx.org/licenses/) where one exists. |
| `name` | Full name. |
| `category` | `open`, `restricted` (published openly but with a limiting clause), `closed` (purchase or membership required) or `unknown`. |
| `url` | Licence text. |
| `note` | Optional short explanation shown with the licence. |

## API

Every build publishes the joined data as static files under
`https://interoperablemobility.org/api/`. `make specs-export` writes the same
files to `generated/api/` without building the site.

| File | Contents |
| --- | --- |
| `index.json` | The endpoints and every vocabulary with its labels. |
| `catalogue.json` | One short record per specification, in display order. |
| `specifications.json` | Every specification with its organizations, licences and verdicts joined in. |
| `specifications/<id>.json` | One specification. |
| `organizations.json` | Organizations, with the specifications each one maintains. |
| `principles.json` | The criteria and what earns each verdict. |
| `licences.json` | The licence list. |
| `export.csv` | Every specification as one flat table. |
| `openapi.json` | OpenAPI 3 description of every file above. |
| `docs/` | Interactive documentation (Swagger UI) for `openapi.json`. Not indexed by search engines. |
